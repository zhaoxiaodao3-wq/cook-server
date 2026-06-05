from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.favorite import FavoriteResponse
from app.services.favorite import add_favorite, remove_favorite

router = APIRouter(prefix="/recipes/{recipe_id}/favorite", tags=["收藏"])


@router.post("", response_model=ApiResponse[FavoriteResponse], summary="添加收藏")
async def add_fav(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await add_favorite(db, recipe_id, current_user.id)
    return ApiResponse(data=FavoriteResponse(favorited=True))


@router.delete("", response_model=ApiResponse[FavoriteResponse], summary="取消收藏")
async def remove_fav(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_favorite(db, recipe_id, current_user.id)
    return ApiResponse(data=FavoriteResponse(favorited=False))
