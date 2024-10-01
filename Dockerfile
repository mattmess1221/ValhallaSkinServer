FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
ENV UV_LINK_MODE=copy

ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen  --no-editable --no-dev

FROM python:3.12-slim

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# default port, heroku can override this
ENV PORT=8080
EXPOSE $PORT
CMD alembic upgrade head && \
    fastapi run valhalla/app.py
