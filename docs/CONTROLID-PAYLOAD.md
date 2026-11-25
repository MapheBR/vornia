# Contrato do payload Control iD (extraído de `PontoJa/services/controlid_api.py`)

Fonte: reads diretos do codigo legado em 2026-11-25. Este arquivo é a
**fonte da verdade** para os mocks HTTP dos testes do Sprint 4. Nenhum campo
deve ser inventado.

## Autenticação

`POST /login.fcgi`
```json
{"username": "<user>", "password": "<pass>"}
```
Variações aceitas pelo firmware: `login` ou `user` no lugar de `username`.
Resposta (JSON):
```json
{"session": "<token>"}
```
Também aceito: `session_id` ou `token`.

## Usuários

`POST /load_users.fcgi`
```json
{"limit": 100, "offset": 0, "session": "<token>"}
```
Resposta:
```json
{"users": [{"id": 42, "nome": "Maria"}]}
```
Variações de campo: `user_id`/`registration` no lugar de `id`; `name` no lugar de `nome`.
Paginação: nova requisição com `offset += 100` enquanto `len(batch) == 100`.

## Batidas AFD

`POST /get_afd.fcgi?mode=671` com `{"session": "<token>"}`.

A resposta pode ser:
1. **Texto puro** (uma linha por batida):
```
2026-11-25T08:00:00-03000000123456789012A1B2
```
   - timestamp: `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[-+]\d{4}|Z)?`
   - sufixo: `0*` + PIS (10–12 dígitos) + hash hexadecimal (2+ chars)
   - eventos `I`/`A` seguidos de PIS são inclusão/alteração de usuário — **não são batidas**
2. **Base64** do texto acima (alguns firmwares).
3. **JSON**: `{"records": [ ... ]}` onde cada item é uma das linhas acima ou
   `{"data_hora"|"timestamp": ..., "usuario_id"|"user_id"|"id": ...,
   "registro_id"|"id": ..., "tipo_registro": ...}`.

## Parsing do código de usuário (legado, `data_processor.py`)
- `lstrip("0")`; se >11 caracteres, trunca em 11; `int(...)`.
- `retorno == raw_code` quando não encontra → **defeito #4**: no Vornia isso
  gera `mapping_status='unmapped'`, nunca um `employee_id` fictício.

## Timezone
- `2026-11-25T08:00:00-0300` (sem dois-pontos no offset) ou `Z`.
- Conversão com `zoneinfo` (`UTC → America/Sao_Paulo`), nunca `replace(tzinfo=...)`.
