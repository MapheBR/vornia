"""Integration test fixtures with PostgreSQL."""

import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio

DEFAULT_TEST_DATABASE_URL = "postgresql://vornia:vornia@localhost:15433/vornia"
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def configure_environment(database_url: str) -> str:
    os.environ["DATABASE_URL"] = database_url
    os.environ["COOKIE_SECURE"] = "false"
    return database_url


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(configure_environment: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = configure_environment
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR),
        env=env,
        check=True,
    )


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_database(database_url: str) -> AsyncGenerator[None, None]:
    pool = await asyncpg.create_pool(database_url)
    assert pool is not None
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM company_users;")
            await conn.execute("DELETE FROM users;")
            await conn.execute("DELETE FROM companies;")
        yield
    finally:
        await pool.close()
