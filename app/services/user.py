from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish
from app.models.user import User
from app.models.rating import Rating
from app.models.suggestion import Suggestion
from app.models.favorite import Favorite


async def get_or_create_user(db: AsyncSession, openid: str, nickname: str = "", avatar_url: str = "") -> User:
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(openid=openid, nickname=nickname or f"用户_{openid[:8]}", avatar_url=avatar_url)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        updated = False
        if nickname and nickname != user.nickname:
            user.nickname = nickname
            updated = True
        if avatar_url and avatar_url != user.avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user: User, name: str | None, bio: str | None, avatar_url: str | None = None) -> User:
    if name is not None:
        user.nickname = name
    if bio is not None:
        user.bio = bio
    if avatar_url is not None:
        user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_stats(db: AsyncSession, user_id: str) -> dict:
    dish_count = await db.scalar(select(func.count(Dish.id)).where(Dish.author_id == user_id))
    rated_count = await db.scalar(select(func.count(Rating.id)).where(Rating.user_id == user_id))
    suggestion_count = await db.scalar(select(func.count(Suggestion.id)).where(Suggestion.user_id == user_id))
    favorite_count = await db.scalar(select(func.count(Favorite.id)).where(Favorite.user_id == user_id))
    return {
        "uploads": dish_count or 0,
        "reviews": rated_count or 0,
        "suggestions": suggestion_count or 0,
        "favorites": favorite_count or 0,
    }
