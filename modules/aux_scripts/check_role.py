from flask import redirect, url_for
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

def check_id(id: str | None, redirect_url: str):
    if(not id is None and not id.isdigit()):
        # Log that some faggot tried to mess with me by passing me shitty id!
        return redirect(url_for(sidebar_urls[redirect_url]))