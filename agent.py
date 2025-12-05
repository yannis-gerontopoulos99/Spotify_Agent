from langchain.agents import create_agent
from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver  
import os
from logger import setup_logger
from dotenv import load_dotenv
from agent_tools import spotify_agent_tools
from spotify import launch_spotify_before_agent

logger = setup_logger()
load_dotenv()

def main():
    # Run Spotify initialization first
    result = launch_spotify_before_agent()
    
    if result is None:
        return
    
    # Continue with agent
    api_key = os.getenv("GOOGLE_API_KEY")
    tools = spotify_agent_tools
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        temperature=0,
    )
    
    agent = create_agent(
        model, 
        tools=tools, 
        checkpointer=InMemorySaver(),
        system_prompt="""You are DJ Spot, a swaggy Spotify assistant. Handle multi-step requests by using the available tools.

When a user asks for an action:
1. Call the appropriate tool(s) to accomplish the task
2. After tools complete, provide a brief, cool response summarizing what you did
3. Include relevant details from the tool output (song name, artist, current track info, etc.)

For multi-step requests like "play next and show song details":
- First call next_track()
- Then call current_user_playing_track() to get the new track details
- Combine the results into one response

Keep responses brief, casual, and always include the actual results (song names, artists, etc.) from the tools.
Always respond with something - never return empty or blank messages."""
    )
    
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


if __name__ == "__main__":
    main()