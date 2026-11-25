"""Processador de jornadas — regras corrigidas do legado PontoJa."""

from datetime import UTC, date, datetime
from typing import Any

from vornia.services.controlid_sync import parse_afd_line

DEFAULT_EXPECTED_HOURS = 8.0


def parse_afd_timestamp(value: str) -> datetime:
    """Converte `YYYY-MM-DDTHH:MM:SS±HHMM` ou `Z` mantendo o offset real."""
    if value.endswith("Z"):
        value = value[:-1] + "+0000"
    if len(value) >= 5 and value[-5] in {"+", "-"} and value[-3] == ":":
        value = value[:-3] + value[-2:]
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


def punches_to_times(punches: list[dict[str, Any]]) -> list[datetime]:
    """Ordena batidas por horário real (UTC), sem descartar nenhuma."""
    parsed = []
    for punch in punches:
        raw = punch.get("raw_data") or punch.get("punched_at", "")
        match = parse_afd_line(str(raw))
        if match is None:
            continue
        # Mesmo fuso do dispositivo: ordenar e exibir em hora local.
        parsed.append(parse_afd_timestamp(match["punched_at"]))
    return sorted(parsed)


def _as_time(value: datetime) -> str:
    return value.strftime("%H:%M:%S")


def process_day(
    punches: list[dict[str, Any]],
    *,
    day: date | None = None,
    expected_hours: float = DEFAULT_EXPECTED_HOURS,
    is_holiday: bool = False,
    tolerance_minutes: int = 5,
) -> dict[str, Any] | None:
    """Processa as batidas de um dia. Nunca inventa horários ausentes."""
    del tolerance_minutes  # reservado para tolerância configurável por tenant
    times = punches_to_times(punches)
    if day is not None and day > datetime.now(UTC).date():
        return None
    if is_holiday and not times:
        return None

    count = len(times)
    result: dict[str, Any] = {
        "entry": None,
        "lunch_exit": None,
        "lunch_return": None,
        "exit": None,
        "worked_hours": 0.0,
        "expected_hours": expected_hours,
        "overtime_hours": 0.0,
        "night_hours": 0.0,
        "status": "complete",
        "notes": None,
        "source_punch_ids": [str(p.get("id", index)) for index, p in enumerate(punches)],
    }

    if times:
        result["entry"] = _as_time(times[0])

    if count == 1:
        result["status"] = "pending"
        result["notes"] = "1 batida: jornada pendente"
    elif count == 2:
        result["exit"] = _as_time(times[1])
        result["worked_hours"] = round((times[1] - times[0]).total_seconds() / 3600, 2)
    elif count == 3:
        result["lunch_exit"] = _as_time(times[1])
        result["exit"] = _as_time(times[2])
        result["worked_hours"] = round((times[2] - times[0]).total_seconds() / 3600, 2)
        result["status"] = "pending"
        result["notes"] = "3 batidas: volta do almoço não informada"
    elif count == 4:
        result["lunch_exit"] = _as_time(times[1])
        result["lunch_return"] = _as_time(times[2])
        result["exit"] = _as_time(times[3])
        worked = (times[1] - times[0]).total_seconds() + (times[3] - times[2]).total_seconds()
        result["worked_hours"] = round(worked / 3600, 2)
    elif count > 4:
        result["status"] = "inconsistency"
        result["notes"] = f"{count} batidas: pares excedentes exigem revisão"
        result["exit"] = _as_time(times[-1])

    result["overtime_hours"] = round(
        max(0.0, float(result["worked_hours"]) - float(expected_hours)), 2
    )
    return result
