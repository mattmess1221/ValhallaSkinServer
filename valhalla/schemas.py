from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import File, Form, UploadFile
from pydantic import AnyHttpUrl
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from pydantic.utils import to_lower_camel

openapi_type_fixes = {
    # type, format
    ("string", "date-time"): ("integer", "int64"),
}


def fix_openapi_schema(openapi: dict[str, Any]):
    """Fix schema for custom serializations.

    Current serialization fixes:
    datetime -> int
    """
    for model in openapi["components"]["schemas"].values():
        for field in model["properties"].values():
            typ, fmt = field["type"], field.get("format")
            if (typ, fmt) in openapi_type_fixes:
                typ, fmt = openapi_type_fixes[typ, fmt]
                field["type"] = typ
                field["format"] = fmt


def serialize_uuid(u: UUID):
    return str(u).replace("-", "")


def serialize_datetime(dt: datetime):
    # convert to milliseconds
    return int(dt.timestamp() * 1000)


class BaseModel(PydanticBaseModel):
    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True
        json_encoders = {
            datetime: serialize_datetime,
            UUID: serialize_uuid,
        }


class LoginMinecraftHandshakeResponse(BaseModel):
    verify_token: int
    server_id: str = ""
    offline: bool = False


class LoginResponse(BaseModel):
    access_token: str
    user_id: UUID


class Texture(BaseModel):
    url: str
    metadata: dict[str, str] | None = None

    class Config:
        schema_extra = {
            "example": {
                "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",  # noqa: B950
                "metadata": {"model": "default"},
            }
        }


class UserTextures(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    profile_id: UUID
    profile_name: str
    textures: dict[str, Texture]

    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1667697567511,
                "profileId": "51aa42eb7aef4b6ab758ab0fadac5ab5",
                "profileName": "Sollace",
                "textures": {"skin": Texture.Config.schema_extra["example"]},
            }
        }


class TextureHistoryEntry(BaseModel):
    url: str
    metadata: dict[str, str] | None = None
    start_time: datetime
    end_time: datetime | None

    class Config:
        schema_extra = {
            "example": {
                "url": "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",  # noqa: B950
                "metadata": {
                    "model": "default",
                },
                "startTime": 1667697567511,
                "endTime": "null",
            }
        }


class UserTextureHistory(BaseModel):
    profile_id: UUID
    profile_name: str
    textures: dict[str, list[TextureHistoryEntry]]

    class Config:
        schema_extra = {
            "example": {
                "profileId": "51aa42eb7aef4b6ab758ab0fadac5ab5",
                "profileName": "Sollace",
                "textures": [
                    TextureHistoryEntry.Config.schema_extra["example"],
                ],
            }
        }


class TextureUpload(BaseModel):
    type: str = Form()
    file: UploadFile = File(media_type="image/png")
    metadata: dict[str, str] | None = Form(None)


class TexturePost(BaseModel):
    type: str
    file: AnyHttpUrl
    metadata: dict[str, str] | None = None


class BulkRequest(BaseModel):
    uuids: list[UUID]

    class Config:
        schema_extra = {
            "example": {
                "uuids": [
                    "51aa42eb7-aef4-b6ab-758a-b0fadac5ab5",
                ]
            }
        }


class BulkResponse(BaseModel):
    users: list[UserTextures]

    class Config:
        schema_extra = {
            "example": {
                "users": [
                    UserTextures.Config.schema_extra["example"],
                ]
            }
        }
