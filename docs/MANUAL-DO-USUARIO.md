# Manual do Usuário — Vornia

## 1. Acesso

1. Abra `http://localhost:8080` (desenvolvimento) ou o domínio de produção.
2. Em **Entrar**, informe e-mail e senha. Se ainda não tem conta, use **Criar conta** (informe empresa, nome, e-mail e senha com 8+ caracteres).
3. O navegador guarda a sessão em cookies seguros — não é preciso copiar tokens.

## 2. Colaboradores

- Em **Colaboradores**, clique em **Novo colaborador** para cadastrar: nome, CPF, PIS, matrícula, cargo, departamento e data de admissão.
- Use a busca para filtrar por nome e o seletor de situação para ver ativos/inativos.
- **Editar** altera os dados; **Desativar** faz exclusão lógica (o histórico é preservado).

## 3. Sincronização do Control iD

- `POST /api/v1/sync/controlid` importa batidas do relógio. A operação é idempotente: repeti-la não duplica registros.
- Batidas com código de usuário desconhecido ficam marcadas como `unmapped` e não geram jornada — cadastre o colaborador com o `control_id` correto.
- `POST /api/v1/sync/process` transforma as batidas em jornadas diárias.

## 4. Dashboard

- Cards mostram total de colaboradores, horas trabalhadas, inconsistências e jornadas pendentes.
- A lista de inconsistências indica jornadas que exigem revisão.

## 5. Corrigir uma batida ou jornada

1. Abra a jornada pendente/inconsistente no dashboard.
2. Ajuste o horário e **informe o motivo** (obrigatório, mínimo 5 caracteres).
3. Ao salvar, o sistema recalcula a jornada **e** o banco de horas na mesma operação. Se algo falhar, nada é alterado.
4. A trilha em **Auditoria** (admin/manager) mostra quem alterou, quando e por quê.

## 6. Exportar

- **Exportar XLSX**: até 10.000 jornadas no período.
- **Exportar PDF**: até 500 jornadas; acima disso o sistema avisa para reduzir o período.
- Filtre por colaborador e intervalo de datas (máximo 366 dias).

## 7. Feriados e banco de horas

- Admin/manager pode cadastrar feriados com jornada especial (padrão: 4h).
- `POST /api/v1/balances/recalculate` consolida o saldo mensal de todos os colaboradores.

## 8. Segurança

- Nunca compartilhe sua senha.
- O CPF aparece completo apenas para admin/manager.
- Sessões expiram: o sistema renova automaticamente o access token usando o refresh token; se expirar, entre novamente.

## 9. Problemas comuns

| Sintoma | Ação |
|---|---|
| "Credenciais inválidas" | Confira e-mail/senha; senha mínimo 8 caracteres |
| Batida não aparece na jornada | Verifique se o `control_id` do colaborador corresponde ao código do relógio |
| 429 ao exportar | Reduza o período ou o número de colaboradores |
| Jornada inconsistente | Revise as batidas do dia e registre a correção com motivo |
