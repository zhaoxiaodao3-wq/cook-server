from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(0, description="业务状态码，0=成功")
    message: str = Field("ok", description="提示信息")
    data: T | None = Field(None, description="响应数据")


class PaginatedData(BaseModel, Generic[T]):
    items: list[T] = Field([], description="数据列表")
    total: int = Field(0, description="总条数")
    page: int = Field(1, description="当前页码")
    pageSize: int = Field(10, description="每页数量", serialization_alias="pageSize")
    hasMore: bool = Field(False, description="是否有更多", serialization_alias="hasMore")

    model_config = {"populate_by_name": True}
