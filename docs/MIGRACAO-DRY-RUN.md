# Resultado do dry-run — migração PontoJa → Vornia

## Execução real (servidor local da Tecnova)

**Data:** 26/11/2026  
**Servidor:** `DESKTOP-HC1CKS3` (Tailscale `100.110.105.86`)  
**Fonte:** `PontoJa/database/controlid.db` (3.211.264 bytes, `LastWriteTime` 13/11/2026 18:00:35 — **inalterado**, aberto em `mode=ro`)  
**Destino:** PostgreSQL do Vornia em Docker Compose (migrations `014 (head)`)

Comando executado (somente leitura, nenhuma escrita):

```bash
python scripts/migrate_pontoja.py --sqlite PontoJa/database/controlid.db --dry-run
```

Saída obtida:

```text
=== RELATÓRIO DE MIGRAÇÃO (dry-run) ===
OK: usuarios: esperado=26, encontrado=26
OK: feriados: esperado=15, encontrado=15
OK: configuracoes: esperado=20, encontrado=20
OK: saldos_usuario: esperado=2, encontrado=2
OK: admins: esperado=2, encontrado=2

=== CONTAGEM POR TABELA DESTINO ===
companies: 1 linha(s)
employees: 26 linha(s)
holidays: 15 linha(s)
settings: 20 linha(s)
time_balances: 2 linha(s)
users: 2 linha(s)
company_users: 2 linha(s)

Nenhuma escrita realizada (--dry-run).
```

**Resultado: ZERO divergências.** As contagens conferem exatamente com o diagnóstico de 23/11/2026.

### Verificação de não-escrita

Consultas read-only no destino, antes e depois do dry-run:

| Tabela | Linhas |
|---|---|
| `employees` | 0 |
| `holidays` | 0 |
| `settings` | 0 |
| `time_balances` | 0 |
| `audit_logs` | 0 |

O arquivo SQLite de origem manteve o mesmo tamanho e `LastWriteTime` — confirmação de que o legado não foi modificado.

## Estado da implementação

A carga real foi implementada com TDD (branch `feat/migracao-real-pontoja`):

- `BEGIN; ... COMMIT;` em **uma única sessão psql** com `ON_ERROR_STOP=1`:
  se qualquer `INSERT` falhar, a transação é revertida por completo.
- Idempotência por chave natural (`ON CONFLICT`) em todas as tabelas:
  `companies(slug)`, `employees(company_id, control_id)`,
  `holidays(company_id, date)`, `settings(company_id, key)`,
  `time_balances(company_id, employee_id, reference_month)`,
  `users(email)` e `company_users(company_id, user_id)`.
- `company_id` determinístico (`uuid5`) e `request.jwt.claims` setado no início
  da transação, conforme a regra de isolamento por tenant.
- Mapeamentos corrigidos para as colunas reais do legado: `feriados.descricao`
  (não `nome`), `configuracoes.valor` convertido para JSONB, e
  `saldos_usuario.usuario_id` ligado ao `employees.control_id`.
- `admins` → `users` + `company_users` com role `admin`.

`pg_dump` **não está instalado no host Windows**: o script usa
`docker compose exec -T postgres pg_dump -U vornia vornia`, redirecionando a
saída para `BACKUP_DIR`. O mesmo mecanismo (`docker compose exec ... psql`)
executa a carga, então não é necessário publicar a porta 5432.

### Senha temporária dos admins

Os hashes do legado são `scrypt:*`, incompatíveis com o `bcrypt` do Vornia.
A carga não os copia: ela gera hashes bcrypt de uma **senha temporária**
fornecida via variável de ambiente (nunca no código, nunca no `.env`):

```powershell
$env:VORNIA_MIGRATION_ADMIN_PASSWORD = '<senha-temporaria-.definida-pelo-operador>'
$env:BACKUP_DIR = 'C:\vornia\backups'
& 'backend\.venv\Scripts\python.exe' scripts/migrate_pontoja.py --sqlite PontoJa/database/controlid.db --backup-first --apply
```

E-mails dos admins são sintetizados como `<usuario>@tecnova.com.br`
(configurável via `--admin-email-domain`). Não usar `.local`: o Pydantic
`EmailStr` rejeita TLDs reservados e o login falha com 422.
`--reference-month` (padrão `2026-11-01`) define o mês de referência dos saldos.

## Regras de segurança (mantidas)

- `--apply` **exige** `--backup-first`: o pg_dump roda antes de qualquer escrita.
- `--dry-run` nunca escreve no PostgreSQL e imprime contagens e divergências.
- `--apply` e `--dry-run` são mutuamente exclusivos.
- CPF/PIS são normalizados para dígitos; usuários sem CPF válido são sinalizados como divergência (não são descartados silenciosamente).
- Legado aberto em `mode=ro` — o SQLite original não é modificado.

## Portão de aprovação

- [x] Dry-run executado com o SQLite real e zero divergências
- [x] Confirmado que nenhuma linha foi escrita no destino
- [x] Carga real implementada e testada (130 testes unitários verdes)
- [ ] **Aprovação humana explícita do código para seguir** (não concedida até o momento)
- [ ] Backup preventivo executado via Docker e validado com restore
- [ ] Spot-check de CPF/saldos após a carga
- [ ] Correção dos e-mails/senhas temporárias dos admins
- [ ] Registro final em `docs/migracao_checklist.md`

**Não executar `--apply` sem a aprovação explícita do usuário.**
