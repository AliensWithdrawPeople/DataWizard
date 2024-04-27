from flask import Flask, render_template
from flask_login import login_required, current_user

import config

app = Flask(__name__)

from modules.auth import auth, login_manager
from modules.lab import lab
from modules.organizations import organizations
from modules.reports.base_report import base_report
from modules.api import api
from modules.aux_scripts.Templates_params import sidebar_urls

app.register_blueprint(auth)
app.register_blueprint(lab)
app.register_blueprint(organizations)
app.register_blueprint(base_report)
app.register_blueprint(api)

app.secret_key = config.secret_key
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