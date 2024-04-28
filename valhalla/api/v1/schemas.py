import re
from datetime import UTC, datetime
from functools import partial
from typing import Annotated
from uuid import UUID

from fastapi import File, Form, UploadFile
from pydantic import AnyHttpUrl, ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel
from pydantic.alias_generators import to_camel
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import AfterValidator


def convert_skin_type_from_legacy(s: str) -> str:
    s = s.lower().replace("_", ":", 1)
    if ":" not in s:
        ns = "minecraft"
        val = s
    else:
        ns, val = s.split(":", 1)
        ns = re.sub(r"[^a-z0-9._-]", "", ns)
        val = re.sub(r"[^a-z0-9./_-]", "", val)
    return f"{ns}:{val}"


def convert_skin_type_to_legacy(s: str) -> str:
    ns, val = s.split(":", 1)
    if ns == "minecraft":
        return val
    return f"{ns}_{val}"


SkinType = Annotated[
    str,
    AfterValidator(convert_skin_type_from_legacy),
    PlainSerializer(convert_skin_type_to_legacy, when_used="json"),
]


def serialize_datetime(dt: datetime) -> int:
    # convert to milliseconds
    return int(dt.timestamp() * 1000)


Timestamp = Annotated[
    datetime,
    PlainSerializer(
        serialize_datetime,
        return_type=int,
        when_used="json-unless-none",
    ),
]


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class LoginMinecraftHandshakeResponse(BaseModel):
    server_id: str
    verify_token: int
    offline: bool = False


class LoginResponse(BaseModel):
    access_token: str
    user_id: UUID


class Texture(BaseModel):
    url: str
    metadata: dict[str, str] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                "metadata": {"model": "default"},
            }
        }
    )


class UserTextures(BaseModel):
    timestamp: Timestamp = Field(default_factory=partial(datetime.now, UTC))
    profile_id: UUID
    profile_name: str
    textures: dict[SkinType, Texture]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": 1667697567511,
                "profileId": "51aa42eb7aef4b6ab758ab0fadac5ab5",
                "profileName": "Sollace",
                "textures": {
                    "skin": {
                        "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                        "metadata": {"model": "default"},
                    }
                },
            }
        }
    )


class TextureHistoryEntry(BaseModel):
    url: str
    metadata: dict[str, str] | None = None
    start_time: Timestamp
    end_time: Timestamp | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skin": {
                    "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                    "metadata": {
                        "model": "default",
                    },
                    "startTime": 1667697567511,
                    "endTime": None,
                }
            }
        }
    )


class UserTextureHistory(BaseModel):
    profile_id: UUID
    profile_name: str
    textures: dict[SkinType, list[TextureHistoryEntry]]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profileId": "51aa42eb7aef4b6ab758ab0fadac5ab5",
                "profileName": "Sollace",
                "textures": [
                    {
                        "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                        "metadata": {
                            "model": "default",
                        },
                        "startTime": 1667697567511,
                        "endTime": "null",
                    }
                ],
            }
        }
    )


class TextureUpload(BaseModel):
    type: SkinType = Form()
    file: UploadFile = File(media_type="image/png")
    metadata: dict[str, str] | None = Form(None)


class TexturePost(BaseModel):
    type: SkinType
    file: AnyHttpUrl
    metadata: dict[str, str] | None = None


class BulkRequest(BaseModel):
    uuids: list[UUID]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uuids": [
                    "51aa42eb7-aef4-b6ab-758a-b0fadac5ab5",
                ]
            }
        }
    )


class BulkResponse(BaseModel):
    users: list[UserTextures]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "timestamp": 1667697567511,
                        "profileId": "51aa42eb7aef4b6ab758ab0fadac5ab5",
                        "profileName": "Sollace",
                        "textures": {
                            "skin": {
                                "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                                "metadata": {"model": "default"},
                            }
                        },
                    },
                ]
            }
        }
    )
