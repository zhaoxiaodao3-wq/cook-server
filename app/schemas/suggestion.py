from pydantic import BaseModel, Field


class SuggestionCreateIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="建议内容")


class SuggestionOut(BaseModel):
    id: str
    userId: str
    userName: str
    userAvatar: str
    content: str
    date: str

    model_config = {"from_attributes": True}
