"""Testes funcionais do migrate_pontoja.py com SQLite sintético."""

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "migrate_pontoja.py"


@pytest.fixture
def legacy_db(tmp_path: Path) -> Path:
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE usuarios (id INTEGER, nome TEXT, cpf TEXT, pis TEXT, matricula TEXT);
        CREATE TABLE feriados (id INTEGER, nome TEXT, data TEXT);
        CREATE TABLE configuracoes (chave TEXT, valor TEXT);
        CREATE TABLE saldos_usuario (usuario_id INTEGER, saldo_banco_horas REAL);
        CREATE TABLE admins (id INTEGER, nome TEXT);
        INSERT INTO usuarios VALUES (1,'Maria','526.018.159-06','123','M-1');
        INSERT INTO usuarios VALUES (2,'Joao',NULL,NULL,NULL);
        INSERT INTO feriados VALUES (1,'Natal','2026-12-25');
        INSERT INTO configuracoes VALUES ('timezone','America/Sao_Paulo');
        INSERT INTO saldos_usuario VALUES (1, 4.5);
        INSERT INTO admins VALUES (1,'Admin');
        """
    )
    conn.commit()
    conn.close()
    return path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def test_dry_run_reports_counts_and_divergences(legacy_db: Path) -> None:
    result = _run("--sqlite", str(legacy_db), "--dry-run")
    assert result.returncode == 0
    assert "RELATÓRIO DE MIGRAÇÃO" in result.stdout
    assert "diverg" in result.stdout.lower()
    assert "employees: 2 linha(s)" in result.stdout
    assert "Nenhuma escrita realizada" in result.stdout


def test_apply_requires_backup_first(legacy_db: Path) -> None:
    result = _run("--sqlite", str(legacy_db), "--apply")
    assert result.returncode != 0
    assert "--backup-first" in result.stderr


def test_normalize_cpf_digits_only() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from migrate_pontoja import normalize_cpf

    assert normalize_cpf("526.018.159-06") == "52601815906"
    assert normalize_cpf(None) is None
