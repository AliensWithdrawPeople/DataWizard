from flask import Flask, render_template, request, redirect, url_for, session
from modules.auth import auth, login_manager
from modules.lab import lab
from modules.search import search
from modules.organizations import organizations
from flask_login import login_required, current_user

from modules.aux_scripts.Templates_params import sidebar_urls

app = Flask(__name__)
app.register_blueprint(auth)
app.register_blueprint(search)
app.register_blueprint(lab)
app.register_blueprint(organizations)

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
    is_admin = True if current_user.get_role() == 'admin' else False # type: ignore
    username = current_user.get_name() # type: ignore
    return render_template('main.html', is_admin=is_admin, username=username, messages=messages, sidebar_urls=sidebar_urls)