#!/bin/sh


export FLASK_APP=hdskins/hdskins.py
export FLASK_DEBUG=1

export DB_FILE=hdskins.db
export SKIN_DIR=textures
export ROOT_URL=127.0.0.1

source $(pipenv --venv)/bin/scripts/activate # Does this work on non-windows?
flask run
