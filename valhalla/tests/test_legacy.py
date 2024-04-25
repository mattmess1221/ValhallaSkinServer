from pathlib import Path
from uuid import uuid4

import pytest

from .conftest import TestClient, TestUser
from .test_app import steve_file, steve_hash, steve_url


def build_request_kwargs(file: str | Path) -> tuple[str, dict]:
    if isinstance(file, Path):
        return "PUT", {
            "files": {"file": (file.name, file.open("rb"), "image/png")},
        }
    return "POST", {
        "data": {"file": file},
    }


@pytest.mark.parametrize(
    "file",
    [steve_file, steve_url],
)
def test_legacy_upload(file: str | Path, client: TestClient, user: TestUser):
    method, kwargs = build_request_kwargs(file)
    resp = client.request(
        method, f"/api/v1/user/{user.uuid}/skin", headers=user.auth_header, **kwargs
    )
    assert resp.status_code == 200, resp.json()


@pytest.mark.parametrize(
    "file",
    [steve_file, steve_url],
)
def test_legacy_upload_wrong_user(file: str | Path, client: TestClient, user: TestUser):
    method, kwargs = build_request_kwargs(file)
    resp = client.request(
        method, f"/api/v1/user/{uuid4()}/skin", headers=user.auth_header, **kwargs
    )
    assert resp.status_code == 403, resp.json()


@pytest.mark.parametrize(
    "file, hash_url",
    [(steve_file, steve_hash), (steve_url, steve_hash)],
)
def test_legacy_v0(file: str | Path, hash_url: str, client: TestClient, user: TestUser):
    method, kwargs = build_request_kwargs(file)
    resp = client.request(
        method, f"/api/user/{user.uuid}/skin", headers=user.auth_header, **kwargs
    )
    assert resp.status_code == 200
    assert resp.json() == {"message": "OK"}

    resp = client.get(f"/api/user/{user.uuid}")
    assert resp.status_code == 200

    data = resp.json()
    skin = data["textures"]["skin"]["url"]
    assert skin == hash_url

    resp = client.delete(f"/api/user/{user.uuid}/skin", headers=user.auth_header)
    assert resp.status_code == 200
    assert resp.json() == {"message": "skin cleared"}

    resp = client.get(f"/api/user/{user.uuid}")
    assert resp.status_code == 200

    assert "skin" not in resp.json()["textures"]
