from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from .xbox import XboxAuth

# ?username=username&serverId=hash&ip=ip"
_VALIDATE = "https://sessionserver.mojang.com/session/minecraft/hasJoined"


class HasJoinedRequest(BaseModel):
    username: str
    server_id: str
    ip: str

    def dict(self):
        return {snake_to_camel(k): v for k, v in super().dict().items()}


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
            return HasJoinedResponse.parse_obj(response.json)
        raise HTTPException(500)


def snake_to_camel(s: str) -> str:
    words = s.split("_")
    words[1:] = [w.capitalize() for w in words[1:]]
    return "".join(words)
