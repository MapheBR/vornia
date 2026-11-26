"""Testes da carga real do migrate_pontoja.py (SQLite sintético, sem dados reais)."""

import sqlite3
import sys
from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import migrate_pontoja as migration  # noqa: E402


@pytest.fixture(autouse=True)
def _admin_temp_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Senha temporária fake para os testes (nunca dado real)."""
    monkeypatch.setenv("VORNIA_MIGRATION_ADMIN_PASSWORD", "temporaria-teste")


@pytest.fixture
def legacy_db(tmp_path: Path) -> Path:
    """SQLite sintético com as colunas reais do legado PontoJa."""
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY, nome TEXT, matricula TEXT, cpf TEXT,
            cargo TEXT, departamento TEXT, ativo INTEGER, foto_path TEXT,
            criado_em TEXT, atualizado_em TEXT, modo_compensacao TEXT,
            salario_base REAL, data_admissao TEXT, carga_horaria TEXT
        );
        CREATE TABLE feriados (
            id INTEGER PRIMARY KEY, data TEXT, descricao TEXT, tipo TEXT,
            criado_em TEXT, jornada_especial REAL
        );
        CREATE TABLE configuracoes (
            id INTEGER PRIMARY KEY, chave TEXT, valor TEXT, atualizado_em TEXT
        );
        CREATE TABLE saldos_usuario (
            id INTEGER PRIMARY KEY, usuario_id INTEGER, modo_compensacao TEXT,
            saldo_banco_horas REAL, saldo_devedor_horas REAL,
            valor_extras_acumulado REAL, atualizado_em TEXT
        );
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY, usuario TEXT, senha_hash TEXT, nome TEXT,
            ativo INTEGER, criado_em TEXT, atualizado_em TEXT
        );
        INSERT INTO usuarios (id, nome, matricula, cpf, cargo, departamento, ativo)
            VALUES (1, 'Maria Teste', 'M-1', '526.018.159-06', 'Analista', 'RH', 1);
        INSERT INTO usuarios (id, nome, matricula, cpf, cargo, departamento, ativo)
            VALUES (2, 'Joao Teste', 'M-2', NULL, 'Tecnico', 'TI', 0);
        INSERT INTO feriados (id, data, descricao, tipo)
            VALUES (1, '2026-12-25', 'Natal', 'nacional');
        INSERT INTO configuracoes (id, chave, valor)
            VALUES (1, 'timezone', 'America/Sao_Paulo');
        INSERT INTO configuracoes (id, chave, valor)
            VALUES (2, 'sync_on_start', 'true');
        INSERT INTO saldos_usuario (id, usuario_id, saldo_banco_horas)
            VALUES (1, 1, 4.5);
        INSERT INTO admins (id, usuario, senha_hash, nome, ativo)
            VALUES (1, 'admin.teste', 'scrypt:hash-antigo', 'Admin Teste', 1);
        """
    )
    conn.commit()
    conn.close()
    return path


def _data(path: Path) -> dict:
    return migration.read_legacy(path)


def test_transform_maps_legacy_employee_columns(legacy_db: Path) -> None:
    rows = migration.transform(_data(legacy_db))["employees"]
    first = rows[0]
    assert first["name"] == "Maria Teste"
    assert first["cpf"] == "52601815906"
    assert first["registration"] == "M-1"
    assert first["job_title"] == "Analista"
    assert first["department"] == "RH"
    assert first["is_active"] is True
    assert first["control_id"] == 1


def test_transform_uses_descricao_for_holiday_name(legacy_db: Path) -> None:
    holidays = migration.transform(_data(legacy_db))["holidays"]
    assert holidays[0]["name"] == "Natal"
    assert holidays[0]["date"] == "2026-12-25"


def test_transform_converts_config_value_to_json(legacy_db: Path) -> None:
    settings = {s["key"]: s["value"] for s in migration.transform(_data(legacy_db))["settings"]}
    assert settings["timezone"] == '"America/Sao_Paulo"'
    assert settings["sync_on_start"] == "true"


def test_transform_links_balance_to_control_id(legacy_db: Path) -> None:
    balances = migration.transform(_data(legacy_db))["time_balances"]
    assert balances[0]["control_id"] == 1
    assert balances[0]["closing_balance"] == 4.5


def test_transform_requires_admin_temp_password(
    legacy_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("VORNIA_MIGRATION_ADMIN_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="VORNIA_MIGRATION_ADMIN_PASSWORD"):
        migration.transform(_data(legacy_db))


def test_transform_maps_admins_to_users_and_company_users(
    legacy_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VORNIA_MIGRATION_ADMIN_PASSWORD", "temporaria-teste")
    result = migration.transform(_data(legacy_db))
    assert result["users"][0]["email"] == "admin.teste@tecnova.local"
    assert result["users"][0]["full_name"] == "Admin Teste"
    assert result["users"][0]["password_hash"].startswith("$2")
    assert result["company_users"][0]["role"] == "admin"


def test_build_sql_is_transactional_and_idempotent(
    legacy_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VORNIA_MIGRATION_ADMIN_PASSWORD", "temporaria-teste")
    sql = migration.build_sql(
        migration.transform(_data(legacy_db)), company_id=migration.company_id_for("tecnova")
    )
    assert "BEGIN;" in sql
    assert "COMMIT;" in sql
    assert "request.jwt.claims" in sql
    for fragment in (
        "ON CONFLICT (slug) DO NOTHING",
        "ON CONFLICT (company_id, control_id) WHERE control_id IS NOT NULL DO UPDATE",
        "ON CONFLICT (company_id, date) DO UPDATE",
        "ON CONFLICT (company_id, key) DO UPDATE",
        "ON CONFLICT (company_id, employee_id, reference_month) DO UPDATE",
        "ON CONFLICT (email) DO NOTHING",
        "ON CONFLICT (company_id, user_id) DO UPDATE",
    ):
        assert fragment in sql, fragment


def test_build_sql_rejects_balance_with_unknown_employee(
    legacy_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VORNIA_MIGRATION_ADMIN_PASSWORD", "temporaria-teste")
    data = _data(legacy_db)
    data["saldos_usuario"][0]["usuario_id"] = 999
    with pytest.raises(RuntimeError, match="usuario_id"):
        migration.transform(data)


def test_apply_load_uses_docker_psql_with_on_error_stop() -> None:
    with mock.patch.object(
        migration.subprocess, "run", return_value=mock.Mock(returncode=0)
    ) as run:
        migration.apply_load("BEGIN; SELECT 1; COMMIT;")
    args = run.call_args.args[0]
    assert args[:3] == ["docker", "compose", "exec"]
    assert "postgres" in args
    assert "psql" in args
    assert "ON_ERROR_STOP=1" in args


def test_apply_load_raises_on_psql_failure() -> None:
    failed = mock.Mock(returncode=3, stderr="erro de SQL")
    with (
        mock.patch.object(migration.subprocess, "run", return_value=failed),
        pytest.raises(RuntimeError, match="psql"),
    ):
        migration.apply_load("BEGIN; SELECT 1; COMMIT;")


def test_run_pg_dump_uses_docker_not_host_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    with mock.patch.object(
        migration.subprocess, "run", return_value=mock.Mock(returncode=0)
    ) as run:
        path = migration.run_pg_dump()
    args = run.call_args.args[0]
    assert args[:3] == ["docker", "compose", "exec"]
    assert "pg_dump" in args
    assert path.parent == tmp_path
    assert path.suffix == ".sql"


def test_run_pg_dump_raises_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    failed = mock.Mock(returncode=1, stderr="pg_dump falhou")
    with (
        mock.patch.object(migration.subprocess, "run", return_value=failed),
        pytest.raises(RuntimeError, match="pg_dump"),
    ):
        migration.run_pg_dump()
