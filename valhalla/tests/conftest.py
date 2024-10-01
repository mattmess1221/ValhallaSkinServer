from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from valhalla.models import User

from ..app import app
from ..auth import current_user
from ..config import Env, settings
from ..crud import CRUD
from ..db import get_db
from ..models import Base

assets = Path(__file__).parent / "assets"

settings.env = Env.TESTING

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker[AsyncSession](engine)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app.router.lifespan_context = app_lifespan


async def override_get_db() -> AsyncGenerator[AsyncSession, Any]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


async def override_current_user(
    crud: Annotated[CRUD, Depends()],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
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
def client(tmpdir: Path) -> Generator[TestClient, Any, None]:
    settings.textures_path = str(tmpdir)
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"


@dataclass
class TestUser:
    uuid: UUID
    name: str

    __test__ = False

    @property
    def auth_header(self) -> dict[str, str]:
        return {"authorization": f"{self.name}:{self.uuid}"}


@pytest.fixture
def user() -> TestUser:
    return TestUser(uuid4(), "TestUser")


@pytest.fixture
def users() -> list[TestUser]:
    """Fixture to get a list of random users"""
    return [TestUser(uuid4(), f"TestUser{n}") for n in range(1, 11)]


@pytest.fixture(scope="function")
def steve_uri(request: pytest.FixtureRequest, httpx_mock: HTTPXMock) -> str | Path:
    uri: tuple[str, Path] | Path = request.param
    if isinstance(uri, tuple):
        url, path = uri
        httpx_mock.add_response(url=url, content=path.read_bytes())
        return url
    return uri
