"""Matriz TDD da calculadora CLT (alíquotas extraídas do PontoJa/payroll_calculator.py)."""

from datetime import date, time

import pytest

from vornia.services.banco_horas import (
    calcular_adicionais,
    calcular_noturno_minutos,
    calcular_saldo_mensal,
)

pytestmark = pytest.mark.unit

DEFAULT = {
    "hora_extra_pct": 50.0,
    "adicional_noturno_pct": 20.0,
    "hora_extra_noturna_pct": 70.0,
}


def test_hora_extra_50_pct() -> None:
    r = calcular_adicionais(horas_extras=2.0, valor_hora=10.0, config=DEFAULT)
    assert r["valor_extras"] == pytest.approx(30.0)


def test_adicional_noturno_20_pct() -> None:
    r = calcular_adicionais(horas_noturnas=1.0, valor_hora=10.0, config=DEFAULT)
    assert r["valor_noturno"] == pytest.approx(2.0)


def test_hora_extra_noturna_70_pct() -> None:
    r = calcular_adicionais(horas_extras=1.0, horas_noturnas=1.0, valor_hora=10.0, config=DEFAULT)
    # No legado, `valor_extra_noturna` é o ADICIONAL sobre a extra (1,70 − 1,50 = 0,20).
    assert r["valor_extra_noturna"] == pytest.approx(2.0)


def test_feriado_dobra_100_pct() -> None:
    r = calcular_adicionais(
        horas_extras=2.0,
        valor_hora=10.0,
        tipo_dia="feriado",
        horas_trabalhadas=8.0,
        config=DEFAULT,
    )
    assert r["valor_extras"] == pytest.approx(60.0)


def test_feriado_mesma_base_extras_e_saldo() -> None:
    """Defeito #8: não pode haver bases distintas."""
    r = calcular_adicionais(
        horas_extras=0.0,
        horas_trabalhadas=4.0,
        tipo_dia="feriado",
        jornada_esperada=4.0,
        valor_hora=10.0,
        config=DEFAULT,
    )
    assert r["saldo_dia"] == pytest.approx(0.0)
    assert r["valor_extras"] == pytest.approx(0.0)


def test_sabado_excesso_descontado_antes_payroll() -> None:
    """Defeito #9: excesso de sábado não pode gerar pagamento duplo."""
    r = calcular_adicionais(
        horas_trabalhadas=10.0,
        tipo_dia="sabado",
        jornada_esperada=8.0,
        valor_hora=10.0,
        config=DEFAULT,
    )
    assert r["excesso_sabado"] == pytest.approx(2.0)
    assert r["valor_extras"] == pytest.approx(0.0)


def test_noturno_por_minutos_reais() -> None:
    """Defeito #10: 22:30→05:30 = 7h exatas, não 6,5h."""
    minutes = calcular_noturno_minutos(time(22, 30), time(5, 30))
    assert minutes == 420


def test_dia_sem_batida_debita_jornada() -> None:
    r = calcular_adicionais(
        horas_trabalhadas=0.0,
        jornada_esperada=8.0,
        status="absence",
        valor_hora=10.0,
        config=DEFAULT,
    )
    assert r["saldo_dia"] == pytest.approx(-8.0)
    assert r["owed_hours"] == pytest.approx(8.0)


def test_saldo_negativo_10h() -> None:
    result = calcular_saldo_mensal(
        jornadas=[
            {
                "date": date(2026, 11, 25),
                "worked_hours": 0.0,
                "expected_hours": 8.0,
                "status": "absence",
            },
        ],
        dias_uteis=1,
        valor_hora=10.0,
        config=DEFAULT,
    )
    assert result["closing_balance"] == pytest.approx(-8.0)
    assert result["owed_hours"] == pytest.approx(8.0)


def test_recalculo_idempotente() -> None:
    first = calcular_saldo_mensal([], dias_uteis=0, valor_hora=10.0, config=DEFAULT)
    second = calcular_saldo_mensal([], dias_uteis=0, valor_hora=10.0, config=DEFAULT)
    assert first == second
