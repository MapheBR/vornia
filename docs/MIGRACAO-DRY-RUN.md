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
employees: 26 linha(s)
holidays: 15 linha(s)
settings: 20 linha(s)
time_balances: 2 linha(s)

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

## ⚠️ Estado da implementação (importante)

`scripts/migrate_pontoja.py` é um **scaffold**: `--apply` **não executa a carga real**. Ele apenas:

1. exige `--backup-first` e roda `pg_dump` antes de qualquer escrita;
2. imprime `Carga real não executada neste scaffold — revisar relatório antes de --apply`.

Portanto, **a migração de dados ainda não está implementada**. Antes de prometer dados migrados ao time, é preciso escrever a carga transacional (com testes, chave natural de idempotência e rollback) — seguindo TDD. A aprovação deste dry-run autoriza apenas o backup preventivo, não uma carga que hoje não existe.

`pg_dump` **não está instalado no host Windows**. Para `--backup-first --apply` será necessário executar o backup pelo container (`docker compose exec -T postgres pg_dump ...`, conforme `scripts/backup-postgres.sh`) ou instalar as ferramentas de cliente PostgreSQL no host.

## Regras de segurança (mantidas)

- `--apply` **exige** `--backup-first`: o pg_dump roda antes de qualquer escrita.
- `--dry-run` nunca escreve no PostgreSQL e imprime contagens e divergências.
- `--apply` e `--dry-run` são mutuamente exclusivos.
- CPF/PIS são normalizados para dígitos; usuários sem CPF válido são sinalizados como divergência (não são descartados silenciosamente).
- Legado aberto em `mode=ro` — o SQLite original não é modificado.

## Portão de aprovação

- [x] Dry-run executado com o SQLite real e zero divergências
- [x] Confirmado que nenhuma linha foi escrita no destino
- [ ] **Aprovação humana explícita para seguir** (não concedida até o momento)
- [ ] Carga real implementada e testada (hoje é scaffold)
- [ ] Backup preventivo executado e validado com restore
- [ ] Spot-check de CPF/saldos após a carga
- [ ] Registro final em `docs/migracao_checklist.md`

**Não executar `--apply` sem a aprovação explícita do usuário.**
