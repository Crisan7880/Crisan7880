from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json, os
import csv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

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

def get_week_dates(start_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    monday = start_date - timedelta(days=start_date.weekday())
    return [(monday + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

def load_weekly_hours_from_csv(username, start_date):
    week_dates = get_week_dates(start_date)
    hours_by_date = {date: 0 for date in week_dates}

    try:
        with open('time_reports.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username and row['date'] in week_dates:
                    hours_by_date[row['date']] += float(row['hours'])
    except FileNotFoundError:
        pass

    return hours_by_date

def load_weekly_projects_from_csv(username, start_date):
    week_dates = get_week_dates(start_date)
    projects_by_date = {date: [] for date in week_dates}

    try:
        with open('time_reports.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (
                    row['username'] == username
                    and row['date'] in week_dates
                ):
                    project = row.get('project', 'Unknown')
                    task = row.get('task', 'No Task')
                    hours = row.get('hours', '0')
                    entry = f"{project} - {task}: {hours}h"
                    projects_by_date[row['date']].append(entry)
    except FileNotFoundError:
        pass

    return projects_by_date

@app.route('/tasks/<project_name>')
def get_tasks_for_project(project_name):
    tasks = []
    try:
        filepath = os.path.join('project_tasks', f'{project_name}.csv')
        with open(filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            tasks = [row[0] for row in reader if row]
    except FileNotFoundError:
        tasks = []
    return jsonify(tasks)


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    users = load_users()
    name = users[username].get('name', '')
    surname = users[username].get('surname', '')

    # Get the current date or the selected date (from form submission)
    if request.method == 'POST':
        project = request.form['project']
        task = request.form['task']
        hours = request.form['hours']
        date = request.form['date']

        # Save the data to the CSV
        with open('time_reports.csv', mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([username, date, project, task, hours])

    # Load weekly data for the specific week (e.g., last week or this week)
    week_start_date = request.args.get('week_start_date', datetime.today().strftime('%Y-%m-%d'))
    weekly_hours = load_weekly_hours_from_csv(username, week_start_date)
    weekly_projects = load_weekly_projects_from_csv(username, week_start_date)

    return render_template(
        'home.html',
        name=name,
        surname=surname,
        weekly_hours=weekly_hours,
        weekly_projects=weekly_projects,
        week_start_date=week_start_date
    )

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

