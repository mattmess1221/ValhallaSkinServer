from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
import sqlalchemy_utils as sau
from sqlalchemy.orm import relationship
from sqlalchemy_utils import generic_repr

from .database import Base


@generic_repr
class SecretSanity(Base):
    __tablename__ = "secret_sanity"
    id = sa.Column(sa.Integer, primary_key=True)
    secret = sa.Column(sau.PasswordType(schemes=["pbkdf2_sha512"]), nullable=False)


@generic_repr
class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(sau.UUIDType, unique=True, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    address = sa.Column(sau.IPAddressType, nullable=False)

    textures = relationship("Texture", back_populates="user")


@generic_repr
class Upload(Base):
    __tablename__ = "uploads"
    id = sa.Column(sa.Integer, primary_key=True)
    hash = sa.Column(sa.String, nullable=False, unique=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    upload_time = sa.Column(sa.DateTime, default=datetime.now, nullable=False)

    user = relationship("User")


@generic_repr
class Texture(Base):
    __tablename__ = "textures"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    upload_id = sa.Column(sa.Integer, sa.ForeignKey("uploads.id"))
    tex_type = sa.Column(sa.String, nullable=False)
    meta = sa.Column(sa.JSON, default=dict)

    start_time = sa.Column(sa.DateTime, default=datetime.now, nullable=False)
    end_time = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="textures")
    upload = relationship("Upload")
