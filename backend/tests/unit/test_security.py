"""Security unit tests."""

import uuid
from datetime import datetime, timezone

import pytest

from vornia.services.security import create_access_token, decode_access_token, hash_password, verify_password

pytestmark = pytest.mark.unit


def test_hash_password_returns_different_values() -> None:
    password = "secret123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert hash1 != password
    assert hash2 != password


def test_verify_password_with_correct_password() -> None:
    password = "secret123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_with_wrong_password() -> None:
    password = "secret123"
    hashed = hash_password(password)

    assert verify_password("wrong", hashed) is False


def test_create_access_token_contains_expected_claims() -> None:
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()

    token = create_access_token(
        user_id=str(user_id),
        email="alice@example.com",
        company_id=str(company_id),
        role="admin",
    )

    assert isinstance(token, str)
    assert len(token) > 0

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["email"] == "alice@example.com"
    assert payload["company_id"] == str(company_id)
    assert payload["role"] == "admin"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(Exception):
        decode_access_token("not-a-valid-token")


def test_decode_access_token_rejects_expired_token() -> None:
    from vornia.services.security import ALGORITHM, _jwt_secret

    expired_payload = {
        "sub": str(uuid.uuid4()),
        "email": "alice@example.com",
        "company_id": str(uuid.uuid4()),
        "role": "admin",
        "iat": 946684800,
        "exp": 946771200,
    }

    import jwt as pyjwt
    expired_token = pyjwt.encode(expired_payload, _jwt_secret(), algorithm=ALGORITHM)

    with pytest.raises(Exception):
        decode_access_token(expired_token)
