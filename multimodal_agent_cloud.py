import os
import uuid
import asyncio
import sounddevice as sd
import soundfile as sf
import edge_tts
import psycopg
import vertexai
from psycopg.rows import dict_row
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client

# LangGraph & LangChain Imports
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.middleware import ModelFallbackMiddleware, PIIMiddleware

# Your local imports
from agent_tools import spotify_agent_tools
from spotify import launch_spotify_before_agent
from deepagents import create_deep_agent 

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_PROJECT_ID"),
    location=os.getenv("LOCATION"),
)

# INITIALIZE CLOUD CLIENTS
DB_URI = os.getenv("DATABASE_URL")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# AGENT SETUP WITH MIDDLEWARE
def get_agent():
    conn_kwargs = {"autocommit": True, "row_factory": dict_row}
    conn = psycopg.connect(DB_URI, **conn_kwargs)
    checkpointer = PostgresSaver(conn)

    # Define Models
    primary_model = ChatMistralAI(
        model="mistral-small-latest", 
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.5
    )
    
    fallback_1 = ChatMistralAI(
        model="mistral-large-latest", 
        api_key=os.getenv("MISTRAL_API_KEY")
    )
    
    fallback_2 = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    return create_deep_agent(
        primary_model, 
        tools=spotify_agent_tools, 
        checkpointer=checkpointer,
        middleware=[
            # PII Redaction for API Keys
            PIIMiddleware(
                "api_key", 
                detector=r"(sk|rk|pk)-[a-zA-Z0-9]{20,}", 
                strategy="block"
            ),
            # Model Fallback Chain
            ModelFallbackMiddleware(fallback_1, fallback_2),
        ],
        system_prompt=(
            """
            You are DJ Spot, a swaggy Spotify assistant. Handle multi-step requests by using the available tools.

            When a user asks for an action:
            1. Call the appropriate tool(s) to accomplish the task
            2. After tools complete, provide a brief, cool response summarizing what you did
            3. Include relevant details from the tool output (song name, artist, current track info, etc.)

            For multi-step requests like "play next and show song details":
            - First call next_track()
            - Then call current_user_playing_track() to get the new track details
            - Combine the results into one response

            When requesting a song search or to be played, always confirm the exact song name and artist in your response,
            to avoid playing songs with different artists.
            Keep responses brief, casual, and always include the actual results (song names, artists, etc.) from the tools.
            Always respond with something - never return empty or blank messages.
            Answer requests only regarding Spotify and music.
            """
        )
    )

async def log_to_postgres(thread_id, role, text, audio_url=None):
    url_to_save = audio_url if audio_url is not None else "" 
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audio_logs (thread_id, role, transcript, audio_url) VALUES (%s, %s, %s, %s)",
                (thread_id, role, text, url_to_save)
            )

async def speak_and_upload(text, thread_id):
    filename = f"dj_{thread_id}.mp3"
    try:
        # A. TTS
        communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="+15%")
        await communicate.save(filename)
        
        # B. Supabase Upload
        cloud_path = f"{thread_id}/{filename}"
        with open(filename, 'rb') as f:
            supabase.storage.from_("agent_audio_logs").upload(path=cloud_path, file=f)
        
        public_url = supabase.storage.from_("agent_audio_logs").get_public_url(cloud_path)

        # C. Log & Play
        await log_to_postgres(thread_id, "assistant", text, public_url)
        data, fs = sf.read(filename)
        sd.play(data, fs)
        sd.wait()
    finally:
        if os.path.exists(filename): os.remove(filename)

def record_and_transcribe():
    fs, seconds = 44100, 5
    print("Listening...")
    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()
    temp_input = "user_input.wav"
    sf.write(temp_input, audio, fs)
    
    with open(temp_input, "rb") as file:
        transcription = groq_client.audio.transcriptions.create(
            file=(temp_input, file.read()),
            model="whisper-large-v3",
        )
    os.remove(temp_input)
    return transcription.text

# --- Main Execution Loop ---

async def main():
    launch_spotify_before_agent()
    agent = get_agent()
    thread_id = f"sess_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\nDJ Spot is Live!")

    while True:
        user_raw = input("\nUser (Press Enter for Voice, or type): ").strip()
        if user_raw.lower() in ['q', 'quit']: break

        mode = "text" 
        if user_raw == "": 
            mode = "voice"
            user_raw = record_and_transcribe()
            print(f"You said: {user_raw}")

        await log_to_postgres(thread_id, "user", user_raw)

        # Agent invocation triggers the Fallback and PII middleware automatically
        result = agent.invoke({"messages": [{"role": "user", "content": user_raw}]}, config)
        response_text = result["messages"][-1].content
        print(f"DJ Spot: {response_text}")

        if mode == "voice":
            await speak_and_upload(response_text, thread_id)
        else:
            await log_to_postgres(thread_id, "assistant", response_text)

if __name__ == "__main__":
    asyncio.run(main())