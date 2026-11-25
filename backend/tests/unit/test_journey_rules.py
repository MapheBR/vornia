"""Matriz TDD do processador de jornadas (regras corrigidas do PontoJa)."""

from datetime import UTC, date

import pytest

from vornia.services.journey import parse_afd_timestamp, process_day, punches_to_times

pytestmark = pytest.mark.unit

TZ = "-0300"


def _punch(day: str, time: str, code: int = 12345678901) -> dict:
    return {
        "punched_at": f"2026-11-{day}T{time}:00{TZ}",
        "control_code": code,
        "raw_data": f"2026-11-{day}T{time}:00{TZ}0{code}A1B2",
    }


def test_two_punches_no_invented_lunch() -> None:
    """Defeito #16: 2 batidas = entrada/saída, sem almoço inventado."""
    result = process_day([_punch("25", "08:00"), _punch("25", "17:00")])
    assert result["entry"] == "08:00:00"
    assert result["lunch_exit"] is None
    assert result["lunch_return"] is None
    assert result["exit"] == "17:00:00"
    assert result["worked_hours"] == 9.0
    assert result["status"] == "complete"


def test_four_punches_full_journey() -> None:
    result = process_day(
        [
            _punch("25", "08:00"),
            _punch("25", "12:00"),
            _punch("25", "13:00"),
            _punch("25", "17:00"),
        ]
    )
    assert result["worked_hours"] == 8.0
    assert result["lunch_exit"] == "12:00:00"
    assert result["lunch_return"] == "13:00:00"
    assert result["status"] == "complete"


def test_six_punches_inconsistency_without_dropping() -> None:
    """Defeito #18: >4 batidas gera inconsistência, não descarta registros."""
    punches = [
        _punch("25", "08:00"),
        _punch("25", "10:00"),
        _punch("25", "12:00"),
        _punch("25", "14:00"),
        _punch("25", "16:00"),
        _punch("25", "18:00"),
    ]
    result = process_day(punches)
    assert result["status"] == "inconsistency"
    assert len(result["source_punch_ids"]) == 6
    assert "6 batidas" in result["notes"]


def test_three_punches_pending_without_invented_return() -> None:
    """Defeito #19: 3 batidas não inventa volta do almoço."""
    result = process_day([_punch("25", "08:00"), _punch("25", "12:00"), _punch("25", "17:00")])
    assert result["lunch_return"] is None
    assert result["status"] == "pending"
    assert "3 batidas" in result["notes"]


def test_first_punch_after_cutoff_is_entry() -> None:
    """Defeito #17: primeira batida do dia nunca é saída de almoço."""
    result = process_day([_punch("25", "11:30"), _punch("25", "17:00")])
    assert result["entry"] == "11:30:00"


def test_holiday_special_journey() -> None:
    """Defeito #8: feriado com jornada especial usa a mesma base de cálculo."""
    result = process_day(
        [
            _punch("26", "08:00"),
            _punch("26", "12:00"),
            _punch("26", "13:00"),
            _punch("26", "17:00"),
        ],
        expected_hours=4.0,
        is_holiday=True,
    )
    assert result["expected_hours"] == 4.0
    assert result["worked_hours"] == 8.0
    assert result["overtime_hours"] == 4.0


def test_holiday_without_punches_is_not_absence() -> None:
    result = process_day([], is_holiday=True)
    assert result is None


def test_future_day_is_ignored() -> None:
    """Defeito #23: dias futuros nunca viram falta."""
    tomorrow = date.today().fromordinal(date.today().toordinal() + 1)
    result = process_day([], day=tomorrow)
    assert result is None


def test_timestamp_conversion_uses_timezone() -> None:
    """Defeitos #5/#20: conversão real, nunca replace(tzinfo)."""
    parsed = parse_afd_timestamp("2026-11-25T08:00:00-0300")
    assert parsed.utcoffset().total_seconds() == -3 * 3600
    assert parsed.astimezone(UTC).hour == 11


def test_punches_to_times_sorted() -> None:
    punches = [_punch("25", "17:00"), _punch("25", "08:00")]
    times = punches_to_times(punches)
    assert times[0].hour == 8
    assert times[1].hour == 17
