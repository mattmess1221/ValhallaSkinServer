from urllib import request
from urllib.error import URLError

_AUTH = "https://authserver.mojang.com"
_URL = _AUTH + "/validate"

def validate(accessToken):
    headers = {"Content-Type": "application/json"}
    data = """{"accessToken":"%s"}""" % accessToken
    req = request.Request(
        url = _URL,
        data = bytes(data, "utf-8"),
        headers = headers,
        method = "POST")
    try:
        request.urlopen(req)
    except URLError as e:
        return False
    else:
        return True
