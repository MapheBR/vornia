# Dívida técnica — Sprint 6 (continuação do Sprint 5)

## Fase 4 — Exportações (não entregue)
- `GET /api/v1/exports/journeys.xlsx` com filtros `employee_id`, `start`, `end`, limite 10.000 linhas, sanitização CSV-injection (`'` prefix).
- `GET /api/v1/exports/journeys.pdf`: **lib leve** (`fpdf2` puro-Python ou HTML+CSS `@media print` via navegador); **não usar ReportLab/WeasyPrint** — peso e wheels nativos em ARM (Oracle Cloud). Limite 500 linhas + 429.
- Matriz de testes 14–17 do plano do Sprint 5.

## Fase 5 — Auditoria e edição manual (não entregue)
- `PATCH /api/v1/journeys/{id}` e `PATCH /api/v1/raw-punches/{id}` com `reason` obrigatório.
- **Cascata atômica (alinhamento do usuário)**: editar `raw_punch` dispara recálculo do `processed_journey` daquele `(employee_id, date)` **e** do `time_balances` do mês, tudo na **mesma transação**; se qualquer passo falhar, nada é persistido (nem o `audit_logs`).
- `audit_logs` append-only (policy já criada na migration 014).
- Matriz de testes 18–22 do plano do Sprint 5.

## E2E no CI (bloqueante para Sprint 7)
- Ver `docs/DEBT-SPRINT-4.md` — job separado com `docker compose up -d` + Playwright.
