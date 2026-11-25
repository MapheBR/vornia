"""Teste de restore real do backup PostgreSQL (roda no CI Linux).

Cria um banco descartável, faz pg_dump do banco de teste, restora o dump
nele e valida que as tabelas voltaram — não apenas que o arquivo existe.
"""

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[3]
BACKUP_SCRIPT = ROOT / "scripts" / "backup-postgres.sh"
RESTORE_DB = "vornia_restore_test"


def _database_url() -> str:
    from tests.integration.conftest import resolve_database_url

    return resolve_database_url()


def _url_for(db_name: str) -> str:
    parts = urlsplit(_database_url())
    return urlunsplit((parts.scheme, parts.netloc, f"/{db_name}", "", ""))


def _psql(url: str, sql: str) -> str:
    result = subprocess.run(
        ["psql", url, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.mark.skipif(shutil.which("pg_dump") is None, reason="pg_dump não disponível")
@pytest.mark.skipif(not Path("/bin/sh").exists(), reason="shell POSIX não disponível")
def test_backup_and_restore_roundtrip(tmp_path: Path) -> None:
    admin_url = _url_for("postgres")
    _psql(admin_url, f"DROP DATABASE IF EXISTS {RESTORE_DB};")
    _psql(admin_url, f"CREATE DATABASE {RESTORE_DB};")

    env = {**os.environ, "BACKUP_DIR": str(tmp_path), "DATABASE_URL": _database_url()}
    backup = subprocess.run(
        ["/bin/sh", str(BACKUP_SCRIPT)], env=env, capture_output=True, text=True
    )
    assert backup.returncode == 0, backup.stderr
    dumps = list(tmp_path.glob("vornia_*.sql.gz"))
    assert len(dumps) == 1

    restore = subprocess.run(
        ["/bin/sh", str(BACKUP_SCRIPT), "--restore", str(dumps[0])],
        env={**env, "DATABASE_URL": _url_for(RESTORE_DB)},
        capture_output=True,
        text=True,
    )
    assert restore.returncode == 0, restore.stderr
    assert "Restore concluído" in restore.stdout

    restored = _psql(
        _url_for(RESTORE_DB),
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' "
        "AND table_name IN ('employees','processed_journeys','time_balances','audit_logs');",
    )
    assert int(restored) == 4

    _psql(admin_url, f"DROP DATABASE IF EXISTS {RESTORE_DB};")
