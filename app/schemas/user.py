from datetime import datetime
from pydantic import BaseModel, Field


class WechatLoginIn(BaseModel):
    code: str = Field(..., description="微信小程序登录凭证")
    nickName: str = Field("", description="用户填写的昵称")
    avatarUrl: str = Field("", description="头像URL，若为https CDN地址则传入")


class UserOut(BaseModel):
    id: str
    name: str
    avatar: str
    bio: str

    model_config = {"from_attributes": True}


class UserStatsOut(BaseModel):
    uploads: int = Field(0, description="上传的菜品数")
    reviews: int = Field(0, description="评分过的菜品数")
    suggestions: int = Field(0, description="写过的建议数")
    favorites: int = Field(0, description="收藏数")


class UserProfileOut(BaseModel):
    id: str
    name: str
    avatar: str
    bio: str
    stats: UserStatsOut | None = None

    model_config = {"from_attributes": True}


class UserUpdateIn(BaseModel):
    name: str | None = Field(None, description="昵称")
    bio: str | None = Field(None, description="简介")


class LoginOut(BaseModel):
    token: str = Field(..., description="JWT 访问令牌")
    expiresIn: int = Field(7200, description="过期时间（秒）")
    user: UserOut


class AvatarOut(BaseModel):
    avatarUrl: str = Field(..., description="头像URL")
