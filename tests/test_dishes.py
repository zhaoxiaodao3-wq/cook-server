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
async def test_create_and_get_dish(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    payload = _recipe(
        title="红烧肉",
        duration=90,
        difficulty="中等",
        cuisine="川菜",
        tags=["精选"],
        servings=4,
        tips="小火慢炖",
        ingredients=[
            {"name": "五花肉", "amount": "500", "unit": "克"},
            {"name": "酱油", "amount": "2", "unit": "勺"},
        ],
        steps=[
            {"desc": "五花肉切块焯水"},
            {"desc": "加酱油小火炖60分钟"},
        ],
    )
    resp = await client.post(
        "/api/v1/recipes", json=payload,
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["title"] == "红烧肉"
    assert data["difficulty"] == "中等"
    assert data["category"] == "lunch"
    assert len(data["ingredients"]) == 2
    assert len(data["steps"]) == 2
    assert data["rating"] == 0.0
    assert data["ratingCount"] == 0

    dish_id = data["id"]

    get_resp = await client.get(f"/api/v1/recipes/{dish_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "红烧肉"


@pytest.mark.asyncio
async def test_update_dish(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="旧菜名"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    update_resp = await client.patch(
        f"/api/v1/recipes/{dish_id}",
        json={"title": "新菜名"},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["title"] == "新菜名"


@pytest.mark.asyncio
async def test_delete_dish(client: AsyncClient, db: AsyncSession, auth_headers):
    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="要删除的菜"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    delete_resp = await client.delete(
        f"/api/v1/recipes/{dish_id}",
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert delete_resp.status_code == 200

    get_resp = await client.get(f"/api/v1/recipes/{dish_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_edit_others_dish(client: AsyncClient, db: AsyncSession, auth_headers):
    from app.models.user import User
    from app.core.security import create_access_token

    cat = Category(name="午餐", key="lunch")
    db.add(cat)
    await db.commit()

    create_resp = await client.post(
        "/api/v1/recipes",
        json=_recipe(title="我的菜"),
        headers={"Authorization": auth_headers["Authorization"]},
    )
    dish_id = create_resp.json()["data"]["id"]

    other_user = User(openid="other", nickname="别人")
    db.add(other_user)
    await db.commit()
    other_token = create_access_token(other_user.id)

    resp = await client.patch(
        f"/api/v1/recipes/{dish_id}",
        json={"title": "我改的"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_dishes_filtering(client: AsyncClient, db: AsyncSession, auth_headers):
    cat_lunch = Category(name="午餐", key="lunch")
    cat_dinner = Category(name="晚餐", key="dinner")
    db.add_all([cat_lunch, cat_dinner])
    await db.commit()

    for i in range(3):
        resp = await client.post(
            "/api/v1/recipes",
            json=_recipe(
                title=f"午餐菜{i}",
                cuisine="川菜" if i < 2 else "粤菜",
                tags=["精选"] if i == 0 else [],
            ),
            headers={"Authorization": auth_headers["Authorization"]},
        )
        assert resp.status_code == 201, resp.text

    resp = await client.get("/api/v1/recipes?category=lunch")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 3

    resp = await client.get("/api/v1/recipes?cuisine=川菜")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 2

    resp = await client.get("/api/v1/recipes?q=午餐")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 3

    resp = await client.get("/api/v1/recipes?tag=精选")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1
