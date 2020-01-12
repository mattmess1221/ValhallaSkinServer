"""Old models from the original code."""

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(sa.String(32), nullable=False, unique=True)
    name = sa.Column(sa.String(16), nullable=False)
    fetched = sa.Column(sa.DateTime, nullable=False, server_default="now()")


class Uploader(Base):
    __tablename__ = 'uploaders'

    id = sa.Column(sa.Integer, primary_key=True)
    user = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    address = sa.Column(sa.String, nullable=False)
    accessed = sa.Column(sa.DateTime, nullable=False, server_default="now()")

    user_obj: User = orm.relationship('User')


class Upload(Base):
    __tablename__ = 'uploads'

    id = sa.Column(sa.Integer, primary_key=True)
    hash = sa.Column(sa.String, nullable=False, unique=True)
    uploader = sa.Column(sa.Integer, sa.ForeignKey('uploaders.id'), nullable=False)
    upload_time = sa.Column(sa.DateTime, nullable=False, server_default="now()")

    uploader_obj: Uploader = orm.relationship("Uploader")


class Texture(Base):
    __tablename__ = 'textures'

    id = sa.Column(sa.Integer, primary_key=True)
    user = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    tex_type = sa.Column(sa.String, nullable=False)
    file = sa.Column(sa.Integer, sa.ForeignKey('uploads.id'))
    metadata_ = sa.Column('metadata', sa.String)

    user_obj: User = orm.relationship("User")
    file_obj: Upload = orm.relationship("Upload")


class Metadata(Base):
    __tablename__ = 'metadata'

    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String, nullable=False)
    value = sa.Column(sa.String)


class Token(Base):
    __tablename__ = 'tokens'

    id = sa.Column(sa.Integer, primary_key=True)
    uploader = sa.Column(sa.Integer, sa.ForeignKey('uploaders.id'), nullable=False, unique=True)
    token = sa.Column(sa.String, nullable=False)
    issued = sa.Column(sa.DateTime, nullable=False, server_default="now()")

    uploader_obj: Uploader = orm.relationship("Uploader")
