from datetime import datetime
from urllib.parse import urljoin
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.exceptions import HTTPException

from ... import models, schemas
from ...crud import CRUD
from .utils import get_textures_url

router = APIRouter(tags=["User information"])


async def resolve_user(user_id: UUID = Path(), crud: CRUD = Depends()):
    return await crud.get_user_by_uuid(user_id)


@router.get("/user/{user_id}", response_model=schemas.UserTextures)
async def get_user_textures_by_uuid(
    user: models.User | None = Depends(resolve_user),
    at: datetime | None = None,
    crud: CRUD = Depends(),
    textures_url: str = Depends(get_textures_url),
) -> schemas.UserTextures:
    """Get the currently logged in user information."""
    if user is None:
        raise HTTPException(404)
    return await get_user_textures(user, at, crud, textures_url)


async def get_user_textures(
    user: models.User,
    at: datetime | None,
    crud: CRUD,
    textures_url: str,
):
    textures = await crud.get_user_textures(user, at=at)
    return schemas.UserTextures(
        profile_id=user.uuid,  # type: ignore
        profile_name=user.name,  # type: ignore
        textures={
            k: schemas.Texture(
                url=urljoin(textures_url, v.upload.hash),
                metadata=v.meta,
            )
            for k, v in textures.items()
        },
    )
