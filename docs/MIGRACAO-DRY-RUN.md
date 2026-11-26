# Resultado do dry-run — migração PontoJa → Vornia (Sprint 7)

> Este é um **exemplo com banco sintético** (`tests/unit/test_migrate_pontoja.py`),
> não dados reais da Tecnova. O relatório definitivo será gerado com o SQLite legado
> na VM, antes de qualquer `--apply`.

Comando:

```bash
python scripts/migrate_pontoja.py --sqlite exports/migracao/controlid.db --dry-run
```

Saída esperada (contagens do diagnóstico 23/11/2026):

```
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

## Regras de segurança

- `--apply` **exige** `--backup-first`: o script roda `pg_dump` antes de qualquer escrita
  e imprime o caminho do backup.
- `--dry-run` nunca escreve no PostgreSQL e imprime contagens e divergências.
- `--apply` e `--dry-run` são mutuamente exclusivos.
- CPF/PIS são normalizados para dígitos; usuários sem CPF válido são sinalizados como
  divergência (não são descartados silenciosamente).
- Legado aberto em `mode=ro` — o SQLite original não é modificado.

## Antes da carga real

1. Conferir o relatório acima com o time da Tecnova.
2. Rodar `--backup-first --apply` em janela de manutenção.
3. Validar contagens no destino e fazer spot-check de CPF/saldos.
4. Registrar tudo em `docs/migracao_checklist.md`.
