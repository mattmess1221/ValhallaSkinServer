from fastapi import FastAPI

from . import auth, bulk, history, textures, user

app = FastAPI(
    title="Valhalla",
    version="v1.0",
    docs_url="/",
)

app.include_router(auth.router)
app.include_router(bulk.router)
app.include_router(history.router)
app.include_router(textures.router)
app.include_router(user.router)
