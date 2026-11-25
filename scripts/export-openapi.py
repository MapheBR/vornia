#!/usr/bin/env python3
"""Exporta o OpenAPI do FastAPI para docs/API.md."""

import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from vornia.main import app  # noqa: E402

spec = app.openapi()
lines = [
    "# API Vornia (OpenAPI)",
    "",
    "Documentação gerada a partir de `/openapi.json` do FastAPI "
    "(`scripts/export-openapi.py`).",
    "",
    f"**Título:** {spec['info']['title']} · **Versão:** {spec['info']['version']}",
    "",
    "## Autenticação",
    "",
    "A API usa **cookies HttpOnly** (`token` com `SameSite=Lax`, `refresh_token` com "
    "`SameSite=Strict` e `Path=/api/v1/auth`). O navegador envia os cookies "
    "automaticamente; o frontend usa `credentials: 'include'`.",
    "",
    "## Convenções",
    "",
    "- Prefixo: `/api/v1`",
    "- Isolamento por tenant via RLS: toda query define `request.jwt.claims` com o `company_id` do token",
    "- Erros: `400` validação, `401` não autenticado, `403` sem permissão, `404` não encontrado/outro tenant, `409` conflito, `422` schema inválido, `429` limite excedido (com `Retry-After`)",
    "",
    "## Endpoints",
    "",
    "| Método | Rota | Descrição |",
    "|---|---|---|",
]

for path, methods in spec["paths"].items():
    for method, detail in methods.items():
        if method in ("get", "post", "patch", "put", "delete"):
            summary = str(detail.get("summary", "")).replace("|", "\\|")
            lines.append(f"| `{method.upper()}` | `{path}` | {summary} |")

lines += [
    "",
    "## Esquemas",
    "",
    "```yaml",
    yaml.safe_dump(spec.get("components", {}).get("schemas", {}), allow_unicode=True, sort_keys=True)[:12000],
    "```",
    "",
]

target = ROOT / "docs" / "API.md"
target.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {target} ({len(lines)} linhas)")
