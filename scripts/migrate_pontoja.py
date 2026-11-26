#!/usr/bin/env python3
"""Migra cadastros e saldos do PontoJa (SQLite) para o Vornia (PostgreSQL).

Regras de segurança (Sprint 7 + branch atual):
- `--apply` EXIGE `--backup-first`: o pg_dump roda via Docker antes de qualquer escrita.
- `--dry-run` não escreve no banco e imprime contagens + divergências.
- Carga em UMA transação (BEGIN/COMMIT) com `ON_ERROR_STOP=1`: se falhar no meio,
  nada é salvo.
- Idempotente por chave natural: rodar `--apply` duas vezes não duplica linhas.
- Nenhum dado real da Tecnova é usado nos testes (fixture sintética).

Uso:
  python scripts/migrate_pontoja.py --sqlite <arquivo.db> --dry-run
  VORNIA_MIGRATION_ADMIN_PASSWORD=<senha-temporaria> \
    python scripts/migrate_pontoja.py --sqlite <arquivo.db> --backup-first --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Contagens registradas no diagnóstico (23/11/2026, leitura read-only).
EXPECTED = {
    "usuarios": 26,
    "feriados": 15,
    "configuracoes": 20,
    "saldos_usuario": 2,
    "admins": 2,
}

TABLE_MAP = {
    "usuarios": "employees",
    "feriados": "holidays",
    "configuracoes": "settings",
    "saldos_usuario": "time_balances",
}

DEFAULT_COMPANY_SLUG = "tecnova"
DEFAULT_COMPANY_NAME = "Tecnova"
DEFAULT_REFERENCE_MONTH = "2026-11-01"
# .local é um TLD reservado e é rejeitado pelo EmailStr do Pydantic no login.
DEFAULT_ADMIN_EMAIL_DOMAIN = "tecnova.com.br"
COMPOSE = ("docker", "compose")


def read_legacy(sqlite_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Lê o legado em modo read-only, sem alterar o arquivo."""
    connection = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        data: dict[str, list[dict[str, Any]]] = {}
        for table in EXPECTED:
            try:
                rows = connection.execute(f"SELECT * FROM {table}").fetchall()
                data[table] = [dict(row) for row in rows]
            except sqlite3.OperationalError:
                data[table] = []
        return data
    finally:
        connection.close()


def normalize_cpf(value: Any) -> str | None:
    digits = "".join(c for c in str(value or "") if c.isdigit())
    return digits or None


def divergences(data: dict[str, list[dict[str, Any]]]) -> list[str]:
    report = []
    for table, expected in EXPECTED.items():
        actual = len(data.get(table, []))
        status = "OK" if actual == expected else "DIVERGÊNCIA"
        report.append(f"{status}: {table}: esperado={expected}, encontrado={actual}")
    orphans = sum(1 for row in data["usuarios"] if not normalize_cpf(row.get("cpf")))
    if orphans:
        report.append(f"DIVERGÊNCIA: {orphans} usuário(s) sem CPF válido")
    return report


def company_id_for(slug: str) -> str:
    """UUID determinístico da empresa, estável entre execuções."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"vornia:company:{slug}"))


def _as_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    return bool(value)


def _json_value(raw: Any) -> str:
    """Converte texto legado em literal JSON para a coluna settings.value."""
    if not isinstance(raw, str):
        return json.dumps(raw)
    try:
        return json.dumps(json.loads(raw))
    except (ValueError, TypeError):
        return json.dumps(raw)


def _password_hash() -> str:
    """Hash bcrypt da senha temporária informada pelo operador (nunca no código)."""
    secret = os.environ.get("VORNIA_MIGRATION_ADMIN_PASSWORD")
    if not secret:
        raise RuntimeError(
            "VORNIA_MIGRATION_ADMIN_PASSWORD é obrigatório para migrar admins "
            "(os hashes scrypt do legado não são compatíveis com o Vornia)."
        )
    from passlib.context import CryptContext

    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(secret)


def transform(
    data: dict[str, list[dict[str, Any]]],
    *,
    company_id: str | None = None,
    company_name: str = DEFAULT_COMPANY_NAME,
    company_slug: str = DEFAULT_COMPANY_SLUG,
    reference_month: str = DEFAULT_REFERENCE_MONTH,
    admin_email_domain: str = DEFAULT_ADMIN_EMAIL_DOMAIN,
    admin_password_hash: str | None = None,
) -> dict[str, Any]:
    """Normaliza o legado para as tabelas de destino (ainda sem escrever)."""
    tenant = company_id or company_id_for(company_slug)
    employees = [
        {
            "control_id": row.get("id"),
            "name": str(row.get("nome", "")).strip(),
            "cpf": normalize_cpf(row.get("cpf")),
            "pis": normalize_cpf(row.get("pis")),
            "registration": str(row.get("matricula", "")).strip() or None,
            "job_title": str(row.get("cargo", "")).strip() or None,
            "department": str(row.get("departamento", "")).strip() or None,
            "is_active": _as_bool(row.get("ativo")),
            "hired_at": str(row.get("data_admissao", "") or "")[:10] or None,
            "photo_url": str(row.get("foto_path", "") or "") or None,
        }
        for row in data["usuarios"]
    ]
    holidays = [
        {
            "date": str(r.get("data", ""))[:10],
            "name": str(r.get("descricao") or r.get("nome") or "").strip(),
        }
        for r in data["feriados"]
    ]
    settings = [
        {"key": str(r.get("chave", ""))[:100], "value": _json_value(r.get("valor"))}
        for r in data["configuracoes"]
    ]
    balances = _balances(data, employees, reference_month)
    users, company_users = _admins(data, tenant, admin_email_domain, admin_password_hash)
    return {
        "companies": [{"id": tenant, "name": company_name, "slug": company_slug}],
        "employees": employees,
        "holidays": holidays,
        "settings": settings,
        "time_balances": balances,
        "users": users,
        "company_users": company_users,
    }


def _balances(
    data: dict[str, list[dict[str, Any]]],
    employees: list[dict[str, Any]],
    reference_month: str,
) -> list[dict[str, Any]]:
    known = {e["control_id"] for e in employees}
    result = []
    for row in data["saldos_usuario"]:
        control_id = row.get("usuario_id")
        if control_id not in known:
            raise RuntimeError(f"usuario_id {control_id} sem employee correspondente")
        result.append(
            {
                "control_id": control_id,
                "reference_month": str(reference_month)[:10],
                "closing_balance": float(row.get("saldo_banco_horas") or 0),
            }
        )
    return result


def _admins(
    data: dict[str, list[dict[str, Any]]],
    tenant: str,
    email_domain: str,
    password_hash: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [r for r in data.get("admins", []) if str(r.get("usuario") or "").strip()]
    if not rows:
        return [], []
    hashed = password_hash or _password_hash()
    users = []
    for row in rows:
        login = str(row["usuario"]).strip().lower().replace(" ", ".")
        users.append(
            {
                "email": f"{login}@{email_domain}",
                "password_hash": hashed,
                "full_name": str(row.get("nome") or row["usuario"]).strip(),
                "is_active": _as_bool(row.get("ativo")),
            }
        )
    links = [{"email": u["email"], "role": "admin"} for u in users]
    return users, links


def _literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _uuid(value: Any) -> str:
    return f"{_literal(value)}::uuid"


def _date(value: Any) -> str:
    return f"{_literal(str(value)[:10])}::date"


def build_sql(transformed: dict[str, Any], *, company_id: str) -> str:
    """Gera um único script SQL transacional e idempotente."""
    claim = json.dumps({"company_id": company_id}, separators=(",", ":"))
    company = transformed["companies"][0]
    lines = [
        "BEGIN;",
        f"SELECT set_config('request.jwt.claims', {_literal(claim)}, true);",
        _company_sql(company),
    ]
    lines.extend(_employees_sql(transformed["employees"], company_id))
    lines.extend(_holidays_sql(transformed["holidays"], company_id))
    lines.extend(_settings_sql(transformed["settings"], company_id))
    lines.extend(_balances_sql(transformed["time_balances"], company_id))
    lines.extend(_users_sql(transformed["users"]))
    lines.extend(_company_users_sql(transformed["company_users"], company_id))
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def _company_sql(company: dict[str, Any]) -> str:
    return (
        f"INSERT INTO companies (id, name, slug) VALUES "
        f"({_uuid(company['id'])}, {_literal(company['name'])}, "
        f"{_literal(company['slug'])}) ON CONFLICT (slug) DO NOTHING;"
    )


def _employees_sql(rows: list[dict[str, Any]], tenant: str) -> list[str]:
    if not rows:
        return []
    values = ",\n".join(
        f"({_uuid(tenant)}, {_literal(r['control_id'])}, {_literal(r['name'])}, "
        f"{_literal(r['registration'])}, {_literal(r['job_title'])}, "
        f"{_literal(r['department'])}, {_literal(r['is_active'])}, "
        f"{_date(r['hired_at']) if r['hired_at'] else 'NULL'}, "
        f"{_literal(r['photo_url'])}, {_literal(r['cpf'])}, {_literal(r['pis'])})"
        for r in rows
    )
    return [
        "INSERT INTO employees (company_id, control_id, name, registration, "
        "job_title, department, is_active, hired_at, photo_url, cpf, pis) VALUES\n"
        f"{values}\nON CONFLICT (company_id, control_id) "
        "WHERE control_id IS NOT NULL DO UPDATE SET "
        "name = EXCLUDED.name, registration = EXCLUDED.registration, "
        "job_title = EXCLUDED.job_title, department = EXCLUDED.department, "
        "is_active = EXCLUDED.is_active, hired_at = EXCLUDED.hired_at, "
        "photo_url = EXCLUDED.photo_url, cpf = EXCLUDED.cpf, pis = EXCLUDED.pis;"
    ]


def _holidays_sql(rows: list[dict[str, Any]], tenant: str) -> list[str]:
    if not rows:
        return []
    values = ",\n".join(
        f"({_uuid(tenant)}, {_date(r['date'])}, {_literal(r['name'])})" for r in rows
    )
    return [
        "INSERT INTO holidays (company_id, date, name) VALUES\n"
        f"{values}\nON CONFLICT (company_id, date) DO UPDATE SET name = EXCLUDED.name;"
    ]


def _settings_sql(rows: list[dict[str, Any]], tenant: str) -> list[str]:
    if not rows:
        return []
    values = ",\n".join(
        f"({_uuid(tenant)}, {_literal(r['key'])}, {_literal(r['value'])}::jsonb)" for r in rows
    )
    return [
        "INSERT INTO settings (company_id, key, value) VALUES\n"
        f"{values}\nON CONFLICT (company_id, key) DO UPDATE SET value = EXCLUDED.value;"
    ]


def _balances_sql(rows: list[dict[str, Any]], tenant: str) -> list[str]:
    return [
        "INSERT INTO time_balances (company_id, employee_id, reference_month, closing_balance)\n"
        f"SELECT {_uuid(tenant)}, e.id, {_date(r['reference_month'])}, "
        f"{_literal(r['closing_balance'])}\n"
        f"FROM employees e WHERE e.company_id = {_uuid(tenant)} "
        f"AND e.control_id = {_literal(r['control_id'])}\n"
        "ON CONFLICT (company_id, employee_id, reference_month) "
        "DO UPDATE SET closing_balance = EXCLUDED.closing_balance;"
        for r in rows
    ]


def _users_sql(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    values = ",\n".join(
        f"({_literal(r['email'])}, {_literal(r['password_hash'])}, "
        f"{_literal(r['full_name'])}, {_literal(r['is_active'])})"
        for r in rows
    )
    return [
        "INSERT INTO users (email, password_hash, full_name, is_active) VALUES\n"
        f"{values}\nON CONFLICT (email) DO NOTHING;"
    ]


def _company_users_sql(rows: list[dict[str, Any]], tenant: str) -> list[str]:
    return [
        "INSERT INTO company_users (company_id, user_id, role)\n"
        f"SELECT {_uuid(tenant)}, u.id, {_literal(r['role'])} FROM users u "
        f"WHERE u.email = {_literal(r['email'])}\n"
        "ON CONFLICT (company_id, user_id) DO UPDATE SET role = EXCLUDED.role;"
        for r in rows
    ]


def run_pg_dump() -> Path:
    """Backup via Docker: não exige pg_dump instalado no host Windows."""
    target = Path(os.environ.get("BACKUP_DIR", "backups"))
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = target / f"pre_migration_{stamp}.sql"
    with path.open("wb") as output:
        result = subprocess.run(
            [*COMPOSE, "exec", "-T", "postgres", "pg_dump", "-U", "vornia", "vornia"],
            stdout=output,
            stderr=subprocess.PIPE,
        )
    if result.returncode != 0:
        stderr = result.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        raise RuntimeError(f"pg_dump falhou: {stderr}")
    return path


def apply_load(sql: str) -> None:
    """Executa o SQL em uma única sessão psql; ON_ERROR_STOP aborta tudo."""
    result = subprocess.run(
        [
            *COMPOSE,
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "vornia",
            "-d",
            "vornia",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        # No Windows o default do subprocess é cp1252; sem UTF-8 explícito,
        # caracteres acentuados do legado geram "invalid byte sequence".
        input=sql.encode("utf-8"),
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        raise RuntimeError(f"psql falhou (transação revertida): {stderr}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-first", action="store_true")
    parser.add_argument("--reference-month", default=DEFAULT_REFERENCE_MONTH)
    parser.add_argument("--company-slug", default=DEFAULT_COMPANY_SLUG)
    parser.add_argument("--company-name", default=DEFAULT_COMPANY_NAME)
    parser.add_argument("--admin-email-domain", default=DEFAULT_ADMIN_EMAIL_DOMAIN)
    args = parser.parse_args()

    if args.apply and args.dry_run:
        parser.error("--apply e --dry-run são mutuamente exclusivos")
    if args.apply and not args.backup_first:
        parser.error("--apply exige --backup-first (pg_dump obrigatório)")

    tenant = company_id_for(args.company_slug)
    legacy = read_legacy(args.sqlite)
    report = divergences(legacy)
    transformed = transform(
        legacy,
        company_id=tenant,
        company_name=args.company_name,
        company_slug=args.company_slug,
        reference_month=args.reference_month,
        admin_email_domain=args.admin_email_domain,
        # Dry-run não precisa de senha: apenas conta linhas, não gera hashes.
        admin_password_hash="dry-run" if args.dry_run else None,
    )

    print("=== RELATÓRIO DE MIGRAÇÃO (dry-run) ===")
    for line in report:
        print(line)
    print("\n=== CONTAGEM POR TABELA DESTINO ===")
    for table, rows in transformed.items():
        print(f"{table}: {len(rows)} linha(s)")

    if args.dry_run:
        print("\nNenhuma escrita realizada (--dry-run).")
        return

    backup = run_pg_dump()
    print(f"\nBackup criado: {backup}")
    apply_load(build_sql(transformed, company_id=tenant))
    print("Carga concluída em uma transação (idempotente por chave natural).")


if __name__ == "__main__":
    main()
