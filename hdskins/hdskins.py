#!/usr/env python3

import base64
import functools
import hashlib
import os
import re
import time
import tempfile
from io import BytesIO

import requests
import rsa
from expiringdict import ExpiringDict
from flask import Flask, Response, abort, jsonify, request, render_template
from PIL import Image

from .validate import *

from.import database, mojang


def env(key):
    var = os.getenv(key)
    if var is None:
        raise KeyError(key + " not specified")
    return var


app = Flask(__name__)

db_file = env('DB_FILE')
root_dir = env('ROOT_DIR')
root_url = env('ROOT_URL')

supported_types = ["skin", "cape", "elytra"]

client_keys = ExpiringDict(max_len=100, max_age_seconds=10)


def authorize(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if 'name' not in request.form:
            raise KeyError("Missing form: name")
        if 'serverId' not in request.form:
            raise KeyError("Missing form: serverId")
        name = request.form['name']
        server_id = request.form['serverId']
        # Don't save this. It is useless once it is refreshed
        if not mojang.validate(name, server_id, request.remote_addr):
            return abort(401, jsonify(message="Not Authorized"))

        return func(*args, **kwargs)
    return decorator


def metadata_json(data):
    for meta in data:
        yield meta.key, meta.val


def textures_json(textures):
    print(type(textures))
    for texType, tex in textures.items():
        texType = str(texType).upper()
        dic = {'url': root_url + '/textures/' + tex.url}
        metadata = dict(metadata_json(tex.metadata))
        if metadata:  # Only include metadata if there is any
            dic['metadata'] = metadata
        yield texType, dic


@app.route('/user/<user>')
@regex(user=uuid)
def get_textures(user):

    with database.Database(db_file) as db:
        user = db.find_user(user, False)
        if not user:
            return abort(403, "User not found")
        textures = dict(textures_json(dict(user.textures)))
        print(textures)
        if not textures:
            return abort(403, "Skins not found")
        return jsonify(
            timestamp=int(time.time()),
            profileId=user.uniqueId,
            profileName=user.name,
            textures=textures
        ), 200


@app.route('/user/<user>/<skinType>', methods=['POST'])
@regex(user=uuid, skin_type=choice(*supported_types))
@authorize
def change_skin(user, skin_type):
    if 'file' not in request.form:
        raise ValueError('Missing required form: file')

    model = request.form["model"]
    url = request.form.get["file"]

    resp = requests.get(url)

    if resp.ok:
        skin = gen_skin_hash(resp.content)

        put_texture(user, skin, skin_type, request.remote_addr, model=model)

    return 'OK'


@app.route('/user/<user>/<skin_type>', methods=['PUT'])
@regex(user=uuid, skin_type=choice(*supported_types))
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

    with database.Database(db_file) as db:
        user = db.find_user(user)
        texture = user.put_texture(url, skin_type, uploader)
        texture.put_metadata(**metadata)


@app.route('/user/<user>/<skin_type>', methods=['DELETE'])
@regex(user=uuid, skin_type=choice(*supported_types))
@authorize
def reset_skin(user, skin_type):
    with database.Database(db_file) as db:
        user = db.find_user(user)
        if user:
            tex = user.textures[skin_type]
            if tex and tex.clear():
                return Response()
            return abort(404, "Unknown texture")
        return abort(404, "Unknown user")


@app.route('/auth/request', methods=["POST"])
def auth_request():
    """Use this endpoint to request the server's public key.

    The public key is used by the client to join a server for verification.

    TODO: is this really needed? Probably
    """
    def get_form(key):
        if key not in request.form:
            raise KeyError("Missing value: " + key)
        return request.form[key]

    if 'name' not in request.form:
        raise KeyError("Missing value: name")
    if 'shared_key' not in request.form:
        raise KeyError("Missing value: shared_key")
    name = get_form("name")
    ckey = base64.decodebytes(get_form("shared_key"))

    client_keys[name] = rsa.PublicKey._load_pkcs1_der(ckey)

    return jsonify(
        public_key=base64.encodebytes(pub_key._save_pkcs1_der())
    )


@app.before_first_request
def init_auth():
    global pub_key, priv_key
    (pub_key, priv_key) = rsa.newkeys(1024)

    with database.Database(db_file) as db:
        db.setup()


@app.errorhandler(404)
def notFound(status):
    # Redirect 404 to 403 for security
    return render_template("403.html"), 403


@app.errorhandler(ValueError)
def valueError(error):
    if app.config['DEBUG']:
        raise error
    return jsonify(error=type(error).__name__, message=str(error)), 400
