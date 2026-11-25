"""FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vornia.api.v1.router import router as api_v1_router
from vornia.infrastructure.database import close_db_pool, get_db_pool
from vornia.infrastructure.rate_limit_setup import setup_rate_limit
from vornia.infrastructure.settings import settings
from vornia.middleware.security_headers import security_headers_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    await get_db_pool()
    setup_rate_limit()
    yield
    await close_db_pool()


app = FastAPI(title="Vornia API", version="0.1.0", lifespan=lifespan)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_v1_router, prefix="/api/v1")
app.middleware("http")(security_headers_middleware)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
