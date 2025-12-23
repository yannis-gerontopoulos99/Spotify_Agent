import os
import uuid
import asyncio
import sounddevice as sd
import soundfile as sf
import edge_tts
import vertexai
from dotenv import load_dotenv

# API Clients & LangChain
from groq import Groq
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import ModelFallbackMiddleware, PIIMiddleware

# Your local imports
from agent_tools import spotify_agent_tools
from spotify import launch_spotify_before_agent
from langchain.agents import create_agent
from logger import setup_logger

logger = setup_logger()
load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_PROJECT_ID"),
    location=os.getenv("LOCATION"),
)

# Initialize Groq for Whisper
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def record_and_transcribe(thread_id):
    """Records voice locally, transcribes via Groq, and cleans up."""
    temp_wav = f"temp_in_{thread_id}.wav"
    fs, seconds = 16000, 5
    try:
        print("DJ Spot is listening...")
        audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        sf.write(temp_wav, audio, fs)
        
        with open(temp_wav, "rb") as f:
            return groq_client.audio.transcriptions.create(
                file=(temp_wav, f.read()),
                model="whisper-large-v3-turbo",
                response_format="text"
            )
    finally:
        if os.path.exists(temp_wav): os.remove(temp_wav)

async def speak_locally(thread_id, text):
    """TTS Playback with local cleanup."""
    temp_mp3 = f"temp_out_{thread_id}.mp3"
    try:
        communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="+15%")
        await communicate.save(temp_mp3)
        data, fs = sf.read(temp_mp3)
        sd.play(data, fs)
        sd.wait()
    finally:
        if os.path.exists(temp_mp3): os.remove(temp_mp3)

async def main():
    # 1. Initialize Spotify
    result_spot = launch_spotify_before_agent()
    if result_spot is None:
        return

    # 2. Setup Models & Middleware
    api_key = os.getenv("MISTRAL_API_KEY")
    
    # Primary Model
    model = ChatMistralAI(model="mistral-small-latest", api_key=api_key, temperature=0.5)
    
    # Fallbacks
    fallback_1 = ChatMistralAI(model="mistral-small-latest", api_key=api_key, temperature=0.5)
    fallback_2 = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )
    
    # 3. Create Agent
    agent = create_agent(
        model, 
        tools=spotify_agent_tools, 
        checkpointer=InMemorySaver(),
        middleware=[
            PIIMiddleware("api_key", detector=r"(sk|rk|pk)-[a-zA-Z0-9]{20,}", strategy="block"),
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
    
    try:
        thread_id = uuid.uuid4().hex[:4]
        config = {"configurable": {"thread_id": thread_id}}
        print("\nDJ Spot is Live! [ENTER] to speak, [Type] to chat, [q] to quit.")
        
        while True:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            
            is_voice = False
            if user_input == "":
                is_voice = True
                user_input = record_and_transcribe(thread_id)
                print(f"User (Voice): {user_input}")

            try:
                # RUN AGENT
                result = agent.invoke({"messages": [{"role": "user", "content": user_input}]}, config)
                
                # Extract response text
                if isinstance(result, dict) and "messages" in result:
                    last_msg = result["messages"][-1].content
                    response = last_msg[0]['text'] if isinstance(last_msg, list) else last_msg
                else:
                    response = str(result)
                
                print("Assistant:", response)
                
                # Conditional Audio Output
                if is_voice:
                    await speak_locally(thread_id, response)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                print("Assistant: Sorry, I encountered an error. Resetting session...")
                
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    asyncio.run(main())