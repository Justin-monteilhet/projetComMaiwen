from flask import Flask, render_template, request, session

from ED_api import APISession

app = Flask(__name__)
app.secret_key = "clé-très-secrète"

@app.route('/', methods=['GET', 'POST'])
def index():
    if "ed-token" in session and "name" in session :    # if logged in, redirects to logs
        logs = APISession(session['ed-token']).sold_logs
        user_logs = logs[session['name']]
        print("session found, rendering logs")
        return render_template('logs.html', logs=user_logs)

    form = request.form 

    if "username" in form and "password" in form:   # if sending a login request, login and redirects to choiceStudent
        username, password = form['username'], form['password']
        api = APISession.from_credentials(username, password)
        session['ed-token'] = api.token
        names = api.names
        print("credentials found, rendering studentChoice")
        return render_template("studentChoice.html", names=names)
    
    if "name" in form and 'ed-token' in session:  # if sending the student name, redirect to logs
        name = form['name']
        session['name'] = name
        user_logs = APISession(session['ed-token']).sold_logs.get(name)
        print("name found, rendering logs")
        return render_template('logs.html', logs=user_logs)

    print("Nothing found, rendering default login")
    return render_template("login.html")    # default

app.run()