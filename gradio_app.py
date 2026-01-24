import os
import uuid
import gradio as gr
import edge_tts
from groq import Groq
from supabase import create_client
import io
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

load_dotenv()

DB_URI = os.getenv("DATABASE_URL")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- NEW: Import your cloud utilities from your existing agent logic ---
from agent_configs import (get_agent, log_to_postgres)
from spotify import launch_spotify_before_agent

agent = get_agent()

pool = ConnectionPool(conninfo=DB_URI, min_size=1, max_size=10)

# --- DATABASE FUNCTIONS FOR SESSION MANAGEMENT ---
def get_db_connection():
    """Create a database connection from DATABASE_URL"""
    return psycopg2.connect(DB_URI)

def fetch_all_sessions():
    """Fetch unique thread_ids with their latest timestamp from the checkpoints table."""
    try:
        # 1. Borrow a connection from the pool
        with pool.connection() as conn:
            # Use dict_row so we can access columns by name: row['thread_id']
            with conn.cursor(row_factory=dict_row) as cur:
                
                # 2. SQL to get the absolute LATEST checkpoint for each unique thread
                # We sort by thread_id first for DISTINCT ON, then by ts for the latest record
                cur.execute("""
                    SELECT DISTINCT ON (thread_id) 
                        thread_id, 
                        checkpoint->>'ts' as ts
                    FROM checkpoints 
                    WHERE thread_id IS NOT NULL 
                    ORDER BY thread_id, checkpoint->>'ts' DESC
                """)
                
                rows = cur.fetchall()

        # 3. Process the results
        session_data = []
        for row in rows:
            raw_ts = row['ts']
            thread_id = row['thread_id']
            
            # Format the timestamp for the UI (e.g., "Jan 24, 21:13")
            try:
                dt = datetime.fromisoformat(raw_ts.replace('Z', '+00:00'))
                readable_date = dt.strftime("%b %d, %H:%M")
            except:
                readable_date = "Unknown Date"
                
            session_data.append({
                "thread_id": thread_id,
                "timestamp": readable_date,
                "raw_ts": raw_ts # Keep raw for sorting
            })

        # 4. Final sort: most recent chat at the top
        session_data.sort(key=lambda x: x['raw_ts'], reverse=True)
        
        return session_data if session_data else [{"thread_id": "New Session", "timestamp": ""}]

    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
        return [{"thread_id": "New Session", "timestamp": ""}]

def load_session_history(thread_id: str):
    with pool.connection() as conn:
        saver = PostgresSaver(conn)
        config = {"configurable": {"thread_id": thread_id}}
        
        # This might return a CheckpointTuple OR a dict
        result = saver.get(config)
        
        if not result:
            return []

        # FIX: Check if result is a dictionary or an object with a .checkpoint attr
        if isinstance(result, dict):
            checkpoint_data = result
        else:
            checkpoint_data = result.checkpoint

        # The actual state data lives in 'channel_values'
        channel_values = checkpoint_data.get("channel_values", {})
        
        # Look for your messages (usually 'messages', but check your State definition)
        raw_messages = channel_values.get("messages", [])
        
        history = []
        for msg in raw_messages:
            # Standard LangChain message mapping
            role = "user" if msg.type == "human" else "assistant"
            history.append({"role": role, "content": msg.content})

        #print(history)    
        return history

async def upload_to_supabase(audio_path, thread_id, turn_index): # Add turn_index here   
    try:
        filename = f"user_{turn_index}.mp3" 
        cloud_path = f"{thread_id}/{filename}"
        
        if not os.path.exists(audio_path): return None
        
        print(f"📤 Uploading User Turn {turn_index} to {cloud_path}...")
        
        with open(audio_path, 'rb') as f:
            supabase.storage.from_("agent_audio_logs").upload(
                path=cloud_path, 
                file=f,
                file_options={"content-type": "audio/mpeg", "upsert": "true"} # Use upsert to avoid 400 errors
            )
        
        response = supabase.storage.from_("agent_audio_logs").get_public_url(cloud_path)
        return response
        
    except Exception as e:
        print(f"❌ Supabase upload error: {e}")
        return None
    

async def process_interaction(message, history, thread_id_state):
    # Guard against None message (empty send or incomplete recording)
    if message is None:
        return history, thread_id_state
    
    user_text = message.get("text", "").strip()
    user_files = message.get("files", [])
    
    # Prevent sending empty messages (no text and no audio files)
    if not user_text and not user_files:
        return history, thread_id_state
    
    # Persist thread_id across the entire conversation
    if thread_id_state is None or thread_id_state == "":
        thread_id = f"sess_{uuid.uuid4().hex[:6]}"
    else:
        thread_id = thread_id_state
    
    # This determines if this is turn 0, 1, 2, etc.
    current_turn = len(history) // 2
    is_voice_input = len(user_files) > 0

    audio_path = None
    user_audio_url = None
    assistant_audio_url = None

    try:
        # --- STEP 1: USER INPUT ---
        if is_voice_input:
            audio_path = user_files[0] 
            
            # 1. UPLOAD USER AUDIO (Only call this ONCE)
            # Pass current_turn here
            user_audio_url = await upload_to_supabase(audio_path, thread_id, current_turn)
            
            # 2. Transcribe via Groq
            with open(audio_path, "rb") as f:
                transcription = groq_client.audio.transcriptions.create(
                    file=f,
                    model="whisper-large-v3-turbo",
                    response_format="text"
                )
            user_text = transcription
            
            # 3. LOG USER DATA
            await log_to_postgres(thread_id, "user", user_text, user_audio_url)

            # Add text and audio player (HTML) for browser-side playback
            if user_audio_url:
                audio_html = f"<audio controls controlsList='nofullscreen' style='width:100%; margin-bottom:10px;'><source src='{user_audio_url}' type='audio/mpeg'></audio>"
                history.append({"role": "user", "content": f"{audio_html}\n{user_text}"})
            else:
                history.append({"role": "user", "content": user_text})
        else:
            history.append({"role": "user", "content": user_text})

        # --- STEP 2: AGENT LOGIC ---
        config = {"configurable": {"thread_id": thread_id}}
        result = agent.invoke({"messages": [{"role": "user", "content": user_text}]}, config)
        
        if isinstance(result, dict) and "messages" in result:
            last_msg = result["messages"][-1].content
            response_text = last_msg[0]['text'] if isinstance(last_msg, list) else last_msg
        else:
            response_text = str(result)

        # --- STEP 3: ASSISTANT OUTPUT ---
        if is_voice_input:
            try:
                # USE current_turn HERE to match the user's file index
                filename = f"assistant_{current_turn}.mp3" 
                cloud_path = f"{thread_id}/{filename}"
                
                communicate = edge_tts.Communicate(response_text, "en-US-AndrewNeural", rate="+15%")
                audio_buffer = io.BytesIO()
                
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio" and "data" in chunk:
                        audio_buffer.write(chunk["data"])
                
                supabase.storage.from_("agent_audio_logs").upload(
                    path=cloud_path, 
                    file=audio_buffer.getvalue(),
                    file_options={"content-type": "audio/mpeg", "upsert": "true"}
                )

                assistant_audio_url = supabase.storage.from_("agent_audio_logs").get_public_url(cloud_path)

            except Exception as e:
                print(f"❌ Error generating/uploading assistant audio: {e}")
            
            await log_to_postgres(thread_id, "assistant", response_text, assistant_audio_url)
            
            # Use HTML audio player for responsive browser-side playback
            if assistant_audio_url:
                audio_html = f"<audio controls autoplay controlsList='nofullscreen' style='width:100%; margin-top:10px;'><source src='{assistant_audio_url}' type='audio/mpeg'></audio>"
                history.append({"role": "assistant", "content": f"{response_text}\n\n{audio_html}"})
            else:
                history.append({"role": "assistant", "content": response_text})
        else:
            history.append({"role": "assistant", "content": response_text})

    except Exception as e:
        print(f"Error in process_interaction: {e}")
        history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})

    return history, thread_id


# --- UI Definition remains largely the same ---
with gr.Blocks() as demo:

    with gr.Sidebar():
        gr.Markdown("## 🎧 DJ Spot History")
        
        # Fetch available sessions on startup
        available_sessions = fetch_all_sessions()
        
        session_list = gr.Radio(
            choices=available_sessions, 
            value="New Session", 
            label="Recent Chats"
        )
        
        def start_new_session():
            """Create a fresh session"""
            return "New Session", [{"role": "assistant", "content": "👋 Hello I am your friendly neighborhood DJ Spot!"}], ""
        
        def load_selected_session(selected_session):
            """Load a selected session's history"""
            if selected_session == "New Session":
                return [{"role": "assistant", "content": "👋 Hello I am your friendly neighborhood DJ Spot!"}], ""
            else:
                # Extract thread_id if selected_session is a dict
                if isinstance(selected_session, dict):
                    thread_id = selected_session.get("thread_id")
                else:
                    thread_id = selected_session
                
                history = load_session_history(thread_id)
                if not history:
                    history = [{"role": "assistant", "content": "👋 Hello I am your friendly neighborhood DJ Spot!"}]
                return history, thread_id
        
        new_btn = gr.Button("➕ Start New Mix", variant="primary")

    gr.Markdown("<h1 style='text-align: center; color: black;'>DJ Spot 🎧</h1>")
    
    # Persist thread_id across the entire conversation session
    thread_id_state = gr.State("")
    
    chatbot = gr.Chatbot(
        value=[{"role": "assistant", "content": "👋 Hello I am your friendly neighborhood DJ Spot!"}],
        height=600,
    )
    chat_input = gr.MultimodalTextbox(
        interactive=True,
        placeholder="Type a message or use the mic (auto-sends)...",
        sources=["microphone"],
        show_label=False
    )

    # Wire up button to start new session
    new_btn.click(
        start_new_session,
        outputs=[session_list, chatbot, thread_id_state]
    )
    
    # Wire up session selection to load that session
    session_list.change(
        load_selected_session,
        inputs=[session_list],
        outputs=[chatbot, thread_id_state]
    )

    chat_input.submit(process_interaction, [chat_input, chatbot, thread_id_state], [chatbot, thread_id_state])
    chat_input.submit(lambda: None, None, chat_input)

# Define the JavaScript logic
shortcut_js = """
(function() {
    console.log("🎧 DJ Spot: Controller Active");

    // Hide volume slider on all audio elements
    const hideVolumeControl = () => {
        const style = document.createElement('style');
        style.textContent = `
            audio::-webkit-media-controls-volume-slider { display: none; }
            audio::-webkit-media-controls-volume-slider-container { display: none; }
            audio::-moz-media-controls-volume-control { display: none; }
        `;
        document.head.appendChild(style);
    };
    hideVolumeControl();

    const handleKey = (e) => {
        const key = e.key.toLowerCase();
        const inputTextArea = document.querySelector('textarea[data-testid="textbox"]');
        
        // 1. Alt+M: Toggle Recording
        if (e.altKey && key === 'm') {
            e.preventDefault();
            const stopBtn = document.querySelector('button[aria-label="Stop recording"]');
            const micBtn = document.querySelector('button[data-testid="microphone-button"]');
            
            if (stopBtn) {
                console.log("⏹️ Stopping recording...");
                stopBtn.click();
            } else if (micBtn) {
                console.log("🎤 Starting recording...");
                if (inputTextArea) inputTextArea.focus();
                micBtn.click();
            }
        }

        // 2. Alt+R: Delete Recording
        if (e.altKey && key === 'r') {
            e.preventDefault();
            const cancelBtn = document.querySelector('button[aria-label="Clear audio"]');
            if (cancelBtn) {
                cancelBtn.click();
                console.log("🗑️ Recording Deleted.");
            }
        }

        // 3. Enter: Send Audio or Text
        if (e.key === 'Enter' && !e.shiftKey) {
            const sendBtn = document.querySelector('button[aria-label="Send"], button.submit-button, button[type="submit"]');
            
            // Check if there's content: either text in the box or a waveform on screen
            const hasText = inputTextArea && inputTextArea.value.trim().length > 0;
            const hasAudio = document.querySelector('button[aria-label="Clear audio"]') !== null;

            if ((hasText || hasAudio) && sendBtn) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log("📤 Sending...");
                sendBtn.click();
                
                // Clear focus and refocus to reset the UI state
                if (inputTextArea) {
                    inputTextArea.blur();
                    setTimeout(() => inputTextArea.focus(), 50);
                }
            }
        }
    };

    // Use 'keydown' with capture (true) to intercept Enter before Gradio handles it
    window.addEventListener('keydown', handleKey, true);
    console.log("✅ Keyboard shortcuts initialized");
})();
"""

if __name__ == "__main__":
    launch_spotify_before_agent()
    demo.launch(
        js=shortcut_js,
        theme=gr.themes.Monochrome(),
    ) 