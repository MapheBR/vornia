# Evidências do Sprint 4 — Control iD + Jornadas

## Payload real (fonte: `PontoJa/services/controlid_api.py`)
Documentado em `docs/CONTROLID-PAYLOAD.md`. Mocks HTTP usam:
- `login.fcgi` → `{"session":"..."}`
- `load_users.fcgi` → `{"users":[{"id":..., "nome":...}]}`
- `get_afd.fcgi?mode=671` → texto AFD `YYYY-MM-DDTHH:MM:SS±HHMM` + `0*` + PIS + hash,
  também aceito em base64 e `{"records":[...]}`.
- Nenhum campo inventado; offset/tz reais (`-0300`, sem dois-pontos).

## Fase 0 — Tabelas e RLS
| Garantia | Teste | Evidência |
|---|---|---|
| FORCE RLS em raw_punches/processed_journeys/sync_state | `test_rls_sprint4.py` | 3 casos parametrizados |
| Claims A não veem batidas de B | `test_runtime_role_cannot_see_other_tenant_punches` | 1 visível, 0 de B |

## Fase 1 — Cliente Control iD
| Garantia | Teste |
|---|---|
| Sessão extraída de session/session_id/token | `test_login_extracts_session` |
| Paginação `limit/offset` | `test_get_users_paginates_with_limit_offset` |
| AFD texto puro e base64 | `test_get_records_*` |
| Lista vazia não autoriza desativação em massa | `test_empty_user_list_never_disables_everyone` |

Defeitos mapeados: #2 cursor real enviado ao dispositivo; #3 salvaguarda; #4 órfãos sinalizados;
#7 UNIQUE natural + `ON CONFLICT DO NOTHING`.

## Fase 2 — Sync endpoint
| Garantia | Teste |
|---|---|
| 3 batidas inseridas (2 mapeadas + 1 órfã) | `test_sync_inserts_punches_and_flags_unmapped` |
| Reexecução não duplica (skipped=3) | `test_sync_is_idempotent` |
| `sync_state` persistido | `test_sync_state_persists_cursor` |
| 401 sem auth | `test_endpoint_requires_auth` |

## Fase 3 — Matriz TDD de jornadas (10 casos)
| # | Caso | Resultado |
|---|---|---|
| 1 | 2 batidas | sem almoço inventado, 9.0h, complete |
| 2 | 4 batidas | 8.0h, almoço 12–13 |
| 3 | 6 batidas | inconsistency, 6 ids preservados |
| 4 | 3 batidas | pending, sem volta inventada |
| 5 | 1ª após corte | entry correto |
| 6 | Feriado 4h | worked 8, expected 4, overtime 4 |
| 7 | Feriado sem batida | None (não é falta) |
| 8 | Dia futuro | None |
| 9 | Timezone -0300 | offset -3h, UTC 11h |
| 10 | Ordenação | 8h antes de 17h |

Arquivo: `tests/unit/test_journey_rules.py`.

## Fase 4 — Endpoint /sync/process
| Garantia | Teste |
|---|---|
| Upsert determinístico (≤1 jornada por dia) | `test_second_process_does_not_duplicate` |
| Endpoint responde 200 | `test_endpoint_process` |

## Quality gates
- 137 testes backend passando
- ruff check/format, mypy (48 arquivos), bandit — limpos
- migrations 009/010/011 aplicadas do zero em banco local

## Fora de escopo (Sprint 5)
`time_balances`, dashboard, CSV, exportações, auditoria/edição manual.
