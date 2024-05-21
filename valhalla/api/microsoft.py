from typing import Annotated
from uuid import UUID

from authlib.integrations.starlette_client import OAuth, OAuthError, StarletteOAuth2App
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..auth import auth, xbox
from ..config import settings
from ..crud import CRUD

router = APIRouter(tags=["OAuth2"])

xboxlive: StarletteOAuth2App = OAuth().register(
    "xboxlive",
    client_id=settings.xbox_live_client_id,
    client_secret=settings.xbox_live_client_secret,
    server_metadata_url="https://login.live.com/.well-known/openid-configuration",
    client_kwargs={"scope": "XboxLive.signin offline_access"},
)  # type: ignore


@router.api_route("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@router.api_route("/auth/xbox")
async def xbox_login(request: Request) -> RedirectResponse:
    callback = request.url_for("xbox_login_callback")
    return await xboxlive.authorize_redirect(request, callback)


@router.api_route("/auth/xbox/callback")
async def xbox_login_callback(
    request: Request, crud: Annotated[CRUD, Depends()]
) -> RedirectResponse:
    if not request.client:
        raise HTTPException(400)
    try:
        token = await xboxlive.authorize_access_token(request)
        profile = await xbox.login_with_xbox(token["access_token"])
    except (OAuthError, xbox.XboxLoginError) as e:
        raise HTTPException(403, str(e)) from None
    else:
        user = await crud.get_or_create_user(UUID(profile["id"]), profile["name"])
        auth.save_user_to_session(request, user)

        await crud.db.commit()
        return RedirectResponse("/")