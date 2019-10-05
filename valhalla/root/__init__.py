from flask import Blueprint

bp = Blueprint("root", __name__, url_prefix='/', static_folder='static', static_url_path='/')

