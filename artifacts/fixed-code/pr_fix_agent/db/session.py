"""
Database Session Management
"""

from __future__ import annotations

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
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
        await _engine.dispose()
        _engine = None
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None

# Error handling in get_db_session
async def get_db_session_with_error_handling():
    try:
        session = get_db_session()
        # Use the session here
        session.close()  # Ensure to close the session
    except Exception as e:
        print(f"Error accessing database: {e}")
    finally:
        await close_db()

# Example usage with asyncio
async def main():
    async with aiohttp.ClientSession() as session:
        # Use your asynchronous code here, passing the session as needed
        await get_db_session_with_error_handling()
        await session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())