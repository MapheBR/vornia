# LGPD — dados pessoais no Vornia

## Inventário de dados pessoais

| Tabela | Dados | Finalidade | Base legal (LGPD) |
|---|---|---|---|
| `companies` | nome, slug | Identificação do tenant (controlador) | Art. 7º, V (execução de contrato) |
| `employees` | nome, matrícula, **CPF**, **PIS**, cargo, departamento, jornada, foto, data de admissão | Gestão de ponto e folha | Art. 7º, V e XII (obrigações legais trabalhistas) |
| `raw_punches` | data/hora da batida, código do relógio, dados brutos AFD | Registro de jornada | Art. 7º, V e XII |
| `processed_journeys` | entradas/saídas, horas, status, observações | Cálculo de jornada e banco de horas | Art. 7º, V |
| `time_balances` | saldo mensal por colaborador | Banco de horas | Art. 7º, V |
| `refresh_tokens` | hash SHA-256 do token, user_id, expiração | Sessão do usuário | Art. 7º, V (segurança) |
| `audit_logs` | quem alterou, quando, motivo, antes/depois | Trilha de auditoria de edições | Art. 7º, V e X (legítimo interesse / prevenção à fraude) |

## Mascaramento

- CPF é exibido **completo apenas para `admin`/`manager`**; em listagens aparece mascarado (`***.***.***-**`) ou omitido.
- Nenhum CPF/PIS é escrito em logs; erros genéricos não expõem dados.
- `token` e `refresh_token` trafegam apenas em cookies `HttpOnly` — nunca em `localStorage`.

## Isolamento

Todas as tabelas de negócio usam `ENABLE` + `FORCE ROW LEVEL SECURITY` com policy por `company_id`.
O runtime usa role `vornia_app` (sem `BYPASSRLS`), e o bootstrap `vornia_auth` apenas em register/login.

## Direitos do titular

| Direito (art. 18) | Como atender no Vornia |
|---|---|
| Confirmação de existência | `GET /api/v1/employees/{id}` (admin/manager do tenant) |
| Acesso | `GET /api/v1/dashboard/summary` + exportações XLSX/PDF |
| Correção | `PATCH /api/v1/raw-punches/{id}` e `PATCH /api/v1/journeys/{id}` com `reason` obrigatório e auditoria |
| Anonimização/blockagem | Soft delete (`is_active=false`) em `employees` |
| Portabilidade | `GET /api/v1/exports/journeys.xlsx` |
| Informação sobre compartilhamento | Este documento + contrato de controlador |

## Retenção

- Batidas e jornadas: conforme obrigação trabalhista (5 anos mínimo, a confirmar com o jurídico).
- Refresh tokens: 7 dias.
- Audit logs: 5 anos (append-only).
- Backups: 7 dias (`scripts/backup-postgres.sh`).

## Incidentes

Qualquer vazamento deve ser comunicado ao DPO em até **72 horas** (art. 48). O `audit_logs` é a trilha primária para investigação.
