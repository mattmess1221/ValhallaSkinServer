# sqlalchemy isn't 100% with type checking, so disable it in pyright
# mypy has it disabled in pyproject.toml
# pyright: reportGeneralTypeIssues=false
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Iterator, cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select, and_, update
from sqlalchemy.sql.expression import func

from . import models
from .db import get_db


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

    async def resolve_uuids(self, uuids: list[UUID]) -> AsyncIterator[models.User]:
        for uid in uuids:
            usr = await self.get_user_by_uuid(uid)
            if usr:
                yield usr

    async def get_user_textures(
        self,
        user: models.User,
        *,
        at: datetime | None = None,
    ) -> dict[str, models.Texture]:
        result: Iterator[models.Texture] = await self.db.scalars(
            select(models.Texture)
            .options(selectinload(models.Texture.upload))
            .where(
                models.Texture.id.in_(
                    select(func.max(models.Texture.id))
                    .where(
                        models.Texture.user_id == user.id,
                        models.Texture.end_time == None  # noqa: E711
                        if at is None
                        else models.Texture.end_time < at,
                    )
                    .order_by(models.Texture.tex_type)
                    .group_by(models.Texture.tex_type)
                )
            )
        )
        return {item.tex_type: item for item in result}

    async def get_user_textures_history(
        self,
        user: models.User,
        *,
        limit: int | None = None,
        at: datetime | None = None,
    ) -> dict[str, list[models.Texture]]:
        result: AsyncIterator[models.Texture] = await self.db.stream_scalars(
            select(models.Texture)
            .options(selectinload(models.Texture.upload))
            .where(
                models.Texture.user_id == user.id,
                *(() if at is None else (models.Texture.end_time < at,)),
            )
            .order_by(models.Texture.tex_type, models.Texture.id.desc())
            .group_by(models.Texture.tex_type, models.Texture.id),
        )

        results: dict[str, list[models.Texture]] = defaultdict(list)
        async for item in result:
            if item.tex_type in results and len(results[item.tex_type]) == limit:
                continue
            results[item.tex_type].append(item)

        return dict(results)

    async def get_or_create_user(self, uuid: UUID, name: str) -> models.User:
        user = await self.get_user_by_uuid(uuid)
        if user is None:
            user = models.User(uuid=uuid, name=name)
            self.db.add(user)
        elif user.name != name:
            user.name = name

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
        upload: models.Upload | None,
        meta: dict[str, str] | None = None,
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
        if upload:
            self.db.add(
                models.Texture(
                    user=user,
                    upload=upload,
                    tex_type=tex_type,
                    meta=meta or {},
                )
            )
        await self.db.commit()
