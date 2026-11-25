"""Testes unitários de tokens opacos: hash, expiração e rotação."""

from datetime import UTC, datetime

import pytest

pytestmark = pytest.mark.unit


def test_hash_is_sha256_hex() -> None:
    from vornia.services.token import hash_token

    token = "abc123"
    hashed = hash_token(token)
    assert len(hashed) == 64
    assert hashed == "6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090"


def test_different_tokens_produce_different_hashes() -> None:
    from vornia.services.token import hash_token

    assert hash_token("a") != hash_token("b")


def test_opaque_token_is_urlsafe_and_long() -> None:
    from vornia.services.token import generate_refresh_token

    token = generate_refresh_token()
    assert len(token) >= 40
    assert "/" not in token and "+" not in token and "=" not in token


def test_expiry_is_in_the_future() -> None:
    from vornia.services.token import refresh_expiry

    assert refresh_expiry() > datetime.now(UTC)


def test_reuse_detection_marks_family_revoked() -> None:
    from vornia.services.token import detect_reuse

    token = {
        "revoked_at": datetime.now(UTC),
        "replaced_by_id": "some-uuid",
    }
    assert detect_reuse(token) is True


def test_fresh_token_is_not_reuse() -> None:
    from vornia.services.token import detect_reuse

    assert detect_reuse({"revoked_at": None, "replaced_by_id": None}) is False
