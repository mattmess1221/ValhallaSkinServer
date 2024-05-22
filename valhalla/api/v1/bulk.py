from typing import Annotated

from fastapi import APIRouter, Depends

from ...crud import CRUD
from ...files import Files
from .schemas import BulkRequest, BulkResponse
from .textures import get_user_textures

router = APIRouter(tags=["User information"])


@router.post("/bulk_textures")
async def bulk_request_textures(
    body: BulkRequest,
    crud: Annotated[CRUD, Depends()],
    files: Annotated[Files, Depends()],
) -> BulkResponse:
    """Bulk request several user textures.

    If a requested user does not have any textures, it is ignored.
    """
    return BulkResponse(
        users=[
            await get_user_textures(user, None, crud, files)
            async for user in crud.resolve_uuids(body.uuids)
        ]
    )
