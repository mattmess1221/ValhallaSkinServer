from fastapi import APIRouter, Depends

from . import v1

router = APIRouter(include_in_schema=False)


def message(msg: str):
    async def view():
        return {"message": msg}

    return view


router.add_api_route("/auth/handshake", v1.auth.minecraft_login, methods=["POST"])
router.add_api_route(
    "/auth/response", v1.auth.minecraft_login_callback, methods=["POST"]
)
router.add_api_route("/user/{user_id}", v1.user.get_user_textures_by_uuid)

router.add_api_route(
    "/user/{user_id}/{skin_type}",
    message("OK"),
    methods=["POST"],
    dependencies=[Depends(v1.legacy.post_skin_old)],
)
router.add_api_route(
    "/user/{user_id}/{skin_type}",
    message("OK"),
    methods=["PUT"],
    dependencies=[Depends(v1.legacy.put_skin_old)],
)
router.add_api_route(
    "/user/{user_id}/{skin_type}",
    message("skin cleared"),
    methods=["DELETE"],
    dependencies=[Depends(v1.legacy.delete_skin_old)],
)
