import pytest

from .assets import steve_file_data
from .conftest import TestClient, TestUser


@pytest.mark.parametrize("skin_type", ["minecraft:skin", "minceraft:elytra"])
def test_namespace_texture(skin_type: str, client: TestClient, user: TestUser) -> None:
    client.headers = user.auth_header
    resp = client.put(
        "/api/v2/textures",
        data={"type": skin_type},
        files={"file": steve_file_data},
    )

    assert resp.status_code == 200, resp.json()


@pytest.mark.parametrize(
    "skin_type",
    [
        "minecraft:custom",  # minecraft is reserved
        "MYMOD:ALLCAPS",  # lowercase only
        "foo.bar:baa",  # no special characters in namespace
        "hat",  # default namespace is minecraft, which is reserved
    ],
)
def test_bad_namespace(skin_type: str, client: TestClient, user: TestUser) -> None:
    client.headers = user.auth_header
    resp = client.put(
        "/api/v2/textures",
        data={"type": skin_type},
        files={"file": steve_file_data},
    )

    assert resp.status_code == 422, resp.json()


def test_multiclear(client: TestClient, user: TestUser) -> None:
    texture_types = ["skin", "minecraft:elytra", "foo:bar"]
    client.headers = user.auth_header

    # setup
    for skin_type in texture_types:
        client.put(
            "/api/v2/textures",
            data={"type": skin_type},
            files={"file": steve_file_data},
        )

    # verify
    resp = client.get("/api/v2/user")
    assert resp.status_code == 200, resp.json()

    data = resp.json()
    for skin_type in texture_types:
        if ":" not in skin_type:
            skin_type = f"minecraft:{skin_type}"
        assert skin_type in data["textures"]

    # clear skins
    resp = client.delete(
        "/api/v2/textures", params=[("type", typ) for typ in texture_types]
    )
    assert resp.status_code == 200

    resp = client.get("/api/v2/user")
    assert resp.status_code == 200, resp.json()
    assert len(resp.json()["textures"]) == 0
