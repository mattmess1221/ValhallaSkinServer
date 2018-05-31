#!/usr/env python3

import hashlib
import os
import re
import sqlite3
import time
from functools import wraps

import requests
from flask import Flask, Response, abort, jsonify, request

from.import database, mojang

app = Flask(__name__)

db_file = os.environ['DB_FILE'] or 'hdskins.db'
skin_dir = os.environ['SKIN_DIR'] or exit

db = database.Database(sqlite3.connect(db_file))


def authorize(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        header = request.headers.get("Authorization")
        access_token = header[7:]  # Splice after Bearer
        # Don't save this. It is useless once it is refreshed
        if not mojang.validate(access_token):
            return abort(Response("Not Authorized", 401))

        return func(args, kwargs)
    return decorator


@app.route('/user/<player>')
def get_textures(player):
    validate_uuid(player)
    return jsonify(fetch_skin_data(player))


def fetch_skin_data(uuid):
    with db:
        user = db.find_user(uuid, False)
        if user is None:
            abort(Response("User not found", 403))
        textures = textures_json(user.textures)
        if not textures:
            abort(Response("Skins not found", 403))
        return {
            'timestamp': time.time,
            'profileId': uuid,
            'profileName': user.name,
            'textures': textures
        }


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


@app.route('/user/<player>/<skinType>', methods=['POST'])
@authorize
def change_skin(player, skinType):
    validate_uuid(player)
    validate_skin_type(skinType)

    model = str(request.form.get("model"))
    url = str(request.form.get("file"))
    file = requests.get(url)

    skin = copy_image(file)


@app.route('/user/<user>/<skinType>', methods=['PUT'])
@authorize
def upload_skin(user, skinType):
    validate_uuid(user)
    validate_skin_type(skinType)

    model = str(request.form.get("model"))
    file = request.form.get("file")
    
    skin = copy_image(file)

    with db:
        user = db.find_user(user)


def copy_image(image):
    sha = hashlib.sha1(image).hexdigest()
    skin = skin_dir + "/" + sha
    with open(skin, "w") as file:
        file.write(image)
    # TODO return URL of skin
    return skin


def copy_url(destination):
    pass


@app.route('/user/<player>/<skinType>', methods=['DELETE'])
@authorize
def reset_skin(player, skinType):
    validate_uuid(player)
    validate_skin_type(skinType)
    validate_auth(request.headers)
    pass


@app.errorhandler(404)
def notFound(status):
    # Redirect 404 to 403 for security
    abort(Response("Forbidden", 403))


def validate_uuid(uuid):
    if not re.match(r"[0-9a-f]{32}", uuid):
        abort(Response("Invalid UUID", 400))


def validate_skin_type(skinType):
    if skinType not in ["SKIN", "CAPE", "ELYTRA"]:
        abort(Response("Invalid skin type", 400))


def validate_auth(headers):
    header = headers.get("Authorization")
    token = header[7, ]  # Splice after Bearer
    # Don't save this. It is useless once it is refreshed
    if not mojang.validate(token):
        abort(Response("Not Authorized", 401))
