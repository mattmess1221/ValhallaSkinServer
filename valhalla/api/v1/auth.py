import secrets
from datetime import timedelta
from typing import Annotated

from expiringdict import ExpiringDict
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response

from ...auth import mojang, token_from_user
from ...config import settings
from ...crud import CRUD
from .schemas import LoginMinecraftHandshakeResponse, LoginResponse

router = APIRouter(tags=["Authentication"])

# Validate tokens are kept 100 at a time for 30 seconds each
validate_tokens: dict[int, tuple[str, str]] = ExpiringDict(100, 30)


def get_client_ip(request: Request) -> str:
    if not request.client:
        raise HTTPException(400)
    return request.headers.get("X-Forwarded-For", request.client.host)


@router.post("/auth/minecraft")
async def minecraft_login(
    client: Annotated[str, Depends(get_client_ip)],
    name: Annotated[str, Form()],
) -> LoginMinecraftHandshakeResponse:
    # Generate a random 32 bit integer. It will be checked later.
    verify_token = secrets.randbits(32)
    validate_tokens[verify_token] = name, client

    return LoginMinecraftHandshakeResponse(
        server_id=settings.server_id,
        verify_token=verify_token,
    )


@router.post("/auth/minecraft/callback")
async def minecraft_login_callback(
    response: Response,
    crud: Annotated[CRUD, Depends()],
    client: Annotated[str, Depends(get_client_ip)],
    name: Annotated[str, Form()],
    verify_token: Annotated[int, Form(alias="verifyToken")],
) -> LoginResponse:
    if verify_token not in validate_tokens:
        raise HTTPException(403)

    try:
        xname, addr = validate_tokens[verify_token]
        if xname != name:
            raise HTTPException(403)
        if addr != client:
            raise HTTPException(403)
    finally:
        del validate_tokens[verify_token]

    joined = await mojang.has_joined(
        username=name,
        server_id=settings.server_id,
    )

    user = await crud.get_or_create_user(joined.id, joined.name)
    token = token_from_user(user, expire_in=timedelta(hours=1))
    auth_header = f"Bearer {token}"

    response.headers["Authorization"] = token

    try:
        return LoginResponse(
            access_token=auth_header,
            user_id=user.uuid,  # type: ignore
        )
    finally:
        await crud.db.commit()


# legacy endpoints

router.add_api_route(
    "/auth/handshake",
    minecraft_login,
    methods=["POST"],
    include_in_schema=False,
)
router.add_api_route(
    "/auth/response",
    minecraft_login_callback,
    methods=["POST"],
    include_in_schema=False,
)
