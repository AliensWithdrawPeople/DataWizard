from logging.config import dictConfig
import pathlib
import os
from dotenv import load_dotenv


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'custom_handler': {
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename' : 'DataWizard.log',
            'backupCount': 30
            # 'level'    : 'WARN'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'custom_handler']
    }
})
            
dotenv_path = pathlib.Path('production.env')
if not load_dotenv(dotenv_path=dotenv_path):
    raise FileNotFoundError("Can't find the environment file (production.env) or file is empty.")


secret_key_val = os.getenv('FLASK_APP_SECRET_KEY')
if secret_key_val is None:
    raise FileNotFoundError("There is no FLASK_APP_SECRET_KEY in the environment file.")
secret_key = bytes(secret_key_val, "utf-8")

warehouse_path = os.getenv('WAREHOUSE_PATH')
if warehouse_path is None:
    raise FileNotFoundError("There is no WAREHOUSE_PATH in the environment file.")
warehouse_path = pathlib.PurePath(warehouse_path)
            
attachment_upload_folder = pathlib.PurePath(warehouse_path, 'uploads')
reports_folder = pathlib.PurePath(warehouse_path, 'reports')

def __local_config_mk_if_not_exist(path: os.PathLike):
        if not os.path.isdir(path):
            os.mkdir(path)
__local_config_mk_if_not_exist(attachment_upload_folder)
__local_config_mk_if_not_exist(reports_folder)