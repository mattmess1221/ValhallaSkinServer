import random
import string

import fs
from flask import Flask, current_app
from flask_alembic import Alembic
from werkzeug.middleware.proxy_fix import ProxyFix

__all__ = [
    "open_fs",
    "offline_mode",
    "blacklist"
]


def offline_mode():
    return current_app.config['OFFLINE']


def blacklist():
    return current_app.config['SKIN_BLACKLIST']


def open_fs():
    path = current_app.config['TEXTURES_FS']
    return fs.open_fs(path, writeable=True)


def create_app(config_import="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_import)

    app.add_url_rule('/textures/<path:filename>',
                     endpoint='textures',
                     build_only=not app.config['DEBUG'],
                     view_func=app.send_static_file)

    #
    # app.url_map = Flask.url_map_class()
    # app.url_map.host_matching = True
    # app.add_url_rule(app.static_url_path + '/<path:filename>',
    #                  endpoint='static',
    #                  host='localhost',
    #                  view_func=app.send_static_file)

    # Reset the url map to remove static
    # app.url_map = Flask.url_map_class()

    from .models import db
    db.app = app
    db.init_app(app)
    alembic = Alembic(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2)

    from .util import UserConverter
    app.url_map.converters['user'] = UserConverter

    register_legacy_v1_api(app)

    from .api.v1 import apiv1

    app.register_blueprint(apiv1)

    from . import cli
    cli.init_app(app)

    @app.before_first_request
    def init_auth():
        app.config['server_id'] = random_string(20)

    return app


def register_legacy_v1_api(app):
    @app.route('/user/<user:user>')
    def get_textures(**kwargs):
        return app.view_functions['api_v1.user_resource'](**kwargs)

    @app.route('/user/<user:user>/<skin_type>', methods=['POST', 'PUT', 'DELETE'])
    def change_skin(**kwargs):
        print("FAIL")
        return app.view_functions['api_v1.texture_resource'](**kwargs)

    @app.route('/auth/handshake', methods=["POST"])
    def auth_handshake(**kwargs):
        return app.view_functions['api_v1.auth_handshake_resource'](**kwargs)

    @app.route('/auth/response', methods=['POST'])
    def auth_response(**kwargs):
        return app.view_functions['api_v1.auth_response_resource'](**kwargs)


def random_string(size, chars=string.ascii_letters + string.digits):
    return ''.join([random.choice(chars) for n in range(size)])
