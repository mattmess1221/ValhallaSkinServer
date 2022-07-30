import itertools
from datetime import datetime
from operator import attrgetter
from typing import Iterator
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from . import models, schemas
from .db import get_db


class CRUD:
    def __init__(self, db: Session = Depends(get_db)) -> None:
        self.db = db

    def _users(self):
        return self.db.query(models.User)

    def get_user(self, user_id: int) -> models.User | None:
        return self._users().filter(models.User.id == user_id).first()

    def get_user_by_uuid(self, uuid: UUID) -> models.User | None:
        return self._users().filter(models.User.uuid == uuid).first()

    def get_user_textures(
        self,
        user: models.User,
        *,
        limit: int | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> Iterator[tuple[str, Iterator[models.Texture]]]:
        return (
            (k, itertools.islice(v, limit))
            for k, v in itertools.groupby(
                self.db.query(models.Texture)
                .join(models.Upload)
                .filter(
                    models.Texture.user == user,
                    *((models.Texture.start_time > after,) if after else ()),
                    *((models.Texture.end_time < before) if before else ()),
                )
                .order_by(models.Texture.start_time.desc())
                .limit(limit),
                key=attrgetter("tex_type"),
            )
        )

    def get_or_create_user(self, uuid: UUID, name: str, address: str) -> models.User:
        user = self.get_user_by_uuid(uuid)
        if user is None:
            user = models.User(
                uuid=uuid,
                name=name,
                address=address,
            )
            self.db.add(user)
        elif user.name != name:
            user.name = name  # type: ignore
            user.address = address  # type: ignore
        else:
            user.address = address  # type: ignore

        self.db.commit()

        return user

    def get_upload(self, texture_hash: str) -> models.Upload | None:
        return (
            self.db.query(models.Upload)
            .filter(models.Upload.hash == texture_hash)
            .one_or_none()
        )

    def put_upload(self, user: models.User, texture_hash: str):
        upload = models.Upload(
            hash=texture_hash,
            uploader=user,
        )
        self.db.add(upload)
        return upload

    def put_texture(
        self,
        user: models.User,
        tex_type: str,
        upload: models.Upload,
        meta: dict[str, str],
    ):
        self.db.query(models.Texture).filter(
            models.Texture.user == user,
            models.Texture.tex_type == tex_type,
        ).update({models.Texture.end_time: datetime.now()})
        self.db.add(
            models.Texture(
                user=user,
                upload=upload,
                tex_type=tex_type,
                meta=meta,
            )
        )
