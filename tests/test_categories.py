import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, db: AsyncSession):
    db.add(Category(name="川菜", sort_order=1))
    db.add(Category(name="粤菜", sort_order=2))
    await db.commit()

    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["name"] == "川菜"
