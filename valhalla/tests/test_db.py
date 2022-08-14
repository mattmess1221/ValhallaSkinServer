from uuid import uuid4

from .conftest import TestClient


async def test_texture_upload(client: TestClient):
    uuid = uuid4()
    auth_header = {"authorization": f"TestUser:{uuid}"}
    resp = await client.post(
        "/api/v1/user/@me",
        headers=auth_header,
        json={
            "type": "skin",
            "file": "http://assets.mojang.com/SkinTemplates/steve.png",
        },
    )
    assert resp.status_code == 200, resp.json()

    user_resp = await client.get(f"/api/v1/user/{uuid}")
    assert user_resp.status_code == 200
    data = user_resp.json()
    skin = data["textures"]["skin"]

    assert (
        skin["url"]
        == "https://localhost/textures/18b1728ad94f13571d903b913f5e58d47cee1b0a"
    )
    assert skin["meta"] == {}

    me_resp = await client.get("/api/v1/user/@me", headers=auth_header)
    assert me_resp.status_code == 200
    assert me_resp.json()["textures"] == data["textures"]


async def test_unknown_user_textures(client: TestClient):
    uuid = uuid4()

    resp = await client.get(f"/api/v1/user/{uuid}")
    assert resp.status_code == 404
