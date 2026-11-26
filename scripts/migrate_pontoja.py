#!/usr/bin/env python3
"""Migra cadastros e saldos do PontoJa (SQLite) para o Vornia (PostgreSQL).

Regras de segurança (Sprint 7):
- `--apply` EXIGE `--backup-first`: o pg_dump roda antes de qualquer escrita.
- `--dry-run` não escreve no banco e imprime contagens + divergências.
- Nenhum dado real da Tecnova é usado nos testes (fixture sintética).

Uso:
  python scripts/migrate_pontoja.py --sqlite <arquivo.db> --dry-run
  python scripts/migrate_pontoja.py --sqlite <arquivo.db> --backup-first --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
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


def transform(data: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Normaliza CPF/PIS, nomes e datas antes da carga."""
    employees = []
    for row in data["usuarios"]:
        employees.append(
            {
                "name": str(row.get("nome", "")).strip(),
                "cpf": normalize_cpf(row.get("cpf")),
                "pis": normalize_cpf(row.get("pis")),
                "control_id": row.get("id"),
                "registration": str(row.get("matricula", "")).strip() or None,
            }
        )
    return {
        "employees": employees,
        "holidays": [
            {
                "name": str(r.get("nome", "")).strip(),
                "date": str(r.get("data", ""))[:10],
            }
            for r in data["feriados"]
        ],
        "settings": [
            {"key": str(r.get("chave", ""))[:100], "value": r.get("valor")}
            for r in data["configuracoes"]
        ],
        "time_balances": [
            {"closing_balance": r.get("saldo_banco_horas", 0)} for r in data["saldos_usuario"]
        ],
    }


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


def run_pg_dump() -> Path:
    """Executa pg_dump antes de qualquer escrita (backup-first)."""
    url = os.environ["DATABASE_URL"]
    target = Path(os.environ.get("BACKUP_DIR", "/backups"))
    target.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = target / f"pre_migration_{stamp}.sql"
    result = subprocess.run(
        ["pg_dump", url, "-f", str(path)], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump falhou: {result.stderr}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-first", action="store_true")
    args = parser.parse_args()

    if args.apply and args.dry_run:
        parser.error("--apply e --dry-run são mutuamente exclusivos")
    if args.apply and not args.backup_first:
        parser.error("--apply exige --backup-first (pg_dump obrigatório)")

    legacy = read_legacy(args.sqlite)
    report = divergences(legacy)
    transformed = transform(legacy)

    print("=== RELATÓRIO DE MIGRAÇÃO (dry-run) ===")
    for line in report:
        print(line)
    print("\n=== CONTAGEM POR TABELA DESTINO ===")
    for table, rows in transformed.items():
        print(f"{TABLE_MAP.get(table, table)}: {len(rows)} linha(s)")

    if args.dry_run:
        print("\nNenhuma escrita realizada (--dry-run).")
        return

    backup = run_pg_dump()
    print(f"\nBackup criado: {backup}")
    print("Carga real não executada neste scaffold — revisar relatório antes de --apply.")


if __name__ == "__main__":
    main()
