import logging
from datetime import timedelta
from typing import List

from flask import Flask, render_template, request, session

from ED_api import APISession, Transaction, IncorrectCredentialsError

app = Flask(__name__)
app.secret_key = "clé-très-secrète"
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=30)

@app.route('/', methods=['GET', 'POST'])
def index():
    # if "ed-token" in session and "name" in session :    # if logged in, redirects to logs
    #     logs = APISession(session['ed-token']).sold_logs
    #     user_logs = logs[session['name']]
    #     print("session found, rendering logs")
    #     return render_template('logs.html', logs=user_logs)

    form = request.form 

    if "username" in form and "password" in form:   # if sending a login request, login and redirects to choiceStudent
        username, password = form['username'], form['password']
        try : 
            api = APISession.from_credentials(username, password)

        except IncorrectCredentialsError :
            return render_template("login.html", code=401)

        sold_logs = api.sold_logs
        names = list(sold_logs.keys())  # key of sold logs are the students' names
        for name, trans_list in sold_logs.items():
            sold_logs[name] = [trans.to_json() for trans in trans_list]

        session['logs'] = sold_logs

        logging.info("credentials found, rendering studentChoice")
        return render_template("studentChoice.html", names=names)
    
    if "name" in form and 'logs' in session:  # if sending the student name, redirect to logs
        name = form['name']
        raw_user_logs : List[dict] = session["logs"].get(name)

        user_logs = list(map(Transaction.from_dict, raw_user_logs))
        logging.info("name found, rendering logs")
        return render_template('logs.html', logs=user_logs)

    logging.info("No data in form/session, rendering default login")
    return render_template("login.html", code=200)    # default

app.run()