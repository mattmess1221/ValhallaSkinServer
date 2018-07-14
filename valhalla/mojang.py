import json

import requests

# ?username=username&serverId=hash&ip=ip"
_VALIDATE = "https://sessionserver.mojang.com/session/minecraft/hasJoined"
_PROFILE = "https://sessionserver.mojang.com/session/minecraft/profile/"


def has_joined(name, serverHash, addr):
    """Validates a login against Mojang's servers

    http://wiki.vg/Protocol_Encryption#Authentication
    """
    return requests.get(_VALIDATE, params={
        "username": name,
        "serverId": serverHash,
        "ip": addr
    })  # 204 means success, but 403 means fail


def fetch_profile_name(uuid):
    """Gets the player's name from Mojang's API.

    http://wiki.vg/Mojang_API#UUID_-.3E_Profile_.2B_Skin.2FCape
    """
    url = _PROFILE + uuid

    response = requests.get(url)
    json = response.json()
    if response.ok:
        return json['name']

    raise MojangError(json['errorMessage'])


class MojangError(Exception):
    pass
