from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Request, UploadFile, status
from fastapi.exceptions import HTTPException
from pydantic import AnyHttpUrl

from ... import models
from ...auth import require_user
from ...crud import CRUD
from ...files import Files
from ...limit import limiter
from . import schemas, textures

router = APIRouter(tags=["User information"])


async def resolve_user(
    crud: Annotated[CRUD, Depends()],
    user_id: Annotated[UUID, Path()],
) -> models.User | None:
    return await crud.get_user_by_uuid(user_id)


@router.get("/user/{user_id}")
@limiter.shared_limit(
    "60/minute",
    scope="user",
    error_message=(
        "You have surpassed the request limit for this endpoint of 60 requests per"
        " minute. Use '/api/v1/bulk_textures' if you have multiple users to request."
        " For more details, see https://skins.minelittlepony-mod.com/api/v1"
    ),
)
async def get_user_textures_by_uuid(
    request: Request,
    files: Annotated[Files, Depends()],
    crud: Annotated[CRUD, Depends()],
    user: Annotated[models.User | None, Depends(resolve_user)],
    at: datetime | None = None,
) -> schemas.UserTextures:
    """Get the currently logged in user information.

    This endpoint has a request limit of 60 per minute. For requesting
    multiple users at once, use the [`/api/v1/bulk_textures`][bt] endpoint.

    [bt]: #/User%20information/bulk_request_textures_api_v1_bulk_textures_post
    """
    if user is None:
        raise HTTPException(404)
    return await textures.get_user_textures(user, at, crud, files)


def check_user(
    user: Annotated[models.User, Depends(require_user)],
    user_id: Annotated[UUID, Path()],
) -> models.User:
    if user_id != user.uuid:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    return user


@router.post("/user/{user_id}/{skin_type}", deprecated=True)
async def post_skin_old(
    request: Request,
    file: Annotated[AnyHttpUrl, Form()],
    user: Annotated[models.User, Depends(check_user)],
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    skin_type: schemas.SkinType,
) -> None:
    """Upload a skin texture from a url

    Deprecated: Use the /textures endpoint to upload skins
    """

    form = await request.form()
    meta = {k: v for k, v in form.items() if isinstance(v, str)}
    body = schemas.TexturePost(type=skin_type, file=file, metadata=meta)
    await textures.post_texture(body=body, user=user, crud=crud, files=files)


@router.put("/user/{user_id}/{skin_type}", deprecated=True)
async def put_skin_old(
    request: Request,
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    user: Annotated[models.User, Depends(check_user)],
    file: Annotated[UploadFile, File()],
    file_size: Annotated[int, Depends(textures.valid_content_length)],
    skin_type: schemas.SkinType,
) -> None:
    """Upload a skin texture from a file

    Deprecated: Use the /textures endpoint to upload skins
    """

    form = await request.form()
    meta = {k: v for k, v in form.items() if isinstance(v, str)}
    await textures.put_texture(
        crud=crud,
        files=files,
        user=user,
        file=file,
        file_size=file_size,
        type=skin_type,
        meta=meta,
    )


@router.delete("/user/{user_id}/{skin_type}", deprecated=True)
async def delete_skin_old(
    user: Annotated[models.User, Depends(check_user)],
    crud: Annotated[CRUD, Depends()],
    skin_type: schemas.SkinType,
) -> None:
    texture = textures.DeleteTexture(type=skin_type)
    await textures.delete_texture(texture, user, crud)
