from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.exceptions import HTTPException

from ... import models, schemas
from ...crud import CRUD

router = APIRouter(tags=["User information"])


async def resolve_user(user_id: UUID = Path(), crud: CRUD = Depends()):
    return await crud.get_user_by_uuid(user_id)


@router.get("/user/{user_id}", response_model=schemas.UserTextures)
async def get_user_textures_by_uuid(
    user: models.User | None = Depends(resolve_user),
    at: datetime | None = None,
    crud: CRUD = Depends(),
) -> schemas.UserTextures:
    """Get the currently logged in user information."""
    if user is None:
        raise HTTPException(404)
    return await get_user_textures(user, at, crud)


async def get_user_textures(
    user: models.User,
    at: datetime | None,
    crud: CRUD,
):
    textures = await crud.get_user_textures(user, limit=1, at=at)
    return schemas.UserTextures(
        profileId=user.uuid,  # type: ignore
        profileName=user.name,  # type: ignore
        textures={k: schemas.Texture.from_orm(v) for k, (v,) in textures.items()},
    )
