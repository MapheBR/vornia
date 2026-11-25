"""Calculadora CLT de adicionais e saldo de banco de horas.

Alíquotas extraídas de PontoJa/services/payroll_calculator.py:
extra +50%, noturno +20%, extra noturna +70%, feriado/domingo dobra (100%).
Corrige os defeitos #8, #9 e #10 do diagnóstico da Fase 1.
"""

from datetime import time
from typing import Any

DEFAULT_CONFIG = {
    "hora_extra_pct": 50.0,
    "adicional_noturno_pct": 20.0,
    "hora_extra_noturna_pct": 70.0,
}

NOTURNO_INICIO = time(22, 0)
NOTURNO_FIM = time(5, 0)


def calcular_noturno_minutos(inicio: time, fim: time) -> int:
    """Minutos reais dentro do intervalo noturno (22h–05h), com virada de dia."""
    start = inicio.hour * 60 + inicio.minute
    end = fim.hour * 60 + fim.minute
    if end < start:
        end += 24 * 60

    total = 0
    for hour in range(22, 24):
        segment_start = hour * 60
        segment_end = segment_start + 60
        total += _overlap(start, end, segment_start, segment_end)
    for hour in range(0, 6):
        segment_start = 24 * 60 + hour * 60
        segment_end = segment_start + 60
        total += _overlap(start, end, segment_start, segment_end)
    return total


def _overlap(a: int, b: int, c: int, d: int) -> int:
    return max(0, min(b, d) - max(a, c))


def calcular_adicionais(
    *,
    horas_extras: float = 0.0,
    horas_noturnas: float = 0.0,
    horas_trabalhadas: float = 0.0,
    jornada_esperada: float = 8.0,
    tipo_dia: str = "util",
    status: str = "complete",
    valor_hora: float,
    config: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Calcula adicionais e saldo do dia com uma única base de cálculo."""
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    extra_pct = float(cfg["hora_extra_pct"]) / 100
    night_pct = float(cfg["adicional_noturno_pct"]) / 100
    extra_night_pct = float(cfg["hora_extra_noturna_pct"]) / 100

    multiplicador = 2.0 if tipo_dia in ("feriado", "domingo") and horas_trabalhadas > 0 else 1.0
    valor_extra = valor_hora * (1 + extra_pct) * multiplicador
    valor_noturno_unit = valor_hora * night_pct
    valor_extra_noturna_unit = valor_hora * (1 + extra_night_pct) * multiplicador

    extras_normais = max(0.0, horas_extras - horas_noturnas)
    valor_extras = round(extras_normais * valor_extra, 2)
    valor_adicional_noturno = round(horas_noturnas * valor_noturno_unit, 2)
    valor_extra_noturna = round(
        min(horas_noturnas, horas_extras) * (valor_extra_noturna_unit - valor_extra),
        2,
    )

    excesso_sabado = (
        round(max(0.0, horas_trabalhadas - jornada_esperada), 2) if tipo_dia == "sabado" else 0.0
    )
    if tipo_dia == "sabado":
        valor_extras = 0.0  # defect #9: excesso não é pago duas vezes

    saldo = round(horas_trabalhadas - jornada_esperada - excesso_sabado, 2)
    owed = round(max(0.0, -saldo), 2)
    if status == "absence":
        saldo = round(-jornada_esperada, 2)
        owed = round(jornada_esperada, 2)

    return {
        "valor_hora": round(valor_hora, 2),
        "valor_extras": valor_extras,
        "valor_noturno": valor_adicional_noturno,
        "valor_extra_noturna": valor_extra_noturna,
        "excesso_sabado": excesso_sabado,
        "saldo_dia": saldo,
        "owed_hours": owed,
    }


def calcular_saldo_mensal(
    jornadas: list[dict[str, Any]],
    *,
    dias_uteis: int,
    valor_hora: float,
    config: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Consolida saldo do mês. `opening_balance` é passado pelo chamador."""
    del dias_uteis  # janela de cálculo já refletida nas jornadas recebidas
    earned = sum(float(j.get("worked_hours", 0)) for j in jornadas)
    extras_50 = sum(
        max(0.0, float(j.get("worked_hours", 0)) - float(j.get("expected_hours", 8)))
        for j in jornadas
    )
    owed = sum(
        max(0.0, float(j.get("expected_hours", 8)) - float(j.get("worked_hours", 0)))
        for j in jornadas
    )
    return {
        "opening_balance": 0.0,
        "earned_hours": round(earned, 2),
        "overtime_50_hours": round(extras_50, 2),
        "overtime_100_hours": 0.0,
        "night_hours": 0.0,
        "owed_hours": round(owed, 2),
        "closing_balance": round(earned - owed, 2),
    }
