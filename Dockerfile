# build the dashboard vite project
FROM node:16-alpine AS dashboard
WORKDIR /src/app/dashboard

RUN npm install -g npm pnpm
COPY dashboard/pnpm-lock.yaml .
RUN pnpm fetch
COPY dashboard/ ./
RUN pnpm install && pnpm build

# base image for python layers
FROM python:3.10-alpine AS python-base

# some configuration.
# python: auto-flush stdout
# pip: disable cache, version checks, and root warnings
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=no \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_ROOT_USER_ACTION=ignore

RUN pip install -q -U pip

# export the lock file to requirements to be used with pip
FROM python-base AS poetry

RUN pip install poetry

WORKDIR /src/app

COPY pyproject.toml poetry.lock ./
RUN poetry export -o requirements.txt

# the final layer, will run the server
FROM python-base

WORKDIR /src/app

# copy over the requirements.txt and install it
COPY --from=poetry /src/app/requirements.txt .
RUN pip install -r requirements.txt

COPY valhalla valhalla
COPY --from=dashboard /src/app .

# default port, heroku can override this
ENV PORT=80
EXPOSE $PORT
CMD gunicorn valhalla:app -k uvicorn.workers.UvicornWorker
