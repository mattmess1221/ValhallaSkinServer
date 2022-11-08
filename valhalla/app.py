import os
from typing import Awaitable, Callable
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

import valhalla

from . import api, models, schemas
from .config import settings
from .database import engine

app = FastAPI(
    title="Valhalla Skin Server",
    version=valhalla.__version__,
    description=valhalla.__usage__,
    license_info={
        "name": "MIT License",
        "url": "https://github.com/killjoy1221/ValhallaSkinServer/blob/main/LICENSE",
    },
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
async def echo(request: Request):
    return {
        "headers": request.headers,
        "url": str(request.url),
        "method": request.method,
    }


@app.on_event("startup")
async def onstart():
    session: AsyncSession
    async with engine.begin() as session:  # type: ignore
        await session.run_sync(models.Base.metadata.create_all)


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(api.router, prefix="/api")

parsed_textures_url = urlparse(settings.textures_fs)
if parsed_textures_url.scheme in ("file", None):
    textures_dir = parsed_textures_url.path[1:]
    os.makedirs(textures_dir, exist_ok=True)
    static_textures = StaticFiles(directory=textures_dir)
    app.mount("/textures", static_textures, name="textures")


schemas.fix_openapi_schema(app.openapi())
