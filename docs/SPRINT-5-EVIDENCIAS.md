# Sprint 5 — Entrega parcial (Fases 0 a 3)

Conforme alinhamento: priorizar Backend/Dashboard; exportações (Fase 4) e auditoria visual (Fase 5) ficam para o Sprint 6.

## Fase 0 — Migrations (012/013/014)
| Garantia | Teste |
|---|---|
| FORCE RLS em holidays/time_balances/audit_logs | `test_rls_sprint5.py` |
| `audit_logs` append-only (sem policies UPDATE/DELETE) | `test_audit_logs_is_append_only` |

## Fase 1 — Calculadora CLT (10 casos, matriz TDD)
| Regra | Valor |
|---|---|
| Hora extra | +50% |
| Adicional noturno | +20% |
| Extra noturna | diferença 70% − 50% |
| Feriado/domingo | dobra (100%) |
| Noturno | minutos reais 22h–05h |
| Defeitos #8/#9/#10 | neutralizados |

Arquivo: `tests/unit/test_banco_horas.py` (10 testes).

## Fase 2 — Endpoints
| Rota | Garantia |
|---|---|
| `POST /balances/recalculate` | upsert determinístico em `time_balances` |
| `GET /balances` | somente dados do tenant (RLS) |
| `POST/GET /holidays` | feriado por tenant com `jornada_especial_hours` |

Arquivo: `tests/integration/test_balances.py` (3 testes).

## Fase 3 — Dashboard
| Rota | Garantia |
|---|---|
| `GET /dashboard/summary` | agregações com RLS (total, horas, inconsistências, pendências) |
| `GET /dashboard/inconsistencies` | só `inconsistency`/`pending`, máx. 100 |

Arquivo: `tests/integration/test_dashboard.py` (2 testes). Tela: `frontend/src/app/dashboard/page.tsx`.

## Quality gates
- 156 testes backend passando
- ruff check/format, mypy (52 arquivos), bandit — limpos
- frontend typecheck limpo

## Pendente para Sprint 6
- Fase 4: exportações XLSX/PDF (PDF com lib leve / HTML+CSS print para ARM)
- Fase 5: auditoria e edição manual com cascata atômica (`raw_punch` → `processed_journey` → `time_balances` na mesma transação)
