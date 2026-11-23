# Migração de Dados -- PontoJa (SQLite legado) -> Vornia (PostgreSQL 16 local)

Projeto: PontoJa -> Vornia (Workforce Intelligence)
Fase: 2 -- Migração de Dados
Data: 23 de novembro de 2026 (atualizado: destino PostgreSQL local + tabela `users`)
Responsável técnico: planner ECC
Referências: docs/DIAGNOSTICO.md (defeitos lógicos Sec.3), docs/PADROES-SEGURANCA.md (padrões JWT/Auth Sec.3-4), docs/PLANEJAMENTO-VORNIA.md, PontoJa/database/db.py (schema legado)

Base legada registrada em 23/11/2026 (leitura read-only): 26 usuarios, 3458 jornadas_processadas, 11036 registros_brutos, 2 saldos_usuario, 2 admins, 15 feriados, 1211 logs_sincronizacao, 4 ponto_auditoria, 0 alertas_jornada, 0 edicoes_manuais, 0 importacoes_csv, 0 backups_log.

---

## 1. Escopo

### Fase 1 -- Cadastros + Saldos (execução condicionada a Fase 2 por ~30 dias rodando do Vornia)

- usuarios (26) -- cadastro de funcionários
- feriados (15) -- cadastro de feriados
- configuracoes (20) -- chave/valor de configuração
- importacoes_csv (0) -- histórico de importações
- backups_log (0) -- log de backups
- saldos_usuario (2) -- saldo acumulado de banco de horas
- admins -> tabela `users` local + `company_users` (detalhe no Sec.7)

### Fase 2 -- Histórico Completo de Jornadas

- jornadas_processadas (3458)
- registros_brutos (11036) -- batidas brutas históricas
- alertas_jornada (0 no legado; montado pelo fluxo do Vornia)
- edicoes_manuais (0 no legado; montado pelo fluxo do Vornia)
- ponto_auditoria (4)
- logs_sincronizacao (1211) -- log operacional, volume aproximado
- Retrabalho de dados defeituosos: recompute/reprocessar pendentes antigos após 30d rodando (Sec.6, item 6).

Condição de execução: o marco de início da Fase 2 é T+30 dias (30 dias rodando do Vornia); a janela histórica do SQLite é o período de jornadas legadas pré-migração.

---

## 2. Mapeamento SQLite -> Vornia

- configuracoes -> configuracoes [Fase 1] (adiciona company_id)
- usuarios -> employees [Fase 1] (adiciona company_id; mapeamento employee_id via migration_ids)
- feriados -> feriados [Fase 1] (adiciona company_id)
- importacoes_csv -> importacoes_csv [Fase 1] (adiciona company_id)
- backups_log -> backups_log [Fase 1] (adiciona company_id)
- saldos_usuario -> saldos_usuario [Fase 1] (adiciona company_id; UNIQUE(company_id, usuario_id))
- admins -> tabela `users` local + `company_users` [Fase 1] (Sec.7)
- registros_brutos -> registros_brutos [Fase 2] (adiciona company_id; usuario_id via mapping)
- jornadas_processadas -> jornadas_processadas [Fase 2] (adiciona company_id; UNIQUE(company_id, usuario_id, data))
- alertas_jornada -> alertas_jornada [Fase 2] (adiciona company_id)
- edicoes_manuais -> edicoes_manuais [Fase 2] (admin_id via mapping)
- ponto_auditoria -> ponto_auditoria [Fase 2] (ponto_id, funcionario_id, alterado_por via mapping)
- logs_sincronizacao -> logs_sincronizacao [Fase 2] (adiciona company_id; volume aproximado 1211)
- app_sync_state -> nao migrar (estado runtime)
- sqlite_sequence -> nao migrar (controle interno)

Convenção: nomes mantêm os legados em português (consistente com docs/PADROES-SEGURANCA.md, ex.: jornadas_processadas). Todas as tabelas recebem NOT NULL company_id -- UUID válido fixo para esta base legada.

---

## 3. Estratégia de Extração

Script plano: vornia/scripts/pontoja_migracao.py (template, não código de produção).

1. Backup antes: PontoJa/exports/migracao/controlid_backup_20261130.db + MD5.
2. Legado read-only: sqlite3.connect("file:controlid.db?mode=ro", uri=True).
3. Por tabela: SELECT * -> JSON em PontoJa/exports/migracao/dump_<tabela>_20261130.json (chunk 10k linhas).
4. Planilha de verificação: migracao_checklist.md com contagens legado vs esperado (fecha na Sec.8).

---

## 4. Estratégia de Transformação

- Normalização global: trim strings; lower() de status/tipo/modo_compensacao; CPF -> somente dígitos; matricula trim; tipo_registro NULL -> 0.
- Datas -> ISO YYYY-MM-DD; data_hora -> ISO timestamptz.
- Horas -> string ISO HH:MM:SS; saldo_* -> DECIMAL; horas_trabalhadas NULL/vazio -> NULL.
- company_id: uuid4 fixo.
- Tabela de mapeamento: migration_ids(tabela, id_legado, id_vornia, data_migracao) -- usar-na para resolver employees.employee_id (Fase 1), edicoes_manuais.admin_id, ponto_auditoria.ponto_id/funcionario_id/alterado_por, registros_brutos.usuario_id (Fase 2).

---

## 5. Estratégia de Carga

1. Ordem: admins -> usuarios -> feriados -> configuracoes -> saldos_usuario -> registros_brutos -> jornadas_processadas -> alertas_jornada -> edicoes_manuais -> ponto_auditoria -> logs_sincronizacao.
2. Cliente asyncpg ou SQLAlchemy 2.0; batches de 500 linhas por upsert (INSERT ... ON CONFLICT DO UPDATE).
3. Sem duplicatas: UNIQUE(company_id, usuario_id, data) em jornadas_processadas; UNIQUE(company_id, usuario_id, data_hora) em registros_brutos; UNIQUE(company_id, usuario_id) em saldos_usuario.
4. Retry: 3 tentativas, backoff exponencial com jitter; log por batch: sucesso/atualizado/falhas.

---

## 6. Tratamento dos 40 Defeitos

Referência: docs/DIAGNOSTICO.md Sec.3.1-3.4. Classificação: Disposição na migração = o que os dados legados determinam.

1. Defeito 4 -- resolve_user_id retorna raw_code inexistente (código). Disposição: Excluído -- 149 registros_brutos órfãos (probe 23/11/2026: 149, 0 NULL usuario_id; jornadas/alertas/saldos sem orfãos).
2. Defeito 6 -- Exceções descartam registros sem log (código). Disposição: Reprocessado em Fase 2 -- 103 jornadas com entrada+saida vazios -> manter como estão, marcar warning e reprocessar a partir de registros_brutos.
3. Defeito 7 -- Fallback em lote loga warning -- perda silenciosa (código). Disposição: Recompute -- registros_intermediarios = COUNT(registros_brutos por usuario_id, data) na transformação.
4. Defeito 8 -- Feriado jornada_especial + saldo com bases diferentes (código). Disposição: Normalizado -- feriados.jornada_especial único; períodos em sábados descontados nas planilhas do Vornia. (0 duplicados por data no legado.)
5. Defeito 12 -- Edições manuais sem validação de formato de hora (código). Disposição: Normalizado -- valor_novo/valor_original -> NULL quando formato inválido; registro migra; legado intacto.
6. Defeito 22 -- saldo_liquido duplicado em dict (código). Disposição: Computado -- saldo_liquido calculado uma vez por período na ficha de verificação; dados legados preservados.
7. Defeito 23 -- Dias futuros marcados como falta (código). Disposição: Verificado em lote -- 0 jornadas com data > now; 0 status pendente com data futura.
8. Defeito 33 -- registros_intermediarios arbitrários (código). Disposição: Recomputado -- COUNT a partir de registros_brutos migrados (source of truth).
9. Defeito 34 -- Configurações de almoço de fontes diferentes (código). Disposição: Unificado -- fonte única (registros_brutos); NULL + reprocessar quando inexistente.
10. Defeito 35 -- ajustar_ponto permite valor_novo = "" (código). Disposição: Normalizado -- valor_novo NULL no legado Vornia; registro migrado preservado.

Nao corrigidos (código legado, sem dados afetados): 1, 2, 3, 5, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 24, 25, 26, 27, 28, 29, 30, 31, 32, 36, 37, 38, 39, 40.

Corrigidos/computados na migração (dados): 10 de 40 (4, 6, 7, 8, 12, 22, 23, 33, 34, 35). Deixados como estão por natureza de código: 30. Total declarado: 40.

---

## 7. Migração de Admins -> Tabela `users` Local

1. Sem senhas hardcoded: senha_hash legada NÃO é importada. Senhas substituídas por senhas aleatórias (`secrets.token_urlsafe`, 32 chars), entregues via vault dedicado (`PontoJa/exports/migracao/credentials/` -- marcar no `.gitignore`). Delivery seguro: entregue aos 2 usuários afetados por e-mail.
2. Criação direta no banco: para cada admin legado (`admin`, `Tecnova.adm` -- ambos ativos):
   - Inserir em `users` (`id`, `email`, `password_hash`, `is_active`, `email_verified`).
   - Inserir em `company_users` (`user_id`, `company_id`, `role = 'owner'` ou `'admin'`).
3. Mapeamento: `migration_ids("admins", id_legado, vornia_user_id, data_migracao)` -- usar-na para resolver `edicoes_manuais.admin_id` e `ponto_auditoria.alterado_por`.
4. Email de login: login legado "admin" -> email "admin@vornia.com.br"; "Tecnova.adm" -> "tecnova.adm@vornia.com.br" -- definir offline com a equipe (deliver via mail).
5. Duplicatas: se o e-mail já existe em `users`, reutilizar o `vornia_user_id` existente e garantir vínculo correto em `company_users`; escalar revisão manual antes da Fase 2.
6. Auditoria: `migracao_auditoria` (tabela, ids, user_count, data). Sem hashes, sem senhas. Sem alteração de `.env` legado.

---

## 8. Rollback e Validação

### Rollback
- Backup do legado ANTES da carga: controlid_backup_20261130.db + MD5 (Sec.3).
- Per batch: transação no PG; rollback per batch em falha.
- Rollback total do Vornia: TRUNCATE das tabelas migradas + reaplicar dump + re-criar admins no Auth.
- Credencial dos admins: senhas aleatórias (não reversíveis) -- rollback Auth: gerar nova senha aleatória + redirecionar por e-mail dos usuários afetados (documentado em migracao_auditoria).
- Nao modificar controlid.db pelo script.

### Validação
1. Contagens: contar por tabela legado vs Vornia -- esperado +/- 0; exceção listada (ponto_auditoria 4).
2. Referencial: ponto_auditoria.ponto_id -> jornadas_processadas.id (spot); edicoes_manuais.admin_id -> mapping.
3. Saldos: SUM(saldo_banco_horas) > 0; saldos_devedores consistentes (jornadas pendentes).
4. Jornadas: COUNT(jornadas) = 3458 legacy; pendentes = 636 (reprocessar Fase 2); inconsistencies = 7 (marcado warning).
5. company_id: DISTINCT = 1; NOT NULL em todas.
6. Anti-duplicatas: verificar constraints: 0 violações.
7. Recompute teste: saldo_devedor_horas por usuário período passado é derivável de jornadas completas (spot-check).
8. Diff: exports/migracao/validacao_fase2_20261130.json para revisão humana.

---

## 9. Cronograma

- Dia 0 (semana 1): Fase 0 -- preparação: dir de exports, backup de controlid.db + MD5, checklist legado registrado, revisão de mapeamento (checkpoint equipe).
- T+30d (semana 2): Fase 1 -- cadastros + saldos: usuarios (26), admins no Auth (2), feriados (15), configuracoes (20), saldos (2), importacoes_csv, backups_log; validação; log de auditoria.
- T+60d (semana 4): Fase 2 -- histórico completo: jornadas_processadas (3458), registros_brutos (11036), alertas_jornada, edicoes_manuais, ponto_auditoria (4), logs_sincronizacao (1211); recompute pendentes (636); recalculo de saldos finais; validação Fase 2; export de validacao_fase2.
- T+75d (semana 6): Cutover -- PontoJa desligado; Vornia ativo; entregáveis finais.

Entregáveis:
- docs/MIGRACAO-DADOS.md (este documento)
- vornia/scripts/pontoja_migracao.py (plano)
- PontoJa/exports/migracao/: controlid_backup_20261130.db + MD5, dump_*.json, migracao_checklist.md, migracao_auditoria.md
- logs/pontoja_migracao_20261130.log
