from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.draft import Draft
from app.models.dish import Dish
from app.models.ingredient import Ingredient
from app.models.step import Step
from app.models.category import Category
from app.schemas.dish import DIFFICULTY_REVERSE


async def get_user_drafts(db: AsyncSession, user_id: str) -> list[Draft]:
    result = await db.execute(
        select(Draft)
        .where(Draft.user_id == user_id)
        .order_by(Draft.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_draft(db: AsyncSession, draft_id: str, user_id: str) -> Draft | None:
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save_draft(db: AsyncSession, user_id: str, draft_id: str | None, data: dict) -> Draft:
    if draft_id:
        result = await db.execute(
            select(Draft).where(Draft.id == draft_id, Draft.user_id == user_id)
        )
        draft = result.scalar_one_or_none()
        if draft is None:
            draft = Draft(user_id=user_id)
            db.add(draft)
    else:
        draft = Draft(user_id=user_id)
        db.add(draft)

    draft.title = data.get("title", "")
    draft.step = data.get("step", 0)
    draft.cover_image = data.get("coverImage", "")
    draft.duration = data.get("duration")
    draft.difficulty = data.get("difficulty", "")
    draft.servings = data.get("servings")
    draft.ingredients = data.get("ingredients", [])
    draft.steps_data = data.get("steps", [])
    draft.category = data.get("category", "")
    draft.cuisine = data.get("cuisine", "")
    draft.tags = data.get("tags", [])
    draft.crowd = data.get("crowd", "")
    draft.tips = data.get("tips", "")

    await db.commit()
    await db.refresh(draft)
    return draft


async def delete_draft(db: AsyncSession, draft_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == user_id)
    )
    draft = result.scalar_one_or_none()
    if draft:
        await db.delete(draft)
        await db.commit()
        return True
    return False


async def publish_draft(db: AsyncSession, draft_id: str, user_id: str) -> Dish:
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == user_id)
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        raise ValueError("草稿不存在")

    difficulty_int = DIFFICULTY_REVERSE.get(draft.difficulty) if draft.difficulty else None

    cat_result = await db.execute(select(Category).where(Category.key == draft.category))
    cat = cat_result.scalar_one_or_none()
    if cat is None:
        fallback = await db.execute(select(Category).limit(1))
        cat = fallback.scalar_one_or_none()

    dish = Dish(
        name=draft.title or "",
        cover=draft.cover_image,
        category_id=cat.id if cat else 1,
        cuisine=draft.cuisine,
        tags=draft.tags if draft.tags else [],
        cooking_time=draft.duration,
        difficulty=difficulty_int,
        servings=draft.servings,
        tips=draft.tips,
        suitable_for=draft.crowd,
        status="published",
        author_id=user_id,
    )
    db.add(dish)
    await db.flush()

    ingredients_data = draft.ingredients or []
    for i, ing in enumerate(ingredients_data):
        db.add(Ingredient(
            dish_id=dish.id,
            name=ing.get("name", ""),
            amount=ing.get("amount", ""),
            unit=ing.get("unit", ""),
            sort_order=i,
        ))

    steps_data = draft.steps_data or []
    for i, step in enumerate(steps_data):
        db.add(Step(
            dish_id=dish.id,
            step_number=i + 1,
            description=step.get("desc", ""),
            image=step.get("image"),
        ))

    await db.delete(draft)
    await db.commit()
    await db.refresh(dish)

    return dish
