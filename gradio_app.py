import os
import uuid
import gradio as gr
import edge_tts
from groq import Groq
from supabase import create_client
import io
from dotenv import load_dotenv

load_dotenv()

#DB_URI = os.getenv("DATABASE_URL")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- NEW: Import your cloud utilities from your existing agent logic ---
from agent_configs import (get_agent, log_to_postgres)
from spotify import launch_spotify_before_agent

agent = get_agent()

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
    

async def process_interaction(message, history):
    user_text = message.get("text", "").strip()
    user_files = message.get("files", [])
    
    # This determines if this is turn 0, 1, 2, etc.
    current_turn = len(history) // 2
    is_voice_input = len(user_files) > 0

    thread_id = f"sess_{uuid.uuid4().hex[:6]}" 
    
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

            history.append({"role": "user", "content": gr.Audio(value=audio_path)})
            history.append({"role": "user", "content": f"{user_text}"})
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
            history.append({"role": "assistant", "content": response_text})
            
            if assistant_audio_url:
                history.append({"role": "assistant", "content": gr.Audio(value=assistant_audio_url, autoplay=True)})
        else:
            history.append({"role": "assistant", "content": response_text})

    except Exception as e:
        print(f"Error in process_interaction: {e}")
        history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})

    return history


# --- UI Definition remains largely the same ---
with gr.Blocks() as demo:
    gr.Markdown("<h1 style='text-align: center; color: black;'>DJ Spot 🎧</h1>")
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

    chat_input.submit(process_interaction, [chat_input, chatbot], [chatbot])
    chat_input.submit(lambda: None, None, chat_input)

# JS and launch code...
if __name__ == "__main__":
    launch_spotify_before_agent()
    demo.launch(theme=gr.themes.Monochrome())

# Define the JavaScript logic
shortcut_js = """
(function() {
    console.log("🎧 DJ Spot: Controller Active");

    const handleKey = (e) => {
        const key = e.key.toLowerCase();
        const inputTextArea = document.querySelector('textarea[data-testid="textbox"]');
        
        // 1. Alt+M: Toggle Recording
        if (e.altKey && key === 'm') {
            e.preventDefault();
            const stopBtn = document.querySelector('button[aria-label="Stop recording"]');
            const micBtn = document.querySelector('button[data-testid="microphone-button"]');
            
            if (stopBtn) {
                stopBtn.click();
            } else if (micBtn) {
                if (inputTextArea) inputTextArea.focus();
                micBtn.click();
            }
        }

        // 2. Alt+R: Delete Recording
        if (e.altKey && key === 'r') {
            e.preventDefault();
            const cancelBtn = document.querySelector('button.cancel-button[aria-label="Clear audio"]');
            if (cancelBtn) {
                cancelBtn.click();
                console.log("🗑️ Recording Deleted.");
            }
        }

        // 3. Enter: Send Audio or Text
        if (e.key === 'Enter' && !e.shiftKey) {
            // Find the send button - Gradio often uses 'Submit' or 'Send' labels
            const sendBtn = document.querySelector('button[aria-label="Send"], button.send-button, button.primary-button');
            
            // Check if there's content: either text in the box or a waveform on screen
            const hasText = inputTextArea && inputTextArea.value.trim().length > 0;
            const hasAudio = document.querySelector('.cancel-button[aria-label="Clear audio"]') !== null;

            if ((hasText || hasAudio) && sendBtn) {
                // Prevent default Enter behavior (new line)
                e.preventDefault();
                e.stopPropagation();
                
                console.log("📤 Sending...");
                
                // Clicking the button directly is the most reliable way in Gradio
                sendBtn.click();
                
                // Clear focus and refocus to reset the UI state
                inputTextArea.blur();
                setTimeout(() => inputTextArea.focus(), 50);
            }
        }
    };

    // Use 'keydown' with capture (true) to intercept Enter before Gradio handles it
    window.addEventListener('keydown', handleKey, true);
})();
"""

if __name__ == "__main__":

    launch_spotify_before_agent()

    demo.launch(
        js=shortcut_js,
        theme=gr.themes.Monochrome(),


    ) 