from io import BytesIO

import pytest

from .assets import steve_file_data, steve_hash, steve_url
from .conftest import TestClient, TestUser


@pytest.mark.parametrize(
    ("api_version", "self_path", "skin_key"),
    [
        ("v1", "textures", "skin"),
        ("v2", "user", "minecraft:skin"),
    ],
)
@pytest.mark.parametrize(
    ("method", "client_args"),
    [
        ("PUT", {"data": {"type": "skin"}, "files": {"file": steve_file_data}}),
        ("POST", {"json": {"type": "skin", "file": steve_url}}),
    ],
)
def test_texture_upload_post(
    api_version: str,
    self_path: str,
    skin_key: str,
    method: str,
    client_args: dict,
    client: TestClient,
    user: TestUser,
) -> None:
    headers = client_args.setdefault("headers", {})
    headers |= user.auth_header
    upload_resp = client.request(method, f"/api/{api_version}/textures", **client_args)
    assert upload_resp.status_code == 200, upload_resp.json()

    user_resp = client.get(f"/api/{api_version}/{self_path}", headers=user.auth_header)
    assert user_resp.status_code == 200, user_resp.json()
    textures = user_resp.json()
    skin = textures[skin_key]

    assert skin["url"] == steve_hash
    assert not skin["metadata"]

    anon_resp = client.get(f"/api/{api_version}/user/{user.uuid}")
    assert anon_resp.status_code == 200, anon_resp.json()
    assert anon_resp.json()["textures"] == textures


@pytest.mark.parametrize("api_version", ["v1", "v2"])
@pytest.mark.parametrize(
    ("method", "client_args"),
    [
        ("PUT", {"data": {"type": "skin"}, "files": {"file": steve_file_data}}),
        ("POST", {"json": {"type": "skin", "url": steve_url}}),
    ],
)
def test_unauthenticated_user_texture_upload(
    api_version: str,
    method: str,
    client_args: dict,
    client: TestClient,
) -> None:
    upload_resp = client.request(method, f"/api/{api_version}/textures", **client_args)
    assert upload_resp.status_code == 401, upload_resp.json()


@pytest.mark.parametrize("api_version", ["v1", "v2"])
def test_non_image_upload(client: TestClient, user: TestUser, api_version: str) -> None:
    resp = client.put(
        f"/api/{api_version}/textures",
        headers=user.auth_header,
        data={"type": "minecraft:skin"},
        files={"file": ("file.txt", BytesIO(b"bad file"))},
    )
    assert resp.status_code == 400, resp.json()
    assert "cannot identify image file" in resp.json()["detail"]


@pytest.mark.parametrize("api_version", ["v1", "v2"])
def test_very_large_upload(
    client: TestClient, user: TestUser, api_version: str
) -> None:
    ten_megabytes_of_zeros = b"\0" * 10_000_000
    resp = client.put(
        f"/api/{api_version}/textures",
        headers={
            **user.auth_header,
            # lie about the content-length
            "content-length": "1000",
        },
        data={"type": "minecraft:skin"},
        files={"file": ("file.txt", BytesIO(ten_megabytes_of_zeros))},
    )
    assert resp.status_code == 413, resp.text  # Request entity too large


def test_unknown_user_textures(client: TestClient, user: TestUser) -> None:
    resp = client.get(f"/api/v1/user/{user.uuid}")
    assert resp.status_code == 404
