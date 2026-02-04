"""
Database Session Management
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
import os

from pr_fix_agent.core.config import Settings, get_settings

engine = None
async_engine = None


def get_db_engine(settings: Settings | None = None):
    global _engine
    if _engine is None:
        if settings is None:
            settings = get_settings()
        
        try:
            # Ensure SSL is enabled for connections when db_ssl_ca is set in the environment variables
            connect_args = {}
            if "db_ssl_ca" in os.environ:
                connect_args["sslmode"] = "require"
                connect_args["sslrootcert"] = str(os.environ.get("db_ssl_ca"))
        
            _engine = create_engine(
                str(settings.database_url),
                poolclass=QueuePool,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                connect_args=connect_args,
                echo=settings.db_echo,
            )
        except Exception as e:
            print(f"Error creating database engine: {e}")
    return _engine


async def get_async_db_engine(settings: Settings | None = None):
    global _async_engine
    if _async_engine is None:
        if settings is None:
            settings = get_settings()
        
        try:
            async_url = str(settings.database_url).replace("postgresql+psycopg2://", "postgresql+asyncpg://")
            _async_engine = create_async_engine(
                async_url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                echo=settings.db_echo,
            )
        except Exception as e:
            print(f"Error creating asynchronous database engine: {e}")
    return _async_engine


def get_db_session() -> Session:
    global _engine
    if _engine is None:
        _engine = get_db_engine()
    
    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return SessionLocal()


async def close_db() -> None:
    global _engine, _async_engine
    
    if _engine is not None:
        try:
            await _engine.dispose()
        except Exception as e:
            print(f"Error disposing database engine: {e}")
    
    if _async_engine is not None:
        try:
            await _async_engine.dispose()
        except Exception as e:
            print(f"Error disposing asynchronous database engine: {e}")