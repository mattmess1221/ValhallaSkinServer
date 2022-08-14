import sys

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from raygun4py import raygunprovider
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from . import api, dashboard, models
from .config import settings
from .database import engine

app = FastAPI()


@app.on_event("startup")
async def onstart():
    session: AsyncSession
    async with engine.begin() as session:
        await session.run_sync(models.Base.metadata.create_all)


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(api.router, prefix="/api")
app.include_router(dashboard.router)

if dashboard.assets:
    app.mount("/dist", dashboard.assets, name="vite")

if settings.textures_fs.startswith("file:///"):
    textures_dir = settings.textures_fs[8:]
    static_textures = StaticFiles(directory=textures_dir)
    app.mount("/textures", static_textures, name="textures")

# public files should be registered last to prevent it from taking over other routes
app.mount("", StaticFiles(packages=[(__package__, "public")]), name="public")

raygun = raygunprovider.RaygunSender(settings.raygun_apikey)


@app.exception_handler(500)
def report_raygun_errors(request: Request, exc: BaseException | None) -> Response:
    raygun.send_exception(exc, sys.exc_info())
    return PlainTextResponse("Internal Server Error", 500)


@app.middleware("http")
async def redirect_localhost(request: Request, call_next):
    if request.url.hostname == "127.0.0.1":
        return RedirectResponse(request.url.replace(hostname="localhost"))
    return await call_next(request)
