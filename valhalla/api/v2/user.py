from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import urljoin
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.exceptions import HTTPException

from ... import models
from ...auth import require_user
from ...crud import CRUD
from ...limit import limiter
from ..utils import get_textures_url
from . import schemas

router = APIRouter(tags=["User information"])


async def get_user_textures(
    user: models.User,
    at: datetime | None,
    crud: CRUD,
    textures_url: str,
) -> schemas.UserTextures:
    textures = await crud.get_user_textures(user, at=at)
    return schemas.UserTextures(
        timestamp=datetime.now(UTC),
        profile_id=user.uuid,
        profile_name=user.name,
        textures={
            k: schemas.Texture(
                url=urljoin(textures_url, v.upload.hash),
                metadata=v.meta,
            )
            for k, v in textures.items()
        },
    )


@router.post("/users")
async def bulk_request_textures(
    body: schemas.BulkRequest,
    crud: Annotated[CRUD, Depends()],
    textures_url: str = Depends(get_textures_url),
) -> schemas.BulkResponse:
    """Bulk request several user textures.

    If a requested user does not have any textures, it is ignored.
    """
    return schemas.BulkResponse(
        users=[
            await get_user_textures(user, None, crud, textures_url)
            async for user in crud.resolve_uuids(body.uuids)
        ]
    )


@router.get("/user")
async def get_texture(
    user: Annotated[models.User, Depends(require_user)],
    crud: Annotated[CRUD, Depends()],
    textures_url: Annotated[str, Depends(get_textures_url)],
) -> schemas.UserTextures:
    return await get_user_textures(user, None, crud, textures_url)


@router.get("/user/{user_id}")
@limiter.shared_limit(
    "60/minute",
    scope="user",
    error_message=(
        "You have surpassed the request limit for this endpoint of 60 requests per"
        " minute. Use '/api/v2/users' if you have multiple users to request."
        " For more details, see https://skins.minelittlepony-mod.com/api/v2"
    ),
)
async def get_user_textures_by_uuid(
    request: Request,
    textures_url: Annotated[str, Depends(get_textures_url)],
    crud: Annotated[CRUD, Depends()],
    user_id: Annotated[UUID, Path()],
    at: datetime | None = None,
) -> schemas.UserTextures:
    """Get the currently logged in user information."""
    user = await crud.get_user_by_uuid(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return await get_user_textures(user, at, crud, textures_url)
