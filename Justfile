dev:
    uv run fastapi dev valhalla/app.py

test:
    uv run pytest

cov:
    just _cov erase
    just _cov run -m pytest
    just _cov report
    just _cov xml

_cov *args:
    uv run coverage {{ args }}

lint:
    - uv run ruff check --fix
    - uv run ruff format

types:
    uv run mypy .
