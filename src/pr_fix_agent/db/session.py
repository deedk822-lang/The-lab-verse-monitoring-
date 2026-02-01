"""
Database Session Management
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from pr_fix_agent.core.config import Settings, get_settings

_engine = None
_async_engine = None


def get_db_engine(settings: Settings | None = None):
    global _engine
    if _engine is None:
        if settings is None:
            settings = get_settings()
        connect_args = {}
        if settings.db_ssl_ca:
            connect_args["sslmode"] = "require"
            connect_args["sslrootcert"] = str(settings.db_ssl_ca)
        _engine = create_engine(
            str(settings.database_url),
            poolclass=QueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            connect_args=connect_args,
            echo=settings.db_echo,
        )
    return _engine


async def get_async_db_engine(settings: Settings | None = None):
    global _async_engine
    if _async_engine is None:
        if settings is None:
            settings = get_settings()
        async_url = str(settings.database_url).replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        _async_engine = create_async_engine(
            async_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.db_echo,
        )
    return _async_engine


def get_db_session() -> Session:
    engine = get_db_engine()
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


async def close_db() -> None:
    global _engine, _async_engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
