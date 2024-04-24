from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..app import app
from ..auth import current_user
from ..config import Env, settings
from ..crud import CRUD
from ..db import get_db
from ..models import reg

assets = Path(__file__).parent / "assets"

settings.env = Env.TESTING

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker[AsyncSession](engine)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(reg.metadata.create_all)
    yield


app.router.lifespan_context = app_lifespan


async def override_get_db():
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
        user = await crud.get_or_create_user(uid, uname)
        await crud.db.commit()
        await crud.db.refresh(user)
        return user
    return None


app.dependency_overrides[current_user] = override_current_user


@pytest.fixture
def client(tmpdir: Path):
    settings.textures_fs = f"file://{tmpdir}"
    with TestClient(app) as client:
        yield client


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
