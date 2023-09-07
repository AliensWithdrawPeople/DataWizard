from flask import Blueprint, redirect, render_template, request, url_for, current_app
from .User_info import User_info
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from .aux_scripts.Templates_params import sidebar_urls

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
            current_app.logger.info('User #%s was successfully logged in.', user.get_id(), exc_info=True)
            return redirect(url_for('index'))
    
    return render_template('login.html', user_email='')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    current_app.logger.info('User #%s was logged out.', current_user.id , exc_info=True) # type: ignore
    return redirect(url_for(sidebar_urls['LogIn']))