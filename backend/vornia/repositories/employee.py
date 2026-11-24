"""Employee repository."""

from typing import Any

import asyncpg

from vornia.schemas.employee import EmployeeCreate, EmployeeUpdate


async def create_employee(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    data: EmployeeCreate,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        INSERT INTO employees (
            company_id, control_id, name, registration, pis, cpf, job_title,
            department, work_schedule, photo_url, is_active, hired_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id, name, cpf, pis, job_title, department, is_active, hired_at, created_at, updated_at
        """,
        company_id,
        data.control_id,
        data.name,
        data.registration,
        data.pis,
        data.cpf,
        data.job_title,
        data.department,
        data.work_schedule,
        data.photo_url,
        data.is_active,
        data.hired_at,
    )
    return dict(row) if row else None


async def update_employee(
    conn: asyncpg.Connection,
    *,
    employee_id: str,
    data: EmployeeUpdate,
) -> dict[str, Any] | None:
    fields = [
        (column, value)
        for column, value in (
            ("control_id", data.control_id),
            ("name", data.name),
            ("registration", data.registration),
            ("pis", data.pis),
            ("cpf", data.cpf),
            ("job_title", data.job_title),
            ("department", data.department),
            ("work_schedule", data.work_schedule),
            ("photo_url", data.photo_url),
            ("is_active", data.is_active),
            ("hired_at", data.hired_at),
        )
        if value is not None
    ]
    if not fields:
        return await get_employee(conn, employee_id)

    clauses = ", ".join(f"{column} = ${index}" for index, (column, _) in enumerate(fields, start=1))
    values = [value for _, value in fields] + [employee_id]
    # colunas vêm de whitelist fixa; valores são placeholders $n
    query = "UPDATE employees SET {clauses} WHERE id = ${placeholder} RETURNING id, name, cpf, pis, job_title, department, is_active, hired_at, created_at, updated_at".format(  # nosec B608  # noqa: UP032
        clauses=clauses, placeholder=len(values)
    )
    row = await conn.fetchrow(query, *values)
    return dict(row) if row else None


async def get_employee(conn: asyncpg.Connection, employee_id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        SELECT id, name, cpf, pis, job_title, department, is_active, hired_at, created_at, updated_at
        FROM employees
        WHERE id = $1
        """,
        employee_id,
    )
    return dict(row) if row else None


async def deactivate_employee(
    conn: asyncpg.Connection,
    *,
    employee_id: str,
) -> bool:
    row = await conn.fetchrow(
        "UPDATE employees SET is_active = false WHERE id = $1 RETURNING id",
        employee_id,
    )
    return row is not None


async def list_employees(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    page: int = 1,
    per_page: int = 20,
    active: bool | None = None,
    search: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    where = ["company_id = $1"]
    params: list[Any] = [company_id]
    if active is not None:
        params.append(active)
        where.append(f"is_active = ${len(params)}")
    if search:
        params.append(f"%{search}%")
        params.append(f"%{search}%")
        where.append(f"(name ILIKE ${len(params) - 1} OR registration ILIKE ${len(params)})")

    where_sql = " AND ".join(where)
    total = await conn.fetchval(
        f"SELECT count(*) FROM employees WHERE {where_sql}",  # nosec B608
        *params,
    )

    # filtros vêm de whitelist fixa; valores são placeholders $n
    query = "SELECT id, name, cpf, pis, job_title, department, is_active, hired_at, created_at, updated_at FROM employees WHERE {where_sql} ORDER BY created_at DESC LIMIT ${limit} OFFSET ${offset}".format(  # nosec B608  # noqa: UP032
        where_sql=where_sql, limit=len(params) + 2, offset=len(params) + 1
    )
    rows = await conn.fetch(query, *params, per_page, (page - 1) * per_page)
    return [dict(row) for row in rows], int(total or 0)
