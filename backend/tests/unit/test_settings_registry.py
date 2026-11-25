"""Testes unitários do registro de settings (allowlist com Pydantic)."""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_known_keys_are_accepted() -> None:
    from vornia.services.settings_registry import DEFAULTS, SETTINGS_REGISTRY, validate_setting

    for key in SETTINGS_REGISTRY:
        result = validate_setting(key, {})
        assert result == DEFAULTS[key]


def test_unknown_key_is_rejected() -> None:
    from vornia.services.settings_registry import validate_setting

    with pytest.raises(ValueError, match="Chave desconhecida"):
        validate_setting("unknown_key", {})


def test_timezone_has_default() -> None:
    from vornia.services.settings_registry import default_for

    assert default_for("timezone") == "America/Sao_Paulo"


def test_invalid_value_type_is_rejected() -> None:
    from vornia.services.settings_registry import validate_setting

    with pytest.raises(ValidationError):
        validate_setting("timezone", {"value": 123})


def test_all_keys_have_defaults() -> None:
    from vornia.services.settings_registry import SETTINGS_REGISTRY, default_for

    for key in SETTINGS_REGISTRY:
        assert default_for(key) is not None
