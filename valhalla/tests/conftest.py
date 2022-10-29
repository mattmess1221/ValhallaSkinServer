from dataclasses import dataclass
from pathlib import Path
from typing import Callable, cast
from uuid import UUID, uuid4

import pytest

# use async-asgi-testclient instead of the starlette one because of
# https://github.com/encode/starlette/issues/472
from async_asgi_testclient import TestClient
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..app import app
from ..auth import current_user
from ..config import Env, settings
from ..crud import CRUD
from ..database import Base
from ..db import get_db

assets = Path(__file__).parent / "assets"

settings.env = Env.TESTING

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = cast(
    Callable[[], AsyncSession],
    sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession),
)


async def override_get_db():
    session: AsyncSession
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


async def override_current_user(
    authorization: str | None = Header(None),
    crud: CRUD = Depends(),
):
    if authorization:
        uname, userid = authorization.split(":")
        userid = UUID(userid)
        return await crud.get_or_create_user(userid, uname)
    return None


app.dependency_overrides[current_user] = override_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def anyio_backend():
    return "asyncio"


@dataclass
class TestUser:
    uuid: UUID
    name: str

    __test__ = False

    @property
    def auth_header(self):
        return {"authorization": f"{self.name}:{self.uuid}"}


@pytest.fixture
def user():
    return TestUser(uuid4(), "TestUser")


@pytest.fixture
def users():
    """Fixture to get a list of random users"""
    return [TestUser(uuid4(), f"TestUser{n}") for n in range(1, 11)]
