from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, Depends

from .v1 import auth, user

router = APIRouter(include_in_schema=False)


def message(msg: str) -> Callable[[], Coroutine[Any, Any, dict[str, str]]]:
    async def view() -> dict[str, str]:
        return {"message": msg}

    return view


router.add_api_route("/auth/handshake", auth.minecraft_login, methods=["POST"])
router.add_api_route("/auth/response", auth.minecraft_login_callback, methods=["POST"])
router.add_api_route("/user/{user_id}", user.get_user_textures_by_uuid)
router.add_api_route(
    "/user/{user_id}/{skin_type}",
    message("OK"),
    methods=["POST"],
    dependencies=[Depends(user.post_skin_old)],
)
router.add_api_route(
    "/user/{user_id}/{skin_type}",
    message("OK"),
    methods=["PUT"],
    dependencies=[Depends(user.put_skin_old)],
)
router.add_api_route(
    "/user/{user_id}/{skin_type}",
    message("skin cleared"),
    methods=["DELETE"],
    dependencies=[Depends(user.delete_skin_old)],
)
