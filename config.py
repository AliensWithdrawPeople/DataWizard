from logging.config import dictConfig
import pathlib

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

#FIXME: Change me before release version.
secret_key = b'35ec60f765926299d8b67586b9f435d4ef92c6398a0d2d2061b0b9e7bbbaf840'

#FIXME: Change me when you will deploy it somewhere else.
warehouse_path = pathlib.PurePath('C:/Windows', '/work', 'MagicWarehouse')
attachment_upload_folder = pathlib.PurePath(warehouse_path, 'uploads')
reports_folder = pathlib.PurePath(warehouse_path, 'reports')