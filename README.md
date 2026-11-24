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
4. Aplique as migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
5. Instale as dependências do backend:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -e ".[dev]"
   ```
6. Instale as dependências do frontend:
   ```bash
   cd frontend
   npm install
   ```
7. Inicie o backend e o frontend:
   ```bash
   cd backend
   uvicorn vornia.main:app --reload --port 8000
   ```
   ```bash
   cd frontend
   npm run dev
   ```
8. O backend estará em `http://localhost:8000` e o frontend em `http://localhost:3000`.

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
