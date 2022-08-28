from io import BytesIO, StringIO
from pathlib import Path

import pytest

from .conftest import TestClient, TestUser

assets = Path(__file__).parent / "assets"
steve_file = assets / "steve.png"
steve_url = "http://assets.mojang.com/SkinTemplates/steve.png"
steve_hash = "https://localhost/textures/18b1728ad94f13571d903b913f5e58d47cee1b0a"


def build_request_kwargs(file: str | Path):
    if isinstance(file, Path):
        return {
            "method": "PUT",
            "files": {
                "file": (file.name, file.open("rb"), "image/png"),
                "type": "skin",
            },
        }
    return {
        "method": "POST",
        "json": {"file": file, "type": "skin"},
    }


@pytest.mark.parametrize(
    "kwargs, hash_url",
    [
        (build_request_kwargs(steve_file), steve_hash),
        (build_request_kwargs(steve_url), steve_hash),
    ],
)
async def test_texture_upload_post(
    kwargs, hash_url, client: TestClient, user: TestUser
):
    upload_resp = await client.open(
        "/api/v1/textures", headers=user.auth_header, **kwargs
    )
    assert upload_resp.status_code == 200, upload_resp.json()

    user_resp = await client.get(f"/api/v1/textures", headers=user.auth_header)
    assert user_resp.status_code == 200, user_resp.json()
    textures = user_resp.json()
    skin = textures["skin"]

    assert skin["url"] == hash_url
    assert skin["meta"] == {}

    anon_resp = await client.get(f"/api/v1/user/{user.uuid}")
    assert anon_resp.status_code == 200, anon_resp.json()
    assert anon_resp.json()["textures"] == textures


async def test_unknown_user_textures(client: TestClient, user: TestUser):
    resp = await client.get(f"/api/v1/user/{user.uuid}")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "kwargs",
    [
        build_request_kwargs(steve_file),
        build_request_kwargs(steve_url),
    ],
)
async def test_unauthenticated_user_texture_upload(kwargs, client: TestClient):
    upload_resp = await client.open("/api/v1/textures", **kwargs)
    assert upload_resp.status_code == 401, upload_resp.json()


async def test_non_image_upload(client: TestClient, user: TestUser):
    resp = await client.put(
        "/api/v1/textures",
        headers=user.auth_header,
        files={"type": "skin", "file": ("file.txt", StringIO("bad file"))},
    )
    assert resp.status_code == 400
    assert "cannot identify image file" in resp.json()["detail"]


async def test_very_large_upload(client: TestClient, user: TestUser):
    ten_megabytes_of_zeros = b"\0" * 10_000_000
    resp = await client.put(
        "/api/v1/textures",
        headers={
            **user.auth_header,
            # lie about the content-length
            "content-length": "1000",
        },
        files={"type": "skin", "file": ("file.txt", BytesIO(ten_megabytes_of_zeros))},
    )
    assert resp.status_code == 413  # Request entity too large
