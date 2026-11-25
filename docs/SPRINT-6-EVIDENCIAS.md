# Evidências do Sprint 6 — Hardening + Pendências

## Fase 0 — Exportações
| Garantia | Teste |
|---|---|
| XLSX com cabeçalho + linhas | `test_xlsx_has_header_and_rows` |
| Sanitização `=cmd|`/`@SUM` | `test_csv_injection_is_neutralized` |
| PDF respeita 500 linhas | `test_pdf_respects_row_limit` |
| PDF válido (`%PDF`) | `test_pdf_generates_valid_file` |

Bibliotecas `openpyxl`/`fpdf2` puras em Python — compatíveis com ARM (Oracle Cloud).

## Fase 1 — Cascata atômica
| Garantia | Teste |
|---|---|
| `reason` obrigatório | `test_reason_is_required` (422) |
| Edição propaga e audita | `test_cascade_creates_journey_and_audit` |
| **Rollback total em falha induzida** | `test_atomic_rollback_on_failure` — nenhuma edição, nenhum log |
| `audit_logs` consultável | `test_audit_logs_append_only` |

Mesma conexão/transação em `raw_punch → processed_journey → time_balances → audit_logs`.

## Fase 2 — E2E no CI
- Job separado `e2e` com `docker compose up -d --build`, health-checks em `localhost:8080`,
  Playwright com `E2E_BASE_URL=http://localhost:8080`.
- `docker compose down -v` em `if: always()`, report como artifact, secrets via `secrets.*`.

## Fase 3 — Segurança
- `security-reviewer`: 5 HIGH + 7 MEDIUM corrigidos (limites no SQL antes do 429, rate limit
  em exports/sync/process/edits, `safe_cell` em todas as colunas, `/audit-logs` restrito,
  CPF mascarado em create/get, UUIDs validados, defesa em profundidade no `company_id`,
  normalização Latin-1 do PDF, UPDATE de `processed` limitado ao intervalo).
- CSP/HSTS e headers no Caddy + middleware FastAPI.
- `scripts/backup-postgres.sh` com `--restore` e teste real de roundtrip
  (`test_backup_restore.py`, executa no CI Linux com `postgresql-client`).
- `docs/PADROES-SEGURANCA.md` corrigido: Bearer → cookies HttpOnly.

## Fase 4 — Documentação
- `docs/API.md` gerado de `/openapi.json`; `docs/LGPD.md`; `docs/MANUAL-DO-USUARIO.md`; README atualizado.

## Quality gates
- 164 testes backend (1 skip local: restore precisa de `/bin/sh` — roda no CI)
- ruff, mypy (57 arquivos), bandit — limpos
- frontend typecheck/lint/build/audit — limpos

## Próximo
Deploy em staging (Sprint 7). Nenhum código de Sprint 7 escrito.
