from flask import redirect, url_for, current_app
from flask_login import current_user
from .Templates_params import sidebar_urls


def check_admin():
    role =  current_user.get_role() # type: ignore
    if role != 'admin':
        current_app.logger.info('Oops! User is not an %s. Therefore they were redirected to the main page.', 'admin', exc_info=True)
        return redirect(url_for(sidebar_urls['Main']))
    
def check_inspector():
    role =  current_user.get_role() # type: ignore
    if role != 'admin' and role != 'inspector':
        current_app.logger.info('Oops! User is not an %s. Therefore they were redirected to the main page.', 'admin or inspector', exc_info=True)
        return redirect(url_for(sidebar_urls['Main']))

def check_id(id: str | None, redirect_url: str):
    if(not id is None and not id.isdigit()):
        current_app.logger.info('some faggot tried to mess with me by passing me a shitty id (%s)!', str(id), exc_info=True)
        return redirect(url_for(sidebar_urls[redirect_url]))