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
async def test_rate_dish(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="测试菜品"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    rate_resp = await client.post(
        f"/api/v1/recipes/{dish_id}/reviews",
        json={"rating": 5},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert rate_resp.status_code == 200, rate_resp.text
    data = rate_resp.json()["data"]
    assert data["recipeRating"] == 5.0
    assert data["ratingCount"] == 1
    assert data["review"]["rating"] == 5


@pytest.mark.asyncio
async def test_update_rating(client: AsyncClient, db: AsyncSession, auth_headers):
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
        f"/api/v1/recipes/{dish_id}/reviews",
        json={"rating": 3},
        headers={"Authorization": auth_headers["Authorization"]},
    )

    update_resp = await client.post(
        f"/api/v1/recipes/{dish_id}/reviews",
        json={"rating": 5},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()["data"]
    assert data["recipeRating"] == 5.0
    assert data["ratingCount"] == 1


@pytest.mark.asyncio
async def test_delete_rating(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="测试菜品3"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/recipes/{dish_id}/reviews",
        json={"rating": 5},
        headers={"Authorization": auth_headers["Authorization"]},
    )

    delete_resp = await client.delete(
        f"/api/v1/recipes/{dish_id}/reviews/me",
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert delete_resp.status_code == 200
    data = delete_resp.json()["data"]
    assert data["recipeRating"] == 0.0
    assert data["ratingCount"] == 0
