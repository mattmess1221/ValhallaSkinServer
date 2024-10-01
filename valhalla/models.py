# from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column()

    textures: Mapped[list["Texture"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    uploads: Mapped[list["Upload"]] = relationship(
        back_populates="user", lazy="selectin"
    )


class Upload(Base):
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(primary_key=True)
    hash: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    upload_time: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(), default=None
    )

    user: Mapped[User] = relationship(back_populates="uploads")
    textures: Mapped[list["Texture"]] = relationship(back_populates="upload")


class Texture(Base):
    __tablename__ = "textures"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"))
    tex_type: Mapped[str] = mapped_column()
    meta: Mapped[Any] = mapped_column(JSON, insert_default=dict)

    start_time: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp()
    )
    end_time: Mapped[datetime | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="textures", lazy="selectin")
    upload: Mapped["Upload"] = relationship(back_populates="textures", lazy="selectin")
