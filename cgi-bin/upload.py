#!/usr/bin/python3
import cgi
import cgitb
import re
import json
import lib.mojang

#import player
cgitb.enable()

class HttpError(Exception):
    def __init__(self, msg = "null", code = 403):
        self.msg = msg
        self.code = code

form = cgi.FieldStorage()
"""The player name"""
name = form.getvalue("name")
"""The player uuid"""
uuid = form.getvalue("uuid")
"""The texture type. Defaults to skin"""
type = form.getvalue("type", "skin")
"""Whether to clear the skin"""
clear = "clear" in form

def change_skin():
    if not name or not uuid:
        raise HttpError("Name and UUID are required", 400)
    if not Validate(name).isValid():
        raise HttpError("Unauthorized", 401)
    if clear:
        #Clear the skin
        pass
    else:
        #Save the uploaded file
        fileitem = form["skin"]
        if not fileitem.file:
            raise HttpError("No skin file was given")
    return {"message":"TODO"}
try:
    response = change_skin()
except HttpError as e:
    print("Status: " + str(e.code))
    response = e.__dict__

print("Content-Type: application/json; charset=utf8")
print()
print(json.dumps(response))
    
    