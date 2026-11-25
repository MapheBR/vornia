"""Exportações de jornadas: XLSX (openpyxl) e PDF (fpdf2).

Ambas são bibliotecas puras em Python — wheels leves e compatíveis com ARM
da Oracle Cloud (sem ReportLab/WeasyPrint).
"""

from io import BytesIO
from typing import Any

from fpdf import FPDF
from openpyxl import Workbook

XLSX_ROW_LIMIT = 10_000
PDF_ROW_LIMIT = 500

HEADERS = ("Colaborador", "Data", "Entrada", "Saída", "Horas", "Situação")


def safe_cell(value: Any) -> str:
    """Neutraliza CSV/formula injection (inclusive tabs/CR antes do '=')."""
    text = str(value).strip()
    text = "".join(c for c in text if c >= " " or c in "\t")
    import unicodedata

    text = unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t") else text


def _rows(journeys: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [
        (
            safe_cell(j.get("employee", "")),
            safe_cell(j.get("date", "")),
            safe_cell(j.get("entry") or ""),
            safe_cell(j.get("exit") or ""),
            safe_cell(j.get("worked_hours", "")),
            safe_cell(j.get("status", "")),
        )
        for j in journeys
    ]


def build_xlsx(journeys: list[dict[str, Any]]) -> bytes:
    if len(journeys) > XLSX_ROW_LIMIT:
        raise ValueError(f"Limite de {XLSX_ROW_LIMIT} linhas excedido")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Jornadas"
    sheet.append(HEADERS)
    for row in _rows(journeys):
        sheet.append(row)
        for cell in sheet[sheet.max_row]:
            cell.data_type = "s"
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_pdf(journeys: list[dict[str, Any]]) -> bytes:
    if len(journeys) > PDF_ROW_LIMIT:
        raise ValueError(f"Limite de {PDF_ROW_LIMIT} linhas excedido")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Vornia - Relatorio de Jornadas", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    for row in _rows(journeys):
        pdf.cell(0, 7, " | ".join(row), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
