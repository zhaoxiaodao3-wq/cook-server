from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.rating import RatingCreateIn, RatingUpdateIn, RatingOut
from app.services.rating import upsert_rating, get_ratings_for_dish

router = APIRouter(prefix="/dishes/{dish_id}/ratings", tags=["评分"])


@router.get("", response_model=ApiResponse[PaginatedData[RatingOut]], summary="菜品评分列表")
async def list_ratings(
    dish_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    ratings, total = await get_ratings_for_dish(db, dish_id, page=page, page_size=page_size)
    return ApiResponse(
        data=PaginatedData(
            items=[RatingOut.model_validate(r) for r in ratings],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=ApiResponse, status_code=201, summary="菜品评分")
async def rate_dish(
    dish_id: str,
    body: RatingCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await upsert_rating(db, dish_id, current_user.id, body.stars)
    return ApiResponse(message="评分成功")


@router.put("", response_model=ApiResponse, summary="修改评分")
async def update_rating(
    dish_id: str,
    body: RatingUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await upsert_rating(db, dish_id, current_user.id, body.stars)
    return ApiResponse(message="评分已更新")
