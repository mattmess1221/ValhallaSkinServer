FROM python:3.13 AS python-base
ENV PIP_NO_CACHE_DIR=no \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_ROOT_USER_ACTION=ignore \
    PDM_USE_VENV=no

FROM python-base AS builder
# heroku provides the SOURCE_VERSION env var with commit
ARG SOURCE_VERSION=0.0.0
ENV PDM_CHECK_UPDATE=False \
    PDM_PEP517_SCM_VERSION=$SOURCE_VERSION \
    PDM_USE_VENV=False

RUN pip install -q pdm==2.20.1

COPY pyproject.toml pdm.lock README.md /project/
COPY valhalla USAGE.md /project/valhalla/

WORKDIR /project
RUN pdm install --prod --frozen-lockfile --no-editable

FROM python-base

WORKDIR /project

COPY --from=builder /project/__pypackages__/3.13 /project
COPY alembic.ini /project/etc/valhalla/alembic.ini

ENV PATH=$PATH:/project/bin \
    PYTHONPATH=/project/lib

ENV ALEMBIC_CONFIG=/project/etc/valhalla/alembic.ini

# default port, heroku can override this
ENV PORT=8080
EXPOSE $PORT
CMD alembic upgrade head && \
    gunicorn valhalla.app:app -k uvicorn.workers.UvicornWorker
