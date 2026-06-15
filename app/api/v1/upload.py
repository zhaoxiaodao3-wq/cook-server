import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/upload", tags=["文件上传"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class UploadOut(BaseModel):
    url: str = Field(..., description="文件访问地址")
    filename: str = Field(..., description="文件名")


@router.post("/image", response_model=ApiResponse[UploadOut], summary="上传图片")
async def upload_image(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}，仅支持 jpg/png/webp")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = upload_dir / filename
    filepath.write_bytes(content)
    logger.info("Uploaded image saved to %s", filepath)

    return ApiResponse(data=UploadOut(url=f"/uploads/{filename}", filename=filename))
