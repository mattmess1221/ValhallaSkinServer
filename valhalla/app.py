from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from . import api, models, schemas
from .config import settings
from .database import engine

app = FastAPI()


@app.middleware("http")
async def redirect_http_to_https(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # redirect to https if using a standard http port. If non-standard, assume dev env
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    port = request.headers.get("X-Forwarded-Port", request.url.port)
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
    async with engine.begin() as session:
        await session.run_sync(models.Base.metadata.create_all)


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(api.router, prefix="/api")

if settings.textures_fs.startswith("file:///"):
    textures_dir = settings.textures_fs[8:]
    static_textures = StaticFiles(directory=textures_dir)
    app.mount("/textures", static_textures, name="textures")


schemas.fix_openapi_schema(app.openapi())
