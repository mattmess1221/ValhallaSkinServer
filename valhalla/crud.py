from datetime import datetime
from operator import attrgetter
from typing import cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import AsyncScalarResult, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select, and_, update

from . import models
from .db import get_db
from .util import agroupby, aislice, alist


class CRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)) -> None:
        self.db = db

    async def get_user(self, user_id: int) -> models.User | None:
        result: ScalarResult = await self.db.scalars(
            cast(Select, select(models.User)).where(models.User.id == user_id).limit(1)
        )
        return result.one_or_none()

    async def get_user_by_uuid(self, uuid: UUID) -> models.User | None:
        result: ScalarResult = await self.db.scalars(
            cast(Select, select(models.User)).where(models.User.uuid == uuid).limit(1)
        )
        return result.one_or_none()

    async def get_user_textures(
        self,
        user: models.User,
        *,
        limit: int | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[tuple[str, list[models.Texture]]]:
        result: AsyncScalarResult = await self.db.stream_scalars(
            cast(Select, select(models.Texture))
            .options(selectinload(models.Texture.upload))
            .where(
                and_(
                    models.Texture.user_id == user.id,
                    *((models.Texture.start_time > after,) if after else ()),
                    *((models.Texture.end_time < before) if before else ()),
                )
            )
            .order_by(models.Texture.start_time.desc())
            .limit(limit)
        )

        return [
            (k, await alist(aislice(v, limit)))
            async for k, v in agroupby(result, key=attrgetter("tex_type"))
        ]

    async def get_or_create_user(
        self, uuid: UUID, name: str, address: str
    ) -> models.User:
        user = await self.get_user_by_uuid(uuid)
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

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_upload(self, texture_hash: str) -> models.Upload | None:
        results: ScalarResult = await self.db.scalars(
            cast(Select, select(models.Upload))
            .where(models.Upload.hash == texture_hash)
            .limit(1)
        )
        return results.one_or_none()

    async def put_upload(self, user: models.User, texture_hash: str):
        upload = models.Upload(
            hash=texture_hash,
            user=user,
        )
        self.db.add(upload)
        return upload

    async def put_texture(
        self,
        user: models.User,
        tex_type: str,
        upload: models.Upload,
        meta: dict[str, str],
    ):
        await self.db.execute(
            update(
                models.Texture,
                whereclause=and_(
                    models.Texture.user == user,
                    models.Texture.tex_type == tex_type,
                ),
                values={models.Texture.end_time: datetime.now()},
            )
        )
        self.db.add(
            models.Texture(
                user=user,
                upload=upload,
                tex_type=tex_type,
                meta=meta,
            )
        )
