#!/usr/bin/python3
from lib.sql import Database
import json

import cgi
#import cgitb
#cgitb.enable()

uuid = cgi.FieldStorage().getvalue("path")
with Database() as db:
    textures = db.get_textures(uuid, False)
if textures is not None and "skin" in textures and "url" in textures["skin"]:
    print("Status: 302 Found")
    print("Location: " + textures["skin"]["url"])
    print()
else:
    print("Status: 404 Not found")
    print("Content-Type: application/json")
    print()
    print(json.dumps({
        "error": "Not Found",
        "message": "The player ID '%s' does not exist on the database" % uuid
    }))
