import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.common import ApiResponse
from app.schemas.user import WechatLoginIn, LoginOut, UserOut
from app.services.user import get_or_create_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/wechat-login", response_model=ApiResponse[LoginOut], summary="微信登录")
async def wechat_login(body: WechatLoginIn, db: AsyncSession = Depends(get_db)):
    if not body.nickName or len(body.nickName) > 32:
        raise HTTPException(status_code=400, detail="昵称不能为空且不超过32字")

    if settings.WECHAT_APP_ID and settings.WECHAT_APP_SECRET:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                    "js_code": body.code,
                    "grant_type": "authorization_code",
                },
            )
            wx_data = resp.json()
            openid = wx_data.get("openid")
            if not openid:
                raise HTTPException(status_code=400, detail=f"微信登录失败: {wx_data.get('errmsg', '未知错误')}")
    else:
        openid = f"dev_{body.code}"

    avatar_url = body.avatarUrl if body.avatarUrl and body.avatarUrl.startswith("https://") else ""
    user = await get_or_create_user(db, openid, nickname=body.nickName, avatar_url=avatar_url)
    token = create_access_token(user.id)

    user_out = UserOut(
        id=user.id,
        name=user.nickname,
        avatar=user.avatar_url or "",
        bio=user.bio or "",
    )
    return ApiResponse(data=LoginOut(
        token=token,
        expiresIn=settings.JWT_EXPIRE_MINUTES * 60,
        user=user_out,
    ))
