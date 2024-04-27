import pytest

from .assets import steve_file as test_skin
from .conftest import TestClient, TestUser


@pytest.mark.parametrize(
    ("api_version", "path"),
    [
        ("v1", "bulk_textures"),
        ("v2", "users"),
    ],
)
def test_unknown_bulk_user(
    api_version: str, path: str, client: TestClient, user: TestUser
) -> None:
    resp = client.post(
        f"/api/{api_version}/{path}",
        json={
            "uuids": [
                str(user.uuid),
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) == 0


@pytest.mark.parametrize(
    ("api_version", "path"),
    [
        ("v1", "bulk_textures"),
        ("v2", "users"),
    ],
)
def test_bulk_users(
    api_version: str, path: str, client: TestClient, users: list[TestUser]
) -> None:
    # setup
    for u in users:
        resp = client.put(
            f"/api/{api_version}/textures",
            headers=u.auth_header,
            files={
                "file": (test_skin.name, test_skin.read_bytes(), "image/png"),
            },
        )
        assert resp.status_code == 200

    uuids = [str(u.uuid) for u in users]

    resp = client.post(f"/api/{api_version}/{path}", json={"uuids": uuids})
    assert resp.status_code == 200

    data = resp.json()
    original_users = [user["profileId"] for user in data["users"]]
    assert original_users == uuids
