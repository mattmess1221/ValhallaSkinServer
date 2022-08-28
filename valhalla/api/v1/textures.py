from typing import AsyncIterable

import anyio
import httpx
from aiofiles.tempfile import TemporaryFile
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from starlette import status

from ... import image, models, schemas
from ...auth import require_user
from ...byteconv import mb
from ...crud import CRUD
from ...files import Files

router = APIRouter(tags=["Texture Uploads"])

max_upload_size = 5 * mb


@router.get("/textures")
async def get_texture(
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
):
    textures = await crud.get_user_textures(user, limit=1)
    return {k: schemas.Texture.from_orm(v) for k, (v,) in textures.items()}


async def download_file(url: str, max_size: int) -> bytes:

    async with httpx.AsyncClient() as http:
        try:
            head_response = await http.head(url)
            head_response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error fetching file: {e}",
            )

        file_size = head_response.headers.get("content-length")
        if not file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file Content-Length is missing",
            )
        if file_size and int(file_size) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file Content-Length is too big",
            )

        async with http.stream("GET", url) as resp:
            file_size = int(resp.headers["content-length"])
            return await read_upload(resp.aiter_bytes(), file_size)


async def read_upload(file: AsyncIterable[bytes], file_size: int):
    real_file_size = 0
    async with TemporaryFile() as temp:
        async for chunk in file:
            real_file_size += len(chunk)
            if real_file_size > file_size:
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            await temp.write(chunk)
        await temp.seek(0)
        return await temp.read()


async def valid_content_length(content_length: int = Header(..., le=max_upload_size)):
    return content_length


async def iter_upload_file(file: UploadFile):
    while chunk := await file.read(1024):
        yield chunk


@router.post("/textures")
async def post_texture(
    texture: schemas.TexturePost,
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
    files: Files = Depends(),
):
    file = await download_file(texture.file, max_upload_size)
    await upload_file(user, texture.type, file, texture.meta, crud, files)


@router.put("/textures")
async def put_texture(
    type: str = Form("skin"),
    file: UploadFile = File(),
    file_size: int = Depends(valid_content_length),
    meta: dict[str, str] | None = Form(None),
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
    files: Files = Depends(),
):
    body = await read_upload(iter_upload_file(file), file_size)
    await upload_file(user, type, body, meta, crud, files)


async def upload_file(
    user: models.User,
    texture_type: str,
    file: bytes,
    meta: dict[str, str] | None,
    crud: CRUD,
    files: Files,
):
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
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
):
    await crud.put_texture(user, texture.type, None)
