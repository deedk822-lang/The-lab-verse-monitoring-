"""
Database Session Management
"""

from __future__ import annotations

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from pr_fix_agent.core.config import Settings, get_settings

def init_db_engine(settings: Settings | None = None) -> str:
    global _engine
    if _engine is None:
        if settings is None:
            settings = get_settings()
        
        # Sanitize the database URL to prevent SQL injection
        db_url = settings.database_url
        # Replace 'postgresql+psycopg2://' with 'postgresql+asyncpg://'
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        
        connect_args = {}
        if settings.db_ssl_ca:
            connect_args["sslmode"] = "require"
            connect_args["sslrootcert"] = str(settings.db_ssl_ca)
        
        # Create the engine with pool size and max overflow
        _engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            connect_args=connect_args,
            echo=settings.db_echo,
        )
        
        # Event to log database connection events
        @event.listens_for(_engine, 'connect')
        def do_connect(dbapi_connection, connection_record):
            print(f"Database connected: {connection_record}")

    return _engine


async def init_async_db_engine(settings: Settings | None = None) -> str:
    global _async_engine
    if _async_engine is None:
        if settings is None:
            settings = get_settings()
        
        # Sanitize the database URL to prevent SQL injection
        db_url = settings.database_url
        
        # Replace 'postgresql+psycopg2://' with 'postgresql+asyncpg://'
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        
        connect_args = {}
        if settings.db_ssl_ca:
            connect_args["sslmode"] = "require"
            connect_args["sslrootcert"] = str(settings.db_ssl_ca)
        
        # Create the engine with pool size and max overflow
        _async_engine = create_async_engine(
            db_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.db_echo,
        )
        
        # Event to log database connection events
        @event.listens_for(_async_engine, 'connect')
        async def do_connect(dbapi_connection, connection_record):
            print(f"Database connected: {connection_record}")

    return _async_engine


def get_db_session() -> Session:
    engine = init_db_engine()
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
