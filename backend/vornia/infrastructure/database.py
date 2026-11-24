"""Database configuration."""

import asyncio

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from vornia.infrastructure.settings import settings

ASYNC_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=NullPool,
    future=True,
)

_db_pool: asyncpg.Pool | None = None
_db_pool_loop: asyncio.AbstractEventLoop | None = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the asyncpg pool for the current event loop."""
    global _db_pool, _db_pool_loop

    current_loop = asyncio.get_running_loop()
    if _db_pool is not None and _db_pool_loop is not current_loop:
        _db_pool = None
        _db_pool_loop = None

    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(settings.database_url)
        _db_pool_loop = current_loop

    if _db_pool is None:
        raise RuntimeError("Failed to create database pool")

    return _db_pool


async def close_db_pool() -> None:
    """Close the current asyncpg pool."""
    global _db_pool, _db_pool_loop
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None
        _db_pool_loop = None
