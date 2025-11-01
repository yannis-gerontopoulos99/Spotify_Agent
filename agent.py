from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver  
import os
from logger import setup_logger
from dotenv import load_dotenv
from agent_tools import spotify_agent_tools

logger = setup_logger()
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

tools = spotify_agent_tools

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    api_key=api_key,
    temperature=0,
)

agent = create_agent(model, tools=tools, checkpointer=InMemorySaver(),
        system_prompt= """You are a helpful Spotify assistant. You can use the Spotify app and tools
        provied to navigate the app and perform actions based on the user requests.
        Your name is DJ Spot.""")

config = {"configurable": {"thread_id": "1"}}

try:
    thread_counter = 1
    config = {"configurable": {"thread_id": str(thread_counter)}}
    
    print("Hello I am your friendly neighborhood DJ Spot!")
    print("\nType 'q', 'quit' or 'exit' to exit this conversation.")
    
    while True:
        text = input("\nUser: ")
        if text.lower() in ["quit", "exit", "q"]:
            break
        
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": text}]},
                config
            )
            
            resposne = (
                result["messages"][-1].content
                if isinstance(result, dict) and "messages" in result
                else str(result)
            )
            
            print("Assistant:", resposne)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            print("Assistant: Sorry, I encountered an error. Starting a fresh conversation...")
            thread_counter += 1
            config = {"configurable": {"thread_id": str(thread_counter)}}
            logger.info(f"Switched to new thread: {thread_counter}")
except KeyboardInterrupt:
    print("\nGoodbye!")
