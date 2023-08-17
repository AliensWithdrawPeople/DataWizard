from sqlalchemy import select 
from sqlalchemy.sql import exists
from passlib.hash import pbkdf2_sha256

from .db_connecter import get_session
from . import Models


class User_info:
    """
    This provides default implementations for the methods that Flask-Login
    expects user objects to have.
    """
    __hash__ = object.__hash__
    
    def __init__(self, id: str):
        # load User data
        session = get_session()
        self._user = session.scalars(select(Models.User).where(Models.User.id == id)).one()
        self._is_good = True
        
    @staticmethod
    def check_and_load(email: str, password: str):
        session = get_session()
        users = list(session.scalars(select(Models.User).where(Models.User.email == email)).all())
        users = [user for user in users if pbkdf2_sha256.verify(password, user.password)]
        
        return User_info(str(users[0].id)) if len(users) == 1 else None
        
    @staticmethod
    def get(user_id: str):
        session = get_session()
        is_exist = session.query(exists().where(Models.User.id == user_id)).scalar()
        return User_info(user_id) if is_exist else None
    
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return self._is_good

    @property
    def is_anonymous(self):
        return False

    def get_role(self):
        return str(self._user.role)
    
    def get_id(self):
        try:
            return str(self._user.id)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override `get_id`") from None

    def __eq__(self, other):
        """
        Checks the equality of two `UserMixin` objects using `get_id`.
        """
        if isinstance(other, User_info):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        """
        Checks the inequality of two `UserMixin` objects using `get_id`.
        """
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal