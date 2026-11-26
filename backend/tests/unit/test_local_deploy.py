"""Testes estáticos do deploy local (self-hosting + Tailscale)."""

import pathlib

import pytest

pytestmark = pytest.mark.unit

ROOT = pathlib.Path(__file__).resolve().parents[3]


def test_caddyfile_prod_serves_http_without_public_domain() -> None:
    text = (ROOT / "docker" / "Caddyfile.prod").read_text(encoding="utf-8")
    assert "auto_https off" in text
    assert ":80 {" in text
    assert "reverse_proxy backend:8000" in text
    assert "reverse_proxy frontend:3000" in text
    # O modo local não pode exigir domínio público nem ACME.
    assert "$VORNIA_DOMAIN" not in text
    assert "redir https" not in text


def test_caddyfile_prod_keeps_headers_without_hsts_on_plain_http() -> None:
    text = (ROOT / "docker" / "Caddyfile.prod").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in text
    assert "X-Content-Type-Options" in text
    assert "X-Frame-Options" in text
    # HSTS só faz sentido com HTTPS; em HTTP puro na VPN seria enganoso.
    assert "Strict-Transport-Security" not in text


def test_tailscale_https_caddyfile_uses_certificate_and_hsts() -> None:
    text = (ROOT / "docker" / "Caddyfile.tailscale-https").read_text(encoding="utf-8")
    assert "tls {$VORNIA_TLS_CERT} {$VORNIA_TLS_KEY}" in text
    assert "Strict-Transport-Security" in text
    assert "reverse_proxy backend:8000" in text
    assert "reverse_proxy frontend:3000" in text


def test_local_compose_publishes_only_caddy_port() -> None:
    text = (ROOT / "docker-compose.local.yml").read_text(encoding="utf-8")
    assert "8080:80" in text
    assert "./docker/Caddyfile.prod" in text
    assert "./docker/certs" in text
    for port in ("5432", "6379", "8000:8000", "3000:3000"):
        assert port not in text, port


def test_local_readiness_script_checks_tailscale_and_health() -> None:
    text = (ROOT / "scripts" / "check-local-readiness.sh").read_text(encoding="utf-8")
    for token in (
        "docker --version",
        "docker compose version",
        ".env",
        "tailscale ip",
        "/health",
        "exit 1",
    ):
        assert token in text, token


def test_deploy_workflow_is_paused() -> None:
    text = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "PAUSADO" in text
    assert text.count("if: false") >= 2
