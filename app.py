from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USER_FILE = 'users.json'

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def home():
    if 'username' in session:
        users = load_users()
        username = session['username']
        name = users[username].get('name', '')
        surname = users[username].get('surname', '')
        return render_template('home.html', name=name, surname=surname)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if username in users:
            # Retrieve the hashed password from the user data
            hashed_password = users[username]['password']
            if check_password_hash(hashed_password, password):
                session['username'] = username
                flash('Logged in successfully!')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password.')
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']

        users = load_users()

        if username in users:
            flash('Username already exists.')
            return redirect(url_for('register'))

        users[username] = {
            'password': generate_password_hash(password),  # You should hash it in real apps
            'name': name,
            'surname': surname
        }

        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

