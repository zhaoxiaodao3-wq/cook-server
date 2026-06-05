from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.suggestion import SuggestionCreateIn, SuggestionOut
from app.services.suggestion import upsert_suggestion, delete_suggestion

router = APIRouter(prefix="/recipes/{recipe_id}/suggestions", tags=["建议"])


@router.post("", response_model=ApiResponse[SuggestionOut], summary="提交建议")
async def suggest_recipe(
    recipe_id: str,
    body: SuggestionCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    suggestion = await upsert_suggestion(db, recipe_id, current_user.id, body.content)
    return ApiResponse(data=SuggestionOut(
        id=suggestion.id,
        userId=suggestion.user_id,
        userName=suggestion.user.nickname if suggestion.user else "",
        userAvatar=suggestion.user.avatar_url or "" if suggestion.user else "",
        content=suggestion.content,
        date=suggestion.created_at.isoformat() if suggestion.created_at else "",
    ))


@router.delete("/me", response_model=ApiResponse, summary="删除我的建议")
async def delete_my_suggestion(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_suggestion(db, recipe_id, current_user.id)
    return ApiResponse(message="删除成功")
