"""Serviço de refresh tokens opacos (SHA-256 no banco)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

REFRESH_TOKEN_EXPIRE_DAYS = 7


def generate_refresh_token() -> str:
    """Gera token opaco de 256 bits (urlsafe, sem '=')."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash SHA-256 em hexadecimal (64 chars)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_expiry() -> datetime:
    """Expiração padrão do refresh token (7 dias)."""
    return datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


def detect_reuse(row: dict[str, Any]) -> bool:
    """Detecta reuso: token já revogado e substituído por outro."""
    return row.get("revoked_at") is not None and row.get("replaced_by_id") is not None
