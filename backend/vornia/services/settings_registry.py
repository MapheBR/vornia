"""Registry de chaves de configuração por empresa (allowlist)."""

from typing import Any

from pydantic import BaseModel


class TimezoneSetting(BaseModel):
    value: str


class IntegerSetting(BaseModel):
    value: int


class BoolSetting(BaseModel):
    value: bool


SETTINGS_REGISTRY: dict[str, type[BaseModel]] = {
    "timezone": TimezoneSetting,
    "workday_minutes": IntegerSetting,
    "tolerance_minutes": IntegerSetting,
    "lunch_minutes": IntegerSetting,
    "overtime_enabled": BoolSetting,
    "week_start": IntegerSetting,
}

DEFAULTS: dict[str, Any] = {
    "timezone": "America/Sao_Paulo",
    "workday_minutes": 480,
    "tolerance_minutes": 5,
    "lunch_minutes": 60,
    "overtime_enabled": False,
    "week_start": 1,
}


def default_for(key: str) -> Any:
    """Retorna o valor padrão de uma chave conhecida."""
    if key not in SETTINGS_REGISTRY:
        raise ValueError(f"Chave desconhecida: {key}")
    return DEFAULTS[key]


def validate_setting(key: str, payload: dict[str, Any]) -> Any:
    """Valida uma chave e seu valor contra o schema do registry."""
    if key not in SETTINGS_REGISTRY:
        raise ValueError(f"Chave desconhecida: {key}")
    model = SETTINGS_REGISTRY[key].model_validate({"value": payload.get("value", DEFAULTS[key])})
    return model.value
