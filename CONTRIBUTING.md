# Contributing to Vornia

Guia de contribuição para o projeto Vornia.

## Requisitos

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose

## Setup de desenvolvimento

1. Clone o repositório.
2. Copie `.env.example` para `.env` e ajuste.
3. Backend:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -e ".[dev]"
   ```
4. Frontend:
   ```bash
   cd frontend
   npm install
   ```

## Fluxo de trabalho

1. Crie uma branch a partir da `main`:
   ```bash
   git checkout -b feat/nome-da-feature
   ```
2. Escreva testes primeiro (TDD).
3. Implemente a feature.
4. Rode os checks localmente:
   ```bash
   cd backend
   ruff check .
   ruff format --check .
   mypy vornia/
   pytest
   bandit -r vornia/
   pip-audit
   ```
   ```bash
   cd frontend
   npm run lint
   npm run typecheck
   npm run build
   ```
5. Abra um Pull Request para a `main`.
6. Só merge após CI verde + code review.

## Tipos de commit

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `refactor:` refatoração sem mudança de comportamento
- `test:` adição/ajuste de testes
- `chore:` manutenção, config, docs
- `docs:` documentação

## Padrões de código

- Python: type hints, funções pequenas, imutabilidade.
- TypeScript: strict mode, componentes funcionais.
- Todo input de usuário validado com Pydantic/Zod.
- Toda query sensível a tenant dentro de transação com RLS context.

## Segurança

- Nunca commitar secrets.
- Nunca hardcodear senhas, tokens ou chaves.
- Rodar scans de segurança antes de PR.

## Dúvidas?

Consulte `docs/ARQUITETURA.md`, `docs/PADROES-SEGURANCA.md` e `docs/FASE3-PLANO.md`.
