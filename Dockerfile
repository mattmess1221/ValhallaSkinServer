FROM python:3.7

ARG YOUR_ENV

ENV YOUR_ENV=${YOUR_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.0.5

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /src/app
COPY poetry.lock pyproject.toml /src/app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY . /src/app

ENV PORT=5000
CMD [ "gunicorn", "wsgi" ]
