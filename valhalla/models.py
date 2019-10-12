from __future__ import annotations

from datetime import datetime
from typing import List

import sqlalchemy as sa
import sqlalchemy_utils as sau
from flask import request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import *
from sqlalchemy_utils import generic_repr

__all__ = [
    "db",
    "User",
    "Upload",
    "Texture",
    "Metadata"
]

db = SQLAlchemy()


@generic_repr
class User(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(sau.UUIDType, unique=True, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    address = sa.Column(sau.IPAddressType, nullable=False,
                        default=lambda: request.remote_addr,
                        onupdate=lambda: request.remote_addr)

    textures: List[Texture] = relationship("Texture", back_populates="user")


@generic_repr
class Upload(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    hash = sa.Column(sa.String, nullable=False, unique=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("user.id"), nullable=False)
    upload_time = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)

    user: User = relationship('User')


@generic_repr
class Metadata(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String, nullable=False)
    value = sa.Column(sa.String, nullable=False)
    texture_id = sa.Column(sa.Integer, sa.ForeignKey("texture.id"), nullable=False)

    def __iter__(self):
        return iter([self.key, self.value])


@generic_repr
class Texture(db.Model):

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    upload_id = sa.Column(sa.Integer, sa.ForeignKey("upload.id"))
    tex_type = sa.Column(sa.String, nullable=False)

    user: User = relationship("User", back_populates="textures")
    upload: Upload = relationship("Upload")
    meta: List[Metadata] = relationship("Metadata")

    def todict(self):
        return {
            'url': url_for('static', filename=f'textures/{self.upload.hash}', _external=True),
            'metadata': {
                k: v for k, v in self.meta
            }
        }
