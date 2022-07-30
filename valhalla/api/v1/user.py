from datetime import datetime
from http.client import UNPROCESSABLE_ENTITY
from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, Path, Request
from fastapi.exceptions import HTTPException
from pydantic.error_wrappers import ErrorWrapper, ValidationError

from ... import image, models, schemas
from ...auth import current_user, require_user
from ...crud import CRUD
from ...files import Files

router = APIRouter()


@router.get(
    "/{user_id}", response_model=schemas.UserTextures, tags=["User Information"]
)
@router.get("/@me", response_model=schemas.UserTextures, tags=["User Information"])
def get_user_textures(
    user_id: UUID | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
):
    """Get the currently logged in user information."""
    if user_id is not None:
        user = crud.get_user_by_uuid(user_id)

    return schemas.UserTextures(
        profileId=user.uuid,  # type: ignore
        profileName=user.name,  # type: ignore
        textures={
            k: schemas.Texture.from_orm(v)
            for k, (v,) in crud.get_user_textures(
                user, limit=1, after=after, before=before
            )
        },
    )


@router.get("/{user_id}/history", tags=["Texture uploads"])
@router.get("/@me/history", tags=["Texture uploads"])
def get_user_texture_history(
    user_id: UUID | None = Path(None),
    user: models.User = Depends(current_user),
    limit: int | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    crud: CRUD = Depends(),
):
    if user_id is not None:
        user = crud.get_user_by_uuid(user_id)

    return schemas.UserTextureHistory(
        profileId=user.uuid,  # type: ignore
        profileName=user.name,  # type: ignore
        textures={
            key: [schemas.TextureHistoryEntry.from_orm(entry) for entry in value]
            for key, value in crud.get_user_textures(
                user, limit=limit, after=after, before=before
            )
        },
    )


import httpx


async def httpx_client():
    async with httpx.AsyncClient() as client:
        yield client


from ...byteconv import mb


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

    await anyio.to_thread.run_sync(
        upload_file, user, texture.type, file, texture.meta, crud, files
    )


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
    await anyio.to_thread.run_sync(
        upload_file, user, texture.type, file, texture.meta, crud, files
    )


def upload_file(
    user: models.User,
    texture_type: str,
    file: bytes,
    meta: dict[str, str],
    crud: CRUD,
    files: Files,
):
    texture_hash = image.gen_skin_hash(file)
    upload = crud.get_upload(texture_hash)
    if not upload:
        files.put_file(texture_hash, file)
        upload = crud.put_upload(user, texture_hash)

    crud.put_texture(user, texture_type, upload, meta)
    crud.db.commit()


@router.post("/{user_id}/{type}", tags=["Texture uploads"], deprecated=True)
def upload_skin(
    request: Request,
    user_id: UUID,
    type: str,
    file: str,
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
    return upload_texture(upload, user, crud)
