from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from . import api, models
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

if settings.textures_fs.startswith("file:///"):
    textures_dir = settings.textures_fs[8:]
    static_textures = StaticFiles(directory=textures_dir)
    app.mount("/textures", static_textures, name="textures")
