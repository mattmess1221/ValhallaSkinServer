from datetime import datetime
from uuid import UUID

from fastapi import File, Form, UploadFile
from pydantic import AnyHttpUrl
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from pydantic.utils import to_lower_camel


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
    metadata: dict[str, str] | None = None


class UserTextures(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    profile_id: UUID
    profile_name: str
    textures: dict[str, Texture]


class TextureHistoryEntry(BaseModel):
    url: str
    metadata: dict[str, str] | None = None
    start_time: datetime
    end_time: datetime | None


class UserTextureHistory(BaseModel):
    profile_id: UUID
    profile_name: str
    textures: dict[str, list[TextureHistoryEntry]] = {}


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


class BulkResponse(BaseModel):
    users: list[UserTextures]
