# Plano aprovado — Sprint 3

Branch: `feat/sprint-3` (de `main` `ffe4092`). Decisões E1–E6 aprovadas em 2026-11-25.

## Acréscimo aprovado: Rede/CORS (Fase 0)

Next.js e FastAPI rodam em portas diferentes localmente; cookies `HttpOnly` com
`SameSite=Strict` (refresh) são bloqueados se a UI chamar `localhost:8000` diretamente.
Solução: **same-origin via Caddy**, exatamente como em produção.

- Caddy (`:80` interno) publicado no host em `http://localhost:8080`.
- `handle /api/*` → `reverse_proxy backend:8000`
- `handle` (default) → `reverse_proxy frontend:3000`
- `NEXT_PUBLIC_API_URL` local = `http://localhost:8080` (mesma origem; o cliente usa
  caminhos relativos `/api/v1/...` e `credentials: "include"`).
- `CORS_ORIGINS` em produção continua `https://vornia.local,https://app.vornia.local`
  (defesa em profundidade; com proxy same-origin o navegador não dispara preflight).

Arquivos: `docker/Caddyfile`, `docker-compose.yml`, `.env.example`, `frontend/src/lib/api.ts`.

## Escopo e fases

| Fase | Entrega | Tamanho |
|---|---|---|
| 0 | Fundação: Caddy same-origin + `api.ts` (fetch nativo, credentials include, 401→refresh→retry), `types.ts`, hooks, config de teste | M |
| 1 | Auth UI: `/login`, `/register`, guarda via `/me`, renovação de sessão | M |
| 2 | UI de colaboradores: listagem paginada, busca/filtro, formulário create/edit, soft delete | G |
| 3 | UI de settings: 6 chaves, editor JSON, validação espelhando allowlist | M |
| 4 | Rate limiting Redis em `/auth/login`, `/register`, `/refresh` (429 + `Retry-After`), Redis no CI | M |
| 5 | Playwright E2E, `docs/SPRINT-3-EVIDENCIAS.md`, README, CI verde, parada para revisão | P |

## Decisões E1–E6

- **E1:** fetch nativo + hook próprio (sem React Query/SWR).
- **E2:** Tailwind puro + base shadcn existente (`button.tsx` com cva); sem novos Radix.
- **E3:** incluir telas de login/registro.
- **E4:** Playwright obrigatório nos fluxos críticos.
- **E5:** rate limiting com Redis; serviço Redis adicionado ao workflow do CI.
- **E6:** branch paralela isolada; só ideias via `docs/DEBT-SPRINT-3.md`, sem merge/cherry-pick.

## Critérios de aceite

- Login → criar colaborador → editar → desativar → settings → logout no Playwright, sem erros de console.
- Nenhum token lido pelo frontend (HttpOnly); 401 renova via `/auth/refresh` e repete.
- Sem chamada a `localhost:8000` no código; tudo por `NEXT_PUBLIC_API_URL` (mesma origem via Caddy).
- Rate limit devolve 429 com `Retry-After` e CI continua verde.
- Cobertura backend ≥80%; ruff/mypy/bandit/npm lint/typecheck/build limpos.

## Riscos

- HttpOnly impede o frontend de ler expiração → sonda `/me` + refresh no 401.
- Redis no CI → serviço adicionado ao workflow (E5).
- Divergência de contrato TS ↔ Pydantic → tipos derivados dos schemas da `main`.
- Branch paralela com nomes/migrations diferentes → nunca mergear.

**Parada ao final para revisão; Sprint 4 somente com aprovação.**
