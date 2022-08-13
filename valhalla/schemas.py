from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import File, Form, UploadFile
from pydantic import AnyHttpUrl, BaseModel, Field, root_validator

from . import models


class LoginMinecraftHandshakeResponse(BaseModel):
    server_id: str = Field(alias="serverId")
    verify_token: int = Field(alias="verifyToken")


class LoginResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    user_id: UUID = Field(alias="userId")

    def dict(self):
        d = super().dict()
        d["userId"] = d["userId"].replace("-", "")
        return d


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
    profileId: UUID
    profileName: str
    textures: dict[str, Texture]


def camel_case(s: str) -> str:
    parts = s.split("_")
    parts[1:] = [_.capitalize() for _ in parts[1:]]
    return "".join(parts)


class TextureHistoryEntry(BaseModel):
    url: str
    meta: dict[str, str] = Field(default_factory=dict)
    startTime: datetime
    endTime: datetime | None

    @root_validator(pre=True)
    def validate_root(cls, values: dict[str, Any]):
        values = {camel_case(k): v for k, v in values.items()}
        if "upload" in values and isinstance(values["upload"], models.Upload):
            upload = values.pop("upload")
            values["url"] = f"https://localhost/textures/{upload.hash}"
        return values

    class Config:
        orm_mode = True


class UserTextureHistory(BaseModel):
    profileId: UUID
    profileName: str
    textures: dict[str, list[TextureHistoryEntry]] = {}


class TextureUpload(BaseModel):
    type: str = Form()
    file: UploadFile = File(media_type="image/png")
    meta: dict[str, str] = Form({})


class TexturePost(BaseModel):
    type: str
    file: AnyHttpUrl
    meta: dict[str, str] = {}
