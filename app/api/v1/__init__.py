from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.recipes import router as recipes_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.recipe_suggestions import router as recipe_suggestions_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.drafts import router as drafts_router
from app.api.v1.upload import router as upload_router
from app.api.v1.categories import router as categories_router
from app.api.v1.meta import router as meta_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(recipes_router)
router.include_router(reviews_router)
router.include_router(recipe_suggestions_router)
router.include_router(favorites_router)
router.include_router(drafts_router)
router.include_router(upload_router)
router.include_router(categories_router)
router.include_router(meta_router)
