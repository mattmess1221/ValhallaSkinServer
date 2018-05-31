#!/bin/sh
export FLASK_APP=hdskins/app.py
export FLASK_DEBUG=1
# source $(pipenv --venv)/bin/activate
flask run
