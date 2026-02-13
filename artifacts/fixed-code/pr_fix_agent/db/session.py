"""
Database Session Management
"""

from __future__ import annotations

from sqlalchemy import create_engine, String
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from pr_fix_agent.core.config import Settings, get_settings

# Database URL and credentials should be securely stored in environment variables or configuration files
DATABASE_URL = "postgresql://user:password@localhost/dbname"
SSL_CA = "/path/to/ca.pem"

_engine = None
_async_engine = None


def get_db_engine(settings: Settings | None = None):
    global _engine
    if _engine is None:
        if settings is None:
            settings = get_settings()
        connect_args = {}
        if SSL_CA:
            connect_args["sslmode"] = "require"
            connect_args["sslrootcert"] = SSL_CA
        engine = create_engine(
            DATABASE_URL,
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
        async_url = DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        engine = create_async_engine(
            async_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.db_echo,
        )
    return _async_engine


def get_db_session() -> Session:
    global _engine
    if _engine is None:
        engine = get_db_engine()
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def close_db() -> None:
    global _engine, _async_engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None