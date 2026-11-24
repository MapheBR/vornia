# Plano da FASE 3 — Implementação do MVP Vornia

**Versão:** 1.1 (GO para código — hospedagem Oracle Cloud Always Free)  
**Data:** 2026-11-23  
**Status:** Sprint 0 e Sprint 1 concluídos; Sprint 2 (colaboradores + configurações) pronto para revisão na branch `feat/sprint-2-employees-settings`

> **Decisão de hospedagem atualizada:** Oracle Cloud Always Free VM ARM (2 OCPU / 12 GB RAM) + Docker Compose + PostgreSQL 16 local + Caddy (HTTPS) + JWT próprio no FastAPI. **Custo: $0/mês.** Nenhum serviço que durma/pause ou viole termos comerciais será usado.

---

## Resumo das Lacunas Fechadas

| Lacuna | Ação | Status |
|---|---|---|
| 0 — Severidade RLS | Reclassificado como CRÍTICO; `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` adicionado e destacado em `SCHEMA-VORNIA.md` e `ARQUITETURA.md` | ✅ |
| 1 — Tempo por sprint | Definido: 1 sprint = 1 semana; MVP = 7 sprints (+ Sprint 8 pós-MVP); execução híbrida IA + revisão humana | ✅ |
| 2 — Identidade visual | Tokens Vornia no Sprint 0; header com logo existente no Sprint 1; site de apresentação no Sprint 8 (pós-MVP) | ✅ |
| 3 — Mapeamento 40 defeitos | Tabela completa em `docs/PLANEJAMENTO-VORNIA.md` Seção 5.1; todos os 5 críticos e 10 altos no MVP | ✅ |
| 4 — Transição PontoJa | Parágrafo de estratégia de coexistência e corte abaixo | ✅ |
| 5 — Custo estimado | Tabela realista Oracle Cloud Always Free abaixo | ✅ |

---

## 1. Duração das Sprints e Execução

- **1 sprint = 1 semana de trabalho**
- **MVP = 7 sprints (7 semanas)**
- **Sprint 8 = pós-MVP (site de apresentação + polish)**

### Quem executa

| Atividade | Responsável |
|---|---|
| Codificação inicial, testes, docs | IA (OpenCode + ECC) |
| Decisões de arquitetura, aprovações, QA | Humano (você) |
| Code review de segurança | Agente ECC `security-reviewer` |
| Code review geral | Agente ECC `code-reviewer` |
| Deploy em produção | Humano (você) aprova; IA executa pipeline |

### Marcos de aprovação humana obrigatória

- Fim do Sprint 0 (scaffold)
- Fim do Sprint 1 (auth + tenant)
- Fim do Sprint 3 (sync Control iD)
- Fim do Sprint 7 (MVP pronto para deploy em staging)

---

## 2. Identidade Visual

### Sprint 0 — Design tokens

Criar `src/styles/tokens.css` (ou equivalente no Next.js) com:

```css
:root {
  --vornia-azul-profundo: #172B40;
  --vornia-verde-suave: #A4D977;
  --vornia-cinza-claro: #F4F6F7;
  --vornia-branco: #FFFFFF;
}
```

### Sprint 1 — Header de autenticação

- Usar a logo existente na pasta do projeto (sem copiar do PontoJa, conforme regra).
- Aplicar tokens Vornia no header de login.

### Sprint 8 — Site de apresentação (pós-MVP)

- Hero "Workforce Intelligence"
- Tagline, navegação e página institucional
- Não faz parte do MVP operacional

---

## 3. Mapeamento dos 40 Defeitos para Sprints

Ver tabela completa em `docs/PLANEJAMENTO-VORNIA.md` Seção 5.1.

**Garantias:**
- **5 críticos:** Sprint 1, 3, 3, 3, 3
- **10 altos:** Sprint 1–6
- **6 itens:** Pós-MVP (Sprint 7)

Nenhum crítico ou alto fica para depois do MVP.

---

## 4. Transição do PontoJa

### Estratégia: coexistência controlada com corte gradual

O **PontoJa continua em produção** durante todo o build do Vornia. Não há big-bang no dia do deploy.

### Fases da transição

1. **Fase de build (Sprints 0–7):** PontoJa opera normalmente. Vornia é desenvolvido em staging.
2. **Fase de migração piloto (Sprint 6):** migração de cadastros + saldos do SQLite para PostgreSQL local em ambiente de homologação. Validar com dados reais (anonimizados se necessário).
3. **Fase de coexistência (2–4 semanas após deploy em produção):** ambos os sistemas operam. Usuários administradores usam Vornia para novas operações; PontoJa permanece como fallback e consulta histórica.
4. **Corte definitivo:** após 30 dias de Vornia rodando com dados reais e sem incidentes críticos, desativa-se o PontoJa. Histórico completo é migrado na Fase 2 (conforme `docs/MIGRACAO-DADOS.md`).

### Comunicação

- **Quem avisa:** responsável humano pelo projeto (você) comunica os administradores com antecedência mínima de 2 semanas.
- **Treinamento:** 1 sessão de 30 minutos para administradores antes do corte.
- **Rollback:** se houver incidente crítico no Vornia, volta-se ao PontoJa em até 24 horas.

---

## 5. Custo Estimado

### Opção selecionada: Oracle Cloud Always Free (controle total)

| Serviço | Camada | Custo | Limite / Nota |
|---|---|---|---|
| **Oracle Cloud Always Free VM** | VM ARM Ampere A1: 2 OCPU + 12 GB RAM | **$0/mês** | 2 instâncias, discos até 200 GB total (boot + block). Não dorme, não pausa. |
| **PostgreSQL 16** | Container Docker na mesma VM | **$0/mês** | Recursos compartilhados com a VM; backups manuais/script. |
| **Caddy** | Container Docker (reverse proxy + HTTPS) | **$0/mês** | Let's Encrypt automático; renovação automática. |
| **FastAPI + Next.js** | Containers Docker na mesma VM | **$0/mês** | Uso dentro da VM Always Free. |
| **Domínio** | Registro próprio (ex.: registro.br) | **~R$ 40/ano** | Único custo obrigatório; pode usar subdomínio do DuckDNS/Dynu gratuitamente para testes. |
| **Backup externo (futuro)** | Object Storage Oracle Free 10 GB ou S3 Glacier | **$0/mês** | 10 GB grátis na Oracle; opcional mas recomendado. |

### Tabela de cenários

| Cenário | Infra | Custo mensal estimado |
|---|---|---|
| **MVP inicial** | Oracle Free VM + Docker Compose + Caddy + PostgreSQL local | **$0** |
| **MVP estável** | Mesma VM + backups automáticos + domínio (rateado) | **$0–$5** |
| **Crescimento** | Oracle Free VM maior (paga) ou segunda VM + load balancer | **$20–100+** |

### Notas

- **Não há custo mensal obrigatório** para manter o sistema ligado 24/7 na camada Always Free.
- **Mitigação Idle Reclamation:** a conta Oracle deve ser convertida para **Pay As You Go (PAYG)**. Os recursos Always Free continuam $0, mas a VM deixa de estar sujeita à política de recuperação por inatividade.
- Cartão de crédito é exigido para verificação de identidade e billing; não há cobrança enquanto estiver dentro dos limites Always Free.
- Custos opcionais futuros: domínio próprio, backup off-site, monitoramento pago (UptimeRobot Pro, etc.), email transacional.

---

## 5.1. Risco Específico: Idle Reclamation da Oracle Cloud

### O risco

A Oracle Cloud Always Free pode recuperar (apagar) VMs que fiquem com **CPU, rede e memória abaixo de 20% por 7 dias**. Sistemas internos de baixo tráfego são vulneráveis.

### Mitigação adotada

**Upgrade da conta Oracle para Pay As You Go (PAYG).**

- Recursos Always Free continuam **$0/mês** dentro dos limites.
- A política de Idle Reclamation **não se aplica** a instâncias associadas a conta PAYG.
- Não gera cobrança automática; só paga se provisionar recursos fora do tier free.

### Ações obrigatórias antes do deploy em produção

- [ ] Conta Oracle convertida para PAYG.
- [ ] Alerta de billing configurado na Oracle (threshold $0 ou $1).
- [ ] Monitoramento de uptime externo configurado (UptimeRobot free ou similar).
- [ ] Backup automático do PostgreSQL configurado.

### Alternativa (não adotada como principal)

Keep-alive via cron a cada 6h chamando `/health`. Não é garantia absoluta e aumenta a complexidade operacional.

---

## 6. Ordem de Implementação (Sprints)

### Sprint 0 — Scaffold e Infraestrutura (1 semana)
1. Criar `.gitignore` (incluindo `.env`, `.env.*`, `__pycache__`, `node_modules`, `.next`, volumes Docker, credenciais) — **primeiro arquivo, antes do `git init`**.
2. Inicializar repositório Git.
3. Criar estrutura de pastas do monorepo Vornia.
4. Configurar `pyproject.toml`, `pytest`, `ruff`, `mypy`.
5. Configurar Next.js + Tailwind + shadcn/ui.
6. Criar tokens Vornia em `src/styles/tokens.css`.
7. Criar `docker-compose.yml` com PostgreSQL 16, Caddy, Redis, volumes e rede.
8. Criar `Dockerfile` para FastAPI e para Next.js.
9. Configurar variáveis de ambiente `.env.example` (sem secrets reais).
10. Documentar no `README.md` a necessidade de upgrade da conta Oracle para PAYG (mitigação Idle Reclamation).
11. Criar pipeline CI/CD mínimo (GitHub Actions).

### Sprint 1 — Migrations + Auth + Tenant (1 semana)
1. Migration inicial: `users`, `companies`, `company_users`, `employees`.
2. Implementar JWT próprio no FastAPI: login, refresh, logout, convite de usuários.
3. Implementar `get_db` dependency (pool, JWT, claims achatadas, RLS).
4. Primeiros endpoints: `GET /health`, `POST /auth/login`, `POST /companies`, `GET /me`.
5. Header de login com logo Vornia.
6. Testes de integração para auth e isolamento por tenant.

### Sprint 2 — Colaboradores e Configurações (1 semana)
1. CRUD de `employees`.
2. Tela no Next.js para gestão de colaboradores.
3. Settings service por empresa.
4. Testes de integração para CRUD.

### Sprint 3 — Importação e Sincronização (1 semana)
1. Upload e importação CSV de batidas.
2. Portar `controlid_api.py`.
3. Implementar endpoint `POST /sync/controlid`.
4. Corrigir sync incremental e salvaguarda contra lista vazia.
5. Testes com mock do Control iD.

### Sprint 4 — Processamento de Jornadas e Banco de Horas (1 semana)
1. Portar parser e processador de jornadas.
2. Endpoint `POST /sync/process`.
3. Portar `banco_horas_calculator.py`.
4. Tabela `processed_journeys` e `time_balances`.
5. Testes regressivos fortes.

### Sprint 5 — Dashboard e Exportações (1 semana)
1. Endpoint `GET /dashboard`.
2. Exportação Excel de jornadas.
3. Exportação PDF.
4. Tela de dashboard no Next.js.

### Sprint 6 — Auditoria, Edição Manual e Hardening (1 semana)
1. Edição manual com auditoria (`audit_logs`).
2. Rate limiting, CSP, headers de segurança.
3. `pip-audit`, `bandit`, `npm audit` passando.
4. Testes E2E críticos.

### Sprint 7 — Migração de Dados e Deploy em Staging (1 semana)
1. Script de migração de cadastros + saldos.
2. Deploy em staging na Oracle Cloud Always Free VM (Docker Compose + Caddy).
3. Validação com dados reais anonimizados.
4. Documentação final da FASE 3.

### Sprint 8 — Site de Apresentação (pós-MVP)
1. Hero "Workforce Intelligence".
2. Página institucional.
3. Polish de UI.

---

## 7. Estratégia de TDD

### Regra geral
**Teste antes do código.** Sempre.

Ciclo por feature:
1. Escrever teste que falha (RED).
2. Implementar código mínimo para passar (GREEN).
3. Refatorar (IMPROVE).
4. Verificar cobertura 80%+.

### Primeiras 3 features com teste antes

1. **Criação de empresa (`POST /companies`)**
   - Teste: usuário autenticado cria empresa; resposta contém `id` e `name`.
   - Por quê: valida auth, RLS, schema e endpoint end-to-end.

2. **Isolamento de tenant (`GET /employees`)**
   - Teste: usuário da empresa A não vê colaboradores da empresa B.
   - Por quê: valida RLS + `get_db` + claims achatadas.

3. **Processamento de jornadas**
   - Teste: 4 batidas em dia útil geram jornada completa com 8.8h.
   - Por quê: domínio core; regressão crítica.

### Tipos de testes

| Tipo | Onde | Exemplos |
|---|---|---|
| Unitários | `tests/unit/` | `time_utils`, parser puro, cálculos |
| Integração | `tests/integration/` | endpoints, repository, RLS |
| E2E | `tests/e2e/` | login → upload CSV → ver dashboard |

---

## 8. Estratégia de Branch

- **`main`**: protegida. Só merge via PR.
- **`feat/<nome>`**: novas funcionalidades.
- **`fix/<nome>`**: correções de bug.
- **`chore/<nome>`**: manutenção, config, docs.
- **`test/<nome>`**: adição/correção de testes isolados.

### Regras de merge

1. CI/CD passando.
2. Code review aprovado (agente ECC ou peer).
3. Cobertura mínima 80%.
4. Sem vulnerabilidades críticas/altas não mitigadas.
5. Commits em conventional commits (`feat:`, `fix:`, `refactor:`, `test:`, `chore:`).

---

## 9. CI/CD Mínimo

Pipeline obrigatório em todo PR:

### Backend (Python)
- `ruff check .`
- `ruff format --check .`
- `mypy vornia/`
- `pytest --cov=vornia --cov-report=term-missing`
- `pip-audit`
- `bandit -r vornia/`

### Frontend (Node)
- `eslint .`
- `tsc --noEmit`
- `prettier --check .`
- `npm test`

### Merge na main
- Deploy automático para staging (Oracle Cloud Always Free VM via Docker Compose + Caddy).
- Deploy para produção somente após aprovação manual.

---

## 10. Checklist de Conclusão do Sprint 0 (Aprovação Humana Obrigatória)

Antes de prosseguir para o Sprint 1, o Sprint 0 só será considerado concluído quando:

| # | Item | Evidência |
|---|---|---|
| 1 | `.gitignore` criado antes do `git init`, com `.env` e secrets | Arquivo no repo |
| 2a | `git init` + commit inicial local | `git log` |
| 2b | Criar repositório **PRIVADO** no GitHub (`vornia`) + `git remote add origin` + `git push -u origin main` + proteger branch `main` (PR obrigatório + CI verde) | URL do repo + print da branch protegida |
| 3 | Estrutura de pastas do monorepo criada | `tree -L 3` ou `find . -maxdepth 3 -type d` |
| 4 | `pyproject.toml` configurado (Python 3.11, FastAPI, pytest, ruff, mypy, asyncpg, PyJWT, passlib) | Arquivo no repo |
| 5 | Ambiente Python instalável via `pip install -e ".[dev]"` | Teste de instalação |
| 6 | Next.js + Tailwind + shadcn/ui configurados e buildável | `npm run build` |
| 7 | Localizar logo existente na pasta VORNIA, copiar para `branding/` e referenciar no `README.md` | Arquivo em `branding/` + menção no `README.md` |
| 8 | Tokens Vornia em `src/styles/tokens.css` | Arquivo no repo |
| 9 | `docker-compose.yml` com PostgreSQL 16, Caddy, Redis, volumes e rede | Arquivo no repo |
| 10 | `Dockerfile` para FastAPI e para Next.js | Arquivos no repo |
| 11 | `.env.example` sem secrets reais | Arquivo no repo |
| 12 | `README.md` com instruções de setup local e nota sobre upgrade Oracle PAYG | Arquivo no repo |
| 13 | Verificar/criar `AGENTS.md` (padrões Vornia) e `CONTRIBUTING.md` (fluxo de PR) na raiz | Arquivos no repo |
| 14 | Pipeline CI/CD mínimo (GitHub Actions) com lint/type/test placeholders | Arquivo no repo |
| 15 | Nenhum secret hardcoded no repo | `grep` por `sk-`, `password`, tokens |

**Só após você aprovar este checklist eu inicio o Sprint 1.**

---

## 11. Critério de "FASE 3 Concluída"

A FASE 3 será considerada concluída quando:

| Critério | Meta |
|---|---|
| Funcionalidades MVP entregues | Auth, tenant, employees, CSV, Control iD sync, jornadas, banco de horas, dashboard, exportação Excel, auditoria |
| Cobertura de testes | ≥ 80% |
| Pipeline CI/CD | Passando em todos os checks |
| Vulnerabilidades | Zero críticas/altas não mitigadas |
| Deploy | Staging funcional com health check e login |
| Documentação | `docs/FASE3-RESUMO.md` com features, cobertura e próximos passos |

### Milestone

> **"Vornia MVP — Core de ponto eletrônico funcional e seguro"**

---

## GO para Código

Após aprovação deste plano:
1. Iniciar **Sprint 0** (scaffold).
2. Parar no fim do Sprint 0 para revisão humana.
3. Só prosseguir para Sprint 1 após aprovação.
