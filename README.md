# Vornia — Workforce Intelligence

Sistema de gestão de ponto eletrônico, jornadas, banco de horas e conformidade CLT. Evolução do PontoJa.

## Stack

- **Backend:** FastAPI + Python 3.11
- **Banco de dados:** PostgreSQL 16
- **Autenticação:** JWT próprio no FastAPI
- **Frontend:** Next.js 14+ + Tailwind CSS + shadcn/ui
- **Hospedagem:** Oracle Cloud Always Free VM (ARM, 2 OCPU / 12 GB RAM) + Docker Compose + Caddy
- **Custo:** $0/mês na camada Always Free

> ⚠️ **Importante:** para evitar a política de *Idle Reclamation* da Oracle Cloud, a conta deve ser convertida para **Pay As You Go (PAYG)**. Os recursos Always Free continuam $0/mês, mas a VM deixa de estar sujeita a recuperação por inatividade.

## Requisitos

- Docker + Docker Compose
- Node.js 20+ (para desenvolvimento local do frontend)
- Python 3.11+ (para desenvolvimento local do backend)
- PostgreSQL 16+ (para desenvolvimento local do backend, ou use Docker)
- Conta Oracle Cloud Always Free (com upgrade para PAYG em produção)

## Setup local

1. Copie `.env.example` para `.env` e ajuste os valores.
2. Gere um `JWT_SECRET`:
   ```bash
   python scripts/generate-jwt-secret.py
   ```
3. Configure o PostgreSQL local (ou use `docker compose up -d postgres`).
4. Provisione as roles de runtime (idempotente, executar como superusuário):
   ```bash
   psql -U postgres -d vornia \
     -v app_password="$VORNIA_APP_PASSWORD" \
     -v auth_password="$VORNIA_AUTH_PASSWORD" \
     -f scripts/provision-db-roles.sql
   ```
5. Aplique as migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
6. Instale as dependências do backend:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -e ".[dev]"
   ```
7. Verifique que o ambiente de desenvolvimento ficou completo:
   ```bash
   python -m pip_audit --version
   pip check
   ```
   O extra `dev` inclui `pytest`, `ruff`, `mypy`, `bandit` e `pip-audit`. Se algum
   desses comandos não existir, o venv foi populado em partes: recrie-o e repita o
   passo 6. O CI valida o mesmo conjunto antes do scan de dependências.
8. Ative os hooks de git do repositório (uma vez por clone):
   ```bash
   git config core.hooksPath .githooks
   ```
   O hook `pre-commit` rejeita arquivos Python vazios e roda `ruff` no que está
   sendo commitado. A garantia definitiva é o teste
   `tests/unit/test_no_empty_source_files.py`, que roda no CI.
9. Instale as dependências do frontend:
   ```bash
   cd frontend
   npm install
   ```
10. Inicie o backend e o frontend:
    ```bash
    cd backend
    uvicorn vornia.main:app --reload --port 8000
    ```
    ```bash
    cd frontend
    npm run dev
    ```
11. O backend estará em `http://localhost:8000` e o frontend em `http://localhost:3000`.

## Segurança multi-tenant (RLS)

O isolamento entre tenants é garantido pelo PostgreSQL, não pelo código Python. Três roles são usadas:

| Role | Uso | Atributos |
|---|---|---|
| `vornia` | owner do schema; Alembic e administração | `DATABASE_URL` |
| `vornia_app` | runtime do FastAPI | `NOBYPASSRLS`, não-owner; `DATABASE_URL_APP` |
| `vornia_auth` | apenas `register`/`login` (bootstrap de tenant) | `BYPASSRLS`; `DATABASE_URL_BOOTSTRAP` |

As tabelas de negócio têm `ENABLE` **e** `FORCE ROW LEVEL SECURITY`: nem o owner escapa das policies. As policies leem `current_setting('request.jwt.claims', true)::json ->> 'company_id'`.

O runtime nunca deve usar `DATABASE_URL` (owner) — o app falha ao subir se `DATABASE_URL_APP` não estiver definida.

Em ambientes com volume já criado, é necessário recriar o volume (`docker compose down -v`) ou rodar o `provision-db-roles.sql` manualmente, pois os scripts de init só executam em banco vazio.

## Proteção da branch `main`

A `main` é protegida por **processo**, não por regra automática do GitHub.

O plano free do GitHub não permite rulesets/branch protection neste repositório: a API responde
`403 — Upgrade to GitHub Pro or make this repository public to enable this feature`. O arquivo
`scripts/ruleset-main.json` está pronto para ser aplicado quando o plano mudar:

```bash
gh api --method POST repos/MapheBR/vornia/rulesets --input scripts/ruleset-main.json
```

Enquanto isso, o contrato é:

1. Nenhum commit direto na `main`; todo trabalho entra por PR.
2. PR só é mergeado com CI verde (backend + frontend) e revisão humana.
3. Merge só com aprovação explícita do responsável pelo projeto.
4. `git log --oneline main` deve mostrar apenas merges de PR.

O CI roda em `push` e `pull_request` para a `main`, então qualquer push direto ainda é
verificado — mas a barreira de revisão é humana e depende deste contrato.

## Testes

```bash
cd backend
pytest
```

Para rodar apenas testes unitários (sem PostgreSQL):
```bash
pytest -m unit
```

Para rodar testes de integração (requer PostgreSQL):
```bash
pytest -m integration
```

## Estrutura

```
.
├── backend/          # FastAPI + lógica de domínio
├── frontend/         # Next.js + interface
├── docker/           # Dockerfiles e Caddyfile
├── branding/         # Logo e assets
├── docs/             # Documentação de planejamento
└── scripts/          # Scripts utilitários
```

## Documentação

- `docs/ARQUITETURA.md` — arquitetura e decisões técnicas
- `docs/SCHEMA-VORNIA.md` — schema do banco de dados
- `docs/PADROES-SEGURANCA.md` — padrões de segurança
- `docs/FASE3-PLANO.md` — plano de implementação do MVP
- `docs/MIGRACAO-DADOS.md` — estratégia de migração do PontoJa

## Licença

Proprietária — Tecnova.
