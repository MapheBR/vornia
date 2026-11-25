# Dívida técnica — Sprint 3 (UI de colaboradores e settings)

## Branch paralela preservada

| Item | Valor |
|---|---|
| Branch local | `feat/sprint-2-employees-settings` (críamos como tracking de `origin/...`) |
| commit | `59a0263dd557fa7a8df144eb46cc40b39a3b3aef` |
| Autor/Data | Marcos Feliphe — 2026-11-24 19:49:30 -0300 |
| Base | `b1ee17d` (main após o merge do Sprint 1) |
| Estado | **NÃO mesclada.** Sem PR, sem CI. Mantida apenas como referência. |

**Regra:** esta branch não deve ser mergeada. Ela viola a decisão D1 (frontend antes da hora), colide as migrations (`006`/`007` vs nossas `006`/`007`/`008`) e não passou pelo CI. O aproveitamento é **por ideia/código copiado e reescrito**, nunca por merge.

## O que é aproveitável

### 1. `frontend/src/components/employees/employee-manager.tsx` (286 linhas)
- Estrutura de componente cliente (`"use client"`) com `useCallback`/`useEffect`/`useState`.
- Formulário de colaborador com os campos: `name`, `registration`, `jobTitle`, `department`, `cpf`, `pis`, `controlId`, `hiredAt`.
- Helpers `fromEmployee()` e `toPayload()` — mapeamento entre o modelo da API e o estado do formulário.
- Fluxo de carregamento → edição → salvamento, com estados `loading`/`saving`/`error`.
- **Aproveitar:** o layout do formulário, a lista de campos e o padrão de estados. **Reescrever:** o mapeamento de payload (ver abaixo).

### 2. `frontend/src/components/settings/settings-manager.tsx` (142 linhas)
- Editor de configurações por chave/valor com `JSON.parse` para o valor e validação amigável (`"O valor deve ser um JSON válido"`).
- **Aproveitar:** a ideia do editor de valor JSON e as mensagens de erro em pt-BR.

### 3. Páginas de rota
- `frontend/src/app/colaboradores/page.tsx` e `frontend/src/app/configuracoes/page.tsx` (5 linhas cada) — rotas simples que renderizam os managers.
- `frontend/src/app/page.tsx` — links de navegação para essas telas.

## O que NÃO aproveitar como está

| Problema | Detalhe |
|---|---|
| **Não compila** | Os componentes importam `employeesApi`/`settingsApi` de `@/lib/api` e os tipos `Employee`/`EmployeePayload` de `@/lib/types` — **esses arquivos não existem na própria branch**. O cliente de API e os tipos precisam ser escritos do zero. |
| **Contrato de API diferente** | O payload usa `job_title`, `control_id`, `hired_at` (snake_case) e os tipos `Employee` com `registration: string | null`. Nosso contrato real usa `schemas/employee.py` com `name`, `registration`, `pis`, `cpf`, `job_title`, `department`, `work_schedule`, `photo_url`, `is_active`, `hired_at`, `control_id` — conferir com `docs/API.md`/OpenAPI antes de ligar. |
| **Sem autenticação no cliente** | Nossa API usa cookie `token` (HttpOnly) e `refresh_token` (path `/api/v1/auth`). O cliente precisa tratar 401 → refresh e 403/404. |
| **Migrations colidentes** | A branch cria `006_employees`/`007_settings`; a main já tem `006_employees`, `007_refresh_tokens`, `008_settings`. Nunca aplicar as migrations dessa branch. |
| **Backend divergente** | Implementação duplicada com nomes no plural (`repositories/employees.py`, `schemas/employees.py`) e sem refresh token. Descartar — a fonte da verdade é a `main` (PR #2). |
| **Sem CI/testes verificados** | Nenhuma run de CI para `59a0263`; os "51 testes / 95.79%" da mensagem do commit não foram validados. Não usar como evidência. |

## Base real para o Sprint 3 (API já mergeada na main)

- `POST /api/v1/employees` — cria (201)
- `GET /api/v1/employees` — lista com `page`, `per_page`, `search`, `active`
- `GET /api/v1/employees/{id}` — detalhe (404 se outro tenant)
- `PATCH /api/v1/employees/{id}` — atualização parcial
- `DELETE /api/v1/employees/{id}` — soft delete (204)
- `GET /api/v1/settings` — configurações efetivas (defaults + overrides)
- `GET /api/v1/settings/{key}` — uma chave
- `PUT /api/v1/settings/{key}` — upsert (422 se chave/tipo inválidos)
- `DELETE /api/v1/settings/{key}` — volta ao default (204)
- `POST /api/v1/auth/refresh` / `POST /api/v1/auth/logout` — ciclo de sessão

## Pendências herdadas do Sprint 2

- **Rate limiting em `/auth/login` e `/auth/refresh`** — adiado pela decisão D6;redis já está no docker-compose. Avaliar no Sprint 3.
- **Foto de colaborador** — campo `photo_url` existe no schema; upload/storage fora de escopo até aqui.
- **CSP restritivo em produção** — item de segurança do projeto, ainda não implementado no Caddy.
