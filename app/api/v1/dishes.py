from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.dish import DishCreateIn, DishUpdateIn, DishListOut, DishDetailOut
from app.services.dish import get_dishes, get_dish_detail, create_dish, update_dish, delete_dish

router = APIRouter(prefix="/dishes", tags=["菜品"])


@router.get("", response_model=ApiResponse[PaginatedData[DishListOut]], summary="菜品列表")
async def list_dishes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: int | None = Query(None, description="分类筛选"),
    difficulty: int | None = Query(None, ge=1, le=3, description="难度筛选：1简单 2中等 3困难"),
    keyword: str | None = Query(None, description="搜索关键词"),
    sort: str = Query("latest", description="排序：latest 最新 / rating 评分 / popular_week 本周热门 / popular_month 本月热门"),
    db: AsyncSession = Depends(get_db),
):
    dishes, total = await get_dishes(
        db, page=page, page_size=page_size, category_id=category_id, difficulty=difficulty, keyword=keyword, sort=sort
    )
    return ApiResponse(
        data=PaginatedData(
            items=[DishListOut.model_validate(d) for d in dishes],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{dish_id}", response_model=ApiResponse[DishDetailOut], summary="菜品详情")
async def get_dish(dish_id: str, db: AsyncSession = Depends(get_db)):
    dish = await get_dish_detail(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return ApiResponse(data=DishDetailOut.model_validate(dish))


@router.post("", response_model=ApiResponse[DishDetailOut], status_code=201, summary="新增菜品")
async def create_new_dish(
    body: DishCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dish = await create_dish(db, current_user.id, body)
    return ApiResponse(data=DishDetailOut.model_validate(dish))


@router.put("/{dish_id}", response_model=ApiResponse[DishDetailOut], summary="编辑菜品")
async def edit_dish(
    dish_id: str,
    body: DishUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dish = await get_dish_detail(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="菜品不存在")
    if dish.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己的菜品")
    dish = await update_dish(db, dish, body)
    return ApiResponse(data=DishDetailOut.model_validate(dish))


@router.delete("/{dish_id}", response_model=ApiResponse, summary="删除菜品")
async def remove_dish(
    dish_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dish = await get_dish_detail(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="菜品不存在")
    if dish.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的菜品")
    await delete_dish(db, dish)
    return ApiResponse(message="删除成功")
