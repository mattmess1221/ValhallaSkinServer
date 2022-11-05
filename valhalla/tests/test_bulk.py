from .conftest import TestClient, TestUser, assets

test_skin = assets / "good" / "64x64.png"


async def test_unknown_bulk_user(client: TestClient, user: TestUser):
    resp = await client.post(
        "/api/v1/bulk_textures",
        json={
            "uuids": [
                str(user.uuid),
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) == 0


async def test_bulk_users(client: TestClient, users: list[TestUser]):
    # setup
    for u in users:
        resp = await client.put(
            "/api/v1/textures",
            headers=u.auth_header,
            files={
                "file": (test_skin.name, test_skin.open("rb"), "image/png"),
            },
        )
        assert resp.status_code == 200

    uuids = [str(u.uuid).replace("-", "") for u in users]

    resp = await client.post("/api/v1/bulk_textures", json={"uuids": uuids})
    assert resp.status_code == 200

    data = resp.json()
    original_users = [user["profileId"] for user in data["users"]]
    assert original_users == uuids
