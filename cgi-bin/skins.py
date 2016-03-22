#!/usr/bin/python3
import cgitb
cgitb.enable()
import cgi
import re, time, json

from lib.sql import Database
data = cgi.FieldStorage()
def build_skin(uuid):
    with Database() as db:
        result = db.get_name(uuid)
        if result is None:
            return {
                "error": "404 Not Found",
                "message":"Player with ID '%s' has no skin"%uuid
            }
        else:
            (name,) = result
            textures = db.get_textures(uuid)
            obj = {
                "timestamp": int(time.time()*1000),
                "profileId": uuid,
                "profileName": name,
                "textures": textures
            }
    return obj

uuid = data.getfirst("uuid")
out = {}
if uuid is None:
    out.update({
        "error": "502 Forbidden",
        "message": "Missing UUID"
    })
elif not re.match("^[\w\d]{32}$", uuid):
    out.update({
        "error": "502 Forbidden",
        "message": "Invalid UUID"
    })
else:
    out.update(build_skin(uuid))
    print("Content-Type: application/json")
    if 'error' in out:
        print("Code: " + out['error'])
    print()
    print(json.dumps(out))
