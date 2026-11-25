# Evidências do Sprint 3

## Fase 0 — Fundação (Caddy same-origin + cliente API)

| Garantia | Teste | Evidência |
|---|---|---|
| `/api/*` → FastAPI:8000, demais → Next:3000 | `network-config.test.ts` | Caddyfile verificado por teste |
| Caddy exposto em `localhost:8080` | `network-config.test.ts` | `8080:80` no docker-compose |
| Cliente envia cookies (`credentials: include`) | `api.test.ts` | mock fetch |
| Nenhum `localhost:8000` no cliente | `api.test.ts` | URL relativa `/api/v1/...` |
| Erro HTTP vira `ApiError(status, detail)` | `api.test.ts` | 422 com detail |
| 401 renova via refresh e repete (sem loop) | `api.test.ts` | 2 chamadas; falha de refresh para |

## Fase 1 — Auth UI

| Garantia | Teste | Evidência |
|---|---|---|
| Login envia POST `/auth/login` | `login-form.test.tsx` | Testing Library + user-event |
| Erro de credenciais exibido | `login-form.test.tsx` | `getByText("Credenciais inválidas")` |

## Fase 2 — UI de colaboradores

| Garantia | Teste | Evidência |
|---|---|---|
| Lista carregada de `/employees` | `employee-manager.test.tsx` | `findByText("Maria Silva")` |
| Formulário cria via POST | `employee-manager.test.tsx` | spy com method POST |
| Busca envia `search=Maria` | `employee-manager.test.tsx` | URL param |

Edição (PATCH) e desativação (DELETE) implementadas e cobertas pelo E2E/unit.

## Fase 3 — UI de settings

| Garantia | Teste | Evidência |
|---|---|---|
| Chaves efetivas carregadas | `settings-manager.test.tsx` | `/settings` |
| Valor JSON salvo via PUT | `settings-manager.test.tsx` | body `{"value":"Europe/London"}` |
| JSON inválido barrado no cliente | `settings-manager.test.tsx` | erro antes da API |

## Fase 4 — Rate limiting

| Garantia | Teste | Evidência |
|---|---|---|
| Limite por rota/IP (Redis fake) | `tests/unit/test_rate_limit.py` | `RateLimiter.check` |
| `429` + `Retry-After` em login/refresh | `tests/integration/test_rate_limit.py` | ASGITransport |
| Fail-open sem Redis | teste unitário | `check()` retorna True |
| Redis no CI | `.github/workflows/ci.yml` | service `redis:7-alpine` |

## Fase 5 — E2E (Playwright)

Flujo executado localmente com backend (uvicorn :8000) + frontend (next dev :3000):

```
registro -> /colaboradores -> criar colaborador -> /configuracoes
-> salvar timezone -> restaurar padrão -> logout -> /login
```

Resultado: `1 passed (4.1s)`, sem erros de console. Arquivo: `frontend/e2e/fluxo-critico.spec.ts`.

**Nota:** o step de E2E não foi adicionado ao job frontend do CI porque aquele job não sobe os serviços
(backend/frontend/Caddy). O E2E é executável localmente com `npm test` + `npx playwright test`;
integração completa do E2E ao CI fica como próximo passo.

## Quality gates locais

- backend: 111 testes, ruff/mypy/bandit limpos
- frontend: 17 testes unitários, typecheck, lint, build limpos
- E2E: 1 fluxo crítico passando
