from fastapi import FastAPI

from . import microsoft, v0, v1


def setup(app: FastAPI) -> None:
    app.include_router(microsoft.router)
    app.mount("/api/v1", v1.app, "api-v1")
    app.include_router(v0.router, prefix="/api")
