from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.category import CategoryOut
from app.services.category import get_all_categories

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", response_model=ApiResponse[list[CategoryOut]], summary="分类列表")
async def list_categories(db: AsyncSession = Depends(get_db)):
    categories = await get_all_categories(db)
    return ApiResponse(data=[CategoryOut.model_validate(c) for c in categories])
