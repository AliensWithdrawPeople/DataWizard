from flask import Blueprint
from .catalogue import catalogue
from .hardware import hardware
from .reports import reports

base_report = Blueprint('base_report', __name__)
base_report.register_blueprint(catalogue)
base_report.register_blueprint(hardware)
base_report.register_blueprint(reports)