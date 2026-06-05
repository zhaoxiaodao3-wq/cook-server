from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite
from app.models.dish import Dish


async def add_favorite(db: AsyncSession, dish_id: str, user_id: str) -> None:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.dish_id == dish_id)
    )
    if result.scalar_one_or_none() is None:
        fav = Favorite(user_id=user_id, dish_id=dish_id)
        db.add(fav)
        await db.commit()


async def remove_favorite(db: AsyncSession, dish_id: str, user_id: str) -> None:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.dish_id == dish_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.commit()


async def is_favorited(db: AsyncSession, dish_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.dish_id == dish_id)
    )
    return result.scalar_one_or_none() is not None


async def get_user_favorites(
    db: AsyncSession, user_id: str, page: int = 1, page_size: int = 10,
) -> tuple[list[Dish], int]:
    fav_subq = select(Favorite.dish_id).where(Favorite.user_id == user_id)

    count_base = select(func.count(Dish.id)).where(Dish.id.in_(fav_subq))
    total_result = await db.execute(count_base)
    total = total_result.scalar_one()

    base = (
        select(Dish)
        .where(Dish.id.in_(fav_subq))
        .options(selectinload(Dish.author), selectinload(Dish.category))
        .order_by(Dish.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(base)
    return list(result.scalars().all()), total


async def get_user_favorite_dish_ids(db: AsyncSession, user_id: str) -> set[str]:
    result = await db.execute(
        select(Favorite.dish_id).where(Favorite.user_id == user_id)
    )
    return {row[0] for row in result.all()}
