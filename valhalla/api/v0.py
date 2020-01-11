from flask import Blueprint, request, current_app

apiv0 = Blueprint("api_v0", __name__)


@apiv0.route('/user/<user:user>')
def get_textures(**kwargs):
    return current_app.view_functions['api_v1.user_resource'](**kwargs)


@apiv0.route('/user/<user:user>/<skin_type>', methods=['POST', 'PUT', 'DELETE'])
def change_skin(**kwargs):
    current_app.view_functions['api_v1.texture_resource'](**kwargs)
    if request.method == 'DELETE':
        return dict(message='skin cleared')
    return dict(message="OK")


@apiv0.route('/auth/handshake', methods=["POST"])
def auth_handshake(**kwargs):
    return current_app.view_functions['api_v1.auth_handshake_resource'](**kwargs)


@apiv0.route('/auth/response', methods=['POST'])
def auth_response(**kwargs):
    return current_app.view_functions['api_v1.auth_response_resource'](**kwargs)
