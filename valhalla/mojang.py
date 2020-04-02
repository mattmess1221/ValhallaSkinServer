import requests

# ?username=username&serverId=hash&ip=ip"
_VALIDATE = "https://sessionserver.mojang.com/session/minecraft/hasJoined"


def has_joined(name: str, server_hash: str, address: str) -> requests.Response:
    """Validates a login against Mojang's servers

    http://wiki.vg/Protocol_Encryption#Authentication
    """
    return requests.get(_VALIDATE, params={
        "username": name,
        "serverId": server_hash,
        "ip": address
    })  # 204 means success, but 403 means fail
