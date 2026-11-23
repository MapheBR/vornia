# Diagnóstico do Projeto Legado PontoJa

**Projeto:** PontoJa → Vornia (Workforce Intelligence)  
**Fase:** 1 — Diagnóstico (somente leitura)  
**Data:** 2026-11-23  
**Metodologia:** Análise estática com agentes ECC (`code-explorer`, `code-reviewer`, `security-reviewer`)

---

## 1. Resumo Executivo

O `PontoJa` é uma aplicação Flask 3.0.2 + SQLite 3 para gestão de ponto eletrônico, com sincronização via API Control iD, processamento de jornadas, cálculo de banco de horas e exportação de relatórios. A base de código possui regras de negócio maduras que podem ser reaproveitadas no Vornia, mas apresenta **defeitos lógicos graves**, **riscos de segurança críticos** e **duplicação de responsabilidades** que impedem o uso direto em produção.

| Dimensão | Status |
|---|---|
| Arquitetura | Legível, mas monolítica e acoplada ao Flask/SQLite |
| Segurança | **Insegura para produção** — 23 riscos (4 críticos): chaves default, senhas default, CSRF isento |
| Lógica de negócio | **40 defeitos lógicos** identificados, 5 deles críticos |
| Testabilidade | Testes existentes, mas baixa cobertura em rotas administrativas |
| Reaproveitamento | Serviços de domínio são o principal ativo reutilizável |

---

## 2. Estrutura e Arquitetura

### 2.1 Stack Tecnológica

- **Python 3.11**
- **Flask 3.0.2** + Flask-WTF 1.2.2 (CSRF)
- **SQLite 3** (`database/controlid.db`)
- **APScheduler 3.11.2** para sincronização/backup agendados
- **Frontend:** Jinja2 + Bootstrap 5 + Chart.js
- **Frontend moderno (não integrado):** React 19 + TypeScript em `frontend/`

### 2.2 Dependências de Produção

```text
Flask==3.0.2
Flask-WTF==1.2.2
requests==2.32.3
openpyxl==3.1.5
APScheduler==3.11.2
python-dotenv==1.0.1
cryptography==46.0.5
holidays==0.63
reportlab==4.2.5
```

### 2.3 Pontos de Entrada

- **`app.py:create_app()`** — factory Flask
- **Servidor:** `python app.py` na porta 5000
- **Blueprints:** 13 módulos sob `routes/`
- **Scheduler:** `services/scheduler_service.py`
- **Scripts CLI:** `reprocessar_jornadas.py`, `scripts/recalcular_jornadas.py`

### 2.4 Blueprints HTTP

| Blueprint | Prefixo | Responsabilidade |
|---|---|---|
| `auth` | `/` | Login/logout web |
| `admin` | `/admin` | Login JSON, edição manual, auditoria, ajuste de ponto |
| `dashboard` | `/` | Dashboard, métricas, gráficos |
| `jornadas` | `/jornadas` | Listagem, filtros, exportação Excel/PDF/folha |
| `usuarios` | `/usuarios` | Colaboradores, banco de horas individual |
| `calculos` | `/calculos` | APIs de salário mínimo, compensação, férias, 13º |
| `sincronizacao` | `/sincronizacao` | Sincronização Control iD |
| `importacao` | `/importacao` | Upload CSV de ponto eletrônico |
| `configuracoes` | `/configuracoes` | Configuração do dispositivo e scheduler |
| `backup` | `/backup` | Backup local/nuvem |
| `feriados` | `/feriados` | CRUD e sync de feriados |
| `health` | `/health` | Health check |

### 2.5 Fluxo de Dados Principal

```
Importação (Control ID / CSV)
    ↓
Parsing e normalização (services/data_processor.py)
    ↓
Processamento de jornadas (services/sync_service.py)
    ↓
Cálculo de banco de horas (services/banco_horas_calculator.py)
    ↓
Exportação Excel/PDF (services/excel_exporter.py, services/pdf_exporter.py)
```

### 2.6 Entidades do Banco (SQLite)

| Tabela | Propósito |
|---|---|
| `configuracoes` | Chave/valor de configuração |
| `usuarios` | Colaboradores sincronizados |
| `registros_brutos` | Batidas brutas de ponto |
| `jornadas_processadas` | Jornadas diárias calculadas |
| `logs_sincronizacao` | Log de sincronizações |
| `app_sync_state` | Estado da sincronização (lock) |
| `feriados` | Feriados nacionais/municipais |
| `alertas_jornada` | Alertas de violações CLT |
| `saldos_usuario` | Saldo acumulado de banco de horas |
| `importacoes_csv` | Histórico de importações CSV |
| `backups_log` | Log de backups |
| `admins` | Administradores |
| `edicoes_manuais` | Log de edições manuais |
| `ponto_auditoria` | Auditoria imutável de ajustes |

### 2.7 Integrações Externas

| Integração | Arquivo | Detalhes |
|---|---|---|
| Control iD | `services/controlid_api.py` | Relógio de ponto — sessão, retry, fallback de firmware |
| BrasilAPI | `services/holidays_service.py` | Feriados nacionais |
| holidays (lib) | `services/holidays_service.py` | Feriados offline |
| BCB / IBGE | `services/salario_minimo_service.py` | Salário mínimo vigente |
| Google Drive / OneDrive | `services/backup_service.py` | Backup em nuvem (opcional) |

---

## 3. Defeitos Lógicos por Severidade

**Total identificados: 40**

### 3.1 Crítico (5)

| # | Problema | Arquivo | Impacto |
|---|---|---|---|
| 1 | Recálculo em ajuste manual usa `jornada_dict` lido **antes** da atualização | `routes/admin.py:488-490, 502-525` | Ajustes manuais não refletem no cálculo de horas e saldo |
| 2 | Sincronização incremental consulta `last_sync` mas **não o envia** para o dispositivo; filtra localmente com comparação lexicográfica de strings | `services/sync_service.py:371-411` | Baixa todos os registros a cada sync; risco de duplicação/perda com fusos |
| 3 | `sync_users` desativa todos os usuários que não estiverem na lista do dispositivo; sem salvaguarda para lista vazia/parcial | `services/sync_service.py:52-117` | Funcionários podem ser desativados em massa |
| 4 | `resolve_user_id` retorna `raw_code` inexistente quando não encontra usuário | `services/sync_service.py:167` | Cria registros órfãos e jornadas não processáveis |
| 5 | `datetime.now()` sem tz subtraído de aware datetime quebra processamento | `services/data_processor.py:241-249` | TypeError em jornadas do dia atual com fusos horários |

### 3.2 Alto (10)

| # | Problema | Arquivo | Impacto |
|---|---|---|---|
| 6 | Exceções genéricas descartam registros sem log | `services/data_processor.py:85` | Registros válidos desaparecem sem rastro |
| 7 | Fallback de inserção em lote apenas loga warning; registros perdidos | `services/sync_service.py:196-216` | Perda silenciosa de batidas |
| 8 | Feriado com jornada especial calcula extras e saldo com bases diferentes | `services/banco_horas_calculator.py:167-188, 221-227` | Banco de horas inconsistente |
| 9 | Excesso de sábado não é descontado de `horas_trabalhadas` antes do payroll | `services/banco_horas_calculator.py:105-121, 199-231` | Possibilidade de pagamento duplicado |
| 10 | Cálculo noturno incrementa 0.5h e verifica apenas hora inteira | `services/banco_horas_calculator.py:305-331` | Horas noturnas imprecisas |
| 11 | SQL injection via f-string em campo de jornada (mesmo com whitelist) | `routes/admin.py:151-152, 488-489` | Fragilidade de segurança/manutenção |
| 12 | Edições manuais não validam formato de hora | `routes/admin.py:104-176` | Valores inválidos persistidos |
| 13 | Recálculo ocorre após commit da transação | `routes/admin.py:171-176` | Estado inconsistente se reprocessamento falhar |
| 14 | `full_sync` ignora configuração `SYNC_INCLUDE_IMAGES` | `routes/sincronizacao.py:202-211` | Fotos nunca sincronizadas via rota completa |
| 15 | Senhas de admin default hardcoded no banco | `database/db.py:246-261` | Risco de segurança operacional grave |

### 3.3 Médio (17)

| # | Problema | Arquivo |
|---|---|---|
| 16 | Inferência de almoço inventa intervalo fixo com apenas 2 batidas | `services/data_processor.py:132-149` |
| 17 | Primeira batida após hora de corte é classificada como saída para almoço | `services/data_processor.py:119-124` |
| 18 | 4+ batidas assumem padrão rígido sem tolerância a esquecimentos | `services/data_processor.py:150-154` |
| 19 | Heurística de 3 batidas confunde volta tarde com saída | `services/data_processor.py:156-175` |
| 20 | Normalização de timezone usa `replace(tzinfo=...)` em vez de conversão | `services/data_processor.py:181-184` |
| 21 | `hours_diff` assume virada de dia para horário invertido | `services/time_utils.py:41-45` |
| 22 | `acumular_periodo` contém chave `saldo_liquido` duplicada | `services/banco_horas_calculator.py:443, 457` |
| 23 | Dias futuros marcados como falta | `services/data_processor.py:286-291` |
| 24 | Exportação PDF sem limite de registros | `routes/jornadas.py:145-212` |
| 25 | Rota `exportar_folha` usa acumulador sem `dt_ini`/`dt_fim` | `routes/jornadas.py:215-242` |
| 26 | `clear_running_if_stale` com possível race condition | `services/sync_state_store.py:33-51` |
| 27 | `login_required` expõe traceback/mensagens internas | `routes/admin.py:30-43` |
| 28 | `/sincronizacao/testar` sem proteção contra repetição | `routes/sincronizacao.py:95-106` |
| 29 | `verificar_faltas` não valida formato de datas | `routes/usuarios.py:39-57` |
| 30 | `listar` usuários não trata `page` inválido | `routes/usuarios.py:63` |
| 31 | Status analyzer não considera dia em andamento com saída para almoço | `services/status_analyzer.py:105, 118-126` |
| 32 | `parse_timedelta_str` ignora microssegundos | `services/time_utils.py:21-38` |

### 3.4 Baixo (8)

| # | Problema | Arquivo |
|---|---|---|
| 33 | `registros_intermediarios` calculado arbitrariamente | `services/data_processor.py:302` |
| 34 | Configurações de almoço inferidas vêm de fontes diferentes | `services/sync_service.py:260-265` |
| 35 | `ajustar_ponto` permite `valor_novo = ""` sem validação | `routes/admin.py:451-456, 490` |
| 36 | `exportar` não sanitiza `usuario` para LIKE | `routes/jornadas.py:86-89, 158-160` |
| 37 | `datetime.strptime(day, "%Y-%m-%d")` redundante | `services/data_processor.py:107` |
| 38 | `sync_images` não registra detalhes de falha total | `services/sync_service.py:324-347` |
| 39 | `listar_dias_com_problemas` com `except:` vazio | `services/status_analyzer.py:239-243` |
| 40 | Assinaturas de `status_analyzer` poderiam usar `Optional` | `services/status_analyzer.py:15-17` |

---

## 4. Riscos de Segurança por Severidade

**Total identificados: 23**

### 4.1 Crítico (4)

| # | Risco | Arquivo | Impacto |
|---|---|---|---|
| 1 | `SECRET_KEY` e `ENCRYPTION_KEY` default hardcoded | `config.py:10-11, 46, 54` | Forja de sessão, decriptação de credenciais do relógio |
| 2 | Senhas de administrador default criadas automaticamente (`admin`/`admin123`, `Tecnova.adm`/`Tec.palmas3225@`) | `database/db.py:242-261` | Comprometimento total do sistema |
| 3 | CSRF desabilitado em `admin_bp` e `sincronizacao_bp` | `app.py:70-73` | Ações administrativas induzidas, alteração de registros de ponto |
| 4 | Senha default do Control iD (`admin`) | `config.py:51` | Acesso não autorizado ao dispositivo de ponto |

### 4.2 Alto (8)

| # | Risco | Arquivo | Impacto |
|---|---|---|---|
| 5 | Dependências com CVEs (`requests`, `Flask`, `APScheduler`) | `requirements.txt` | Vazamento de credenciais, cache de respostas sensíveis, RCE potencial |
| 6 | Formulários POST sem token CSRF | vários templates | Ações induzidas em backup, importação, feriados, configurações |
| 7 | Ausência de rate limiting no login | `routes/auth.py:22-41`, `routes/admin.py:46-63` | Ataque de força bruta |
| 8 | Cookie de sessão sem flag `Secure` | `app.py:29-31` | Roubo de sessão via MITM |
| 9 | Validação de SSL desabilitada por padrão | `config.py:53`, `services/controlid_api.py:23, 41-42` | MITM entre app e relógio de ponto |
| 10 | Path traversal na restauração de backup | `routes/backup.py:37-44`, `services/backup_service.py:33-39` | Sobrescrita de arquivos arbitrários |
| 11 | Exposição de PII no repositório (`192.168.1.38.har`) | raiz do projeto | Violação de privacidade/LGPD |

### 4.3 Médio (7)

| # | Risco | Arquivo |
|---|---|---|
| 12 | Concatenação SQL de colunas em rotas administrativas | `routes/admin.py:151-152`, `routes/admin.py:488-489` |
| 13 | Exposição de `db_path` e erros no `/health` público | `routes/health.py:13-25` |
| 14 | Exposição de detalhes de erro em rotas administrativas | `routes/admin.py:30-44` |
| 15 | Validação insuficiente de datas em filtros | `services/auth_service.py:161-166`, `routes/usuarios.py:42-57` |
| 16 | CORS não configurado explicitamente | `app.py` |
| 17 | `APScheduler` com CVE de deserialização insegura | `requirements.txt` |
| 18 | Risco de debug ativo em produção (`FLASK_DEBUG` não bloqueado) | `.env.example:4`, `app.py` |
| 18 | Risco de debug ativo em produção (`FLASK_DEBUG` não bloqueado) | `.env.example:4`, `app.py` |

### 4.4 Baixo (4)

| # | Risco | Arquivo |
|---|---|---|
| 18 | Mensagens de query string renderizadas em templates | `templates/backup.html`, `templates/importacao.html` |
| 19 | Tipo de feriado não validado contra whitelist | `routes/feriados.py:23, 57` |
| 20 | Template `ajustar_ponto.html` com conteúdo duplicado/corrompido | `templates/ajustar_ponto.html:178-252` |
| 21 | `/calculos/api/salario-minimo` sem validação/rate limiting | `routes/calculos.py:21-26` |

### 4.5 Detalhamento de Riscos Específicos

#### CORS não configurado explicitamente
- **Arquivo:** `app.py` (ausência de `flask-cors` ou headers manuais)
- **Descrição:** A aplicação não define uma política de CORS. Embora a maioria das rotas use sessão, endpoints JSON (`/health`, `/calculos/api/*`, `/admin/*`) podem receber requisições cross-origin inesperadas.
- **Impacto:** Ataques CSRF cross-origin, vazamento de dados em APIs abertas.
- **Mitigação:** Configurar CORS com whitelist explícita de origins; manter autenticação por sessão + CSRF para rotas baseadas em navegador.

#### Debug em produção
- **Arquivos:** `.env.example:4` (`FLASK_DEBUG=0` como string, não validado), `app.py` (sem bloqueio explícito)
- **Descrição:** Não há mecanismo que impeça `FLASK_DEBUG=1` ou `FLASK_ENV=development` em produção. Debug ativo expõe stack traces detalhados e recarregamento automático.
- **Impacto:** Vazamento de código/caminhos internos, RCE potencial via Werkzeug debugger, negação de serviço.
- **Mitigação:** Forçar `FLASK_DEBUG=False` quando `FLASK_ENV=production`; rejeitar subida em modo debug em ambientes produtivos.

#### Dependências desatualizadas (pip-audit / safety)
- **Arquivo:** `requirements.txt`
- **Descrição:** Não há verificação automática de vulnerabilidades no CI/CD. Pacotes como `requests==2.32.3`, `Flask==3.0.2` e `APScheduler==3.11.2` possuem CVEs conhecidos.
- **Impacto:** Vazamento de credenciais `.netrc`, cache de respostas sensíveis, deserialização insegura.
- **Mitigação:**
  - Integrar `pip-audit` ou `safety check` no CI/CD.
  - Atualizar `requests>=2.32.4`, `Flask>=3.1.x`.
  - Avaliar atualização do `APScheduler` e evitar serialização de dados não confiáveis.
  - Congelar versões apenas após validação de segurança.

---

## 5. Avaliação de Reaproveitamento

### 5.1 Reaproveitável Diretamente

| Componente | Arquivo(s) | Justificativa |
|---|---|---|
| Parser de registros de ponto | `services/data_processor.py` | Lida com AFD, ISO timestamps, PIS, duplicatas |
| Cliente Control iD | `services/controlid_api.py` | Sessão, retry, fallback de firmware |
| Cálculo de jornadas | `services/data_processor.py::process_jornadas()` | Lógica de 4 batidas, inferência de almoço, sábado, feriado |
| Calculadora de banco de horas | `services/banco_horas_calculator.py` | Saldo dia/período, modo compensação |
| Regras CLT | `services/clt_rules.py` | Limites legais, alertas, base legal |
| Feriados | `services/holidays_service.py` | Integração holidays + BrasilAPI |
| Exportadores | `services/excel_exporter.py`, `services/pdf_exporter.py` | Excel/PDF já funcionais |
| Utilitários de tempo | `services/time_utils.py` | parse_time, parse_timedelta_str, hours_diff |
| Validação de configuração | `services/validation_service.py` | IP, porta, endpoint, hora |
| Lock de sincronização | `services/sync_lock.py` | Cross-platform file lock |
| Backup local | `services/backup_service.py` (parte local) | Cópia do SQLite com rotação |

### 5.2 Reaproveitável com Refatoração

| Componente | Observação |
|---|---|
| `services/status_analyzer.py` | Unificar com `data_processor.py` em única fonte de verdade |
| `services/auth_service.py` | Separar autenticação de regras de edição |
| `services/payroll_calculator.py` | Validar precisão fiscal do Vornia |
| `services/benefits_calculator.py` | Validar fórmulas contábeis |
| `services/dashboard_service.py` | Extrair queries SQL inline, normalizar parsing de horas |

### 5.3 Descartar ou Reescrever

| Componente | Motivo |
|---|---|
| UI Flask/Jinja2 (`templates/`, `static/`) | Obsoleta para Vornia |
| `frontend-clean/`, `frontend/` | Não integrados, placeholder |
| `Organizador/` | Projeto paralelo/incompleto |
| `config/settings.json` + tabela `configuracoes` | Dupla fonte de config |
| Credenciais default em `config.py`, `database/db.py` | Risco crítico |
| SQLite legado (`database/controlid.db`, `data/*.db`) | Avaliar PostgreSQL/SQLAlchemy |
| Scheduler APScheduler inline | Não escala horizontalmente |
| Upload nuvem Google/OneDrive | Opcional, depende de stack |
| Lógica de edição manual em `routes/admin.py` | Acoplada ao Flask/SQLite |

---

## 6. Recomendações Prioritárias

### Antes de qualquer reutilização

1. **Não copiar credenciais, chaves ou segredos** do PontoJa para o Vornia.
2. **Não copiar a logo** do PontoJa sem aprovação explícita.
3. **Não usar** `config.py`, `database/db.py` ou `.env.example` como base sem revisão de segurança.

### Correções críticas no legado (se o PontoJa continuar rodando)

1. Remover todos os defaults de `SECRET_KEY`, `ENCRYPTION_KEY`, senhas de admin e senha do Control iD.
2. Remover `csrf.exempt(admin_bp)` e `csrf.exempt(sincronizacao_bp)`.
3. Corrigir `routes/admin.py:ajustar_ponto` para recalcular com o `valor_novo`.
4. Implementar sincronização incremental real passando `last_sync` para o Control iD.
5. Adicionar salvaguarda em `sync_users` contra lista vazia/parcial.
6. Remover o arquivo `192.168.1.38.har` do repositório e do histórico Git.
7. Atualizar dependências com CVEs conhecidos.

### Para o novo projeto Vornia

1. Extrair camada de domínio pura (sem Flask, sem SQLite).
2. Unificar motor de cálculo de status/horas em uma única fonte de verdade.
3. Construir API REST com validação estrita (Pydantic/Marshmallow).
4. Usar PostgreSQL + SQLAlchemy/Alembic.
5. Implementar autenticação moderna (JWT/OAuth2 ou sessão segura).
6. Adicionar rate limiting, CSP, headers de segurança.
7. Migrar testes para a nova stack com cobertura mínima de 80%.

---

## 7. Riscos Abertos e Próximos Passos

### Riscos que precisam de decisão

| Risco | Decisão Necessária |
|---|---|
| Qual stack do Vornia? | FastAPI/Node/Next.js? PostgreSQL/Supabase? |
| Manter compatibilidade com Control iD? | Sim — cliente já existe e é reaproveitável |
| Frontend do Vornia será SPA separado? | Sim — descartar templates Jinja2 |
| Autenticação será sessão ou JWT? | JWT recomendado para API + frontend moderno |
| Hospedagem local, cloud ou híbrida? | Afeta scheduler, backup e segurança |
| Importação de dados históricos do SQLite? | Requer migração controlada dos dados |

### O que falta para completar a FASE 1

- [x] Mapeamento de arquitetura
- [x] Identificação de defeitos lógicos
- [x] Identificação de riscos de segurança
- [x] Avaliação de reaproveitamento
- [x] Consolidação em `docs/DIAGNOSTICO.md`

### Próxima fase sugerida (FASE 2)

**Planejamento da arquitetura do Vornia:**

1. Definir stack tecnológica final.
2. Desenhar a nova arquitetura (camadas, API, banco, frontend).
3. Mapear quais serviços do PontoJa serão portados, refatorados ou reescritos.
4. Criar o primeiro esboço do schema de dados do Vornia.
5. Definir plano de migração de dados (se aplicável).
6. Estabelecer padrões de segurança e qualidade desde o início.

---

## 8. Agentes ECC Utilizados

| Agente | Função | Escopo Analisado |
|---|---|---|
| `code-explorer` | Mapeamento de arquitetura, pontos de entrada, fluxo de dados, integrações e reaproveitamento | `app.py`, `config.py`, `requirements.txt`, `database/db.py`, `routes/`, `services/`, `templates/`, `static/`, `frontend/`, `Organizador/` |
| `code-reviewer` | Defeitos lógicos, race conditions, cálculos incorretos, edge cases, tratamento de erros | `services/data_processor.py`, `services/sync_service.py`, `services/banco_horas_calculator.py`, `services/time_utils.py`, `services/status_analyzer.py`, `routes/admin.py`, `routes/jornadas.py`, `routes/sincronizacao.py`, `routes/usuarios.py` |
| `security-reviewer` | Auditoria de segurança: secrets, autenticação, autorização, SQL/XSS/CSRF, configurações, dependências, PII | `config.py`, `database/db.py`, `app.py`, `routes/auth.py`, `routes/admin.py`, `routes/backup.py`, `routes/calculos.py`, `routes/sincronizacao.py`, `routes/usuarios.py`, `routes/health.py`, `routes/feriados.py`, `services/controlid_api.py`, `services/auth_service.py`, `services/security_service.py`, `templates/*.html`, `requirements.txt`, `192.168.1.38.har` |
| `spec-miner` | Não acionado nesta fase | Reservado para onboarding adicional de brownfield se necessário em fases futuras |

---

## 9. Checklist de Segurança Consolidada

| Item | Status |
|---|---|
| Nenhuma chave/segredo hardcoded | ❌ |
| Senhas armazenadas com hash forte | ✅ (Werkzeug) |
| SQL injection prevention (parametrizado) | ⚠️ Parcial (colunas concatenadas) |
| XSS prevention (autoescape) | ✅ |
| CSRF protection em todas as rotas mutáveis | ❌ |
| Rate limiting em login | ❌ |
| HTTPS + cookies Secure/HttpOnly/SameSite | ⚠️ Parcial |
| Validação de entrada em formulários | ⚠️ Parcial |
| Dependências sem CVEs conhecidos | ❌ |
| Scan de dependências (pip-audit / safety) no CI/CD | ❌ |
| PII/PHI não versionado | ❌ |
| Error messages genéricas | ⚠️ Parcial |
| CORS configurado explicitamente | ❌ |
| Debug bloqueado em produção | ❌ |
| Path traversal validado | ❌ |

---

**Fim do diagnóstico da FASE 1.**
