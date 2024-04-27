from uuid import uuid4

import pytest

from .assets import steve_file_data, steve_hash, steve_url
from .conftest import TestClient, TestUser


@pytest.mark.parametrize(
    ("method", "client_args"),
    [
        ("PUT", {"files": {"file": steve_file_data}}),
        ("POST", {"data": {"file": steve_url}}),
    ],
)
def test_legacy_upload(
    method: str, client_args: dict, client: TestClient, user: TestUser
) -> None:
    client_args["headers"] = user.auth_header
    resp = client.request(method, f"/api/v1/user/{user.uuid}/skin", **client_args)
    assert resp.status_code == 200, resp.json()


@pytest.mark.parametrize(
    ("method", "client_args"),
    [
        ("PUT", {"files": {"file": steve_file_data}}),
        ("POST", {"data": {"file": steve_url}}),
    ],
)
def test_legacy_upload_wrong_user(
    method: str, client_args: dict, client: TestClient, user: TestUser
) -> None:
    client_args["headers"] = user.auth_header
    resp = client.request(method, f"/api/v1/user/{uuid4()}/skin", **client_args)
    assert resp.status_code == 403, resp.json()


@pytest.mark.parametrize(
    ("method", "client_args"),
    [
        ("PUT", {"files": {"file": steve_file_data}}),
        ("POST", {"data": {"file": steve_url}}),
    ],
)
def test_legacy_v0(
    method: str, client_args: dict, client: TestClient, user: TestUser
) -> None:
    client_args["headers"] = user.auth_header
    resp = client.request(method, f"/api/user/{user.uuid}/skin", **client_args)
    assert resp.status_code == 200
    assert resp.json() == {"message": "OK"}

    resp = client.get(f"/api/user/{user.uuid}")
    assert resp.status_code == 200

    data = resp.json()
    skin = data["textures"]["skin"]["url"]
    assert skin == steve_hash

    resp = client.delete(f"/api/user/{user.uuid}/skin", headers=user.auth_header)
    assert resp.status_code == 200
    assert resp.json() == {"message": "skin cleared"}

    resp = client.get(f"/api/user/{user.uuid}")
    assert resp.status_code == 200

    assert "skin" not in resp.json()["textures"]
