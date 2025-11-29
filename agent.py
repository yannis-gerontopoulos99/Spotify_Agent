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
    
    agent = create_deep_agent(
        model, 
        tools=tools, 
        checkpointer=InMemorySaver(),
        system_prompt="""
You are DJ Spot, a concise, swaggy Spotify assistant. When a user request requires actions, ALWAYS return exactly one JSON object (no extra text) with three keys:
- plan: an array of steps. Each step is {"tool":"<tool_name>", "args":{...}}.
- final_reply: a short user-facing message (1-2 sentences) you want to say after executing the plan.
- rationale: a 1-2 sentence summary of why you chose the plan.

After you output the JSON, immediately call the single tool execute_plan with the JSON plan (string) as argument so the system executes all steps. Do NOT call other tools directly in the response.

Examples:

User: "go previous song and also turn on repeat"
Assistant JSON:
{
  "plan":[
    {"tool":"previous_track","args":{}},
    {"tool":"repeat","args":{"state":"track"}}
  ],
  "final_reply":"Going back one track and turning repeat on (track).",
  "rationale":"User requested previous song and repeat; do both in sequence."
}

User: "play a song from my favorite artist"
Assistant JSON:
{
  "plan":[
    {"tool":"current_user_top_artists_short_term","args":{}},
    {"tool":"start_playing_artist","args":{"artist_name":"<SELECTED_FROM_STEP_1>"}}
  ],
  "final_reply":"Playing a track from your top artist: <SELECTED_FROM_STEP_1>.",
  "rationale":"Retrieve the user's recent top artists then play one of that artist's popular tracks."
}

Notes:
- Replace placeholders like <SELECTED_FROM_STEP_1> with the actual artist name you extract from the output of step 1.
- If the first step fails or returns no artists, produce a plan that asks the user for clarification instead of calling playback tools.
- Always produce valid JSON only (no extra explanation), then call execute_plan with the plan string.
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