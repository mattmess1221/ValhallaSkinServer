from datetime import datetime
from uuid import UUID

import anyio
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from pydantic import AnyHttpUrl
from pydantic.error_wrappers import ErrorWrapper, ValidationError

from ... import image, models, schemas
from ...auth import require_user
from ...byteconv import mb
from ...crud import CRUD
from ...files import Files

router = APIRouter()


@router.get("/@me", response_model=schemas.UserTextures, tags=["User Information"])
async def get_current_user_textures(
    user: models.User = Depends(require_user),
    after: datetime | None = None,
    before: datetime | None = None,
    crud: CRUD = Depends(),
) -> schemas.UserTextures:
    return await get_user_textures(user, after, before, crud)


@router.get(
    "/{user_id}", response_model=schemas.UserTextures, tags=["User Information"]
)
async def get_user_textures_by_uuid(
    user_id: UUID,
    after: datetime | None = None,
    before: datetime | None = None,
    crud: CRUD = Depends(),
) -> schemas.UserTextures:
    """Get the currently logged in user information."""
    user = await crud.get_user_by_uuid(user_id)
    if user is None:
        raise HTTPException(404)
    return await get_user_textures(user, after, before, crud)


async def get_user_textures(
    user: models.User,
    after: datetime | None,
    before: datetime | None,
    crud: CRUD,
):
    return schemas.UserTextures(
        profileId=user.uuid,  # type: ignore
        profileName=user.name,  # type: ignore
        textures={
            k: schemas.Texture.from_orm(v)
            for k, (v,) in await crud.get_user_textures(
                user, limit=1, after=after, before=before
            )
        },
    )


@router.get("/@me/history", tags=["Texture uploads"])
async def get_current_user_texture_history(
    user: models.User = Depends(require_user),
    limit: int | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    crud: CRUD = Depends(),
):
    return await get_user_texture_history(user, limit, after, before, crud)


@router.get("/{user_id}/history", tags=["Texture uploads"])
async def get_user_texture_history_by_uuid(
    user_id: UUID,
    limit: int | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    crud: CRUD = Depends(),
):
    user = await crud.get_user_by_uuid(user_id)
    if user is None:
        raise HTTPException(404)

    return await get_user_texture_history(user, limit, after, before, crud)


async def get_user_texture_history(
    user: models.User,
    limit: int | None,
    after: datetime | None,
    before: datetime | None,
    crud: CRUD,
):
    return schemas.UserTextureHistory(
        profileId=user.uuid,  # type: ignore
        profileName=user.name,  # type: ignore
        textures={
            key: [schemas.TextureHistoryEntry.from_orm(entry) for entry in value]
            for key, value in await crud.get_user_textures(
                user, limit=limit, after=after, before=before
            )
        },
    )


async def httpx_client():
    async with httpx.AsyncClient() as client:
        yield client


@router.post("/@me", tags=["Texture uploads"])
async def post_texture(
    texture: schemas.TexturePost,
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
    files: Files = Depends(),
    http: httpx.AsyncClient = Depends(httpx_client),
):
    head_response = await http.head(texture.file)
    try:
        head_response.raise_for_status()
    except httpx.HTTPError as e:
        raise ValidationError([ErrorWrapper(e, ("body", "file"))], schemas.TexturePost)

    size = int(head_response.headers["content-length"])
    if size > 5 * mb:
        e = Exception("Requested file was too big")
        raise ValidationError([ErrorWrapper(e, ("body", "file"))], schemas.TexturePost)

    get_response = await http.get(texture.file)

    file = await get_response.aread()

    await upload_file(user, texture.type, file, texture.meta, crud, files)


@router.put("/{user_id}")
async def put_texture(
    texture: schemas.TextureUpload,
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
    files: Files = Depends(),
):
    size = int(texture.file.headers["content-length"])
    if size > 5 * mb:
        e = Exception("Requested file was too big")
        raise ValidationError([ErrorWrapper(e, ("body", "file"))], schemas.TexturePost)

    file = await texture.file.read()
    await upload_file(user, texture.type, file, texture.meta, crud, files)


async def upload_file(
    user: models.User,
    texture_type: str,
    file: bytes,
    meta: dict[str, str],
    crud: CRUD,
    files: Files,
):
    texture_hash = await anyio.to_thread.run_sync(image.gen_skin_hash, file)
    upload = await crud.get_upload(texture_hash)
    if not upload:
        await anyio.to_thread.run_sync(files.put_file, texture_hash, file)
        upload = await crud.put_upload(user, texture_hash)

    await crud.put_texture(user, texture_type, upload, meta)
    await crud.db.commit()


@router.post("/{user_id}/{type}", tags=["Texture uploads"], deprecated=True)
async def upload_skin(
    request: Request,
    user_id: UUID,
    type: str,
    file: AnyHttpUrl,
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
):
    """Upload a skin texture

    Deprecated: Use the endpoint starting with /user/@me to upload skins
    """
    if user_id != user.uuid:
        raise HTTPException(401)

    meta = dict(request.query_params)
    meta.pop("file")
    upload = schemas.TexturePost(type=type, file=file, meta=meta)
    return await post_texture(upload, user, crud)
