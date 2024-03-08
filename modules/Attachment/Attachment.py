# from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import re

_windows_device_files = (
    "CON",
    "AUX",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "LPT1",
    "LPT2",
    "LPT3",
    "PRN",
    "NUL",
)

_filename_strip_re = re.compile(r"[^A-Za-zа-яА-ЯёЁ0-9_.-]")


def secure_filename(filename: str) -> str:
    if isinstance(filename, str):
        from unicodedata import normalize
        filename = normalize("NFKD", filename)

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")

    filename = str(_filename_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )
    
    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"

    return filename

class Attachment:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}
    @staticmethod
    def allowed_filename(filename: str | None) -> str | None:
        if not filename is None and '.' in filename and filename.rsplit('.', 1)[1].lower() in Attachment.ALLOWED_EXTENSIONS:
            return secure_filename(filename)
        return None  
    
    def __init__(self, file: FileStorage | None, filename: str | None = None) -> None:
        print(f"filename = {filename}")
        if file is None:
            return None
        if filename is None:
            filename = Attachment.allowed_filename(file.filename)
        print(f"secure filename = {filename}")

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
