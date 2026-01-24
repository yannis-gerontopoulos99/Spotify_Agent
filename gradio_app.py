import os
import uuid
import gradio as gr
import edge_tts
from groq import Groq
from supabase import create_client
import io
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json

load_dotenv()

DB_URI = os.getenv("DATABASE_URL")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- NEW: Import your cloud utilities from your existing agent logic ---
from agent_configs import (get_agent, log_to_postgres)
from spotify import launch_spotify_before_agent

agent = get_agent()

# --- DATABASE FUNCTIONS FOR SESSION MANAGEMENT ---
def get_db_connection():
    """Create a database connection from DATABASE_URL"""
    return psycopg2.connect(DB_URI)

def fetch_all_sessions():
    """Fetch all session IDs from the langchain checkpoints table, ordered by most recent timestamp"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Query to get distinct thread_ids with their most recent checkpoint
        cur.execute("""
            SELECT DISTINCT ON (thread_id) thread_id, checkpoint
            FROM checkpoints 
            WHERE thread_id IS NOT NULL 
            ORDER BY (checkpoint->>'ts') DESC
            LIMIT 5
        """)
        sessions = cur.fetchall()
        cur.close()
        conn.close()
        
        # Sort sessions by timestamp in descending order (most recent first)
        session_list = []
        session_data = []
        
        for session in sessions:
            try:
                checkpoint_data = session['checkpoint']
                if isinstance(checkpoint_data, str):
                    checkpoint_data = json.loads(checkpoint_data)
                
                ts = checkpoint_data.get('ts', '1970-01-01T00:00:00+00:00')
                session_data.append((session['thread_id'], ts))
            except Exception as e:
                print(f"Error parsing session timestamp: {e}")
                session_data.append((session['thread_id'], '1970-01-01T00:00:00+00:00'))
        
        # Sort by timestamp descending (most recent first)
        session_data.sort(key=lambda x: x[1], reverse=True)
        session_list = [s[0] for s in session_data]
        
        return session_list if session_list else ["New Session"]
    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
        return ["New Session"]

def load_session_history(thread_id):
    """Load chat history for a specific session from LangGraph checkpoints"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to get all checkpoints for the thread, ordered by timestamp
        cur.execute("""
            SELECT checkpoint FROM checkpoints 
            WHERE thread_id = %s 
            ORDER BY (checkpoint->>'ts') ASC
        """, (thread_id,))
        
        checkpoints = cur.fetchall()
        cur.close()
        conn.close()
        
        history = []
        seen_messages = set()  # Track messages we've already added to avoid duplicates
        
        print(f"🔍 Loading {len(checkpoints)} checkpoints for thread {thread_id}")
        
        # Parse the checkpoint data to extract messages from channel_values
        for idx, checkpoint_row in enumerate(checkpoints):
            try:
                # The checkpoint column might be already parsed as dict or a JSON string
                checkpoint_data = checkpoint_row['checkpoint']
                
                # If it's a string, parse it; if it's already a dict, use it as is
                if isinstance(checkpoint_data, str):
                    checkpoint_data = json.loads(checkpoint_data)
                elif not isinstance(checkpoint_data, dict):
                    continue
                
                print(f"\n📋 Checkpoint {idx}: Keys = {list(checkpoint_data.keys())}")
                
                # Extract messages from channel_values
                if 'channel_values' in checkpoint_data:
                    channel_values = checkpoint_data['channel_values']
                    print(f"   channel_values keys: {list(channel_values.keys())}")
                    
                    # Try different locations where messages might be stored
                    messages = None
                    
                    # Try 'messages' key first
                    if 'messages' in channel_values:
                        messages = channel_values['messages']
                        print(f"   Found 'messages' key with {len(messages) if isinstance(messages, list) else 'non-list'} items")
                    
                    # Try other common keys
                    for key in ['__input__', '__output__', 'history', 'chat']:
                        if key in channel_values and messages is None:
                            potential_messages = channel_values[key]
                            print(f"   Checking '{key}': {type(potential_messages)}")
                            if isinstance(potential_messages, list):
                                messages = potential_messages
                    
                    if messages and isinstance(messages, list) and len(messages) > 0:
                        print(f"   Processing {len(messages)} messages...")
                        for msg in messages:
                            try:
                                # Extract content and type
                                content = None
                                msg_type = None
                                
                                if isinstance(msg, dict):
                                    content = msg.get('content', '')
                                    msg_type = msg.get('type', '')
                                    print(f"     Dict message: type={msg_type}, content_len={len(str(content))}")
                                elif hasattr(msg, 'content') and hasattr(msg, 'type'):
                                    content = msg.content
                                    msg_type = msg.type
                                    print(f"     Object message: type={msg_type}, content_len={len(str(content))}")
                                
                                if not content or not msg_type:
                                    continue
                                
                                msg_id = f"{msg_type}_{str(content)[:50]}"  # Simple dedup key
                                
                                # Skip if we've seen this message before
                                if msg_id in seen_messages:
                                    continue
                                seen_messages.add(msg_id)
                                
                                # Determine role from type
                                if msg_type == 'human':
                                    role = 'user'
                                elif msg_type == 'ai':
                                    role = 'assistant'
                                else:
                                    continue
                                
                                history.append({"role": role, "content": str(content)})
                                print(f"     ✅ Added {role} message: {str(content)[:60]}...")
                                
                            except Exception as e:
                                print(f"     Error parsing individual message: {e}")
                                continue
                    else:
                        print(f"   No messages found in this checkpoint")
                else:
                    print(f"   No 'channel_values' in checkpoint")
                    
            except Exception as e:
                print(f"Error parsing checkpoint {idx}: {e}")
                continue
        
        print(f"\n📊 Total messages loaded: {len(history)}")
        return history if history else []
    except Exception as e:
        print(f"❌ Error loading session history: {e}")
        return []

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
                    if chunk["type"] == "audio":
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
        gr.Markdown("## 🎧 DJ Spot Sessions")
        
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
                history = load_session_history(selected_session)
                if not history:
                    history = [{"role": "assistant", "content": "👋 Hello I am your friendly neighborhood DJ Spot!"}]
                return history, selected_session
        
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