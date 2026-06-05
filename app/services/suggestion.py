from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.suggestion import Suggestion
from app.models.dish import Dish


async def upsert_suggestion(db: AsyncSession, dish_id: str, user_id: str, content: str) -> Suggestion:
    result = await db.execute(
        select(Suggestion).where(Suggestion.dish_id == dish_id, Suggestion.user_id == user_id)
    )
    suggestion = result.scalar_one_or_none()
    if suggestion:
        suggestion.content = content
    else:
        suggestion = Suggestion(dish_id=dish_id, user_id=user_id, content=content)
        db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    result = await db.execute(
        select(Suggestion).where(Suggestion.id == suggestion.id).options(selectinload(Suggestion.user))
    )
    return result.scalar_one()


async def delete_suggestion(db: AsyncSession, dish_id: str, user_id: str) -> None:
    result = await db.execute(
        select(Suggestion).where(Suggestion.dish_id == dish_id, Suggestion.user_id == user_id)
    )
    suggestion = result.scalar_one_or_none()
    if suggestion:
        await db.delete(suggestion)
        await db.commit()


async def get_user_suggestion_for_dish(db: AsyncSession, dish_id: str, user_id: str) -> Suggestion | None:
    result = await db.execute(
        select(Suggestion).where(Suggestion.dish_id == dish_id, Suggestion.user_id == user_id)
    )
    return result.scalar_one_or_none()
