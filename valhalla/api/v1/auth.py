import secrets
from datetime import timedelta

from authlib.integrations.starlette_client import OAuth, OAuthError, StarletteOAuth2App
from expiringdict import ExpiringDict
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from ... import auth, mojang, xbox
from ...config import settings
from ...crud import CRUD
from ...schemas import LoginMinecraftHandshakeResponse, LoginResponse

router = APIRouter(tags=["Authentication"])


# Validate tokens are kept 100 at a time for 30 seconds each
validate_tokens: dict[str, str] = ExpiringDict(100, 30)


@router.get("/auth/logout", status_code=302)
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("token")
    return response


@router.post("/auth/minecraft", response_model=LoginMinecraftHandshakeResponse)
async def minecraft_login(
    request: Request, name: str = Form()
) -> LoginMinecraftHandshakeResponse:
    if not request.client:
        raise HTTPException(400)

    # Generate a random 32 bit integer. It will be checked later.
    verify_token = secrets.randbits(32)
    validate_tokens[verify_token] = name, request.client.host

    return LoginMinecraftHandshakeResponse(
        serverId=settings.server_id,
        verifyToken=verify_token,
    )


@router.post("/auth/minecraft/callback", response_model=LoginResponse)
async def minecraft_login_callback(
    request: Request,
    response: Response,
    name: str,
    verify_token: int = Form(alias="verifyToken"),
    crud: CRUD = Depends(),
) -> LoginResponse:
    if not request.client:
        raise HTTPException(400)
    if verify_token not in validate_tokens:
        raise HTTPException(403)

    try:
        xname, addr = validate_tokens[verify_token]
        if xname != name:
            raise HTTPException(403)
        if addr != request.client.host:
            raise HTTPException(403)
    finally:
        del validate_tokens[verify_token]

    joined = await mojang.has_joined(
        mojang.HasJoinedRequest(
            username=name,
            server_id=settings.server_id,
            ip=request.client.host,
        )
    )

    user = await crud.get_or_create_user(joined.id, joined.name, request.client.host)
    token = auth.token_from_user(user, expire_in=timedelta(hours=1))
    auth_header = f"Bearer {token}"

    response.headers["Authorization"] = token

    return LoginResponse(
        accessToken=auth_header,
        userId=user.uuid,  # type: ignore
    )


xboxlive: StarletteOAuth2App = OAuth().register(
    "xboxlive",
    client_id=settings.xbox_live_client_id,
    client_secret=settings.xbox_live_client_secret,
    server_metadata_url=settings.xbox_live_server_metadata_url,
    client_kwargs=settings.xbox_live_client_kwargs,
)


@router.api_route("/auth/xbox")
async def xbox_login(request: Request):
    callback = request.url_for("xbox_login_callback")
    callback = callback.replace("http://127.0.0.1", "http://localhost")
    return await xboxlive.authorize_redirect(request, callback)


@router.api_route("/auth/xbox/callback")
async def xbox_login_callback(request: Request, crud: CRUD = Depends()):
    if not request.client:
        raise HTTPException(400)
    try:
        token = await xboxlive.authorize_access_token(request)
        profile = await xbox.login_with_xbox(token["access_token"])
        user = await crud.get_or_create_user(
            profile.id, profile.name, request.client.host
        )
        expires = timedelta(days=365)
        token = auth.token_from_user(user, expire_in=expires)

        response = RedirectResponse("/")
        response.headers["Authorization"] = f"Bearer {token}"
        response.set_cookie(
            "token",
            token,
            secure=True,
            httponly=True,
            expires=int(expires.total_seconds()),
        )

        return response
    except (OAuthError, xbox.XboxLoginError) as e:
        raise HTTPException(403, str(e))
