from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ... import models, schemas
from ...auth import require_user
from ...crud import CRUD

router = APIRouter(tags=["User History"])


@router.get("/history")
async def get_current_user_texture_history(
    user: models.User = Depends(require_user),
    limit: int | None = None,
    at: datetime | None = None,
    crud: CRUD = Depends(),
):
    return await get_user_texture_history(user, limit, at, crud)


@router.get("/history/{user_id}")
async def get_user_texture_history_by_uuid(
    user_id: UUID,
    limit: int | None = None,
    at: datetime | None = None,
    crud: CRUD = Depends(),
):
    user = await crud.get_user_by_uuid(user_id)
    if user is None:
        raise HTTPException(404)

    return await get_user_texture_history(user, limit, at, crud)


async def get_user_texture_history(
    user: models.User,
    limit: int | None,
    at: datetime | None,
    crud: CRUD,
):
    textures = await crud.get_user_textures(user, limit=limit, at=at)
    return schemas.UserTextureHistory(
        profile_id=user.uuid,  # type: ignore
        profile_name=user.name,  # type: ignore
        textures={
            key: [schemas.TextureHistoryEntry.from_orm(entry) for entry in value]
            for key, value in textures.items()
        },
    )
