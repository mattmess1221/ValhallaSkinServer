FROM python:3.13

# heroku provides the SOURCE_VERSION env var with commit
ARG SOURCE_VERSION=0.0.0

ENV UV_NO_DEFAULT_GROUPS=1 \
    UV_LOCKED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_LOCKED=1 \
    UV_NO_MANAGED_PYTHON=1

WORKDIR /app

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project

COPY . /app

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync

ENV PATH=$PATH:/app/.venv/bin

# default port, heroku can override this
ENV PORT=8080
CMD alembic upgrade head && \
    fastapi run --port $PORT --proxy-headers

