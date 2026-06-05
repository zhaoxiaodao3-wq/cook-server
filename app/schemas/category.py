from datetime import datetime
from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: int
    name: str
    key: str | None = None
    icon: str | None = None
    sort_order: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
