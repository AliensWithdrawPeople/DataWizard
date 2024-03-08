from flask import send_file, Response, request, current_app
from sqlalchemy import select 
from sqlalchemy.exc import NoResultFound
import os
from pathlib import PurePath

from wtforms import FileField

from .Attachment import Attachment
from ..db_connecter import get_session
from .. import Models

import config


class AttachmentHandler:
    """ Singleton. """
    upload_folder = config.attachment_upload_folder

    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if AttachmentHandler.__instance is None:
            return AttachmentHandler()
        return AttachmentHandler.__instance
    
    def __init__(self):
        if AttachmentHandler.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            AttachmentHandler.__instance = self
    
    @classmethod
    def upload(cls, file: Attachment) -> int | None:
        """Upload image to the server.

        Parameters
        ----------
        file : Attachment
            Image to upload.

        Returns
        -------
        str or None
            image id in images table (Models.Img sqlalchemy orm model) or None if file was not saved.

        Raises
        ------
        RuntimeError
            File was not saved.
        """
        session_db = get_session()
        img = Models.Img(src = '')
        session_db.add(img)
        session_db.flush()
        
        path = PurePath(AttachmentHandler.upload_folder, f'img_{img.id}.{file.extension}')
        is_saved = file.save(path)
        if not is_saved:
            session_db.delete(img)
            session_db.flush()
            session_db.commit()
            current_app.logger.warning('Attachment %s was not saved.', path.name, exc_info=True)
            return None
        img.src = str(path)
        img_id = img.id
        session_db.commit()
        session_db.connection().close()
        session_db.close()
        return int(img_id)
    
    @classmethod
    def download(cls, img_id: int) -> Response:
        """Download image from the server.

        Parameters
        ----------
        img_id : str
            id of the destination image

        Returns
        -------
        Response
            Response with image.

        Raises
        ------
        ValueError
            img_id is not valid.
        FileNotFoundError
            img_id points to a file that does not exist. This id will be deleted from the Database.
        """
        session_db = get_session()
        selected = select(Models.Img).where(Models.Img.id == img_id)
        try:
            img = session_db.scalars(selected).one()
        except NoResultFound:
            raise ValueError(f'img_id ={img_id} is not valid.')
        path = PurePath(img.src)
        session_db.connection().close()
        session_db.close()
        
        if not os.path.isfile(path):
            raise FileNotFoundError(f'img_id = {img_id} points to a file that does not exist. This id will be deleted from the Database.')
        return send_file(path)
    
    @classmethod        
    def update(cls, img_id: int, file: Attachment) -> bool:
        """Updates Image (Image.id == img_id) with the file.

        Parameters
        ----------
        img_id : str
            id of the destination image
        file : Attachment
            new image

        Returns
        -------
        bool
           True if new image is successfully 

        Raises
        ------
        ValueError
            img_id is not valid.
        """
        session_db = get_session()
        selected = select(Models.Img).where(Models.Img.id == img_id)
        try:
            img = session_db.scalars(selected).one()
        except NoResultFound:
            raise ValueError(f'img_id = {img_id} is not valid.')
        prev_path = PurePath(img.src)
        path = PurePath(AttachmentHandler.upload_folder, f'img_{img_id}.{file.extension}')
        is_saved = file.save(path)
        if not is_saved:
            session_db.close()
            current_app.logger.warning('Attachment %s with img_id=%s was not updated cause file was not saved.', path.name, img_id, exc_info=True)
            return False
        
        img.src = str(path)
        session_db.commit()
        session_db.close()
        if os.path.isfile(prev_path) and prev_path != path:
            os.remove(prev_path)
        return True
    
    @classmethod
    def load_img_from_form(cls, img_field: FileField, img_id: int | None = None)-> int | bool | None:
        """Load image related to img_field from frontend and upload (or update if img_id is provided) it to the server's Attachment service.

        Parameters
        ----------
        img_field : wtforms.FileField
            wtforms' field related to this image.
        img_id : str | None, optional
            id in images table if you need to update image, by default None which means you want to create a new entry in images table.

        Returns
        -------
        str | bool | None
            img_id if new entry in images table was registered | True if the file was successfully updated | No data in the field.
        """
        if not img_field.name in request.files or request.files[img_field.name].mimetype.split('/')[0] != 'image':
            current_app.logger.warning('Image was not loaded from form cause either it is not an image or it was not provided by user.', exc_info=True)
            return None
        image_data = request.files[img_field.name]
        image_attachment = Attachment(image_data)
        if not img_id is None:
            try:
                return cls.update(img_id, image_attachment)
            except ValueError as e:
                current_app.logger.warning(f'DB problem: %s', e, exc_info=True)
                return False
        else:
            try:
                return cls.upload(image_attachment)
            except RuntimeError as e:
                current_app.logger.critical(f'Problem with saving files: %s', e, exc_info=True)
                return None