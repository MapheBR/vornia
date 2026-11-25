"""Serviço de banco de horas: recálculo mensal com saldo por colaborador."""

from typing import Any

from vornia.middleware.rls import rls_connection
from vornia.services.banco_horas import calcular_saldo_mensal


async def recalculate_month(
    *, company_id: str, month: str, conn: Any | None = None
) -> dict[str, int]:
    """Recalcula `time_balances` para todas as jornadas do mês (upsert)."""
    from datetime import date

    year, number = (int(part) for part in month.split("-")[:2])
    first_day = date(year, number, 1)
    next_month = date(year + (number == 12), (number % 12) + 1, 1)
    last_day = date.fromordinal(next_month.toordinal() - 1)

    if conn is not None:
        journeys = await conn.fetch(
            """
            SELECT employee_id, date, worked_hours, expected_hours, status
            FROM processed_journeys
            WHERE company_id = $1 AND date BETWEEN $2 AND $3
            ORDER BY employee_id, date
            """,
            company_id,
            first_day,
            last_day,
        )
        by_employee: dict[str, list[dict[str, Any]]] = {}
        for row in journeys:
            by_employee.setdefault(str(row["employee_id"]), []).append(dict(row))

        for employee_id, items in by_employee.items():
            result = calcular_saldo_mensal(
                items,
                dias_uteis=len(items),
                valor_hora=10.0,
            )
            await conn.execute(
                """
                INSERT INTO time_balances (
                    company_id, employee_id, reference_month, earned_hours,
                    overtime_50_hours, owed_hours, closing_balance, calculated_at
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7, now())
                ON CONFLICT (company_id, employee_id, reference_month)
                DO UPDATE SET
                    earned_hours = EXCLUDED.earned_hours,
                    overtime_50_hours = EXCLUDED.overtime_50_hours,
                    owed_hours = EXCLUDED.owed_hours,
                    closing_balance = EXCLUDED.closing_balance,
                    calculated_at = now(), updated_at = now()
                """,
                company_id,
                employee_id,
                first_day,
                result["earned_hours"],
                result["overtime_50_hours"],
                result["owed_hours"],
                result["closing_balance"],
            )
        return {"recalculated": len(by_employee)}
    else:
        async with rls_connection(claims={"company_id": company_id}) as conn:
            return await recalculate_month(company_id=company_id, month=month, conn=conn)


async def list_balances(*, company_id: str) -> list[dict[str, Any]]:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        rows = await conn.fetch(
            "SELECT employee_id, reference_month, closing_balance FROM time_balances WHERE company_id = $1",
            company_id,
        )
    return [dict(row) for row in rows]
