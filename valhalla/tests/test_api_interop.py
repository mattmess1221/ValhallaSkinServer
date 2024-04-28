import pytest

from valhalla.models import Texture, Upload, User

from .assets import steve_file_data
from .conftest import TestClient, TestingSessionLocal, TestUser


def test_interop_v1_to_v2(client: TestClient, user: TestUser) -> None:
    client.headers = user.auth_header

    client.put(
        "/api/v1/textures",
        data={"type": "foo_bar"},
        files={"file": steve_file_data},
    )

    resp = client.get("/api/v2/user")

    assert "foo:bar" in resp.json()["textures"]


def test_interop_v2_to_v1(client: TestClient, user: TestUser) -> None:
    client.headers = user.auth_header

    client.put(
        "/api/v2/textures",
        data={"type": "foo:bar"},
        files={"file": steve_file_data},
    )

    resp = client.get("/api/v1/textures")

    assert "foo_bar" in resp.json()


@pytest.fixture(scope="function")
async def old_db_texture_upload(user: TestUser) -> None:
    async with TestingSessionLocal() as session:
        db_user = User(
            uuid=user.uuid,
            name=user.name,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        db_upload = Upload(
            user_id=db_user.id,
            hash="foobar",
        )
        session.add(db_upload)
        await session.commit()
        await session.refresh(db_user)
        await session.refresh(db_upload)

        db_texture = Texture(
            tex_type="foo_bar",
            upload_id=db_upload.id,
            user_id=db_user.id,
        )
        session.add(db_texture)
        await session.commit()


@pytest.mark.usefixtures("old_db_texture_upload")
def test_old_database_in_v2(client: TestClient, user: TestUser) -> None:
    resp = client.get(f"/api/v2/user/{user.uuid}")

    assert resp.status_code == 200, resp.json()
    assert "foo:bar" in resp.json()["textures"]
