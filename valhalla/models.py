from datetime import datetime
from typing import List

import sqlalchemy as sa
import sqlalchemy_utils as sau
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import *

__all__ = [
    "db",
    "User",
    "Upload",
    "Texture",
    "Metadata"
]

db = SQLAlchemy()


class User(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(sau.UUIDType, unique=True, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    fetched = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    address = sa.Column(sau.IPAddressType, nullable=False)

    textures = relationship("Texture.id", back_populates="user")


class Upload(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    hash = sa.Column(sa.String, nullable=False, unique=True)
    user_id = sa.Column(sa.String, sa.ForeignKey(User.id), nullable=False)
    upload_time = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)


class Metadata(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String, nullable=False)
    value = sa.Column(sa.String, nullable=False)
    texture_id = sa.Column(sa.Integer, sa.ForeignKey("texture.id"), nullable=False)


class Texture(db.Model):
    id: int = sa.Column(sa.Integer, primary_key=True)
    user_id: int = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    upload_id: int = sa.Column(sa.Integer, sa.ForeignKey("upload.id"))
    tex_type: str = sa.Column(sa.String, nullable=False)

    user: User = relationship(User, back_populates="texture")
    upload: Upload = relationship(Upload)
    meta: List[Metadata] = relationship(Metadata)
