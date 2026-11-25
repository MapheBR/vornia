"""Processamento e persistência determinística de jornadas por tenant."""

from collections import defaultdict
from datetime import date
from typing import Any

from vornia.middleware.rls import rls_connection
from vornia.services.journey import parse_afd_timestamp, process_day


async def process_company(*, company_id: str, conn: Any | None = None) -> dict[str, int]:
    """Processa batidas não processadas e faz upsert por (tenant, employee, date)."""
    counters = {"processed": 0, "skipped": 0}
    if conn is not None:
        rows = await conn.fetch(
            """
            SELECT id, employee_id, punched_at, raw_data, processed
            FROM raw_punches
            WHERE company_id = $1 AND employee_id IS NOT NULL
            ORDER BY punched_at
            """,
            company_id,
        )
        by_day: dict[tuple[str, date], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            punched = row["punched_at"]
            raw_value = punched.isoformat() if hasattr(punched, "isoformat") else str(punched)
            dt = parse_afd_timestamp(raw_value if "T" in raw_value else row["raw_data"][:25])
            by_day[(str(row["employee_id"]), dt.date())].append(dict(row))

        for (employee_id, day), punches in by_day.items():
            processed = process_day(punches, day=day)
            if processed is None:
                counters["skipped"] += 1
                continue
            await conn.execute(
                """
                INSERT INTO processed_journeys (
                    company_id, employee_id, date, entry, lunch_exit, lunch_return, exit,
                    worked_hours, expected_hours, overtime_hours, night_hours, status, notes
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                ON CONFLICT (company_id, employee_id, date)
                DO UPDATE SET
                    entry = EXCLUDED.entry, lunch_exit = EXCLUDED.lunch_exit,
                    lunch_return = EXCLUDED.lunch_return, exit = EXCLUDED.exit,
                    worked_hours = EXCLUDED.worked_hours,
                    overtime_hours = EXCLUDED.overtime_hours,
                    status = EXCLUDED.status, notes = EXCLUDED.notes, updated_at = now()
                """,
                company_id,
                employee_id,
                day,
                processed["entry"],
                processed["lunch_exit"],
                processed["lunch_return"],
                processed["exit"],
                processed["worked_hours"],
                processed["expected_hours"],
                processed["overtime_hours"],
                processed["night_hours"],
                processed["status"],
                processed["notes"],
            )
            await conn.execute(
                "UPDATE raw_punches SET processed = true WHERE company_id = $1 AND employee_id = $2",
                company_id,
                employee_id,
            )
            counters["processed"] += 1
    else:
        async with rls_connection(claims={"company_id": company_id}) as conn:
            return await process_company(company_id=company_id, conn=conn)

    return counters
