from flask import Blueprint, current_app
from flask_login import login_required
from modules.Attachment.AttachmentHandler import AttachmentHandler
from sqlalchemy import select 
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from .db_connecter import get_session
from . import Models

from .aux_scripts.check_role import check_id, check_inspector


api = Blueprint('api', __name__)

attach_handler = AttachmentHandler.getInstance()

@api.route('/api/data/img/<id>')
@login_required
def send_image(id):
    check_inspector()
    check_id(id, 'Organizations')
    session_db = get_session()
    current_app.logger.info(f'Requested img_id = {id}')
    try:
        img_id = session_db.scalars(select(Models.Img.id).where(Models.Img.id == id)).one()
    except (MultipleResultsFound, NoResultFound) as e: 
        current_app.logger.warning("Can't find img_id = %s cause %s", id, e, exc_info=True)
        img_id = None
    finally:
        session_db.connection().close()
    current_app.logger.info(f'Found logo with img_id = {id}')
    default_res = {}
    if not img_id is None:
        try:
            current_app.logger.info('Passing img_id = %s to attach_handler', img_id, exc_info=True)
            return attach_handler.download(int(img_id))
        except ValueError as e:
            current_app.logger.warning('Yo! Im gonna return nothing cause %s', e, exc_info=True)
            return default_res
        except FileNotFoundError as e:
            current_app.logger.warning('Yo! Im gonna return nothing cause %s', e, exc_info=True)
            return default_res   
    current_app.logger.warning('Yo! Im gonna return nothing cause img_id = %s is None', id, exc_info=True)
    return default_res 
