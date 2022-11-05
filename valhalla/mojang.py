from uuid import UUID

import httpx
from fastapi import HTTPException

from .schemas import BaseModel

# ?username=username&serverId=hash&ip=ip"
_VALIDATE = "https://sessionserver.mojang.com/session/minecraft/hasJoined"


class HasJoinedRequest(BaseModel):
    username: str
    server_id: str
    ip: str


class HasJoinedResponse(BaseModel):
    id: UUID
    name: str


async def has_joined(params: HasJoinedRequest) -> HasJoinedResponse:
    """Validates a login against Mojang's servers

    http://wiki.vg/Protocol_Encryption#Authentication
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(_VALIDATE, params=params.dict())
        if response.is_success:
            return HasJoinedResponse.parse_obj(response.json())
        raise HTTPException(401)
