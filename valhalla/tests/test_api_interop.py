from .assets import steve_file_data
from .conftest import TestClient, TestUser


def test_interop_v1_to_v2(client: TestClient, user: TestUser) -> None:
    client.headers = user.auth_header

    client.put(
        "/api/v1/textures",
        data={"type": "foo_bar"},
        files={"file": steve_file_data},
    )

    resp = client.get("/api/v2/user")

    assert "foo:bar" in resp.json()["textures"]


def test_interop_v2_to_v3(client: TestClient, user: TestUser) -> None:
    client.headers = user.auth_header

    client.put(
        "/api/v2/textures",
        data={"type": "foo:bar"},
        files={"file": steve_file_data},
    )

    resp = client.get("/api/v1/textures")

    assert "foo_bar" in resp.json()
