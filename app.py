from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'snakegamesecret'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move')
def handle_move(direction):
    emit('move_response', {'direction': direction}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
