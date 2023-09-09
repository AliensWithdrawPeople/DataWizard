from flask import Blueprint
from .reports_cat import catalogue
from .reports_hardware import hardware

reports = Blueprint('reports', __name__)
reports.register_blueprint(catalogue)
reports.register_blueprint(hardware)