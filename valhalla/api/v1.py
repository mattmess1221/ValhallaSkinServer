import calendar
import functools
import hashlib
import json
import random
from datetime import datetime
from io import BytesIO
from typing import List
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from expiringdict import ExpiringDict
from flask import Blueprint, current_app, jsonify, request, g
from flask_httpauth import HTTPTokenAuth
from flask_restx import Api, Resource, abort
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

from .. import *
from ..models import *
from ..mojang import *

apiv1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

auth = HTTPTokenAuth()
api = Api(apiv1)


def gen_auth_token(user: User, expiration):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user.id})


@auth.error_handler
def auth_failed():
    return abort(401, "Authentication failed")


@auth.verify_token
def verify_auth_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    else:
        g.user = User.query.get(data['id'])
        return g.user


def require_formdata(*formdata):
    def call(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            for data in formdata:
                if data not in request.form:
                    abort(404, f"Missing required form: '{data}'")
            return func(*args, **kwargs)

        return decorator

    return call


@api.route('/user/<user:user>')
class UserResource(Resource):
    def get(self, user: User):
        if user is None:
            return abort(404, "User not found")

        def textures_json(texture_list: List[Texture]):
            if not texture_list:
                return None
            for tex in texture_list:
                typ = tex.tex_type.upper()
                upload = tex.upload
                if upload is None:
                    yield typ, None
                else:
                    dic = tex.todict()
                    if not dic['metadata']:
                        del dic['metadata']
                    yield typ, dic

        active = Texture.query. \
            order_by(Texture.tex_type, Texture.id.desc()). \
            filter_by(user=user). \
            distinct(Texture.tex_type). \
            all()

        textures = {k: v for k, v in textures_json(active) if v}

        if not textures:
            return abort(404, "Skins not found")
        return {
            'timestamp': calendar.timegm(datetime.utcnow().utctimetuple()),
            'profileId': str(user.uuid).replace('-', ''),
            'profileName': user.name,
            'textures': dict(textures)
        }


@api.route('/user/<user:user>/<skin_type>')
class TextureResource(Resource):

    @auth.login_required
    def dispatch_request(self, user, skin_type):
        if skin_type in blacklist():
            abort(400, f"Type '{skin_type}' is not allowed. ")
        if user != g.user:
            abort(403, "Cannot change another user's textures")
        super().dispatch_request(user, skin_type)

    @require_formdata('file')
    def post(self, user: User, skin_type):
        form = request.form.copy()
        url = form.pop("file")
        try:
            with requests.get(url) as resp:
                resp.raise_for_status()
                metadata = dict(form)
                put_texture(user, resp.content, skin_type, **metadata)
        except requests.HTTPError as e:
            abort(400, "File download failed", error=str(e))

        return "", 202

    def put(self, user: User, skin_type):
        if 'file' not in request.files:
            raise abort(400, 'Missing required file: file')
        file = request.files['file']

        if not file:
            raise abort(400, "Empty file?")

        metadata = dict(request.form)
        put_texture(user, file.read(), skin_type, **metadata)

        return "", 202

    def delete(self, user: User, skin_type):
        db.session.add(Texture(
            user=user,
            tex_type=skin_type,
            upload=None,
            metadata=None)
        )
        db.session.commit()
        return "", 202


def gen_skin_hash(image_data):
    with Image.open(BytesIO(image_data)) as image:
        if image.format != "PNG":
            raise abort(400, f"Format not allowed: {image.format}")

        # Check size of image.
        # width should be same as or double the height
        # Width is then checked for predefined values
        # 64, 128, 256, 512, 1024

        # set of supported width sizes. Height is either same or half
        sizes = {64, 128, 256, 512, 1024}
        (width, height) = image.size
        valid = width / 2 == height or width == height

        if not valid or width not in sizes:
            raise abort(404, f"Unsupported image size: {image.size}")

        # Create a hash of the image and use it as the filename.
        return hashlib.sha1(image.tobytes()).hexdigest()


def put_texture(user: User, file, skin_type, **metadata):
    try:
        skin_hash = gen_skin_hash(file)
    except UnidentifiedImageError as e:
        raise abort(400, str(e))

    upload = Upload.query.filter_by(hash=skin_hash).first()

    try:
        with open_fs() as fs:
            skin_file = f'textures/{skin_hash}'
            if not fs.exists(skin_file):
                with fs.open(skin_file, "wb") as f:
                    f.write(file)
    except Exception as e:
        import traceback
        traceback.print_exc()
        abort(500, f"Error saving texture file: {type(e).__name__}: {e}")

    if upload is None:
        upload = Upload(hash=skin_hash, user=user)
        db.session.add(upload)

    tex = Texture(user=user,
                  tex_type=skin_type,
                  upload=upload,
                  meta=metadata)

    db.session.add(tex)
    db.session.commit()
    return tex


# Validate tokens are kept 100 at a time for 30 seconds each
validate_tokens = ExpiringDict(100, 30)


@api.route('/auth/handshake')
class AuthHandshakeResource(Resource):

    @api.doc(params={
        'name': 'The username'
    }, verify=True)
    def post(self):
        """Use this endpoint to receive an authentication request.

        The public key is used by the client to join a server for verification.
        """
        name = request.form['name']

        # Generate a random 32 bit integer. It will be checked later.
        verify_token = random.getrandbits(32)
        validate_tokens[name] = verify_token, request.remote_addr

        return {
            'offline': offline_mode(),
            'serverId': current_app.config['server_id'],
            'verifyToken': verify_token
        }


@api.route('/auth/response')
class AuthResponseResource(Resource):
    @api.doc(params={
        'name': "The player username",
        "verifyToken": "The token gotten from /auth/handshake"
    }, verify=True)
    def post(self):
        """Call after a handshake and Mojang's joinServer.

        This calls hasJoined to verify it.
        """
        if offline_mode():
            abort(501)  # Not Implemented

        name = str(request.form['name'])
        verify_token = int(request.form['verifyToken'])

        if name not in validate_tokens:
            abort(403, 'The user has not requested a token or it has expired')

        try:
            token, addr = validate_tokens[name]

            if token != verify_token:
                abort(403, 'The verify token is not valid')
            if addr != request.remote_addr:
                abort(403, 'IP does not match')
        finally:
            del validate_tokens[name]

        with has_joined(name, current_app.config['server_id'], request.remote_addr) as response:
            if not response.ok:
                abort(403)

            try:
                j = response.json()
            except json.JSONDecodeError:
                # Variables here for raygun
                status = response.status_code
                headers = response.headers
                text = response.text
                raise OSError("Bad response from login servers.")

        uuid = j['id']
        name = j['name']

        update_or_insert_user(uuid, name)
        user = User.query.filter_by(uuid=uuid).one()
        # Expire token after 1 hour
        token = f"Bearer {gen_auth_token(user, expiration=3600).decode('ascii')}"

        resp = jsonify(
            accessToken=token,
            userId=str(user.uuid).replace('-', '')
        )
        resp.status_code = 200
        resp.headers['Authorization'] = token

        return resp


def update_or_insert_user(uuid: UUID, name: str):
    user = User.query.filter_by(uuid=uuid).one_or_none()
    if user is None:
        user = User(uuid=uuid, name=name)
        db.session.add(user)
    else:
        user.name = name
    db.session.commit()
