import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.user import UserProfileOut, UserStatsOut, UserUpdateIn, AvatarOut
from app.schemas.dish import RecipeListItem, AuthorBrief
from app.schemas.rating import UserReviewOut
from app.services.user import update_user as svc_update_user, get_user_stats
from app.services.dish import get_user_dishes
from app.services.rating import get_user_ratings
from app.services.favorite import get_user_favorites

router = APIRouter(prefix="/users", tags=["用户"])


def _user_to_name(user: User) -> str:
    return user.nickname


def _dish_to_list_item(dish, is_fav_set: set | None = None) -> RecipeListItem:
    from app.schemas.dish import DIFFICULTY_MAP
    fav = None if is_fav_set is None else dish.id in is_fav_set
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


@router.get("/me", response_model=ApiResponse[UserProfileOut], summary="获取当前用户信息与统计")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_user_stats(db, current_user.id)
    return ApiResponse(data=UserProfileOut(
        id=current_user.id,
        name=current_user.nickname,
        avatar=current_user.avatar_url or "",
        bio=current_user.bio or "",
        stats=UserStatsOut(**stats),
    ))


@router.patch("/me", response_model=ApiResponse[UserProfileOut], summary="更新用户信息")
async def update_me(
    body: UserUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await svc_update_user(db, current_user, body.name, body.bio)
    stats = await get_user_stats(db, user.id)
    return ApiResponse(data=UserProfileOut(
        id=user.id,
        name=user.nickname,
        avatar=user.avatar_url or "",
        bio=user.bio or "",
        stats=UserStatsOut(**stats),
    ))


@router.post("/me/avatar", response_model=ApiResponse[AvatarOut], summary="上传头像")
async def upload_avatar(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"avatar_{uuid.uuid4().hex}{ext}"
    filepath = upload_dir / filename
    filepath.write_bytes(content)

    avatar_url = f"/uploads/{filename}"
    await svc_update_user(db, current_user, None, None, avatar_url)

    return ApiResponse(data=AvatarOut(avatarUrl=avatar_url))


@router.get("/me/recipes", response_model=ApiResponse[PaginatedData[RecipeListItem]], summary="我的菜谱")
async def my_recipes(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dishes, total = await get_user_dishes(db, current_user.id, page=page, page_size=pageSize)
    return ApiResponse(data=PaginatedData(
        items=[_dish_to_list_item(d) for d in dishes],
        total=total,
        page=page,
        pageSize=pageSize,
        hasMore=(page * pageSize) < total,
    ))


@router.get("/me/reviews", response_model=ApiResponse[PaginatedData[UserReviewOut]], summary="我的评价")
async def my_reviews(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ratings, total = await get_user_ratings(db, current_user.id, page=page, page_size=pageSize)
    items = []
    for r in ratings:
        recipe_data = None
        if r.dish:
            recipe_data = {
                "id": r.dish.id,
                "title": r.dish.name,
                "coverImage": r.dish.cover,
            }
        items.append(UserReviewOut(
            recipeId=r.dish_id,
            rating=r.stars,
            date=r.created_at.isoformat() if r.created_at else "",
            recipe=recipe_data,
        ))
    return ApiResponse(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        hasMore=(page * pageSize) < total,
    ))


@router.get("/me/favorites", response_model=ApiResponse[PaginatedData[RecipeListItem]], summary="我的收藏")
async def my_favorites(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dishes, total = await get_user_favorites(db, current_user.id, page=page, page_size=pageSize)
    fav_set = {d.id for d in dishes}
    return ApiResponse(data=PaginatedData(
        items=[_dish_to_list_item(d, fav_set) for d in dishes],
        total=total,
        page=page,
        pageSize=pageSize,
        hasMore=(page * pageSize) < total,
    ))
