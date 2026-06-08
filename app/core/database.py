import sys
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import settings

USE_WINDOWS_SYNC = sys.platform == "win32"
DB_MODE = "windows-sync" if USE_WINDOWS_SYNC else "async"


def _to_sync_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgresql+asyncpg://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix) :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


if USE_WINDOWS_SYNC:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    _windows_engine = None
    _windows_sessionmaker = None

    def _get_windows_sessionmaker():
        global _windows_engine, _windows_sessionmaker
        if _windows_sessionmaker is None:
            _windows_engine = create_engine(_to_sync_url(settings.DATABASE_URL))
            _windows_sessionmaker = sessionmaker(
                bind=_windows_engine, expire_on_commit=False
            )
        return _windows_sessionmaker

    class _WindowsSyncSession:
        """Windows 本地：避免 psycopg 异步 + ProactorEventLoop 冲突。"""

        def __init__(self) -> None:
            self._session: Session = _get_windows_sessionmaker()()

        def add(self, instance: Any) -> None:
            self._session.add(instance)

        async def execute(self, statement: Any, *args: Any, **kwargs: Any):
            return self._session.execute(statement, *args, **kwargs)

        async def scalar(self, statement: Any, *args: Any, **kwargs: Any):
            return self._session.scalar(statement, *args, **kwargs)

        async def flush(self) -> None:
            self._session.flush()

        async def commit(self) -> None:
            self._session.commit()

        async def refresh(self, instance: Any, attribute_names: Any = None) -> None:
            self._session.refresh(instance, attribute_names)

        async def delete(self, instance: Any) -> None:
            self._session.delete(instance)

        async def close(self) -> None:
            self._session.close()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            if exc_type is not None:
                self._session.rollback()
            await self.close()

    def async_session():
        return _WindowsSyncSession()

else:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={
            "prepare_threshold": None,
            "connect_timeout": 10,
        },
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[Any, None]:
    async with async_session() as session:
        yield session
