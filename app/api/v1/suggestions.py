from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.suggestion import SuggestionCreateIn, SuggestionUpdateIn, SuggestionOut
from app.services.suggestion import create_suggestion, upsert_suggestion, get_suggestions_for_dish

router = APIRouter(prefix="/dishes/{dish_id}/suggestions", tags=["建议"])


@router.get("", response_model=ApiResponse[PaginatedData[SuggestionOut]], summary="菜品建议列表")
async def list_suggestions(
    dish_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    suggestions, total = await get_suggestions_for_dish(db, dish_id, page=page, page_size=page_size)
    return ApiResponse(
        data=PaginatedData(
            items=[SuggestionOut.model_validate(s) for s in suggestions],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=ApiResponse, status_code=201, summary="提交建议")
async def add_suggestion(
    dish_id: str,
    body: SuggestionCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await create_suggestion(db, dish_id, current_user.id, body.content)
    return ApiResponse(message="建议已提交")


@router.put("", response_model=ApiResponse, summary="编辑建议")
async def edit_suggestion(
    dish_id: str,
    body: SuggestionUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await upsert_suggestion(db, dish_id, current_user.id, body.content)
    return ApiResponse(message="建议已更新")
