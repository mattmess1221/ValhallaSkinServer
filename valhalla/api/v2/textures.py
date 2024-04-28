from collections.abc import Sequence
from typing import Annotated

import anyio.to_thread
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from starlette import status

from valhalla.config import settings
from valhalla.utils import (
    download_file,
    read_upload,
    valid_content_length,
)

from ... import image, models
from ...auth import require_user
from ...crud import CRUD
from ...files import Files
from . import schemas

router = APIRouter(tags=["Texture Uploads"])


@router.post("/textures")
async def post_texture(
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    user: Annotated[models.User, Depends(require_user)],
    body: schemas.TexturePost,
) -> None:
    file = await download_file(str(body.file))
    await upload_file(user, body.type, file, body.metadata, crud, files)
    await crud.db.commit()


@router.put("/textures")
async def put_texture(
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    user: Annotated[models.User, Depends(require_user)],
    file: Annotated[UploadFile, File()],
    file_size: Annotated[int, Depends(valid_content_length)],
    type: Annotated[schemas.SkinType, Form()] = "minecraft:skin",
    meta: Annotated[dict[str, str] | None, Form()] = None,
) -> None:
    body = await read_upload(file, file_size)
    await upload_file(user, type, body, meta, crud, files)
    await crud.db.commit()


async def upload_file(
    user: models.User,
    texture_type: str,
    file: bytes,
    meta: dict[str, str] | None,
    crud: CRUD,
    files: Files,
) -> None:
    if texture_type in settings.texture_type_denylist:
        raise HTTPException(status.HTTP_400, "That texture type is not allowed")
    texture_hash = await anyio.to_thread.run_sync(image.gen_skin_hash, file)
    upload = await crud.get_upload(texture_hash)
    if not upload:
        await anyio.to_thread.run_sync(files.put_file, texture_hash, file)
        upload = await crud.put_upload(user, texture_hash)

    await crud.put_texture(user, texture_type, upload, meta or {})


@router.delete("/textures")
async def delete_texture(
    user: Annotated[models.User, Depends(require_user)],
    crud: Annotated[CRUD, Depends()],
    type: Annotated[Sequence[schemas.SkinType], Query()] = ("minecraft:skin",),
) -> None:
    """Delete textures.

    By default, deletes 'minecraft:skin', but can delete
    multiple textures by providing multiple `?type=` query parameters.
    """
    for skin_type in type:
        await crud.put_texture(user, skin_type, None)
    await crud.db.commit()
