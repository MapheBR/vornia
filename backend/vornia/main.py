"""FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from vornia.api.v1.router import router as api_v1_router
from vornia.infrastructure.database import close_db_pool, get_db_pool


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    await get_db_pool()
    yield
    await close_db_pool()


app = FastAPI(title="Vornia API", version="0.1.0", lifespan=lifespan)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
