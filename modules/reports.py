from flask import Blueprint
from .reports_cat import catalogue

reports = Blueprint('reports', __name__)
reports.register_blueprint(catalogue)