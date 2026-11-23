# Porte de Serviços do PontoJa para o Vornia

**Projeto:** Vornia — evolução do PontoJa  
**Stack destino:** FastAPI + Python 3.11, PostgreSQL 16 local, JWT próprio no FastAPI, Next.js  
**Modelo de tenancy:** multi-tenant-ready (`company_id` + RLS)  
**Data:** 2026-11-23 (atualizado para PostgreSQL local + JWT próprio)

---

## 1. Matriz de Porte

| Serviço (PontoJa) | Decisão | Arquivo destino no Vornia | Risco / Esforço | Observações |
|---|---|---|---|---|
| `data_processor.py` | **Reusar** | `vornia/domain/point/parser.py` + `vornia/domain/point/journey_processor.py` | Médio / Médio | Parser e agrupamento de batidas são sólidos; separar concerns |
| `controlid_api.py` | **Reusar** | `vornia/integrations/controlid/client.py` | Baixo / Baixo | Cliente HTTP maduro com retry/fallback; adaptar tipos |
| `sync_service.py` | **Refatorar** | `vornia/services/sync/orchestrator.py` + `records.py` + `users.py` | Alto / Alto | Corrigir sync incremental, lista vazia de usuários, IDs inexistentes |
| `banco_horas_calculator.py` | **Refatorar** | `vornia/domain/hours/balance_calculator.py` | Alto / Médio | Corrigir feriado/sábado/noturno; extrair lógica pura |
| `payroll_calculator.py` | **Refatorar** | `vornia/domain/payroll/calculator.py` | Médio / Médio | Validar precisão fiscal; integrar com novo schema |
| `benefits_calculator.py` | **Refatorar** | `vornia/domain/payroll/benefits.py` | Médio / Médio | Férias e 13º; revisar fórmulas contábeis |
| `clt_rules.py` | **Reusar** | `vornia/domain/clt/rules.py` | Baixo / Baixo | Regras CLT e alertas são portáveis |
| `holidays_service.py` | **Reusar** | `vornia/services/calendar/holidays.py` | Baixo / Baixo | Integração holidays + BrasilAPI; adicionar cache |
| `csv_importer.py` | **Refatorar** | `vornia/services/import/csv_importer.py` | Médio / Médio | Manter aliases de colunas; validação strict e streaming |
| `excel_exporter.py` | **Reusar** | `vornia/services/export/excel.py` | Baixo / Médio | Adaptar para novo schema; adicionar limites |
| `pdf_exporter.py` | **Reusar** | `vornia/services/export/pdf.py` | Baixo / Médio | Adaptar templates; adicionar limites |
| `time_utils.py` | **Reusar** | `vornia/domain/time/utils.py` | Baixo / Baixo | Utilitários puros; corrigir `hours_diff` |
| `validation_service.py` | **Reusar** | `vornia/domain/validation/network.py` | Baixo / Baixo | Validação de IP, porta, endpoint, hora |
| `status_analyzer.py` | **Refatorar** | `vornia/domain/point/status_analyzer.py` | Médio / Alto | Unificar com `data_processor` em única fonte de verdade |
| `auth_service.py` | **Reescrever** | `vornia/services/auth/dependencies.py` | Médio / Médio | Substituir por JWT próprio no FastAPI; manter vínculo tenant/role |
| `auth_guard.py` | **Reescrever** | `vornia/services/auth/guard.py` | Baixo / Baixo | Substituir proteção Flask por middleware FastAPI |
| `security_service.py` | **Descartar** | — | Baixo | Não usaremos Fernet para senhas; usar hashing bcrypt/Argon2 no JWT próprio |
| `settings_service.py` | **Refatorar** | `vornia/services/tenant/settings.py` | Médio / Médio | Carregar settings por empresa; tipar valores |
| `dashboard_service.py` | **Refatorar** | `vornia/services/analytics/dashboard.py` | Médio / Médio | Extrair queries SQL inline; usar repositories |
| `backup_service.py` | **Refatorar** | `vornia/services/backup/local.py` + `cloud.py` | Médio / Médio | Manter backup local; cloud opcional; validar path traversal |
| `sync_lock.py` | **Reusar** | `vornia/services/sync/lock.py` | Baixo / Baixo | Cross-platform file lock; futuro: advisory lock Postgres |
| `sync_coordinator.py` | **Refatorar** | `vornia/services/sync/coordinator.py` | Baixo / Médio | Substituir lock de arquivo por transação + estado no banco |
| `sync_state_store.py` | **Refatorar** | `vornia/services/sync/state.py` | Médio / Médio | Resolver race condition; usar banco com transação |
| `scheduler_service.py` | **Reescrever** | `vornia/jobs/scheduler.py` | Médio / Alto | Substituir APScheduler inline por scheduler externo (Celery/Redis ou cron local) |
| `salario_minimo_service.py` | **Reusar** | `vornia/services/external/salario_minimo.py` | Baixo / Baixo | APIs BCB/IBGE; adicionar cache |

---

## 2. Justificativa por Grupo

### Reaproveitável diretamente (8 serviços)

`data_processor` (parser), `controlid_api`, `clt_rules`, `holidays_service`, `excel_exporter`, `pdf_exporter`, `time_utils`, `validation_service`, `salario_minimo_service`.

Esses serviços têm pouco ou nenhum acoplamento com Flask/SQLite e representam o conhecimento de domínio mais valioso do PontoJa.

### Refatorar (11 serviços)

`sync_service`, `banco_horas_calculator`, `payroll_calculator`, `benefits_calculator`, `csv_importer`, `status_analyzer`, `settings_service`, `dashboard_service`, `backup_service`, `sync_coordinator`, `sync_state_store`.

Boa lógica de negócio, mas precisam de:
- Adaptação ao novo schema (`company_id`, UUIDs, tipos).
- Correção de defeitos lógicos conhecidos.
- Separação de concerns (sync, status, dashboard).
- Tipagem e testes.

### Reescrever (3 serviços)

`auth_service.py`, `auth_guard.py`, `scheduler_service.py`.

- Auth: substituído por JWT próprio no FastAPI + middleware.
- Scheduler: APScheduler inline não escala; usar scheduler externo.

### Descartar (1 serviço)

`security_service.py`: criptografia Fernet deixa de fazer sentido com JWT próprio. Senhas são hasheadas com bcrypt/Argon2; segredos de integração (Control iD) usarão env vars.

---

## 3. Serviços Críticos que Precisam de Testes Regressivos

| Serviço | Por quê |
|---|---|
| `data_processor.py` | Parser de AFD e agrupamento de batidas são sensíveis a formatos |
| `banco_horas_calculator.py` | Impacto financeiro direto em folha de pagamento |
| `sync_service.py` | Pode perder batidas ou desativar funcionários em massa |
| `controlid_api.py` | Integração com hardware; regressões difíceis de detectar |
| `payroll_calculator.py` | Cálculos trabalhistas têm validação fiscal |

---

## 4. Serviços Dependentes de Flask/SQLite Específicos

| Serviço | Dependência | Ação |
|---|---|---|
| `auth_service.py` | Flask `session`, Werkzeug | Reescrever |
| `auth_guard.py` | Flask `before_request` | Reescrever como middleware FastAPI |
| `settings_service.py` | SQLite + `current_app` | Refatorar para repository PostgreSQL |
| `dashboard_service.py` | SQLite + queries inline | Refatorar para repository |
| `backup_service.py` | Paths Flask/Windows | Refatorar com `pathlib` + validação |
| `scheduler_service.py` | APScheduler + Flask app context | Reescrever |
| `sync_service.py` | SQLite `get_connection` | Refatorar para asyncpg/repository |

---

## 5. Recomendação de Ordem de Porte

### Fase 1 — Fundação do domínio
1. `time_utils.py`
2. `validation_service.py`
3. `clt_rules.py`
4. `holidays_service.py`

### Fase 2 — Parser e processamento
5. `data_processor.py`
6. `csv_importer.py`

### Fase 3 — Integração e sync
7. `controlid_api.py`
8. `sync_lock.py`
9. `sync_coordinator.py` / `sync_state_store.py`
10. `sync_service.py`

### Fase 4 — Cálculos
11. `banco_horas_calculator.py`
12. `payroll_calculator.py`
13. `benefits_calculator.py`
14. `status_analyzer.py` (unificado)

### Fase 5 — Infraestrutura e utilitários
15. `settings_service.py`
16. `dashboard_service.py`
17. `backup_service.py`
18. `excel_exporter.py` / `pdf_exporter.py`
19. `salario_minimo_service.py`

### Fase 6 — Auth e scheduler (novos)
20. `auth_service.py` / `auth_guard.py` (reescrever)
21. `scheduler_service.py` (reescrever)

---

## 6. Serviços que Não Serão Portados

| Serviço | Motivo |
|---|---|
| `security_service.py` | JWT próprio substitui criptografia de senhas; integrações usarão env vars |

---

**Próximo passo:** `docs/MIGRACAO-DADOS.md` — estratégia de migração do SQLite legado.
