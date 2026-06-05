from pydantic import BaseModel, Field


class FavoriteResponse(BaseModel):
    favorited: bool = Field(..., description="收藏状态")
