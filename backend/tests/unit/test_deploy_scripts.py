"""Testes estáticos dos scripts de deploy/provisionamento do Sprint 7."""

import pathlib

import pytest

pytestmark = pytest.mark.unit

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"


def test_vm_readiness_script_covers_required_checks() -> None:
    text = (SCRIPTS / "check-vm-readiness.sh").read_text(encoding="utf-8")
    for token in (
        "docker --version",
        "docker compose version",
        "id deploy",
        ".env",
        "stat -c %a",
        "df -Pm",
        "exit 1",
    ):
        assert token in text, token


def test_caddyfile_serves_local_http_without_domain() -> None:
    # Deploy local substituiu o plano Oracle: não há domínio público nem ACME.
    text = (ROOT / "docker" / "Caddyfile.prod").read_text(encoding="utf-8")
    assert "auto_https off" in text
    assert ":80 {" in text
    assert "reverse_proxy backend:8000" in text
    assert "reverse_proxy frontend:3000" in text


def test_prod_compose_does_not_expose_internal_ports() -> None:
    text = (ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "5432" not in text
    assert "6379" not in text
    assert "8000:8000" not in text
    assert "3000:3000" not in text
    assert "80:80" in text
    assert "443:443" in text


def test_deploy_workflow_uses_ssh_and_tags() -> None:
    text = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    for token in (
        "workflow_dispatch",
        "tags:",
        "appleboy/ssh-action",
        "secrets.DEPLOY_SSH_KEY",
        "check-vm-readiness.sh",
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d",
        "alembic upgrade head",
    ):
        assert token in text, token


def test_migration_script_has_backup_first_and_dry_run() -> None:
    text = (SCRIPTS / "migrate_pontoja.py").read_text(encoding="utf-8")
    assert "--backup-first" in text
    assert "--dry-run" in text
    assert "--apply" in text
    assert "pg_dump" in text
    assert "diverg" in text.lower()


def test_rollback_script_restores_previous_tag() -> None:
    text = (SCRIPTS / "rollback.sh").read_text(encoding="utf-8")
    assert ".deploy-version" in text
    assert "git checkout" in text
    assert "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d" in text
