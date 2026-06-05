from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.draft import MetaFiltersOut
from app.services.category import get_all_categories

router = APIRouter(prefix="/meta", tags=["元数据"])

DEFAULT_CUISINES = ["川菜", "粤菜", "鲁菜", "苏菜", "其他"]
DEFAULT_TAGS = ["减脂", "素食", "精选", "快手菜"]
DEFAULT_DIFFICULTIES = ["简单", "中等", "困难"]


@router.get("/filters", response_model=ApiResponse[MetaFiltersOut], summary="筛选项元数据")
async def get_filters(db: AsyncSession = Depends(get_db)):
    categories = await get_all_categories(db)
    category_list = [{"key": "all", "label": "全部"}]
    for c in categories:
        category_list.append({"key": c.key or c.name, "label": c.name})

    return ApiResponse(data=MetaFiltersOut(
        categories=category_list,
        cuisines=DEFAULT_CUISINES,
        tags=DEFAULT_TAGS,
        difficulties=DEFAULT_DIFFICULTIES,
    ))
