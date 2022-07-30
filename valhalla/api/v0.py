from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request, Response
from pydantic import BaseModel

from .. import models
from ..auth import require_user
from ..crud import CRUD
from ..schemas import LoginMinecraftHandshakeResponse, LoginResponse, UserTextures
from . import v1

router = APIRouter(include_in_schema=False)


class Result(BaseModel):
    message: str


@router.api_route("/user/{user_id}", response_model=UserTextures)
def get_textures(user_id: UUID, crud: CRUD = Depends()):
    return v1.user.get_user_textures(user_id, crud=crud)


@router.api_route(
    "/user/{user_id}/{type}", methods=["POST", "PUT", "DELETE"], response_model=Result
)
def change_skin(
    request: Request,
    user_id: UUID,
    type: str,
    file: str,
    user: models.User = Depends(require_user),
    crud: CRUD = Depends(),
):
    v1.user.upload_skin(request, user_id, type, file, user, crud)
    if request.method == "DELETE":
        return Result(message="skin cleared")
    return Result(message="OK")


@router.api_route(
    "/auth/handshake", methods=["POST"], response_model=LoginMinecraftHandshakeResponse
)
async def auth_handshake(request: Request, name: str = Form()):
    return await v1.auth.minecraft_login(request, name)


@router.api_route("/auth/response", methods=["POST"], response_model=LoginResponse)
def auth_response(
    request: Request,
    response: Response,
    name: str,
    verify_token: int = Form(alias="verifyToken"),
    crud: CRUD = Depends(),
):
    return v1.auth.minecraft_login_callback(request, response, name, verify_token, crud)
