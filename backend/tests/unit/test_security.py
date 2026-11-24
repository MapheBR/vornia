"""Unit tests for password hashing and JWT helpers."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from vornia.services.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit

TEST_SECRET = "unit-test-secret-not-used-in-production"


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch: pytest.MonkeyPatch) -> str:
    """Provide a deterministic JWT secret for every test in this module."""
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    return TEST_SECRET


def test_hash_password_uses_unique_salt_per_call() -> None:
    first = hash_password("strong-password")
    second = hash_password("strong-password")

    assert first != second
    assert first.startswith("$2")


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("strong-password")

    assert verify_password("strong-password", hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("strong-password")

    assert verify_password("wrong-password", hashed) is False


def test_create_access_token_includes_expected_claims() -> None:
    token = create_access_token(
        user_id="user-1",
        email="alice@example.com",
        company_id="company-1",
        role="admin",
    )

    claims = decode_access_token(token)

    assert claims["sub"] == "user-1"
    assert claims["email"] == "alice@example.com"
    assert claims["company_id"] == "company-1"
    assert claims["role"] == "admin"
    assert claims["exp"] - claims["iat"] == 24 * 60 * 60


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-valid-token")


def test_decode_access_token_rejects_expired_token() -> None:
    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": "user-1",
            "email": "alice@example.com",
            "company_id": "company-1",
            "role": "admin",
            "iat": now - timedelta(hours=48),
            "exp": now - timedelta(hours=24),
        },
        TEST_SECRET,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)
