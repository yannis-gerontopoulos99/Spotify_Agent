import os
import psycopg
import vertexai
from psycopg.rows import dict_row
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# LangGraph & LangChain Imports
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.middleware import ModelFallbackMiddleware, PIIMiddleware

# Your local imports
from agent_tools import spotify_agent_tools
from langchain.agents import create_agent
from deepagents import create_deep_agent 

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_PROJECT_ID"),
    location=os.getenv("LOCATION"),
)

DB_URI = os.getenv("DATABASE_URL")

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

    return create_agent(
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

# Create a global pool (put this outside your functions)
# min_size=1 keeps a connection ready, max_size=10 handles concurrent Gradio users
pool = ConnectionPool(conninfo=DB_URI, min_size=1, max_size=10)

async def log_to_postgres(thread_id, role, transcript, audio_url=None):
    """Logs conversation to Postgres using a connection pool to avoid 'too many connections' error."""
    try:
        # Use the pool to get a connection
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audio_logs (thread_id, role, transcript, audio_url, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (thread_id, role, transcript, audio_url)
                )
            # Connection is automatically returned to the pool here, not closed
            conn.commit()
    except Exception as e:
        print(f"Postgres Logging Error: {e}")