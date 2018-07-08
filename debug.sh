#!/bin/sh

export FLASK_APP=hdskins/hdskins.py
export FLASK_DEBUG=1

export DB_FILE=hdskins.db
export ROOT_DIR=$(pwd)
export ROOT_URL=http://127.0.0.1:5000

source $(pipenv --venv)/scripts/activate # Does this work on non-windows?
flask run
