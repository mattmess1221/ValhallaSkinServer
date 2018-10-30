#!/usr/env python3

import base64
import calendar
import functools
import hashlib
import os
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
from uuid import uuid1

import requests
from expiringdict import ExpiringDict
from flask import Flask, abort, jsonify, request, send_file
from fs import open_fs
from PIL import Image

from . import database, mojang
from .validate import regex

app = Flask(__name__)

db_path = os.getenv('DATABASE_URL', 'sqlite://hdskins.sqlite')
textures_fs = os.getenv('TEXTURES_FS', 'file://.')
root_url = os.getenv('ROOT_URL', 'http://127.0.0.1')
offline_mode = bool(os.getenv('OFFLINE', False))

supported_types = ["skin", "cape", "elytra"]

upload_fs = open_fs(textures_fs, cwd='textures', writeable=True)

# Customize the FS upload args if they exist. Mostly for S3
if hasattr(upload_fs, 'upload_args'):
    upload_fs.upload_args = {
        'ContentType': 'image/png',
        'ACL': 'public-read'  # S3: Make public
    }


def open_database():
    return database.Database(db_path)


def authorize(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):

        if not offline_mode:
            if 'Authorization' not in request.headers:
                return jsonify(message="Authorization token not provided"), 403
            token = str(request.headers['Authorization'])

            with open_database() as db:

                user = db.find_user(kwargs['user'])

                if token is None or user is None:
                    return jsonify(message="Unauthorized"), 401
                uploader = db.find_uploader(user, request.remote_addr)
                access = db.find_token(uploader)
                if access is None or access.token != token:
                    return jsonify(message="Authorization failed"), 403
                if datetime.now() - access.issued > timedelta(hours=4):
                    return jsonify(message="Access token expired"), 401

                uploader.accessed = datetime.now()

                db.commit()

        return func(*args, **kwargs)

    return decorator


class BadRequest(Exception):
    pass


def require_formdata(*formdata):
    def call(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            for data in formdata:
                if data not in request.form:
                    raise BadRequest("Missing required form: '%s'" % data)
            return func(*args, **kwargs)

        return decorator

    return call


@app.route('/user/<user>')
@regex(user=regex.UUID)
def get_textures(user):
    with open_database() as db:
        user = db.find_user(user)
        if user is None:
            return jsonify(message="User not found"), 403

        def metadata_json(data):
            for meta in data:
                yield meta.key, meta.value

        def textures_json(textures):
            if not textures:
                return None
            for tex_type, tex in textures.items():
                typ = tex_type.upper()
                upload = tex.file
                if upload is None:
                    continue
                dic = {'url': root_url + '/textures/' + upload.hash}
                metadata = dict(metadata_json(tex.metadata))
                if metadata:  # Only include metadata if there is any
                    dic['metadata'] = metadata
                yield typ, dic

        textures = dict(textures_json(db.find_textures(user)))
        if not textures:
            return jsonify(message="Skins not found"), 403
        return jsonify(
            timestamp=calendar.timegm(datetime.utcnow().utctimetuple()),
            profileId=user.uuid,
            profileName=user.name,
            textures=dict(textures)
        )


if bool(app.config['DEBUG']):
    @app.route('/textures/<image>')
    def get_image(image):
        """Debug endpoint used to fetch skins. Production should use a separate server such as S3"""
        if upload_fs.exists(image):
            return send_file(upload_fs.open(image, 'rb'), mimetype='image/png')
        else:
            abort(404)


@app.route('/robots.txt')
def robots():
    return send_file('../robots.txt')


def get_metadata_map(form):
    for k, v in form.items():
        if k != 'file':
            yield k, v


@app.route('/user/<user>/<skinType>', methods=['POST'])
@regex(user=regex.UUID, skin_type=regex.choice(*supported_types))
@require_formdata('file')
@authorize
def change_skin(user, skin_type):
    url = request.form["file"]
    resp = requests.get(url)
    if not resp.ok:
        raise BadRequest("File url not found.")

    metadata = get_metadata_map(request.form)
    put_texture(user, resp.content, skin_type, **dict(metadata))

    return jsonify(message='OK')


@app.route('/user/<user>/<skin_type>', methods=['PUT'])
@regex(user=regex.UUID, skin_type=regex.choice(*supported_types))
@authorize
def upload_skin(user, skin_type):
    if 'file' not in request.files:
        raise BadRequest('Missing required file: file')
    file = request.files['file']

    if not file:
        raise BadRequest("Empty file?")

    metadata = get_metadata_map(request.form)
    put_texture(user, file.read(), skin_type, **dict(metadata))

    return jsonify(message="OK")


def gen_skin_hash(image_data):
    image = Image.open(BytesIO(image_data))

    if image.format != "PNG":
        raise ValueError("Format not allowed: " + image.format)

    # Check size of image.
    # width should be same as or double the height
    # Width is then checked for predefined values
    # 64, 128, 256, 512, 1024

    # set of supported width sizes. Height is either same or half
    sizes = {64, 128, 256, 512, 1024}
    (width, height) = image.size
    valid = width / 2 == height or width == height

    if not valid or width not in sizes:
        raise ValueError("Unsupported image size: " + image.size)

    # Create a hash of the image and use it as the filename.
    return hashlib.sha1(image.tobytes()).hexdigest()


def put_texture(uuid, file, skin_type, **metadata):
    with open_database() as db:

        def insert_meta():
            for k, v in metadata.items():
                md = db.db((db.db.metadata.key == k) and (db.db.metadata.value == v)).select().first()
                if md is None:
                    md = db.db.metadata.insert(key=k, value=v)
                yield md.id

        user = db.find_user(uuid)
        assert user is not None
        uploader = db.find_uploader(user, request.remote_addr)
        assert uploader is not None

        skin_hash = gen_skin_hash(file)

        upload = db.db(db.db.uploads.hash == skin_hash).select().first()

        if upload is None:
            with upload_fs.open(skin_hash, "wb") as f:
                f.write(file)

            upload = db.db.uploads.insert(hash=skin_hash, uploader=uploader)

        db.db.textures.insert(user=user,
                              tex_type=skin_type,
                              file=upload,
                              metadata=list(insert_meta()) or None)
        db.commit()


@app.route('/user/<user>/<skin_type>', methods=['DELETE'])
@regex(user=regex.UUID, skin_type=regex.choice(*supported_types))
@authorize
def reset_skin(user, skin_type):
    with open_database() as db:
        user = db.find_user(user)
        if user is not None:
            db.db.textures.insert(user=user,
                                  tex_type=skin_type,
                                  file=None,
                                  metadata=None)
            db.commit()
            return jsonify(message="skin cleared")
        return jsonify(message="Unknown user"), 404


# Validate tokens are kept 100 at a time for 30 seconds each
validate_tokens = ExpiringDict(100, 30)


@app.route('/auth/handshake', methods=["POST"])
@require_formdata('name')
def auth_handshake():
    """Use this endpoint to receive an authentication request.

    The public key is used by the client to join a server for verification.
    """

    name = request.form['name']

    # Generate a random 32 bit integer. It will be checked later.
    verify_token = random.getrandbits(32)
    validate_tokens[name] = verify_token, request.remote_addr

    return jsonify(
        offline=offline_mode,
        serverId=server_id,
        verifyToken=verify_token
    )


@app.route('/auth/response', methods=['POST'])
@require_formdata('name', 'verifyToken')
def auth_response():
    if offline_mode:
        abort(501)  # Not Implemented

    name = str(request.form['name'])
    verify_token = int(request.form['verifyToken'])

    def forbidden(msg):
        abort(403, jsonify(error="Forbidden", message=msg))

    if name not in validate_tokens:
        forbidden('The user has not requested a token or it has expired')

    try:
        token, addr = validate_tokens[name]

        if token != verify_token:
            forbidden('The verify token is not valid')
        if addr != request.remote_addr:
            forbidden('IP does not match')
    finally:
        del (validate_tokens[name])

    response = mojang.has_joined(name, server_id, request.remote_addr)

    if not response.ok:
        abort(403)

    json = response.json()

    uuid = json['id']
    name = json['name']

    with open_database() as db:
        user = db.find_user(uuid, name)
        assert user is not None

        uploader = db.find_uploader(user, addr)
        assert uploader is not None
        # Generate unique access token. uuid1 guarentees it
        token = str(base64.b64encode(uuid1().bytes, altchars=b"-_"), 'utf-8')

        db.put_token(uploader, token)

        db.commit()

        return jsonify(
            accessToken=token,
            userId=user.uuid,
        )


@app.before_first_request
def init_auth():
    global server_id

    server_id = random_string(20)

    with open_database() as db:
        db.commit()


def random_string(size=20, chars=string.ascii_letters + string.digits):
    return ''.join([random.choice(chars) for n in range(size)])


@app.errorhandler(405)
def methodNotAllowed(status):
    return jsonify(error="Method Not Allowed"), 405


@app.errorhandler(BadRequest)
def raiseUserError(error):
    return jsonify(message=type(error).__name__ + ": " + str(error)), 400
