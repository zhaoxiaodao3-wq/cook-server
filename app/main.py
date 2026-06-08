import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.database import async_session

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="菜品小程序 API",
    description="记录菜品制作步骤流程的服务端接口，支持菜品管理、评分和建议",
    version="0.1.0",
    lifespan=lifespan,
)

upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db():
    """检查数据库连通性（联调排错用）"""
    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "database": str(exc)},
        )


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    """开发期返回具体错误，便于小程序 Network 面板排查 500"""
    logger.exception("Unhandled %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": str(exc), "data": None},
    )
