from datetime import datetime
from pydantic import BaseModel, Field

DIFFICULTY_MAP = {1: "简单", 2: "中等", 3: "困难"}
DIFFICULTY_REVERSE = {"简单": 1, "中等": 2, "困难": 3}


class AuthorBrief(BaseModel):
    id: str
    name: str
    avatar: str

    model_config = {"from_attributes": True}


class IngredientIn(BaseModel):
    name: str = Field(..., description="食材名称")
    amount: str = Field("", description="用量")
    unit: str = Field("", description="单位")


class IngredientOut(BaseModel):
    name: str
    amount: str
    unit: str

    model_config = {"from_attributes": True}


class StepIn(BaseModel):
    id: int | None = Field(None, description="步骤ID（前端时间戳）")
    desc: str = Field(..., description="步骤说明")
    image: str | None = Field(None, description="步骤配图")


class StepOut(BaseModel):
    id: int
    desc: str
    image: str | None = None

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: str
    userId: str
    userName: str
    userAvatar: str
    rating: int
    date: str

    model_config = {"from_attributes": True}


class SuggestionOut(BaseModel):
    id: str
    userId: str
    userName: str
    userAvatar: str
    content: str
    date: str

    model_config = {"from_attributes": True}


class RecipeCreateIn(BaseModel):
    title: str = Field(..., max_length=128, description="菜谱名称")
    coverImage: str | None = Field(None, description="封面图URL")
    duration: int | None = Field(None, description="烹饪时长（分钟）")
    difficulty: str | None = Field(None, description="难度：简单/中等/困难")
    category: str = Field(..., description="分类：breakfast/lunch/dinner/dessert")
    cuisine: str | None = Field(None, description="菜系")
    tags: list[str] = Field([], description="标签")
    servings: int | None = Field(None, description="份量")
    ingredients: list[IngredientIn] = Field([], description="食材清单")
    steps: list[StepIn] = Field([], description="制作步骤")
    tips: str | None = Field(None, description="贴士")
    crowd: str | None = Field(None, description="适合人群")


class RecipeUpdateIn(BaseModel):
    title: str | None = Field(None, max_length=128, description="菜谱名称")
    coverImage: str | None = Field(None, description="封面图URL")
    duration: int | None = Field(None, description="烹饪时长（分钟）")
    difficulty: str | None = Field(None, description="难度：简单/中等/困难")
    category: str | None = Field(None, description="分类")
    cuisine: str | None = Field(None, description="菜系")
    tags: list[str] | None = Field(None, description="标签")
    servings: int | None = Field(None, description="份量")
    ingredients: list[IngredientIn] | None = Field(None, description="食材清单")
    steps: list[StepIn] | None = Field(None, description="制作步骤")
    tips: str | None = Field(None, description="贴士")
    crowd: str | None = Field(None, description="适合人群")


class RecipeListItem(BaseModel):
    id: str
    title: str
    coverImage: str | None
    author: AuthorBrief | None = None
    rating: float
    ratingCount: int
    createdAt: str
    duration: int | None
    difficulty: str | None
    category: str | None
    cuisine: str | None
    tags: list[str] = []
    servings: int | None
    isFavorite: bool | None = None

    model_config = {"from_attributes": True}


class RecipeDetailOut(BaseModel):
    id: str
    title: str
    coverImage: str | None
    author: AuthorBrief | None = None
    rating: float
    ratingCount: int
    createdAt: str
    duration: int | None
    difficulty: str | None
    category: str | None
    cuisine: str | None
    tags: list[str] = []
    servings: int | None
    ingredients: list[IngredientOut] = []
    steps: list[StepOut] = []
    tips: str | None
    crowd: str | None
    reviews: list[ReviewOut] = []
    suggestions: list[SuggestionOut] = []
    isFavorite: bool | None = None
    myReview: dict | None = None
    mySuggestion: dict | None = None

    model_config = {"from_attributes": True}


class RankedRecipeOut(BaseModel):
    id: str
    title: str
    coverImage: str | None
    author: AuthorBrief | None = None
    rating: float
    ratingCount: int
    createdAt: str
    duration: int | None
    difficulty: str | None
    category: str | None
    cuisine: str | None
    tags: list[str] = []
    servings: int | None
    isFavorite: bool | None = None

    model_config = {"from_attributes": True}
