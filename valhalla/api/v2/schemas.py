import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AnyHttpUrl, ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel
from pydantic.alias_generators import to_camel
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import AfterValidator

ProfileID = Annotated[UUID, Field(examples=["51aa42eb7-aef4-b6ab-758a-b0fadac5ab5"])]
ProfileName = Annotated[str, Field(examples=["Sollace"])]

ProfileIDs = Annotated[
    list[UUID], Field(examples=[["51aa42eb7-aef4-b6ab-758a-b0fadac5ab5"]])
]


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


def validate_skin_type(data: str) -> str:
    if ":" in data:
        ns, val = data.split(":", 1)
    else:
        ns = "minecraft"
        val = data

    if not re.fullmatch(r"[a-z._-]+", ns) or not re.fullmatch(r"[a-z./_-]+", val):
        msg = f"invalid characters in identifier: {data}"
        raise ValueError(msg)

    if ns == "minecraft" and val not in {"skin", "cape", "elytra"}:
        msg = "the 'minecraft' namespace is reserved"
        raise ValueError(msg)

    return f"{ns}:{val}"


def serialize_skin_type(data: str) -> str:
    if ":" in data:
        return data

    if "_" in data:
        ns, vl = data.split("_", 1)
        return f"{ns}:{vl}"

    return f"minecraft:{data}"


SkinType = Annotated[
    str,
    AfterValidator(validate_skin_type),
    Field(
        examples=[
            "minecraft:skin",
            "minecraft:elytra",
        ]
    ),
]
MetadataDict = Annotated[dict[str, str], Field(examples=[{"model": "default"}])]
TextureUrl = Annotated[
    str,
    Field(
        examples=[
            "https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73"
        ]
    ),
]


class Texture(BaseModel):
    url: TextureUrl
    metadata: MetadataDict | None = None


OutSkinType = Annotated[str, PlainSerializer(serialize_skin_type)]
TexturesDict = Annotated[
    dict[OutSkinType, Texture],
    Field(
        examples=[
            {
                "minecraft:skin": Texture(
                    url="https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                    metadata={"model": "default"},
                )
            }
        ]
    ),
]


class UserTextures(BaseModel):
    timestamp: datetime
    profile_id: ProfileID
    profile_name: ProfileName
    textures: TexturesDict


class TextureHistoryEntry(BaseModel):
    url: TextureUrl
    metadata: MetadataDict | None = None
    start_time: datetime
    end_time: datetime | None = None


TexturesHistory = Annotated[
    dict[SkinType, list[TextureHistoryEntry]],
    Field(
        examples=[
            {
                "minecraft:skin": [
                    TextureHistoryEntry(
                        url="https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                        metadata={"model": "default"},
                        start_time=datetime.fromisoformat(
                            "2022-11-06T01:19:27.511000+00:00"
                        ),
                    ),
                    TextureHistoryEntry(
                        url="https://textures.minelittlepony-mod.com/textures/4bbd43fd83ee1053c42994c4bf1db9496ede6b73",
                        metadata={"model": "default"},
                        start_time=datetime.fromisoformat(
                            "2022-11-06T01:19:27.511000+00:00"
                        ),
                        end_time=datetime.fromisoformat(
                            "2022-11-10T10:23:21.511716+00:00"
                        ),
                    ),
                ]
            }
        ]
    ),
]


class UserTextureHistory(BaseModel):
    profile_id: ProfileID
    profile_name: ProfileName
    textures: TexturesHistory


# class TextureUpload(BaseModel):
#     type: Annotated[SkinType, Form()]
#     file: Annotated[UploadFile, File(media_type="image/png")]
#     metadata: Annotated[MetadataDict | None, Form()] = None


class TexturePost(BaseModel):
    type: SkinType
    file: AnyHttpUrl
    metadata: MetadataDict | None = None


class BulkRequest(BaseModel):
    uuids: ProfileIDs


class BulkResponse(BaseModel):
    users: list[UserTextures]
