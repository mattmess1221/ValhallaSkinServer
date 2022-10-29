from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import File, Form, UploadFile
from pydantic import AnyHttpUrl
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, root_validator
from pydantic.utils import to_lower_camel

from . import models


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
    server_id: str
    verify_token: int


class LoginResponse(BaseModel):
    access_token: str
    user_id: UUID


class Texture(BaseModel):
    url: str
    meta: dict[str, str] | None = None

    @root_validator(pre=True)
    def validate_root(cls, values: dict[str, Any]):
        values = dict(values)
        if "upload" in values and isinstance(values["upload"], models.Upload):
            upload = values.pop("upload")
            values["url"] = f"https://localhost/textures/{upload.hash}"
        return values

    class Config:
        orm_mode = True


class UserTextures(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    profile_id: UUID
    profile_name: str
    textures: dict[str, Texture]


class TextureHistoryEntry(BaseModel):
    url: str
    meta: dict[str, str] = Field(default_factory=dict)
    start_time: datetime
    end_time: datetime | None

    @root_validator(pre=True)
    def validate_root(cls, values: dict[str, Any]):
        if "upload" in values and isinstance(values["upload"], models.Upload):
            upload = values.pop("upload")
            values["url"] = f"https://localhost/textures/{upload.hash}"
        return values

    class Config:
        orm_mode = True


class UserTextureHistory(BaseModel):
    profile_id: UUID
    profile_name: str
    textures: dict[str, list[TextureHistoryEntry]] = {}


class TextureUpload(BaseModel):
    type: str = Form()
    file: UploadFile = File(media_type="image/png")
    meta: dict[str, str] | None = Form(None)


class TexturePost(BaseModel):
    type: str
    file: AnyHttpUrl
    meta: dict[str, str] | None = None


class BulkRequest(BaseModel):
    uuids: list[UUID]


class BulkResponse(BaseModel):
    users: list[UserTextures]
