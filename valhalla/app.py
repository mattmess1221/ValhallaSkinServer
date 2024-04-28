import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import valhalla

from . import api, models
from .config import settings
from .database import engine


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    async with engine.begin() as session:
        await session.run_sync(models.reg.metadata.create_all)

    if settings.textures_bucket:
        from .files import verify_aws_credentials

        verify_aws_credentials()

    yield


app = FastAPI(
    title="Valhalla Skin Server",
    version=valhalla.__version__,
    description=valhalla.__usage__,
    license_info={
        "name": "MIT License",
        "url": "https://github.com/killjoy1221/ValhallaSkinServer/blob/main/LICENSE",
    },
    lifespan=app_lifespan,
)


@app.middleware("http")
async def redirect_http_to_https(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # redirect to https if using a standard http port. If non-standard, assume dev env
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    port = int(request.headers.get("X-Forwarded-Port", request.url.port or 0))
    if port in (80, 443) and scheme == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url, status.HTTP_308_PERMANENT_REDIRECT)
    return await call_next(request)


@app.api_route("/echo", include_in_schema=False)
async def echo(request: Request) -> dict[str, Any]:
    return {
        "headers": request.headers,
        "url": str(request.url),
        "method": request.method,
    }


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(api.router, prefix="/api")

if settings.textures_bucket is None:
    os.makedirs(settings.textures_path, exist_ok=True)
    static_textures = StaticFiles(directory=settings.textures_path)
    app.mount("/textures", static_textures, name="textures")
