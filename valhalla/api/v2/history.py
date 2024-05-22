from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ... import models
from ...auth import require_user
from ...crud import CRUD
from ...files import Files
from . import schemas

router = APIRouter(tags=["User History"])


@router.get("/history")
async def get_current_user_texture_history(
    user: Annotated[models.User, Depends(require_user)],
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    limit: int | None = None,
    at: datetime | None = None,
) -> schemas.UserTextureHistory:
    return await get_user_texture_history(user, limit, at, crud, files)


@router.get("/history/{user_id}")
async def get_user_texture_history_by_uuid(
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    user_id: UUID,
    limit: int | None = None,
    at: datetime | None = None,
) -> schemas.UserTextureHistory:
    user = await crud.get_user_by_uuid(user_id)
    if user is None:
        raise HTTPException(404)

    return await get_user_texture_history(user, limit, at, crud, files)


async def get_user_texture_history(
    user: models.User,
    limit: int | None,
    at: datetime | None,
    crud: CRUD,
    files: Files,
) -> schemas.UserTextureHistory:
    textures = await crud.get_user_textures_history(user, limit=limit, at=at)
    return schemas.UserTextureHistory(
        profile_id=user.uuid,  # type: ignore
        profile_name=user.name,  # type: ignore
        textures={
            key: [
                schemas.TextureHistoryEntry(
                    url=files.url_for(path=entry.upload.hash),
                    metadata=entry.meta,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                )
                for entry in value
            ]
            for key, value in textures.items()
        },
    )
