"""Global pytest configuration."""

import os

# Defaults para desenvolvimento local; CI e .env sobrescrevem via ambiente.
os.environ.setdefault("JWT_SECRET", "test-secret-for-all-tests-only-not-used-in-production")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://vornia:vornia@localhost:15433/vornia")
os.environ.setdefault(
    "DATABASE_URL_APP",
    "postgresql://vornia_app:vornia_app@localhost:15433/vornia",
)
os.environ.setdefault(
    "DATABASE_URL_BOOTSTRAP",
    "postgresql://vornia_auth:vornia_auth@localhost:15433/vornia",
)
