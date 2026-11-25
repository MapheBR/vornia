"""Testes unitários das exportações (matriz 14–17 do Sprint 5)."""

from datetime import date

import pytest

pytestmark = pytest.mark.unit

JOURNEYS = [
    {
        "id": "e1",
        "employee": "Maria",
        "date": date(2026, 11, 25),
        "entry": "08:00:00",
        "exit": "17:00:00",
        "worked_hours": 9.0,
        "status": "complete",
    },
    {
        "id": "e2",
        "employee": "=cmd|'/c calc'!A1",
        "date": date(2026, 11, 24),
        "entry": "08:00:00",
        "exit": "12:00:00",
        "worked_hours": 4.0,
        "status": "pending",
    },
]


def test_xlsx_has_header_and_rows() -> None:
    from vornia.services.exports import build_xlsx

    data = build_xlsx(JOURNEYS)
    assert data[:2] == b"PK"
    assert len(data) > 100


def test_csv_injection_is_neutralized() -> None:
    from vornia.services.exports import safe_cell

    assert safe_cell("=cmd|'/c calc'!A1").startswith("'")
    assert safe_cell("@SUM(A1)").startswith("'")
    assert safe_cell("Maria") == "Maria"


def test_pdf_respects_row_limit() -> None:
    from vornia.services.exports import PDF_ROW_LIMIT, build_pdf

    assert PDF_ROW_LIMIT == 500
    with pytest.raises(ValueError, match="500"):
        build_pdf([{"employee": "x"}] * (PDF_ROW_LIMIT + 1))


def test_pdf_generates_valid_file() -> None:
    from vornia.services.exports import build_pdf

    data = build_pdf(JOURNEYS)
    assert data.startswith(b"%PDF")
