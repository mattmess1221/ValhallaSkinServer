import json

import requests

_VALIDATE = "https://authserver.mojang.com/validate"
_PROFILE = "https://sessionserver.mojang.com/session/minecrafrt/profile/"


def validate(accessToken):
    """Validate's an access token against Mojang's servers

    http://wiki.vg/Authentication#Validate
    """
    headers = {"Content-Type": "application/json"}
    data = {"accessToken": accessToken}
    response = requests.post(_VALIDATE, json.dumps(data), headers)
    return response.ok()  # 204 means success, but 403 means fail


def get_name(uuid):
    """Gets the player's name from Mojang's API.

    http://wiki.vg/Mojang_API#UUID_-.3E_Profile_.2B_Skin.2FCape
    """
    url = _PROFILE + uuid

    response = requests.get(url)
    return response.json()['name']
