"""Sincronização de batidas Control iD com idempotência e rastreio de órfãos."""

import re
from datetime import UTC, datetime
from typing import Any

from vornia.middleware.rls import rls_connection

ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[-+]\d{4}|Z)?")


def parse_afd_line(line: str) -> dict[str, Any] | None:
    """Extrai timestamp, código do usuário e tipo de uma linha AFD real."""
    match = ISO_RE.search(line)
    if match is None:
        return None
    timestamp = match.group(0)
    suffix = line[match.end() :].strip()
    if re.match(r"^[IA]\d{10,12}", suffix):
        return None  # eventos de inclusão/alteração não são batidas
    punch = re.match(r"^0*(\d{10,12})(?:[0-9a-fA-F]{2,})?$", suffix)
    if punch is None:
        return None
    raw_code = punch.group(1).lstrip("0")
    code = int(raw_code[:11]) if raw_code else None
    record_type = int(suffix[:5]) if len(suffix) >= 5 and suffix[:5].isdigit() else None
    return {
        "punched_at": timestamp,
        "control_code": code,
        "record_type": record_type,
        "raw_data": line,
        "external_id": suffix[-11:] if len(suffix) >= 11 else line,
    }


def _parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+0000"
    if len(value) >= 5 and value[-5] in {"+", "-"} and value[-3] == ":":
        value = value[:-3] + value[-2:]
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").astimezone(UTC)


async def fetch_punches(*, company_id: str, since: datetime | None = None) -> list[str]:
    """Busca no Control iD. Substituído por mock nos testes."""
    import os

    from vornia.integrations.controlid import ControlIDClient, ControlIDConfig

    config = ControlIDConfig(
        base_url=os.environ["CONTROLID_BASE_URL"],
        username=os.environ["CONTROLID_USER"],
        password=os.environ["CONTROLID_PASSWORD"],
    )
    client = ControlIDClient(config)
    try:
        return await client.get_records(since=since)
    finally:
        await client.aclose()


async def get_sync_state(*, company_id: str) -> dict[str, Any] | None:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        row = await conn.fetchrow(
            """
            SELECT resource, last_cursor, last_sync_at, status, error_message
            FROM sync_state WHERE company_id = $1 AND resource = 'punches'
            """,
            company_id,
        )
    return dict(row) if row else None


async def _upsert_state(*, company_id: str, status: str, error: str | None = None) -> None:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        await conn.execute(
            """
            INSERT INTO sync_state (company_id, resource, last_sync_at, status, error_message)
            VALUES ($1, 'punches', now(), $2, $3)
            ON CONFLICT (company_id, resource)
            DO UPDATE SET last_sync_at = now(), status = EXCLUDED.status,
                          error_message = EXCLUDED.error_message, updated_at = now()
            """,
            company_id,
            status,
            error,
        )


async def sync_company(*, company_id: str, full: bool = False) -> dict[str, int]:
    """Importa batidas, mapeando códigos conhecidos e sinalizando órfãos."""
    counters = {"inserted": 0, "skipped": 0, "unmapped": 0, "failed": 0}
    lines: list[str] = []
    try:
        lines = await fetch_punches(company_id=company_id)
        async with rls_connection(claims={"company_id": company_id}) as conn:
            employees = {
                int(row["control_id"]): str(row["id"])
                for row in await conn.fetch(
                    "SELECT id, control_id FROM employees WHERE company_id = $1 AND control_id IS NOT NULL",
                    company_id,
                )
            }
            for line in lines:
                parsed = parse_afd_line(line)
                if parsed is None:
                    counters["skipped"] += 1
                    continue
                employee_id = employees.get(parsed["control_code"])
                if employee_id is None:
                    counters["unmapped"] += 1
                result = await conn.execute(
                    """
                    INSERT INTO raw_punches
                        (company_id, employee_id, external_id, punched_at, record_type, raw_data, mapping_status, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, 'controlid')
                    ON CONFLICT DO NOTHING
                    """,
                    company_id,
                    employee_id,
                    parsed["external_id"],
                    _parse_timestamp(parsed["punched_at"]),
                    parsed["record_type"],
                    parsed["raw_data"],
                    "unmapped" if employee_id is None else "ok",
                )
                if result.endswith("1"):
                    counters["inserted"] += 1
                else:
                    counters["skipped"] += 1
    except Exception as exc:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).exception("Falha ao sincronizar Control iD: %s", exc)
        counters["failed"] = 1
        counters["inserted"] = 0
    await _upsert_state(
        company_id=company_id,
        status="error" if counters["failed"] else "success",
        error=None if not counters["failed"] else "falha na sincronização",
    )
    return counters
