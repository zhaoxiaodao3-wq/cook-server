import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


def _recipe(**overrides):
    data = {
        "title": "测试菜",
        "category": "lunch",
        "ingredients": [{"name": "食材", "amount": "1", "unit": "个"}],
        "steps": [{"desc": "步骤"}],
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_add_suggestion(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="测试菜品"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    sug_resp = await client.post(
        f"/api/v1/recipes/{dish_id}/suggestions",
        json={"content": "可以多放点姜"},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert sug_resp.status_code == 200, sug_resp.text
    data = sug_resp.json()["data"]
    assert data["content"] == "可以多放点姜"
    assert data["userId"] == auth_headers["user"].id


@pytest.mark.asyncio
async def test_delete_suggestion(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="测试菜品2"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/recipes/{dish_id}/suggestions",
        json={"content": "这个建议待删除"},
        headers={"Authorization": auth_headers["Authorization"]},
    )

    delete_resp = await client.delete(
        f"/api/v1/recipes/{dish_id}/suggestions/me",
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert delete_resp.status_code == 200


@pytest.mark.asyncio
async def test_suggestion_too_long(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="测试菜品3"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    resp = await client.post(
        f"/api/v1/recipes/{dish_id}/suggestions",
        json={"content": "x" * 501},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 422
