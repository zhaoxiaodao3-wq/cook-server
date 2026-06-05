from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish
from app.models.ingredient import Ingredient
from app.models.rating import Rating
from app.models.step import Step
from app.models.suggestion import Suggestion
from app.models.category import Category
from app.schemas.dish import RecipeCreateIn, RecipeUpdateIn, DIFFICULTY_REVERSE


def _tags_include(tag: str):
    """JSONB 数组是否包含标签（避免 JSON 类型误生成 LIKE 导致 500）"""
    return and_(Dish.tags.isnot(None), Dish.tags.contains([tag]))


async def get_dishes(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    category: str | None = None,
    cuisine: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
    sort: str = "createdAt",
    user_id: str | None = None,
) -> tuple[list[Dish], int]:
    base = select(Dish).where(Dish.status == "published")
    count_base = select(func.count(Dish.id)).where(Dish.status == "published")

    if category and category != "all":
        subq = select(Category.id).where(Category.key == category)
        base = base.where(Dish.category_id.in_(subq))
        count_base = count_base.where(Dish.category_id.in_(subq))

    if cuisine:
        base = base.where(Dish.cuisine == cuisine)
        count_base = count_base.where(Dish.cuisine == cuisine)

    if tag:
        tag_cond = _tags_include(tag)
        base = base.where(tag_cond)
        count_base = count_base.where(tag_cond)

    if keyword:
        keyword_cond = or_(
            Dish.name.ilike(f"%{keyword}%"),
            Dish.id.in_(select(Ingredient.dish_id).where(Ingredient.name.ilike(f"%{keyword}%"))),
            _tags_include(keyword),
        )
        base = base.where(keyword_cond)
        count_base = count_base.where(keyword_cond)

    total_result = await db.execute(count_base)
    total = total_result.scalar_one()

    if sort == "rating":
        base = base.order_by(Dish.avg_rating.desc())
    else:
        base = base.order_by(Dish.created_at.desc())

    base = base.options(selectinload(Dish.author), selectinload(Dish.category))
    base = base.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(base)
    dishes = list(result.scalars().all())

    return dishes, total


async def get_ranked_dishes(
    db: AsyncSession,
    limit: int = 10,
    user_id: str | None = None,
) -> list[Dish]:
    result = await db.execute(
        select(Dish)
        .where(Dish.status == "published", Dish.avg_rating > 0)
        .options(selectinload(Dish.author), selectinload(Dish.category))
        .order_by(Dish.avg_rating.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_dish_detail(db: AsyncSession, dish_id: str) -> Dish | None:
    result = await db.execute(
        select(Dish)
        .where(Dish.id == dish_id)
        .options(
            selectinload(Dish.author),
            selectinload(Dish.category),
            selectinload(Dish.ingredients),
            selectinload(Dish.steps),
            selectinload(Dish.ratings).selectinload(Rating.user),
            selectinload(Dish.suggestions).selectinload(Suggestion.user),
        )
    )
    dish = result.scalar_one_or_none()
    if dish:
        for s in dish.suggestions:
            _ = s.user
    return dish


async def create_dish(db: AsyncSession, author_id: str, data: RecipeCreateIn) -> Dish:
    from app.models.category import Category

    category_result = await db.execute(select(Category).where(Category.key == data.category))
    category_obj = category_result.scalar_one_or_none()
    if category_obj is None:
        fallback = await db.execute(select(Category).limit(1))
        category_obj = fallback.scalar_one_or_none()

    difficulty_int = DIFFICULTY_REVERSE.get(data.difficulty) if data.difficulty else None

    dish = Dish(
        name=data.title,
        cover=data.coverImage,
        category_id=category_obj.id if category_obj else 1,
        cuisine=data.cuisine,
        tags=data.tags if data.tags else [],
        cooking_time=data.duration,
        difficulty=difficulty_int,
        servings=data.servings,
        tips=data.tips,
        suitable_for=data.crowd,
        status="published",
        author_id=author_id,
    )
    db.add(dish)
    await db.flush()

    for i, ing in enumerate(data.ingredients):
        db.add(Ingredient(
            dish_id=dish.id, name=ing.name, amount=ing.amount or "", unit=ing.unit or "", sort_order=i,
        ))
    for i, step in enumerate(data.steps):
        db.add(Step(
            dish_id=dish.id, step_number=i + 1, description=step.desc, image=step.image,
        ))

    await db.commit()
    await db.refresh(dish)
    return await get_dish_detail(db, dish.id)


async def update_dish(db: AsyncSession, dish: Dish, data: RecipeUpdateIn) -> Dish:
    from app.models.category import Category

    if data.title is not None:
        dish.name = data.title
    if data.coverImage is not None:
        dish.cover = data.coverImage
    if data.duration is not None:
        dish.cooking_time = data.duration
    if data.difficulty is not None:
        dish.difficulty = DIFFICULTY_REVERSE.get(data.difficulty)
    if data.category is not None:
        cat_result = await db.execute(select(Category).where(Category.key == data.category))
        cat = cat_result.scalar_one_or_none()
        if cat:
            dish.category_id = cat.id
    if data.cuisine is not None:
        dish.cuisine = data.cuisine
    if data.tags is not None:
        dish.tags = data.tags
    if data.servings is not None:
        dish.servings = data.servings
    if data.tips is not None:
        dish.tips = data.tips
    if data.crowd is not None:
        dish.suitable_for = data.crowd

    if data.ingredients is not None:
        existing = await db.execute(select(Ingredient).where(Ingredient.dish_id == dish.id))
        for ing in existing.scalars().all():
            await db.delete(ing)
        for i, ing in enumerate(data.ingredients):
            db.add(Ingredient(dish_id=dish.id, name=ing.name, amount=ing.amount or "", unit=ing.unit or "", sort_order=i))

    if data.steps is not None:
        existing = await db.execute(select(Step).where(Step.dish_id == dish.id))
        for step in existing.scalars().all():
            await db.delete(step)
        for i, step in enumerate(data.steps):
            db.add(Step(dish_id=dish.id, step_number=i + 1, description=step.desc, image=step.image))

    await db.commit()
    await db.refresh(dish)
    return await get_dish_detail(db, dish.id)


async def delete_dish(db: AsyncSession, dish: Dish) -> None:
    await db.delete(dish)
    await db.commit()


async def get_user_dishes(
    db: AsyncSession, user_id: str, page: int = 1, page_size: int = 10,
) -> tuple[list[Dish], int]:
    base = select(Dish).where(Dish.author_id == user_id).options(selectinload(Dish.author), selectinload(Dish.category))
    count_base = select(func.count(Dish.id)).where(Dish.author_id == user_id)
    total_result = await db.execute(count_base)
    total = total_result.scalar_one()
    base = base.order_by(Dish.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(base)
    return list(result.scalars().all()), total
