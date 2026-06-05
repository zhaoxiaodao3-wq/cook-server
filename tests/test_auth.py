import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_wechat_login_dev_mode(client: AsyncClient):
    resp = await client.post("/api/v1/auth/wechat-login", json={
        "code": "test123",
        "nickName": "测试用户",
        "avatarUrl": "",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "token" in data["data"]
    assert data["data"]["user"]["name"] == "测试用户"


@pytest.mark.asyncio
async def test_wechat_login_missing_nickname(client: AsyncClient):
    resp = await client.post("/api/v1/auth/wechat-login", json={
        "code": "test123",
        "nickName": "",
        "avatarUrl": "",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.post("/api/v1/recipes", json={"title": "test"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_optional_auth(client: AsyncClient):
    resp = await client.get("/api/v1/recipes")
    assert resp.status_code == 200
