from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dish import RecipeDetailOut, AuthorBrief, IngredientOut, StepOut, DIFFICULTY_MAP
from app.schemas.draft import DraftIn, DraftOut, DraftIngredient, DraftStep
from app.services.draft import get_user_drafts, save_draft, delete_draft, publish_draft

router = APIRouter(prefix="/drafts", tags=["草稿"])


def _draft_to_out(draft) -> DraftOut:
    return DraftOut(
        id=draft.id,
        title=draft.title or "",
        step=draft.step or 0,
        coverImage=draft.cover_image or "",
        duration=draft.duration,
        difficulty=draft.difficulty or "",
        servings=draft.servings,
        ingredients=[DraftIngredient(**ing) for ing in (draft.ingredients or [])],
        steps=[DraftStep(**st) for st in (draft.steps_data or [])],
        category=draft.category or "",
        cuisine=draft.cuisine or "",
        tags=draft.tags or [],
        crowd=draft.crowd or "",
        tips=draft.tips or "",
        savedAt=draft.updated_at.isoformat() if draft.updated_at else "",
    )


@router.get("", response_model=ApiResponse[list[DraftOut]], summary="我的草稿")
async def list_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    drafts = await get_user_drafts(db, current_user.id)
    return ApiResponse(data=[_draft_to_out(d) for d in drafts])


@router.put("/{draft_id}", response_model=ApiResponse[DraftOut], summary="保存草稿")
async def upsert_draft(
    draft_id: str,
    body: DraftIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    draft = await save_draft(db, current_user.id, draft_id, body.model_dump())
    return ApiResponse(data=_draft_to_out(draft))


@router.delete("/{draft_id}", response_model=ApiResponse, summary="删除草稿")
async def remove_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_draft(db, draft_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="草稿不存在")
    return ApiResponse(message="删除成功")


@router.post("/{draft_id}/publish", response_model=ApiResponse[RecipeDetailOut], summary="发布草稿")
async def publish(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dish = await publish_draft(db, draft_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="草稿不存在")

    return ApiResponse(data=RecipeDetailOut(
        id=dish.id,
        title=dish.name,
        coverImage=dish.cover,
        author=AuthorBrief(
            id=dish.author.id if dish.author else "",
            name=dish.author.nickname if dish.author else "",
            avatar=dish.author.avatar_url or "" if dish.author else "",
        ) if dish.author else None,
        rating=float(dish.avg_rating),
        ratingCount=dish.rating_count,
        createdAt=dish.created_at.isoformat() if dish.created_at else "",
        duration=dish.cooking_time,
        difficulty=DIFFICULTY_MAP.get(dish.difficulty) if dish.difficulty else None,
        category=dish.category.key if dish.category else None,
        cuisine=dish.cuisine,
        tags=dish.tags or [],
        servings=dish.servings,
        ingredients=[IngredientOut(name=ing.name, amount=ing.amount or "", unit=ing.unit or "") for ing in (dish.ingredients or [])],
        steps=[StepOut(id=s.step_number, desc=s.description, image=s.image) for s in (dish.steps or [])],
        tips=dish.tips,
        crowd=dish.suitable_for,
        reviews=[],
        suggestions=[],
    ))
