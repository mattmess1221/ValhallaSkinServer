#!/usr/env python3

import base64
import functools
import hashlib
import os
import random
import time
import uuid as guid
from io import BytesIO

import requests
import rsa
from expiringdict import ExpiringDict
from flask import Flask, Response, abort, jsonify, request, render_template
from PIL import Image

from .validate import regex

from.import database, mojang

app = Flask(__name__)

db_file = os.getenv('DB_FILE', 'hdskins.db')
root_dir = os.getenv('ROOT_DIR', os.getcwd())
root_url = os.getenv('ROOT_URL', '127.0.0.1')
offline_mode = bool(os.getenv('OFFLINE', False))

supported_types = ["skin", "cape", "elytra"]


def open_database():
    return database.Database(db_file)


def authorize(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):

        if not offline_mode:
            if 'Authorization' not in request.headers:
                abort(403)
            auth = str(request.headers['Authorization'])
            print(auth)  # TODO: Remove this before publishing

            with open_database() as db:
                access = db.find_access_token(auth)
                if access is None or access.address != request.remote_addr:
                    abort(403)
                if access.expires < time.time:
                    abort(401)
                if access.user.uuid != kwargs['uuid']:
                    abort(401)

        return func(*args, **kwargs)
    return decorator


def require_formdata(*formdata):
    def callable(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            for data in formdata:
                if data not in request.form:
                    raise KeyError("Missing required form: '%s'" % data)
            return func(*args, **kwargs)
        return decorator
    return callable


def metadata_json(data):
    for meta in data:
        yield meta.key, meta.val


def textures_json(textures):
    for texType, tex in textures:
        texType = str(texType).upper()
        dic = {'url': root_url + '/textures/' + tex.url}
        metadata = dict(metadata_json(tex.metadata))
        if metadata:  # Only include metadata if there is any
            dic['metadata'] = metadata
        yield texType, dic


@app.route('/user/<user>')
@regex(user=regex.UUID)
def get_textures(user):

    with open_database() as db:
        user = db.find_user(user, False)
        if not user:
            return abort(403, "User not found")
        textures = textures_json(user.textures)
        if not textures:
            return abort(403, "Skins not found")
        return jsonify(
            timestamp=int(time.time()),
            profileId=user.uniqueId,
            profileName=user.name,
            textures=dict(textures)
        ), 200


@app.route('/user/<user>/<skinType>', methods=['POST'])
@regex(user=regex.UUID, skin_type=regex.choice(*supported_types))
@require_formdata('file')
@authorize
def change_skin(user, skin_type):

    model = request.form["model"] or 'default'
    url = request.form["file"]

    resp = requests.get(url)

    if resp.ok:
        skin = gen_skin_hash(resp.content)

        put_texture(user, skin, skin_type, request.remote_addr, model=model)

    return 'OK'


@app.route('/user/<user>/<skin_type>', methods=['PUT'])
@regex(user=regex.UUID, skin_type=regex.choice(*supported_types))
@authorize
def upload_skin(user, skin_type):

    if 'file' not in request.files:
        raise ValueError('Missing required file: file')
    file = request.files['file']
    if 'model' in request.form:
        model = request.form["model"]
    else:
        model = None

    if not file:
        raise ValueError("Empty file?")

    (image, skin) = gen_skin_hash(file.read())

    image.save(os.path.join(root_dir, "textures", skin), format="PNG")

    # TODO: support for arbitrary metadata

    put_texture(user, skin, skin_type, request.remote_addr, model=model)

    return Response()


def gen_skin_hash(image_data):

    image = Image.open(BytesIO(image_data))

    if image.format != "PNG":
        raise ValueError("Format not allowed: " + image.format)

    # Check size of image.
    # width should be same as or double the height
    # Width is then checked for predefined values
    # 64, 128, 256, 512, 1024

    # set of supported width sizes. Height is either same or half
    sizes = set([64, 128, 256, 512, 1024])
    (width, height) = image.size
    valid = width / 2 == height or width == height

    if not valid or width not in sizes:
        raise ValueError("Unsupported image size: " + image.size)

    # Create a hash of the image and use it as the filename.
    return image, hashlib.sha1(image.tobytes()).hexdigest()


def put_texture(user, url, skin_type, uploader, **metadata):

    with open_database() as db:
        user = db.find_user(user)
        texture = user.put_texture(url, skin_type, uploader)
        texture.put_metadata(**metadata)


@app.route('/user/<user>/<skin_type>', methods=['DELETE'])
@regex(user=regex.UUID, skin_type=regex.choice(*supported_types))
@authorize
def reset_skin(user, skin_type):
    with open_database() as db:
        user = db.find_user(user)
        if user:
            tex = user.textures[skin_type]
            if tex and tex.clear():
                return Response()
            return abort(404, "Unknown texture")
        return abort(404, "Unknown user")


# Validate tokens are kept 100 at a time for 30 seconds each
validate_tokens = ExpiringDict(100, 30)


@app.route('/auth/handshake', methods=["POST"])
@require_formdata('name')
def auth_handshake():
    """Use this endpoint to receive an authentication request.

    The public key is used by the client to join a server for verification.
    """

    if offline_mode:
        return jsonify(offline=True)

    name = request.form['name']

    # Generate a random 32 bit integer. It will be checked later.
    verify_token = random.getrandbits(32)
    validate_tokens[name] = verify_token, request.remote_addr

    return jsonify(
        offline=False,
        serverId="",
        publicKey=str(base64.b64encode(pub_key.save_pkcs1(format="DER"))),
        verifyToken=verify_token
    )


@app.route('/auth/response', methods=['POST'])
@require_formdata('name', 'sharedSecret', 'verifyToken')
def auth_response():

    if offline_mode:
        abort(501)  # Not Implemented

    name = str(request.form['name'])
    verify_token = int(request.form['verifyToken'])
    shared_secret = bytes(request.form['sharedSecret'], encoding="UTF-8")
    secret = base64.b64decode(shared_secret)

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
        del(validate_tokens[name])

    server_id = hash_digest("", pub_key, secret)

    response = mojang.has_joined(name, server_id, request.remote_addr)

    if not response.ok:
        abort(403)

    json = response.json()

    uuid = json.id
    name = json.name

    with open_database() as db:
        user = db.find_user(uuid, name)

        # Invalidate the previous access token
        user.clear_access_token()

        # Generate unique access token
        token = base64.b64encode(guid.uuid4(), altchars="-_")
        # No duplicates
        while db.find_access_token(token) is not None:
            token = base64.b64encode(guid.uuid4(), altchars="-_")
        expires = user.put_access_token(token, request.remote_addr).expires

        return jsonify(
            accessToken=token,
            userId=user.uniqueId,
            expires=int(expires)
        )


def hash_digest(server_id, public_key, secret_key):
    sha = hashlib.sha1()
    sha.update(server_id.encode('utf-8'))
    sha.update(secret_key)
    sha.update(public_key)

    intHash = int.from_bytes(sha.digest(), byteorder='big', signed=True)

    return format(intHash, 'x')


@app.before_first_request
def init_auth():
    global pub_key, priv_key
    (pub_key, priv_key) = rsa.newkeys(1024)

    with open_database() as db:
        db.setup()


@app.errorhandler(404)
def notFound(status):
    # Redirect 404 to 403 for security
    abort(403)


@app.errorhandler(405)
def methodNotAllowed(status):
    return jsonify(error="Method Not Allowed"), 405


@app.errorhandler(ValueError)
@app.errorhandler(KeyError)
def valueError(error):
    # if app.config['DEBUG']:
    #     raise error
    return jsonify(error=type(error).__name__, message=str(error)), 400
