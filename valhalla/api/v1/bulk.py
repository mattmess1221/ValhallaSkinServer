from typing import Annotated
from fastapi import APIRouter, Depends

from valhalla.api.v1.utils import get_textures_url

from ...crud import CRUD
from ...schemas import BulkRequest, BulkResponse
from .user import get_user_textures

router = APIRouter(tags=["User information"])


@router.post("/bulk_textures", response_model=BulkResponse)
async def bulk_request_textures(
    body: BulkRequest,
    crud: Annotated[CRUD, Depends()],
    textures_url: str = Depends(get_textures_url),
):
    """Bulk request several user textures.

    If a requested user does not have any textures, it is ignored.
    """
    return BulkResponse(
        users=[
            await get_user_textures(user, None, crud, textures_url)
            async for user in crud.resolve_uuids(body.uuids)
        ]
    )
