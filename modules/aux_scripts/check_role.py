from flask import redirect, url_for, session
from flask_login import current_user
from .Templates_params import sidebar_urls


def check_admin():
    role =  current_user.get_role() # type: ignore
    if role != 'admin':
        return redirect(url_for(sidebar_urls['Main']))
    
def check_inspector():
    role =  current_user.get_role() # type: ignore
    if role != 'admin' and role != 'inspector':
        return redirect(url_for(sidebar_urls['Main']))