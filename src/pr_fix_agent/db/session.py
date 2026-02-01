"""
Database connection management
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..core.config import settings


def get_db_engine():
    """Get synchronous database engine"""
    return create_async_engine(
        settings.database.url.replace("postgresql://", "postgresql+psycopg2://"),
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        pool_recycle=settings.database.pool_recycle,
    )


def get_async_db_engine():
    """Get asynchronous database engine"""
    return create_async_engine(
        settings.database.url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        pool_recycle=settings.database.pool_recycle,
        poolclass=NullPool,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    engine = get_async_db_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db_engine():
    """Close database engine"""
    engine = get_async_db_engine()
    await engine.dispose()