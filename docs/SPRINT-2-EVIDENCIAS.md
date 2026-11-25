# Evidências do Sprint 2 — Fases 2 a 4

## Fase 2 — CRUD de colaboradores

| Garantia | Teste | RED → GREEN |
|---|---|---|
| `employees` com FORCE RLS e policies | `tests/integration/test_rls.py::test_employees_rls_is_forced` | RED: tabela ausente → GREEN: migration 006 |
| Isolamento real no banco (claims A não veem B) | `test_employee_from_other_tenant_is_invisible` | RED: `UndefinedTableError` → GREEN: 0 linhas |
| INSERT cross-tenant bloqueado por WITH CHECK | `test_app_role_cannot_insert_employee_for_other_tenant` | RED: tabela ausente → GREEN: `InsufficientPrivilegeError` |
| CPF/PIS válidos (dígitos verificadores) | `tests/unit/test_identity.py` | RED: módulo ausente → GREEN: 22 casos |
| CRUD, paginação, filtros, soft delete, 409 | `tests/integration/test_employees.py` | RED: endpoints 404 → GREEN: 9 testes |
| CPF mascarado em listagens | `tests/unit/test_employee_schema.py::test_masks_by_role` | GREEN: admin vê completo, user não |

Prova SQL (role `vornia_app`, claims da Empresa A):

```text
 companies_visiveis = 1 (apenas A)
 SELECT ... WHERE id = <colaborador B>  ->  (0 linha)
 INSERT INTO employees (company_id = B) -> ERRO: new row violates row-level security policy
```

## Fase 3 — Refresh Token

| Garantia | Teste |
|---|---|
| Token opaco 256 bits e hash SHA-256 | `tests/unit/test_token_service.py` |
| Rotação invalida o token anterior | `test_refresh_rotates_token_and_invalidates_old` |
| Reuso revoga a família | `test_refresh_rotates_token_and_invalidates_old` |
| Logout revoga refresh | `test_logout_revokes_refresh_token` |
| Hash no banco, nunca plaintext | `test_refresh_token_hash_is_stored_not_plaintext` |
| Role de runtime sem acesso à tabela | `test_runtime_role_cannot_read_refresh_tokens` |
| Access token 30 min | `tests/unit/test_security.py` |

## Fase 4 — Settings

| Garantia | Teste |
|---|---|
| Allowlist Pydantic (6 chaves) | `tests/unit/test_settings_registry.py` |
| Chave desconhecida → 422 | `test_unknown_key_is_rejected` |
| Tipo inválido → 422 | `test_invalid_value_type_is_rejected` |
| Defaults mesclados + persistência | `test_list_settings_returns_defaults`, `test_put_get_and_delete_setting` |
| Isolamento por tenant | `test_settings_are_isolated_per_tenant` |

## Quality gates (CI run 45482505709 — verde)

- backend: 83 testes, 92.61% cobertura (antes das Fases 3–4); 105 testes localmente após.
- frontend: lint, typecheck, build, npm audit — pass.
- ruff, mypy, bandit — 0 issues.
