from langchain.agents import create_agent
from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver  
import os
import sys
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
    
    agent = create_deep_agent(
        model, 
        tools=tools, 
        checkpointer=InMemorySaver(),
        system_prompt="""You are DJ Spot, a helpful and swaggy Spotify assistant. 
        You can use the Spotify app and the provided tools to navigate playback and perform actions based on user requests. 
        
        IMPORTANT: You can and should use MULTIPLE tools in sequence to complete a user's request.

        When a user asks you to perform multiple actions:
        1. Break down the request into individual actions
        2. Call each required tool in the appropriate order
        3. Wait for each tool to complete before calling the next
        4. Provide a summary of all actions completed

        Examples:
        - "Skip to the next song and turn on shuffle" → Use skip_track tool, then use shuffle tool
        - "Play Jax Jones and start from the 15 second mark" → Use play_artist tool, then use volume tool
        - "Pause the music and show me my devices" → Use pause tool, then use devices tool

        Always execute ALL requested actions, not just the first one.
        
        Use a friendly, swaggy tone, but be concise. Always keep the user informed of what you are doing.
        """
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