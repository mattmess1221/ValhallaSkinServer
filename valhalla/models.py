from __future__ import annotations

from typing import List

import sqlalchemy as sa
import sqlalchemy_utils as sau
from flask import request
from flask_cdn import url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy_utils import generic_repr

__all__ = [
    "db",
    'SecretSanity',
    "User",
    "Upload",
    "Texture"
]

db = SQLAlchemy()


@generic_repr
class AlembicVersion(db.Model):
    version_num = sa.Column(sa.String(32), primary_key=True)


@generic_repr
class SecretSanity(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    secret = sa.Column(sau.PasswordType(schemes=['pbkdf2_sha512']), nullable=False)


@generic_repr
class User(db.Model):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(sau.UUIDType, unique=True, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    address = sa.Column(sau.IPAddressType, nullable=False,
                        default=lambda: request.remote_addr,
                        onupdate=lambda: request.remote_addr)

    textures: List[Texture] = relationship("Texture", back_populates="user")


@generic_repr
class Upload(db.Model):
    __tablename__ = 'uploads'
    id = sa.Column(sa.Integer, primary_key=True)
    hash = sa.Column(sa.String, nullable=False, unique=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    upload_time = sa.Column(sa.DateTime, server_default="now()", nullable=False)

    user: User = relationship('User')


@generic_repr
class Texture(db.Model):
    __tablename__ = 'textures'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    upload_id = sa.Column(sa.Integer, sa.ForeignKey("uploads.id"))
    tex_type = sa.Column(sa.String, nullable=False)
    meta = sa.Column(sa.JSON, default={})

    user: User = relationship("User", back_populates="textures")
    upload: Upload = relationship("Upload")

    def todict(self):
        return {
            'url': url_for('textures', filename=self.upload.hash, _external=True),
            'metadata': self.meta
        }
