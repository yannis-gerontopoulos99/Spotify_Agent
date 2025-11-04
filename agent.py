from langchain.agents import create_agent
from deepagents import create_deep_agent
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
    model="gemini-2.5-flash",
    api_key=api_key,
    temperature=0,
)

agent = create_deep_agent(model, tools=tools, checkpointer=InMemorySaver(),
        system_prompt= """You are DJ Spot, a helpful and swaggy Spotify assistant. 
You can use the Spotify app and the provided tools to navigate playback and perform actions based on user requests. 
You can handle multiple requests at once. 

When a user asks for multiple actions, follow these rules:
1. Think carefully before acting.
2. Evaluate which tools you have and which sequence of steps makes sense.
3. Perform actions step by step, in a logical order.
    - For example, if the user says "Play a Harry Styles song and start it from 20 seconds," first call the 'play_song' tool, then call the 'seek_to' tool.
    - If the user asks to "skip" then "seek," always call 'next_song' first, then 'seek_to'.
4. Wait for each tool’s response before invoking the next.
5. Confirm successful completion of each action when appropriate.

Use a friendly, swaggy tone, but be concise. Always keep the user informed of what you are doing.
""")

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
            
            # Extract response handling both formats
            if isinstance(result, dict) and "messages" in result:
                last_message = result["messages"][-1].content
                if isinstance(last_message, list):
                    response = last_message[0]['text'] if last_message else ""
                else:
                    response = last_message
            else:
                response = str(result)
                
            print("Assistant:", response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            print("Assistant: Sorry, I encountered an error. Starting a fresh conversation...")
            thread_counter += 1
            config = {"configurable": {"thread_id": str(thread_counter)}}
            logger.info(f"Switched to new thread: {thread_counter}")
except KeyboardInterrupt:
    print("\nGoodbye!")
