from flask import Flask, render_template, request, redirect, url_for, session
from modules.auth import auth, login_manager
from flask_login import login_required

app = Flask(__name__)
app.register_blueprint(auth)
app.secret_key = b'35ec60f765926299d8b67586b9f435d4ef92c6398a0d2d2061b0b9e7bbbaf840'
login_manager.init_app(app)

messages = [{'title': 'Message One',
             'content': 'Message One Content'},
            {'title': 'Message Two',
             'content': 'Message Two Content'},
            {'title': 'Message Three',
             'content': 'Message 3 Content'},
            {'title': 'Message Nth',
             'content': 'Message Nth Content'}
            ]

@app.route('/')
@login_required
def index():
    return render_template('main.html', messages=messages)

@app.route('/create/', methods=('GET', 'POST'))
@login_required
def create():
    return render_template('create.html')

@app.route("/search", methods=('GET', 'POST'))
@login_required
def read():
    return redirect(url_for('index'))