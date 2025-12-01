FROM python:3.14 AS python-base
ENV PIP_NO_CACHE_DIR=no \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_ROOT_USER_ACTION=ignore

FROM python-base AS builder
# heroku provides the SOURCE_VERSION env var with commit
ARG SOURCE_VERSION=0.0.0
ENV PDM_CHECK_UPDATE=False \
    PDM_PEP517_SCM_VERSION=$SOURCE_VERSION

RUN pip install -q pdm==2.20.1

COPY pyproject.toml pdm.lock README.md /project/
COPY valhalla USAGE.md /project/valhalla/

WORKDIR /project
RUN pdm install --prod --frozen-lockfile --no-editable

FROM python-base

WORKDIR /project

COPY --from=builder /project/.venv .venv
COPY alembic.ini alembic.ini
COPY app.py app.py

ENV PATH=$PATH:/project/.venv/bin

# default port, heroku can override this
ENV PORT=8080
CMD alembic upgrade head && \
    fastapi run --port $PORT --proxy-headers
