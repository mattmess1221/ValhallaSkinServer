from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
import sqlalchemy_utils as sau

from .database import Base, C, R, SQLType, col, fk, pk, rel

Integer = cast(type[SQLType[int]], sa.Integer)
String = cast(type[SQLType[str]], sa.String)
DateTime = cast(type[SQLType[datetime]], sa.DateTime)
JSON = cast(type[SQLType[dict[str, str]]], sa.JSON)
UUIDType = cast(type[SQLType[UUID]], sau.UUIDType)


@sau.generic_repr
class User(Base):
    __tablename__ = "users"
    id: C[int] = pk(default=None)
    uuid: C[UUID] = col(UUIDType, unique=True, nullable=False)
    name: C[str] = col(String, nullable=False)

    textures: R[list[Texture]] = rel("Texture", back_populates="user", default=None)


@sau.generic_repr
class Upload(Base):
    __tablename__ = "uploads"
    id: C[int] = pk(default=None)
    hash: C[str] = col(String, nullable=False, unique=True)
    user_id: C[int] = fk("users.id", nullable=False, default=None)
    upload_time: C[datetime] = col(DateTime, default=datetime.now, nullable=False)

    user: R[User] = rel("User", default=None)


@sau.generic_repr
class Texture(Base):
    __tablename__ = "textures"

    id: C[int] = pk(default=None)
    user_id: C[int] = fk("users.id", nullable=False, default=None)
    upload_id: C[int] = fk("uploads.id", nullable=False, default=None)
    tex_type: C[str] = col(String, nullable=False)
    meta: C[dict[str, str]] = col(JSON, default=dict)

    start_time: C[datetime] = col(DateTime, default=datetime.now, nullable=False)
    end_time: C[datetime | None] = col(DateTime, default=None)

    user: R[User] = rel("User", default=None, back_populates="textures")
    upload: R[Upload] = rel("Upload", default=None)
