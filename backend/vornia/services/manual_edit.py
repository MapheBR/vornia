"""Edição manual com cascata atômica.

Ordem dentro de UMA transação: UPDATE raw_punch → recalcula processed_journey
→ recalcula time_balances → INSERT audit_logs. Qualquer falha faz rollback total.
"""

from datetime import UTC, datetime
from typing import Any

from vornia.middleware.rls import rls_connection


async def recalculate_for_punch(
    conn: Any, *, company_id: str, employee_id: str, punched_at: datetime
) -> dict[str, Any]:
    """Recalcula a jornada do dia e o saldo do mês usando a mesma conexão."""
    from vornia.services.balance_service import recalculate_month
    from vornia.services.journey_processing import process_company

    day = punched_at.astimezone(UTC).date()
    await process_company(company_id=company_id, conn=conn)
    await recalculate_month(
        company_id=company_id,
        month=f"{day.year:04d}-{day.month:02d}",
        conn=conn,
    )
    return {"employee_id": employee_id, "date": str(day)}


async def edit_punch(
    *,
    company_id: str,
    punch_id: str,
    punched_at: str,
    reason: str,
    changed_by: str,
) -> dict[str, Any]:
    """Edita uma batida e propaga o recálculo — tudo na mesma transação."""
    if len(reason.strip()) < 5:
        raise ValueError("reason deve ter pelo menos 5 caracteres")

    new_value = datetime.fromisoformat(punched_at.replace("Z", "+00:00"))
    async with rls_connection(claims={"company_id": company_id}) as conn:
        before = await conn.fetchrow(
            "SELECT employee_id, punched_at FROM raw_punches WHERE id = $1",
            punch_id,
        )
        if before is None:
            raise LookupError("Batida não encontrada")

        await conn.execute(
            "UPDATE raw_punches SET punched_at = $2 WHERE id = $1",
            punch_id,
            new_value,
        )
        result = await recalculate_for_punch(
            conn,
            company_id=company_id,
            employee_id=str(before["employee_id"]),
            punched_at=new_value,
        )
        await conn.execute(
            """
            INSERT INTO audit_logs
                (company_id, entity_type, entity_id, action, changed_by, reason, before_data, after_data)
            VALUES ($1,'raw_punch',$2,'update',$3,$4,$5::jsonb,$6::jsonb)
            """,
            company_id,
            punch_id,
            changed_by,
            reason,
            __import__("json").dumps({"punched_at": str(before["punched_at"])}),
            __import__("json").dumps({"punched_at": str(new_value)}),
        )
    return {"recalculated": True, **result}
