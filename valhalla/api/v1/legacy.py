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

router.add_api_route("/auth/handshake", auth.minecraft_login, methods=["POST"])
router.add_api_route("/auth/response", auth.minecraft_login_callback, methods=["POST"])


def check_user(
    user_id: UUID = Path(),
    user: models.User = Depends(require_user),
) -> models.User:
    if user_id != user.uuid:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    return user


@router.post("/user/{user_id}/{skin_type}", tags=["Texture Uploads"])
async def post_skin_old(
    request: Request,
    skin_type: str,
    file: AnyHttpUrl = Form(),
    user: models.User = Depends(check_user),
    crud: CRUD = Depends(),
    files: Files = Depends(),
):
    """Upload a skin texture from a url

    Deprecated: Use the /textures endpoint to upload skins
    """

    meta = dict(await request.form())
    meta.pop("file")
    texture_data = schemas.TexturePost(type=skin_type, file=file, meta=meta)
    return await textures.post_texture(texture_data, user, crud, files)


@router.put("/user/{user_id}/{skin_type}", tags=["Texture Uploads"])
async def put_skin_old(
    request: Request,
    skin_type: str,
    file: UploadFile = File(),
    file_size: int = Depends(textures.valid_content_length),
    user: models.User = Depends(check_user),
    crud: CRUD = Depends(),
    files: Files = Depends(),
):
    """Upload a skin texture from a file

    Deprecated: Use the /textures endpoint to upload skins
    """

    meta = dict(await request.form())
    meta.pop("file")
    return await textures.put_texture(
        skin_type, file, file_size, meta, user, crud, files
    )


@router.delete("/user/{user_id}/{skin_type}", tags=["Texture Uploads"])
async def delete_skin_old(
    skin_type: str,
    user: models.User = Depends(check_user),
    crud: CRUD = Depends(),
):
    texture = textures.DeleteTexture(type=skin_type)
    await textures.delete_texture(texture, user, crud)
