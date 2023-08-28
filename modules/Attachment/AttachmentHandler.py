from genericpath import isfile

from flask import send_file, Response
from sqlalchemy import select 
from sqlalchemy.exc import NoResultFound
import os
from pathlib import PurePath, Path

from .Attachment import Attachment
from ..db_connecter import get_session
from .. import Models

class AttachmentHandler(object):
    upload_folder = '/uploads'

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(AttachmentHandler, cls).__new__(cls)
        return cls.instance
    
    def upload(self, file: Attachment) -> str | None:
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
        img = Models.Img(src = 'tmp.png')
        session_db.add(img)
        session_db.flush()
        
        path = PurePath(AttachmentHandler.upload_folder, f'img_{img.id}.{file.extension}')
        is_saved = file.save(path)
        if not is_saved:
            session_db.delete(img)
            session_db.flush()
            session_db.commit()
            # log that 'File was not saved.'
            return None
        img.src = str(path)
        img_id = img.id
        session_db.commit()
        session_db.close()
        return str(img_id)
    
    def download(self, img_id: str) -> Response:
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
        session_db.close()
        
        if not os.path.isfile(path):
            raise FileNotFoundError(f'img_id = {img_id} points to a file that does not exist. This id will be deleted from the Database.')
        return send_file(path)
            
    def update(self, img_id: str, file: Attachment) -> bool:
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
            return False
        
        img.src = str(path)
        session_db.commit()
        session_db.close()
        if os.path.isfile(prev_path) and prev_path != path:
            os.remove(prev_path)
        return True