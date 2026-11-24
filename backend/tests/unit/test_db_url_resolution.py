"""Tests for the integration database URL resolution."""

import pytest

from tests.integration.conftest import DEFAULT_TEST_DATABASE_URL, resolve_database_url

pytestmark = pytest.mark.unit


def test_prefers_test_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql://test@host:5000/test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://app@host:5000/app")

    assert resolve_database_url() == "postgresql://test@host:5000/test"


def test_falls_back_to_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://app@host:5000/app")

    assert resolve_database_url() == "postgresql://app@host:5000/app"


def test_falls_back_to_local_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert resolve_database_url() == DEFAULT_TEST_DATABASE_URL
