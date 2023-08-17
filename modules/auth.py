from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from .User_info import User_info
from flask_login import LoginManager, login_user, current_user

login_manager = LoginManager()
    
auth = Blueprint('auth', __name__)

# This callback is used to reload the user object from the user ID stored in the session. It should take the str ID of a user, and return the corresponding user object.
@login_manager.user_loader
def load_user(user_id):
    return User_info.get(user_id)

@login_manager.unauthorized_handler
def redirect_to_login():
    return redirect(url_for('auth.login'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') == 'true' else False
        if(email is None):
            return render_template('login.html', user_email='')
        if(password is None):
            return render_template('login.html', user_email=email)
        user = User_info.check_and_load(email, password=password)

        if user is None:
            return render_template('login.html', user_email=email)
        else:
            login_user(user, remember=remember)
            flash("Logged in successfully!")
            return redirect(url_for('index'))
    
    return render_template('login.html', user_email='')

@auth.route('/signup')
def signup():
    return 'Signup'

@auth.route('/logout')
def logout():
    return 'Logout'