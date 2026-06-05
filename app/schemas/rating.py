from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreateIn(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="评分：1-5")


class ReviewOut(BaseModel):
    id: str
    userId: str
    userName: str
    userAvatar: str
    rating: int
    date: str

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    review: ReviewOut
    recipeRating: float
    ratingCount: int


class ReviewDeleteResponse(BaseModel):
    recipeRating: float
    ratingCount: int


class UserReviewOut(BaseModel):
    recipeId: str
    rating: int
    date: str
    recipe: dict | None = None

    model_config = {"from_attributes": True}
