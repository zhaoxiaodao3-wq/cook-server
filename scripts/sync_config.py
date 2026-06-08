"""读取 .env 中的本地 / 远程数据库配置与同步开关。"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

# 业务表（按外键依赖顺序：先父后子）
SYNC_TABLES = [
    "users",
    "categories",
    "dishes",
    "ingredients",
    "steps",
    "ratings",
    "suggestions",
    "favorites",
    "drafts",
]


class SyncSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cookbook"
    LOCAL_DATABASE_URL: str = ""
    REMOTE_DATABASE_URL: str = ""
    DB_SYNC_ENABLED: bool = False


def to_psycopg2_url(url: str) -> str:
    """SQLAlchemy / Alembic 异步 URL → psycopg2 同步 URL。"""
    for prefix in ("postgresql+psycopg://", "postgresql+asyncpg://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    return url


def to_async_url(url: str) -> str:
    """确保 Alembic 可用的 async URL。"""
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def get_local_url(settings: SyncSettings | None = None) -> str:
    settings = settings or SyncSettings()
    raw = settings.LOCAL_DATABASE_URL.strip() or settings.DATABASE_URL
    return to_psycopg2_url(raw)


def get_remote_url(settings: SyncSettings | None = None) -> str:
    settings = settings or SyncSettings()
    raw = settings.REMOTE_DATABASE_URL.strip()
    if not raw:
        raise ValueError(
            "未配置 REMOTE_DATABASE_URL。请在 .env 中填写 Supabase Direct 连接串（端口 5432）。"
        )
    return to_psycopg2_url(raw)


def ensure_sync_enabled(settings: SyncSettings | None = None) -> SyncSettings:
    settings = settings or SyncSettings()
    if not settings.DB_SYNC_ENABLED:
        raise RuntimeError(
            "数据库同步已关闭。请在 .env 中设置 DB_SYNC_ENABLED=true 后再执行。"
        )
    return settings
