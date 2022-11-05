FROM python:3.10 AS python-base
ENV PIP_NO_CACHE_DIR=no \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_ROOT_USER_ACTION=ignore \
    PDM_USE_VENV=no

FROM python-base AS builder

RUN pip install pdm

COPY pyproject.toml pdm.lock README.md /project/
COPY /valhalla /project/valhalla

WORKDIR /project
RUN pdm install --prod -G prod --no-lock --no-editable

FROM python-base

WORKDIR /project

COPY --from=builder /project/__pypackages__/3.10 /project

ENV PATH=$PATH:/project/bin \
    PYTHONPATH=/project/lib

ENV PATH=$PATH:/project/__pypackages__/$python_release/bin \
    PYTHONPATH=/project/__pypackages__/$python_release/lib

# default port, heroku can override this
ENV PORT=8080
EXPOSE $PORT
CMD gunicorn valhalla:app -k uvicorn.workers.UvicornWorker
