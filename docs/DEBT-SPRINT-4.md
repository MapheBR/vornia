# Dívida técnica — Sprint 4 (Hardening)

## CI do Playwright E2E — **bloqueante para deploy de produção (Sprint 7)**

### Situação atual
- O teste `frontend/e2e/fluxo-critico.spec.ts` existe e **passa localmente**
  (registro → colaborador → settings → logout, sem erros de console).
- O job `frontend` do GitHub Actions **não sobe a stack**: não há backend,
  frontend servindo e Caddy naquele job. Por isso o step de E2E foi removido
  do workflow para manter o CI verde.
- Evidência local: `docs/SPRINT-3-EVIDENCIAS.md` (1 fluxo, 4.1s).

### Tarefa
Criar um **job separado** `e2e` em `.github/workflows/ci.yml` que:

1. Faz checkout, `setup-python@3.11` e `setup-node@20` com cache npm.
2. Instala dependências do backend (`pip install -e ".[dev]"`) e do frontend
   (`npm ci`), além de `npx playwright install --with-deps chromium`.
3. Cria o `.env` do CI (via variáveis do repositório, **nunca hardcoded**) com
   `DATABASE_URL`, `DATABASE_URL_APP`, `DATABASE_URL_BOOTSTRAP`, `JWT_SECRET`,
   `COOKIE_SECURE=false`, `RATE_LIMIT_ENABLED=false`.
4. Sobe a stack com `docker compose up -d --build` e aguarda:
   - `curl --retry 15 http://localhost:8080/health`
   - `curl --retry 15 http://localhost:8080/` (Next.js via Caddy)
5. Roda `npx playwright test` com `E2E_BASE_URL=http://localhost:8080`.
6. Faz `docker compose down -v` no `if: always()` e faz upload do
   `playwright-report/` como artifact.

### Aceite
- Job `e2e` verde em PR e push na `main`.
- Falha de qualquer serviço derruba o job (não pode ficar falso-verde).
- Nenhum secret hardcoded; tudo via `secrets.*`/`vars.*` do GitHub.
- Report e traces disponíveis como artifact.

### Por que é bloqueante
Sem esse job, a integração real (Caddy + cookies HttpOnly + refresh) só é
validada na máquina local. O deploy de produção (Sprint 7) depende dessa
garantia no CI.

---

## Outras pendências de hardening

| Item | Origem | Quando |
|---|---|---|
| CSP restritivo no Caddy para produção | `docs/PADROES-SEGURANCA.md` | Sprint 7 |
| Branch protection da `main` (impossível no plano free) | `scripts/ruleset-main.json` | Quando migrar de plano |
| Upload de foto de colaborador (`photo_url` já existe) | `docs/DEBT-SPRINT-3.md` | Backlog |
