from ..subapp import SubApp
from . import history, textures, user

app = SubApp(
    title="Valhalla",
    version="v2.0",
    docs_url="/",
)

app.include_router(history.router)
app.include_router(textures.router)
app.include_router(user.router)
