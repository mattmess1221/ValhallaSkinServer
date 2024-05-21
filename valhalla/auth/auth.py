from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2
from starlette import status

from .. import models
from ..config import settings
from ..crud import CRUD

auth_scheme = OAuth2(auto_error=False)

USER_SESSION_KEY = "user"


async def current_user(
    request: Request,
    crud: Annotated[CRUD, Depends()],
    header: Annotated[str | None, Depends(auth_scheme)],
) -> models.User | None:
    if header:
        return await load_user_from_header(header, crud)

    return await load_user_from_session(request, crud)


def require_user(
    user: Annotated[models.User | None, Depends(current_user)],
) -> models.User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return user


def token_from_user(user: models.User, *, expire_in: timedelta) -> str:
    payload = {
        "sid": user.id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + expire_in,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


async def user_from_token(token: str, crud: CRUD) -> models.User | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None

    user_id = payload.get("sid")
    if isinstance(user_id, int):
        return await crud.get_user(user_id)
    return None


def save_user_to_session(request: Request, user: models.User) -> None:
    request.session[USER_SESSION_KEY] = user.id


async def load_user_from_session(request: Request, crud: CRUD) -> models.User | None:
    user_id = request.session.get(USER_SESSION_KEY)
    if isinstance(user_id, int):
        return await crud.get_user(user_id)
    return None


async def load_user_from_header(header: str, crud: CRUD) -> models.User | None:
    token_type, _, token = header.partition(" ")
    if token_type.lower() != "bearer":
        return None

    return await user_from_token(token, crud)
