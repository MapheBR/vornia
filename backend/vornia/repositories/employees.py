"""Employee repository (asyncpg, parameterized queries only)."""

from typing import Any

import asyncpg

COLUMNS = (
    "id",
    "company_id",
    "name",
    "control_id",
    "registration",
    "pis",
    "cpf",
    "job_title",
    "department",
    "work_schedule",
    "photo_url",
    "is_active",
    "hired_at",
    "created_at",
    "updated_at",
)

UPDATABLE_COLUMNS = (
    "name",
    "control_id",
    "registration",
    "pis",
    "cpf",
    "job_title",
    "department",
    "work_schedule",
    "photo_url",
    "is_active",
    "hired_at",
)

_SELECT_COLUMNS = ", ".join(COLUMNS)
# SQL estatico montado apenas com constantes deste modulo; valores do usuario
# sempre entram como parametros ligados ($1, $2, ...).
LIST_SQL = f"SELECT {_SELECT_COLUMNS} FROM employees WHERE is_active = true ORDER BY name"  # nosec B608
GET_SQL = f"SELECT {_SELECT_COLUMNS} FROM employees WHERE id = $1 AND is_active = true"  # nosec B608
RETURNING_SQL = f"RETURNING {_SELECT_COLUMNS}"


async def create(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    columns = ["company_id", *data.keys()]
    placeholders = [f"${index}" for index in range(1, len(columns) + 1)]
    values = [company_id, *data.values()]
    statement = (
        "INSERT INTO employees ("  # nosec B608
        + ", ".join(columns)
        + ") VALUES ("
        + ", ".join(placeholders)
        + ") "
        + RETURNING_SQL
    )
    row = await conn.fetchrow(statement, *values)
    return dict(row) if row else {}


async def list_all(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(LIST_SQL)
    return [dict(row) for row in rows]


async def get_by_id(conn: asyncpg.Connection, employee_id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(GET_SQL, employee_id)
    return dict(row) if row else None


async def update(
    conn: asyncpg.Connection,
    *,
    employee_id: str,
    changes: dict[str, Any],
) -> dict[str, Any] | None:
    if not changes:
        return await get_by_id(conn, employee_id)

    assignments = [f"{column} = ${index}" for index, column in enumerate(changes, start=2)]
    statement = (
        "UPDATE employees SET "  # nosec B608
        + ", ".join(assignments)
        + ", updated_at = now() WHERE id = $1 AND is_active = true "
        + RETURNING_SQL
    )
    row = await conn.fetchrow(statement, employee_id, *changes.values())
    return dict(row) if row else None


async def soft_delete(conn: asyncpg.Connection, employee_id: str) -> bool:
    result = await conn.execute(
        """
        UPDATE employees
        SET is_active = false, updated_at = now()
        WHERE id = $1 AND is_active = true
        """,
        employee_id,
    )
    return bool(result.endswith("1"))
