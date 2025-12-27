import os
import uuid
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import base64

# Import your agent logic
from multimodal_agent_cloud import get_agent, log_to_postgres, speak_and_upload, record_and_transcribe, groq_client
from spotify import launch_spotify_before_agent

load_dotenv()

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Init agent once
launch_spotify_before_agent()
dj_spot_agent = get_agent()

@app.route('/chat/new', methods=['POST'])
def new_chat():
    """Create a new session ID for the frontend"""
    session_id = f"sess_{uuid.uuid4().hex[:6]}"
    return jsonify({'session_id': session_id})

async def speak_and_upload_for_web(text, thread_id):
    """Generate TTS audio and upload to Supabase, then log to database"""
    import edge_tts
    from multimodal_agent_cloud import supabase
    
    filename = f"reply_{uuid.uuid4().hex[:6]}.mp3"
    cloud_path = f"{thread_id}/{filename}"
    
    try:
        # Generate TTS
        communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="+15%")
        await communicate.save(filename)
        
        # Upload to Supabase
        with open(filename, 'rb') as f:
            supabase.storage.from_("agent_audio_logs").upload(path=cloud_path, file=f)
        
        public_url = supabase.storage.from_("agent_audio_logs").get_public_url(cloud_path)
        
        # Log assistant response with URL
        await log_to_postgres(thread_id, "assistant", text, public_url)
        
        if os.path.exists(filename):
            os.remove(filename)
        
        return public_url
    except Exception as e:
        app.logger.error(f"Error in speak_and_upload_for_web: {e}")
        # Still log the response even if audio generation fails
        await log_to_postgres(thread_id, "assistant", text, None)
        raise

@app.route('/chat/<session_id>', methods=['POST'])
def chat(session_id):
    """Primary endpoint for Text interactions"""
    try:
        data = request.json
        user_text = data.get('message', '')
        mode = data.get('mode', 'text')

        if not user_text:
            return jsonify({'error': 'No message provided'}), 400

        # 1. Log User Message to Postgres
        asyncio.run(log_to_postgres(session_id, "user", user_text))

        # 2. Invoke Agent (this executes the action like playing music)
        config = {"configurable": {"thread_id": session_id}}
        result = dj_spot_agent.invoke(
            {"messages": [{"role": "user", "content": user_text}]}, 
            config
        )
        response_text = result["messages"][-1].content
        app.logger.info(f"Agent response: {response_text}")

        # 3. Generate Audio Response & Upload (wait for completion)
        audio_url = asyncio.run(speak_and_upload_for_web(response_text, session_id))
        app.logger.info(f"Audio URL generated: {audio_url}")

        # 4. Return complete response after everything is done
        return jsonify({
            'message': response_text,
            'session_id': session_id,
            'audio_url': audio_url
        })

    except Exception as e:
        app.logger.error(f"Chat Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Fetch conversation history from Postgres"""
    import psycopg
    from psycopg.rows import dict_row
    
    DB_URI = os.getenv("DATABASE_URL")
    try:
        with psycopg.connect(DB_URI, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, transcript, audio_url, created_at FROM audio_logs WHERE thread_id = %s ORDER BY created_at ASC",
                    (session_id,)
                )
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/interact/<session_id>', methods=['POST'])
def audio_interaction(session_id):
    """Receives base64 audio from the frontend"""
    try:
        data = request.json
        audio_b64 = data.get('audio')
        
        if not audio_b64:
            return jsonify({'error': 'No audio data provided'}), 400

        app.logger.info(f"Received audio for session {session_id}")

        # 1. Decode and Save Temporary Audio File
        temp_filename = f"input_{session_id}.wav"
        try:
            with open(temp_filename, "wb") as f:
                f.write(base64.b64decode(audio_b64))
            app.logger.info(f"Audio file saved: {temp_filename}")
        except Exception as e:
            app.logger.error(f"Failed to decode audio: {e}")
            return jsonify({'error': 'Failed to decode audio'}), 400

        try:
            # 2. Transcribe using Groq Whisper
            with open(temp_filename, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_filename, file.read()),
                    model="whisper-large-v3",
                )
            user_text = transcription.text
            app.logger.info(f"Transcribed: {user_text}")
        except Exception as e:
            app.logger.error(f"Transcription failed: {e}")
            return jsonify({'error': 'Transcription failed'}), 500
        finally:
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        if not user_text:
            return jsonify({'error': 'Could not transcribe audio'}), 400

        # 3. Log user transcript
        asyncio.run(log_to_postgres(session_id, "user", user_text))
        app.logger.info(f"User message logged to database")

        # 4. Invoke Agent (this executes actions like playing music)
        try:
            config = {"configurable": {"thread_id": session_id}}
            result = dj_spot_agent.invoke(
                {"messages": [{"role": "user", "content": user_text}]}, 
                config
            )
            response_text = result["messages"][-1].content
            app.logger.info(f"Agent response: {response_text}")
        except Exception as e:
            app.logger.error(f"Agent invocation failed: {e}")
            return jsonify({'error': 'Agent failed to respond'}), 500

        # 5. Generate Audio Response & Upload (wait for completion before returning)
        try:
            audio_url = asyncio.run(speak_and_upload_for_web(response_text, session_id))
            app.logger.info(f"Audio generated and uploaded: {audio_url}")
        except Exception as e:
            app.logger.error(f"Audio generation failed: {e}")
            # If audio fails, still return the text response
            asyncio.run(log_to_postgres(session_id, "assistant", response_text, None))
            audio_url = None

        # 6. Return complete response ONLY after everything is done
        return jsonify({
            'user_said': user_text,
            'assistant_said': response_text,
            'audio_url': audio_url,
            'session_id': session_id
        })

    except Exception as e:
        app.logger.error(f"Audio Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/all-conversations', methods=['GET'])
def get_all_conversations():
    """Fetch all unique conversations with summary"""
    import psycopg
    from psycopg.rows import dict_row
    
    DB_URI = os.getenv("DATABASE_URL")
    try:
        with psycopg.connect(DB_URI, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        thread_id as session_id,
                        (array_agg(transcript ORDER BY created_at ASC))[1] as first_message,
                        COUNT(*) as message_count,
                        MAX(created_at) as last_message_time
                    FROM audio_logs
                    GROUP BY thread_id
                    ORDER BY last_message_time DESC
                """)
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/delete/<session_id>', methods=['DELETE'])
def delete_conversation(session_id):
    """Delete all messages in a conversation"""
    import psycopg
    
    DB_URI = os.getenv("DATABASE_URL")
    try:
        with psycopg.connect(DB_URI) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM audio_logs WHERE thread_id = %s",
                    (session_id,)
                )
            conn.commit()
        return jsonify({'success': True, 'message': 'Conversation deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use threaded=True or a production server like Gunicorn to handle async
    app.run(debug=True, port=5000, threaded=True)