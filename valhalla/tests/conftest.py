from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Callable, cast
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, Header
from fastapi.testclient import TestClient
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
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,  # type: ignore
    ),
)


async def override_get_db():
    session: AsyncSession
    async with engine.begin() as session:  # type: ignore
        await session.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


async def override_current_user(
    crud: Annotated[CRUD, Depends()],
    authorization: Annotated[str | None, Header()] = None,
):
    if authorization:
        uname, userid = authorization.split(":")
        uid = UUID(userid)
        return await crud.get_or_create_user(uid, uname)
    return None


app.dependency_overrides[current_user] = override_current_user


@pytest.fixture
def client(tmpdir: Path):
    settings.textures_fs = f"file://{tmpdir}"
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
