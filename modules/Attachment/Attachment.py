from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os


class Attachment:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}
    @staticmethod
    def allowed_filename(filename: str | None) -> str | None:
        if not filename is None and '.' in filename and filename.rsplit('.', 1)[1].lower() in Attachment.ALLOWED_EXTENSIONS:
            return secure_filename(filename)
        return None  
    
    def __init__(self, file: FileStorage | None, filename: str | None = None) -> None:
        if file is None:
            return None
        if filename is None:
            filename = Attachment.allowed_filename(file.filename)
        
        if filename is None:
            raise ValueError(f'Wrong  filename of {file.name} field.')
        self.__file = file
        self.__filename = filename

    @property
    def name(self):
        return self.__filename
    
    @property
    def extension(self):
        return self.__filename.rsplit('.', 1)[1].lower()
    
    def save(self, dst_path: str | os.PathLike) -> bool:
        self.__file.save(dst_path)
        return os.path.isfile(dst_path)
