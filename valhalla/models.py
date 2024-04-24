# from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship
from sqlalchemy.types import JSON

reg = registry()


@reg.mapped_as_dataclass
class User:
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    uuid: Mapped[UUID] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column()

    textures: Mapped[list["Texture"]] = relationship(
        back_populates="user", init=False, lazy="selectin", repr=False
    )
    uploads: Mapped[list["Upload"]] = relationship(
        back_populates="user", init=False, lazy="selectin", repr=False
    )


@reg.mapped_as_dataclass
class Upload:
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    hash: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    upload_time: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(), default=None
    )

    user: Mapped[User] = relationship(back_populates="uploads", init=False, repr=False)
    textures: Mapped[list["Texture"]] = relationship(
        back_populates="upload", init=False, repr=False
    )


@reg.mapped_as_dataclass
class Texture:
    __tablename__ = "textures"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"))
    tex_type: Mapped[str] = mapped_column()
    meta: Mapped[Any] = mapped_column(JSON, default_factory=dict)

    start_time: Mapped[datetime] = mapped_column(
        insert_default=func.current_timestamp(),
        default=None,
    )
    end_time: Mapped[datetime | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(
        back_populates="textures", init=False, lazy="selectin", repr=False
    )
    upload: Mapped["Upload"] = relationship(
        back_populates="textures", init=False, lazy="selectin", repr=False
    )
