import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import OAuth2
from joserfc import jwk, jwt
from joserfc.errors import JoseError
from starlette import status

from . import models
from .config import settings
from .crud import CRUD

auth_scheme = OAuth2(auto_error=False)


async def current_user(
    crud: Annotated[CRUD, Depends()],
    header: Annotated[str | None, Depends(auth_scheme)],
    cookie: Annotated[str | None, Cookie(alias="token")] = None,
) -> models.User | None:
    if header and header.startswith("Bearer "):
        header = header[7:]
    token = header or cookie
    if token is None:
        return None

    try:
        return await user_from_token(token, crud)
    except JoseError:
        return None


def require_user(
    user: Annotated[models.User | None, Depends(current_user)],
) -> models.User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return user


jose_key = jwk.import_key(
    hashlib.sha256(settings.secret_key.encode()).digest(), key_type="oct"
)


def token_from_user(user: models.User, *, expire_in: timedelta) -> str:
    header = {"alg": "HS256"}
    claims = {
        "sid": user.id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + expire_in,
    }
    return jwt.encode(header, claims, key=jose_key)


async def user_from_token(token: str, crud: CRUD) -> models.User | None:
    claims = jwt.decode(token, key=jose_key, algorithms=["HS256"]).claims
    sid = claims["sid"]
    return await crud.get_user(sid)
