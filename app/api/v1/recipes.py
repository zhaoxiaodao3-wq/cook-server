from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.dish import (
    RecipeCreateIn, RecipeUpdateIn, RecipeListItem, RecipeDetailOut,
    AuthorBrief, IngredientOut, StepOut, ReviewOut, SuggestionOut as SugOut,
    DIFFICULTY_MAP,
)
from app.services.dish import get_dishes, get_ranked_dishes, get_dish_detail, create_dish, update_dish, delete_dish
from app.services.favorite import get_user_favorite_dish_ids
from app.services.rating import get_user_rating_for_dish
from app.services.suggestion import get_user_suggestion_for_dish

router = APIRouter(prefix="/recipes", tags=["菜谱"])


def _dish_to_list_item(dish, fav_set: set | None = None) -> RecipeListItem:
    fav = None if fav_set is None else dish.id in fav_set
    return RecipeListItem(
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
        isFavorite=fav,
    )


def _dish_to_detail(dish, fav: bool = False, my_review: dict | None = None, my_suggestion: dict | None = None) -> RecipeDetailOut:
    reviews = []
    if dish.ratings:
        for r in dish.ratings:
            reviews.append(ReviewOut(
                id=r.id,
                userId=r.user_id,
                userName=r.user.nickname if r.user else "",
                userAvatar=r.user.avatar_url or "" if r.user else "",
                rating=r.stars,
                date=r.created_at.isoformat() if r.created_at else "",
            ))

    suggestions = []
    if dish.suggestions:
        for s in dish.suggestions:
            suggestions.append(SugOut(
                id=s.id,
                userId=s.user_id,
                userName=s.user.nickname if s.user else "",
                userAvatar=s.user.avatar_url or "" if s.user else "",
                content=s.content,
                date=s.created_at.isoformat() if s.created_at else "",
            ))

    return RecipeDetailOut(
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
        reviews=reviews,
        suggestions=suggestions,
        isFavorite=fav,
        myReview=my_review,
        mySuggestion=my_suggestion,
    )


@router.get("", response_model=ApiResponse[PaginatedData[RecipeListItem]], summary="菜谱列表")
async def list_recipes(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50, alias="pageSize"),
    q: str | None = Query(None, description="关键词搜索"),
    category: str | None = Query(None, description="分类"),
    cuisine: str | None = Query(None, description="菜系"),
    tag: str | None = Query(None, description="标签"),
    sort: str = Query("createdAt", description="排序：rating / createdAt"),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    dishes, total = await get_dishes(
        db, page=page, page_size=pageSize,
        category=category, cuisine=cuisine, tag=tag,
        keyword=q, sort=sort,
    )
    fav_set = None
    if current_user:
        fav_set = await get_user_favorite_dish_ids(db, current_user.id)
    return ApiResponse(data=PaginatedData(
        items=[_dish_to_list_item(d, fav_set) for d in dishes],
        total=total,
        page=page,
        pageSize=pageSize,
        hasMore=(page * pageSize) < total,
    ))


@router.get("/ranked", response_model=ApiResponse[list[RecipeListItem]], summary="评分榜")
async def ranked_recipes(
    limit: int = Query(10, ge=1, le=50),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    dishes = await get_ranked_dishes(db, limit=limit)
    fav_set = None
    if current_user:
        fav_set = await get_user_favorite_dish_ids(db, current_user.id)
    return ApiResponse(data=[_dish_to_list_item(d, fav_set) for d in dishes])


@router.get("/{recipe_id}", response_model=ApiResponse[RecipeDetailOut], summary="菜谱详情")
async def get_recipe(
    recipe_id: str,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    dish = await get_dish_detail(db, recipe_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="菜谱不存在")

    fav = False
    my_review = None
    my_suggestion = None
    if current_user:
        fav = dish.id in (await get_user_favorite_dish_ids(db, current_user.id))
        rating = await get_user_rating_for_dish(db, recipe_id, current_user.id)
        if rating:
            my_review = {"id": rating.id, "rating": rating.stars}
        sug = await get_user_suggestion_for_dish(db, recipe_id, current_user.id)
        if sug:
            my_suggestion = {"id": sug.id, "content": sug.content}

    return ApiResponse(data=_dish_to_detail(dish, fav=fav, my_review=my_review, my_suggestion=my_suggestion))


@router.post("", response_model=ApiResponse[RecipeDetailOut], status_code=201, summary="发布菜谱")
async def create_recipe(
    body: RecipeCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.title:
        raise HTTPException(status_code=400, detail="菜谱名称不能为空")
    if not body.ingredients or not any(i.name for i in body.ingredients):
        raise HTTPException(status_code=400, detail="至少需要一项食材")
    if not body.steps or not any(s.desc for s in body.steps):
        raise HTTPException(status_code=400, detail="至少需要一个步骤")

    dish = await create_dish(db, current_user.id, body)
    return ApiResponse(data=_dish_to_detail(dish))


@router.patch("/{recipe_id}", response_model=ApiResponse[RecipeDetailOut], summary="编辑菜谱")
async def edit_recipe(
    recipe_id: str,
    body: RecipeUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dish = await get_dish_detail(db, recipe_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    if dish.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己的菜谱")
    dish = await update_dish(db, dish, body)
    return ApiResponse(data=_dish_to_detail(dish))


@router.delete("/{recipe_id}", response_model=ApiResponse, summary="删除菜谱")
async def remove_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dish = await get_dish_detail(db, recipe_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    if dish.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的菜谱")
    await delete_dish(db, dish)
    return ApiResponse(message="删除成功")
