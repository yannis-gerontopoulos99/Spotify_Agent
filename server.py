from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from dotenv import load_dotenv
from logger import setup_logger
from datetime import datetime

load_dotenv()
logger = setup_logger()

app = Flask(__name__)
CORS(app)

# Store active chat sessions (in production, use database)
chat_sessions = {}

@app.route('/chat/new', methods=['POST'])
def new_chat():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        'id': session_id,
        'created_at': datetime.now().isoformat(),
        'messages': [],
        'title': 'New Chat'
    }
    return jsonify({'session_id': session_id})

@app.route('/chat/sessions', methods=['GET'])
def get_chat_sessions():
    """Get all previous chat sessions"""
    sessions = list(chat_sessions.values())
    return jsonify({'sessions': sessions})

@app.route('/chat/<session_id>', methods=['GET'])
def get_chat_session(session_id):
    """Get specific chat session"""
    if session_id not in chat_sessions:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(chat_sessions[session_id])

@app.route('/chat/<session_id>', methods=['POST'])
def chat(session_id):
    """Send message in a chat session"""
    try:
        if session_id not in chat_sessions:
            return jsonify({'error': 'Session not found'}), 404
            
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Use session_id as thread_id for consistent agent memory
        result = process_agent_message(message, session_id)
        
        # Store message in session
        chat_sessions[session_id]['messages'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        chat_sessions[session_id]['messages'].append({
            'role': 'assistant',
            'content': result,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update chat title from first message
        if len(chat_sessions[session_id]['messages']) == 2:
            chat_sessions[session_id]['title'] = message[:50]
        
        return jsonify({'message': result, 'session_id': session_id})
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<session_id>', methods=['DELETE'])
def delete_chat(session_id):
    """Delete a chat session"""
    if session_id not in chat_sessions:
        return jsonify({'error': 'Session not found'}), 404
    del chat_sessions[session_id]
    return jsonify({'success': True})

def process_agent_message(text, thread_id):
    # Import and run agent logic from agent.py
    from agent import get_postgres_saver
    from agent_tools import spotify_agent_tools
    from langchain_mistralai import ChatMistralAI
    import os
    from langchain.agents import create_agent
    #from deepagents import create_deep_agent
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_mistralai import ChatMistralAI
    from langchain.agents.middleware import (ModelFallbackMiddleware, PIIMiddleware,)
    from spotify import launch_spotify_before_agent

    #result = launch_spotify_before_agent()
    
    #if result is None:
    #    return
    
    api_key = os.getenv("MISTRAL_API_KEY")
    model = ChatMistralAI(model="mistral-medium-latest", api_key=api_key, temperature=0.5)
    tools = spotify_agent_tools
    checkpointer = get_postgres_saver()
    
    fallback_model_1 = ChatMistralAI(
        model="mistral-small-latest",
        api_key=api_key,
        temperature=0.5,
    )

    fallback_model_2 = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )
    
    agent = create_agent(
        model, 
        tools=tools, 
        checkpointer=checkpointer,
        middleware=[
            PIIMiddleware(
                "api_key",
                detector=r"(sk|rk|pk)-[a-zA-Z0-9]{20,}",
                strategy="block",
            ),
            ModelFallbackMiddleware(fallback_model_1, fallback_model_2),
        ],
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
        # Use session_id as thread_id for consistency
        config = {"configurable": {"thread_id": thread_id}}
        
        result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
        
        if isinstance(result, dict) and "messages" in result:
            last_message = result["messages"][-1].content
            return last_message if isinstance(last_message, str) else str(last_message[0]['text'])
        return str(result)
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return "Sorry, I encountered an error."

if __name__ == '__main__':
    app.run(debug=True, port=5000)