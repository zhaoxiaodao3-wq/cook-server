from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.rating import ReviewCreateIn, ReviewResponse, ReviewDeleteResponse, ReviewOut
from app.services.rating import upsert_rating, delete_rating, get_dish_rating_count

router = APIRouter(prefix="/recipes/{recipe_id}/reviews", tags=["评分"])


@router.post("", response_model=ApiResponse[ReviewResponse], summary="提交评分")
async def rate_recipe(
    recipe_id: str,
    body: ReviewCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rating = await upsert_rating(db, recipe_id, current_user.id, body.rating)
    dish = rating.dish
    count = await get_dish_rating_count(db, recipe_id)
    return ApiResponse(data=ReviewResponse(
        review=ReviewOut(
            id=rating.id,
            userId=rating.user_id,
            userName=rating.user.nickname if rating.user else "",
            userAvatar=rating.user.avatar_url or "" if rating.user else "",
            rating=rating.stars,
            date=rating.created_at.isoformat() if rating.created_at else "",
        ),
        recipeRating=float(dish.avg_rating),
        ratingCount=count,
    ))


@router.delete("/me", response_model=ApiResponse[ReviewDeleteResponse], summary="删除我的评分")
async def delete_my_review(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avg, count = await delete_rating(db, recipe_id, current_user.id)
    return ApiResponse(data=ReviewDeleteResponse(recipeRating=avg, ratingCount=count))
