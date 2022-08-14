from .conftest import TestClient


async def test_app(client: TestClient):
    resp = await client.get("/", allow_redirects=False)
    assert resp.status_code == 308
    assert resp.headers["Location"] == "/dashboard"


async def test_dashboard_template(client: TestClient):
    resp = await client.get("/dashboard")
    assert resp.status_code == 200
    assert "@vite/client" in resp.text
