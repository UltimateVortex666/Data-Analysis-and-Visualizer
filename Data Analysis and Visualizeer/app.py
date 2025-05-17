from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from chatbot_logic import handle_user_input
from dotenv import load_dotenv
from flask import send_from_directory
# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")  # replace in prod
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UP=app.config['UPLOAD_FOLDER']
# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


df = None

# -------------------- DB Setup --------------------
def init_db():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")

init_db()

# -------------------- Auth Routes --------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists!"
        except sqlite3.Error as e:
            return f"Error signing up: {e}"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = c.fetchone()
            conn.close()

            if result and check_password_hash(result[0], password):
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return "Invalid username or password"
        except sqlite3.Error as e:
            return f"Error logging in: {e}"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# -------------------- Main DataBot Routes --------------------

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global df
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})

    if file.filename.endswith('.csv'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        df = pd.read_csv(file_path)

        column_info = df.dtypes.apply(lambda x: str(x)).to_dict()
        column_count = len(df.columns)

        return jsonify({
            'status': 'success',
            'message': f'File uploaded successfully with {column_count} columns.',
            'column_info': column_info
        })
    return jsonify({'status': 'error', 'message': 'Please upload a CSV file'})

@app.route('/chat', methods=['POST'])
def chat():
    global df
    if 'username' not in session:
        return jsonify({'response': 'Please log in to use the chatbot.'})

    user_input = request.json['message']
    response = handle_user_input(user_input, df, UP)

    return jsonify({'response': response})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        image = request.form.get('filename')  # Filename only
        return render_template('search.html', image=image)
    return render_template('search.html', image=None)


if __name__ == '__main__':
    # Run the app with debug mode depending on the environment
    app.run(debug=True if os.getenv('FLASK_ENV') == 'development' else False)