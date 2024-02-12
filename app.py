from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vishnujonnadasecret'  # Change this to a secure secret key
app.config['MONGO_URI'] = 'mongodb+srv://jonnadavishnu4444:vishnu@cluster0.u2a73ud.mongodb.net/'  # Replace 'your_database_name' with your MongoDB database name
socketio = SocketIO(app)
mongo = PyMongo(app)
login_manager = LoginManager(app)

stream_status = False


# User model
class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = str(user_id)
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(str(user_id))})
    if user_data:
        return User(user_data['_id'], user_data['username'])
    else:
        return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the username already exists
        if mongo.db.users.find_one({'username': username}):
            return "Username already exists. Please choose a different username."
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)
        # Insert the new user into the database
        user_id = mongo.db.users.insert_one({'username': username, 'password': hashed_password}).inserted_id
        user = User(user_id, username)
        login_user(user)
        return redirect(url_for('stream'))
    return render_template('signup.html')


@socketio.on('start_stream')
@login_required
def start_stream():
    global stream_status
    stream_status = True
    emit('stream_status', stream_status, broadcast=True)

@socketio.on('stop_stream')
@login_required
def stop_stream():
    global stream_status
    stream_status = False
    emit('stream_status', stream_status, broadcast=True)

def stream_is_available():
    global stream_status
    return stream_status

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = mongo.db.users.find_one({'username': username})
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['_id'], user_data['username'])
            login_user(user)
            return redirect(url_for('stream'))
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/stream')
@login_required
def stream():
    return render_template('stream.html')

@socketio.on('watch_stream')
@login_required
def watch_stream():
    # Backend logic to check if a stream is available
    if stream_is_available():  
        emit('start_watch_stream', broadcast=True)
    else:
        emit('no_stream_available', broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
