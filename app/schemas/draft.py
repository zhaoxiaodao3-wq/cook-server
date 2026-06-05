from datetime import datetime
from pydantic import BaseModel, Field


class DraftIngredient(BaseModel):
    name: str
    amount: str = ""
    unit: str = ""


class DraftStep(BaseModel):
    id: int | None = None
    desc: str
    image: str | None = None


class DraftIn(BaseModel):
    id: str | None = None
    title: str = ""
    step: int = 0
    coverImage: str = ""
    duration: int | None = None
    difficulty: str = ""
    servings: int | None = None
    ingredients: list[DraftIngredient] = []
    steps: list[DraftStep] = []
    category: str = ""
    cuisine: str = ""
    tags: list[str] = []
    crowd: str = ""
    tips: str = ""


class DraftOut(BaseModel):
    id: str
    title: str
    step: int
    coverImage: str
    duration: int | None
    difficulty: str
    servings: int | None
    ingredients: list[DraftIngredient] = []
    steps: list[DraftStep] = []
    category: str
    cuisine: str
    tags: list[str] = []
    crowd: str
    tips: str
    savedAt: str

    model_config = {"from_attributes": True}


class MetaFiltersOut(BaseModel):
    categories: list[dict] = []
    cuisines: list[str] = []
    tags: list[str] = []
    difficulties: list[str] = ["简单", "中等", "困难"]
