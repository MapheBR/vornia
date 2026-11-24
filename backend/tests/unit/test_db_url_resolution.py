"""Tests for the integration database URL resolution."""

import pytest

from tests.integration.conftest import (
    DEFAULT_TEST_DATABASE_URL,
    DEFAULT_TEST_DATABASE_URL_APP,
    DEFAULT_TEST_DATABASE_URL_BOOTSTRAP,
    resolve_app_database_url,
    resolve_bootstrap_database_url,
    resolve_database_url,
)

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


def test_app_url_prefers_test_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_DATABASE_URL_APP", "postgresql://app@host:5000/app")
    monkeypatch.setenv("DATABASE_URL_APP", "postgresql://other@host:5000/app")

    assert resolve_app_database_url() == "postgresql://app@host:5000/app"


def test_app_url_falls_back_to_local_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL_APP", raising=False)
    monkeypatch.delenv("DATABASE_URL_APP", raising=False)

    assert resolve_app_database_url() == DEFAULT_TEST_DATABASE_URL_APP


def test_bootstrap_url_uses_database_url_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL_BOOTSTRAP", raising=False)
    monkeypatch.setenv("DATABASE_URL_BOOTSTRAP", "postgresql://auth@host:5000/app")

    assert resolve_bootstrap_database_url() == "postgresql://auth@host:5000/app"


def test_bootstrap_url_falls_back_to_local_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL_BOOTSTRAP", raising=False)
    monkeypatch.delenv("DATABASE_URL_BOOTSTRAP", raising=False)

    assert resolve_bootstrap_database_url() == DEFAULT_TEST_DATABASE_URL_BOOTSTRAP
