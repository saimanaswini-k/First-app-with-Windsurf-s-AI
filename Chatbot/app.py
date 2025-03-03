from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import random
from datetime import datetime
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chatbotsecret123'
socketio = SocketIO(app)

# Set OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Game state
game_states = {}

def get_gpt_response(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a friendly and helpful AI assistant. You can:
                 1. Answer questions on any topic
                 2. Help with coding and technical problems
                 3. Provide explanations and examples
                 4. Engage in casual conversation
                 5. Tell jokes and share fun facts
                 Be concise, friendly, and use emojis appropriately.
                 If the user asks about the weather, remind them that you don't have access to real-time weather data.
                 If the user asks about personal information, remind them that you're an AI assistant focused on helping with questions and tasks."""},
                {"role": "user", "content": message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error with GPT API: {e}")
        return get_fallback_response(message)

def get_fallback_response(message):
    # Fallback responses when API fails
    responses = {
        "greeting": {
            "patterns": ["hi", "hello", "hey", "greetings"],
            "responses": [
                "Hello! 👋 How can I assist you today?",
                "Hi there! Ready to chat and help! 😊",
                "Hey! Looking forward to our conversation! ✨"
            ]
        },
        "error": {
            "responses": [
                "I'm having trouble connecting to my knowledge base right now. Let me try a simpler response! 🤔",
                "Oops! My advanced features are taking a brief break. I'll help you with my basic knowledge! 💡",
                "Technical hiccup! But I can still chat with you using my basic responses! 🔧"
            ]
        }
    }
    
    for category, data in responses.items():
        if category == "greeting" and any(pattern in message.lower() for pattern in data["patterns"]):
            return random.choice(data["responses"])
    
    return random.choice(responses["error"]["responses"])

def handle_game(message, session_id):
    try:
        guess = int(message)
        game_state = game_states[session_id]
        game_state["attempts"] += 1
        
        if guess == game_state["number"]:
            result = f"🎉 Congratulations! You got it in {game_state['attempts']} attempts! The number was {game_state['number']}!"
            del game_states[session_id]
            return result
        elif guess < game_state["number"]:
            return "Higher! 👆 Try again!"
        else:
            return "Lower! 👇 Try again!"
    except ValueError:
        if message.lower() in ["quit", "exit", "stop"]:
            if session_id in game_states:
                del game_states[session_id]
                return "Game ended. Feel free to start a new game anytime! 🎮"
        return "Please enter a valid number or type 'quit' to end the game! 🎯"

def get_bot_response(message, session_id):
    message = message.lower()
    
    # Check if there's an active game
    if session_id in game_states:
        return handle_game(message, session_id)
    
    # Handle game start command
    if "play game" in message:
        game_states[session_id] = {
            "number": random.randint(1, 100),
            "attempts": 0
        }
        return "Let's play a number guessing game! 🎲\nI'm thinking of a number between 1 and 100. Try to guess it!"
    
    # For all other messages, use GPT
    return get_gpt_response(message)

@app.route('/')
def home():
    return render_template('index.html')

@socketio.on('send_message')
def handle_message(data):
    user_message = data['message']
    session_id = request.sid
    bot_response = get_bot_response(user_message, session_id)
    socketio.emit('receive_message', {
        'message': bot_response,
        'sender': 'bot'
    })

if __name__ == '__main__':
    if not openai.api_key:
        print("Warning: OpenAI API key not found. Please set it in the .env file.")
    socketio.run(app, debug=True, port=5001)
