"""Integration test fixtures with PostgreSQL."""

import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from vornia.main import app

DEFAULT_TEST_DATABASE_URL = "postgresql://vornia:vornia@localhost:15433/vornia"
DEFAULT_TEST_DATABASE_URL_APP = "postgresql://vornia_app:vornia_app@localhost:15433/vornia"
DEFAULT_TEST_DATABASE_URL_BOOTSTRAP = "postgresql://vornia_auth:vornia_auth@localhost:15433/vornia"
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def resolve_database_url() -> str:
    """Resolve the owner/migrations database URL.

    Priority: TEST_DATABASE_URL, then DATABASE_URL (set by CI), then the local
    development default.
    """
    return (
        os.environ.get("TEST_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or DEFAULT_TEST_DATABASE_URL
    )


def resolve_app_database_url() -> str:
    """Resolve the RLS-enforced runtime database URL."""
    return (
        os.environ.get("TEST_DATABASE_URL_APP")
        or os.environ.get("DATABASE_URL_APP")
        or DEFAULT_TEST_DATABASE_URL_APP
    )


def resolve_bootstrap_database_url() -> str:
    """Resolve the BYPASSRLS bootstrap database URL used by register/login."""
    return (
        os.environ.get("TEST_DATABASE_URL_BOOTSTRAP")
        or os.environ.get("DATABASE_URL_BOOTSTRAP")
        or DEFAULT_TEST_DATABASE_URL_BOOTSTRAP
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    return resolve_database_url()


@pytest.fixture(scope="session", autouse=True)
def configure_environment(database_url: str) -> str:
    os.environ["DATABASE_URL"] = database_url
    os.environ["DATABASE_URL_APP"] = resolve_app_database_url()
    os.environ["DATABASE_URL_BOOTSTRAP"] = resolve_bootstrap_database_url()
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
async def clean_database() -> AsyncGenerator[None, None]:
    """Limpa os dados usando a role de bootstrap (BYPASSRLS).

    Com FORCE ROW LEVEL SECURITY, o owner tambem esta sujeito a RLS e nao
    conseguiria apagar linhas sem claims.
    """
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM company_users;")
            await conn.execute("DELETE FROM users;")
            await conn.execute("DELETE FROM employees;")
            await conn.execute("DELETE FROM companies;")
        yield
    finally:
        await pool.close()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="function")
async def other_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
