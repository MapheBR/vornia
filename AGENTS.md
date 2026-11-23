# Agent Instructions — Vornia

Este arquivo contém regras específicas para agentes de IA trabalhando no projeto Vornia.

## Stack e arquitetura

- Backend: FastAPI + Python 3.11
- Banco: PostgreSQL 16 local (Docker)
- Auth: JWT próprio no FastAPI (PyJWT + bcrypt/Argon2)
- Frontend: Next.js 14+ + Tailwind CSS + shadcn/ui
- Infra: Oracle Cloud Always Free VM + Docker Compose + Caddy

## Regras obrigatórias

1. **Nunca escreva código antes de testes** para novas features (TDD).
2. **Cobertura mínima de 80%** em todo código novo.
3. **Nunca mutar objetos** — sempre retornar novas instâncias.
4. **Nenhum secret hardcoded** — usar variáveis de ambiente.
5. **Toda query sensível a tenant** deve rodar dentro de transação com `request.jwt.claims` setado.
6. **RLS habilitado** em todas as tabelas de negócio (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
7. **Input validation** via Pydantic em todos os endpoints.
8. **Commits em conventional commits**: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`.
9. **Branch `main` protegida** — só merge via PR com CI verde.
10. **Não apagar arquivos nem dados** sem confirmação explícita do usuário.

## Convenções de código

- Python: PEP 8, type hints obrigatórios, funções pequenas (<50 linhas).
- TypeScript: strict mode, paths `@/*` para imports do src.
- Nomeação: snake_case para Python, camelCase para TypeScript.
- Idioma: português do Brasil para nomes de domínio e documentação.

## Segurança

- Rodar `bandit`, `pip-audit` e `npm audit` antes de merge.
- Nunca logar PII, senhas ou tokens completos.
- Cookies `HttpOnly`, `Secure`, `SameSite=Strict`.
- CSP restritivo em produção.

## Testes

- Unitários: `backend/tests/unit/`
- Integração: `backend/tests/integration/`
- E2E: `tests/e2e/` (Playwright)

## Comunicação

- Responder sempre em português do Brasil.
- Ao final de cada sprint, entregar: resumo, o que falta, riscos abertos.
- Não iniciar próximo sprint sem aprovação humana.
