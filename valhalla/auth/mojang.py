from typing import TypedDict

import httpx
from fastapi import HTTPException

# ?username=username&serverId=hash&ip=ip"
_VALIDATE = "https://sessionserver.mojang.com/session/minecraft/hasJoined"


class HasJoinedResponse(TypedDict):
    id: str
    name: str


async def has_joined(*, username: str, server_id: str) -> HasJoinedResponse:
    """Validates a login against Mojang's servers

    http://wiki.vg/Protocol_Encryption#Authentication
    """
    params = {
        "username": username,
        "serverId": server_id,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(_VALIDATE, params=params)
        if response.is_success:
            try:
                data = response.json()
            except ValueError:
                pass
            else:
                return HasJoinedResponse(data)
        raise HTTPException(401)
