import random
import string
import warnings

import fs
from flask import Flask, Blueprint, redirect, url_for, current_app
from werkzeug.middleware.proxy_fix import ProxyFix

__all__ = [
    "root_url",
    "open_fs",
    "offline_mode",
    "blacklist"
]


def root_url():
    warnings.warn("Use a endpoing with url_for", DeprecationWarning)
    return current_app.config['ROOT_URL']


def offline_mode():
    return current_app.config['OFFLINE']


def blacklist():
    return current_app.config['SKIN_BLACKLIST']


def open_fs():
    path = current_app.config['TEXTURES_FS']
    return fs.open_fs(path, cwd='textures', writeable=True)


def create_app(config_import="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_import)

    from .models import db
    db.app = app
    db.init_app(app)

    db.create_all()

    app.wsgi_app = ProxyFix(app.wsgi_app)

    from .util import UserConverter
    app.url_map.converters['user'] = UserConverter

    register_legacy_v1_api(app)

    from .root import bp
    from .api.v1 import apiv1

    app.register_blueprint(bp)
    app.register_blueprint(apiv1)

    if bool(app.config['DEBUG']):
        app.register_blueprint(Blueprint("textures", __name__, static_folder="textures", static_url_path="/textures"))

    @app.before_first_request
    def init_auth():
        app.config['server_id'] = random_string(20)

    return app


def register_legacy_v1_api(app):
    @app.route('/user/<uuid:user>')
    def get_textures(**kwargs):
        return redirect(url_for('api_v1.user_resource', **kwargs), 308)

    @app.route('/user/<uuid:user>/<skinType>', methods=['POST', 'PUT', 'DELETE'])
    def change_skin(**kwargs):
        return redirect(url_for('api_v1.texture_resource', **kwargs), 308)

    @app.route('/auth/handshake', methods=["POST"])
    def auth_handshake():
        return redirect(url_for('api_v1.auth_handshake_resource'), 308)

    @app.route('/auth/response', methods=['POST'])
    def auth_response():
        return redirect(url_for('api_v1.auth_response_resource'), 308)


def random_string(size, chars=string.ascii_letters + string.digits):
    return ''.join([random.choice(chars) for n in range(size)])
