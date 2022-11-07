from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import OAuth2
from jose import JWTError, jwt
from starlette import status

from . import models
from .config import settings
from .crud import CRUD

auth_scheme = OAuth2(auto_error=False)


async def current_user(
    header: str | None = Depends(auth_scheme),
    cookie: str | None = Cookie(default=None, alias="token"),
    crud: CRUD = Depends(),
) -> models.User | None:
    if header and header.startswith("Bearer "):
        header = header[7:]
    token = header or cookie
    if token is None:
        return None

    try:
        return await user_from_token(token, crud)
    except JWTError:
        return None


def require_user(user: models.User | None = Depends(current_user)) -> models.User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return user


def token_from_user(user: models.User, *, expire_in: timedelta) -> str:
    payload = {
        "sid": user.id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + expire_in,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


async def user_from_token(token: str, crud: CRUD) -> models.User | None:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    sid = payload["sid"]
    return await crud.get_user(sid)
