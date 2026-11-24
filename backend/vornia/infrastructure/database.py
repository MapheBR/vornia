"""Database configuration."""

import asyncio
from contextlib import suppress

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

_pools: dict[str, tuple[asyncpg.Pool, asyncio.AbstractEventLoop]] = {}


async def _get_pool(name: str, url: str) -> asyncpg.Pool:
    """Return a pool bound to the current event loop, recreating it if needed."""
    current_loop = asyncio.get_running_loop()
    entry = _pools.get(name)

    if entry is not None and entry[1] is not current_loop:
        with suppress(Exception):
            await entry[0].close()
        entry = None

    if entry is None:
        entry = (await asyncpg.create_pool(url), current_loop)
        _pools[name] = entry

    return entry[0]


def _require(value: str, env_name: str) -> str:
    if not value:
        raise RuntimeError(f"{env_name} environment variable is not set")
    return value


async def get_db_pool() -> asyncpg.Pool:
    """Pool de runtime, sujeito a RLS (role vornia_app)."""
    return await _get_pool(
        "app",
        _require(settings.database_url_app, "DATABASE_URL_APP"),
    )


async def get_bootstrap_pool() -> asyncpg.Pool:
    """Pool de bootstrap de tenant, com BYPASSRLS (role vornia_auth)."""
    return await _get_pool(
        "bootstrap",
        _require(settings.database_url_bootstrap, "DATABASE_URL_BOOTSTRAP"),
    )


async def close_db_pool() -> None:
    """Close every pool created by this process."""
    for name in list(_pools):
        pool, _ = _pools.pop(name)
        with suppress(Exception):
            await pool.close()
