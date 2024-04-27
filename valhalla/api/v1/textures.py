from datetime import datetime
from typing import Annotated
from urllib.parse import urljoin

import anyio.to_thread
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from starlette import status

from ... import image, models
from ...auth import require_user
from ...config import settings
from ...crud import CRUD
from ...files import Files
from ...utils import download_file, read_upload, valid_content_length
from ..utils import get_textures_url
from . import schemas

router = APIRouter(tags=["Texture Uploads"])


async def get_user_textures(
    user: models.User,
    at: datetime | None,
    crud: CRUD,
    textures_url: str,
) -> schemas.UserTextures:
    textures = await crud.get_user_textures(user, at=at)
    return schemas.UserTextures(
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


@router.get("/textures")
async def get_texture(
    user: Annotated[models.User, Depends(require_user)],
    crud: Annotated[CRUD, Depends()],
    textures_url: Annotated[str, Depends(get_textures_url)],
) -> dict[str, schemas.Texture]:
    user_texts = await get_user_textures(user, None, crud, textures_url)
    return user_texts.textures


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
    type: Annotated[str, Form()] = "skin",
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


class DeleteTexture(BaseModel):
    type: str


@router.delete("/texture")
async def delete_texture(
    texture: DeleteTexture,
    user: Annotated[models.User, Depends(require_user)],
    crud: Annotated[CRUD, Depends()],
) -> None:
    await crud.put_texture(user, texture.type, None)
    await crud.db.commit()
