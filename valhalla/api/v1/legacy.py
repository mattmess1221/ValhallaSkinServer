from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Request,
    UploadFile,
)
from pydantic import AnyHttpUrl
from starlette import status

from ... import models, schemas
from ...auth import require_user
from ...crud import CRUD
from ...files import Files
from . import auth, textures

router = APIRouter(deprecated=True)

router.add_api_route(
    "/auth/handshake",
    auth.minecraft_login,
    methods=["POST"],
    tags=["Authentication"],
    summary="Start authentication via Minecraft",
    description="Aliased to `/api/v1/auth/minecraft`",
)
router.add_api_route(
    "/auth/response",
    auth.minecraft_login_callback,
    methods=["POST"],
    tags=["Authentication"],
    summary="Callback for authentication via Minecraft",
    description="Aliased to `/api/v1/auth/minecraft/callback`",
)


def check_user(
    user: Annotated[models.User, Depends(require_user)],
    user_id: Annotated[UUID, Path()],
) -> models.User:
    if user_id != user.uuid:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    return user


@router.post("/user/{user_id}/{skin_type}", tags=["Texture Uploads"])
async def post_skin_old(
    request: Request,
    file: Annotated[AnyHttpUrl, Form()],
    user: Annotated[models.User, Depends(check_user)],
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    skin_type: str,
) -> None:
    """Upload a skin texture from a url

    Deprecated: Use the /textures endpoint to upload skins
    """

    form = await request.form()
    meta = {k: v for k, v in form.items() if isinstance(v, str)}
    body = schemas.TexturePost(type=skin_type, file=file, meta=meta)
    await textures.post_texture(body=body, user=user, crud=crud, files=files)


@router.put("/user/{user_id}/{skin_type}", tags=["Texture Uploads"])
async def put_skin_old(
    request: Request,
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
    user: Annotated[models.User, Depends(check_user)],
    file: Annotated[UploadFile, File()],
    file_size: Annotated[int, Depends(textures.valid_content_length)],
    skin_type: str,
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


@router.delete("/user/{user_id}/{skin_type}", tags=["Texture Uploads"])
async def delete_skin_old(
    user: Annotated[models.User, Depends(check_user)],
    crud: Annotated[CRUD, Depends()],
    skin_type: str,
) -> None:
    texture = textures.DeleteTexture(type=skin_type)
    await textures.delete_texture(texture, user, crud)
