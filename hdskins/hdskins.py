#!/usr/env python3

import base64
import functools
import hashlib
import os
import re
import sqlite3
import time

import imageio
import requests
import rsa
from expiringdict import ExpiringDict
from flask import Flask, Response, abort, jsonify, make_response, request

from.import database, mojang, validate

app = Flask(__name__)


def env(key):
    var = os.getenv(key)
    if var is None:
        raise KeyError(key + " not specified")
    return var

db_file = env('DB_FILE')
root_dir = env('ROOT_DIR')
root_url = env('ROOT_URL')

db = database.Database(sqlite3.connect(db_file))

supported_types = ["skin", "cape", "elytra"]

client_keys = ExpiringDict(max_len=100, max_age_seconds=10)


def authorize(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        header = request.headers.get("Authorization")
        access_token = header[7:]  # Splice after Bearer
        # Don't save this. It is useless once it is refreshed
        if not mojang.validate(access_token, "a", request.remote_addr):
            return abort(make_response(jsonify(message="Not Authorized"), 401))

        return func(args, kwargs)
    return decorator


@app.route('/user/<user>')
@validate.regex(user=validate.uuid)
def get_textures(user):
    with db:
        user = db.find_user(user, False)
        if user is None:
            abort(Response("User not found", 403))
        textures = textures_json(user.textures)
        if not textures:
            abort(Response("Skins not found", 403))
        return make_response(jsonify(
            timestamp=time.time,
            profileId=user.profileId,
            profileName=user.name,
            textures=textures
        ), 200)


def textures_json(textures):
    textures = sorted(textures, lambda item: item.timestamp, True)
    texts = {}
    for tex in textures:
        texType = tex.type.upper()
        if not texts[texType]:  # Only include the first of every type
            dic = {'url': tex.url}
            metadata = metadata_json(tex.metadata)
            if metadata:  # Only include metadata if there is any
                dic.metadata = metadata
            texts[texType] = dic
    return texts


def metadata_json(data):
    metadata = {}
    for meta in data:
        metadata[meta.key] = meta.val
    return metadata


@app.route('/user/<user>/<skinType>', methods=['POST'])
@validate.regex(user=validate.uuid, skin_type=validate.choice(supported_types))
@authorize
def change_skin(user, skin_type):
    model = str(request.form.get("model"))
    url = str(request.form.get("file"))

    skin = copy_image(url)


@app.route('/user/<user>/<skin_type>', methods=['PUT'])
@validate.regex(user=validate.uuid, skin_type=validate.choice(supported_types))
@authorize
def upload_skin(user, skin_type):

    model = str(request.form.get("model"))
    file = request.form.get("file")

    skin = copy_image(file)

    with db:
        user = db.find_user(user)
        user.put_texture(skin, model)

    return ('', 200)


def copy_image(image):
    im = imageio.imread(uri=image, format="png")
    # TODO: check image dimensions.
    # Needs to be power of 2 between 64 and 1024
    sha = hashlib.sha1(im).hexdigest()
    skin = "/textures/" + sha
    with open(root_dir + skin, "w") as file:
        imageio.imwrite(uri=file, im=im, format="png")

    return root_url + skin


@app.route('/user/<user>/<skin_type>', methods=['DELETE'])
@validate.regex(user=validate.uuid, skin_type=validate.choice(supported_types))
@authorize
def reset_skin(user, skin_type):
    # Unimplemented
    pass


@app.route('/auth/request', methods=["POST"])
def auth_request():
    """Use this endpoint to request the server's public key.

    The public key is used by the client to join a server for verification.

    TODO: is this really needed? Probably
    """
    uuid = request.form.get("uuid")
    ckey = base64.decodebytes(request.form.get("client_key"))

    client_keys[uuid] = rsa.PublicKey._load_pkcs1_der(ckey)

    return jsonify(
        public_key=base64.encodebytes(pub_key._save_pkcs1_der())
    )


@app.before_first_request
def init_auth():
    global pub_key, priv_key
    (pub_key, priv_key) = rsa.newkeys(1024)


@app.errorhandler(404)
def notFound(status):
    # Redirect 404 to 403 for security
    abort(make_response(jsonify(message="Forbidden", status=403), 403))


@app.errorhandler(validate.RegexError)
def valueError(error):
    abort(make_response(jsonify(message=error.message, status=400), 400))
