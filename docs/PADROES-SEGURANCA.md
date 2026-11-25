# Padrões de Segurança — Vornia (Workforce Intelligence)

**Versão:** 1.1  
**Status:** Atualizado  
**Aplica-se a:** Backend FastAPI (Oracle Cloud VM), Frontend Next.js (Oracle Cloud VM), Banco PostgreSQL 16 local (Docker), Auth JWT próprio  

## 1. Objetivo

Este documento estabelece os padrões mínimos de segurança para o Vornia, considerando:

- A arquitetura aprovada: **FastAPI + Python 3.11**, **Next.js 14+**, **PostgreSQL 16** (container local), **JWT próprio** no FastAPI.
- O requisito de ser **multi-tenant-ready** desde o primeiro deploy, com isolamento via **Row Level Security (RLS)**.
- Os aprendizados da migração do **PontoJa**, que apresentou **23 riscos de segurança**, sendo **4 críticos**. Nenhum desses padrões pode ser ignorado, relaxado ou postergado para uma "próxima sprint".

> **Princípio orientador:** *Segurança não é uma feature. É condição de existência para um sistema que processa dados de trabalhadores e empresas.*

---

## 2. Checklist de Segurança do Vornia

### 2.1. Aprendizado com o PontoJa

Os riscos identificados no PontoJa devem ser categoricamente evitados no Vornia:

- [ ] **Nenhuma credencial hardcoded** em código, notebooks, scripts ou variáveis de exemplo.
- [ ] **Nenhuma query SQL montada por concatenação** ou f-string (mesmo em migrações ad-hoc).
- [ ] **Nenhum endpoint exposto sem validação de entrada** e sem autenticação/autorização.
- [ ] **Nenhuma política de RLS omitida** em tabelas que contenham dados de tenant, funcionário, jornada ou pagamento.
- [ ] **Nenhum log contendo PII, senhas, tokens ou JWT completos**.
- [ ] **Nenhuma dependência desatualizada** sem justificativa documentada e aprovação de segurança.
- [ ] **Nenhuma resposta de erro expondo stack trace, query ou estrutura interna** do banco.
- [ ] **Nenhum cookie ou token persistido de forma insegura** no frontend.

### 2.2. Checklist Geral por Camada

#### Backend (FastAPI / Oracle Cloud VM)

- [ ] Todas as rotas sensíveis protegidas por dependency de autenticação.
- [ ] Validação de entrada via Pydantic em **todos** os endpoints (`POST`, `PUT`, `PATCH`, query params e path params).
- [ ] Uso obrigatório do padrão RLS: abrir transação, setar `request.jwt.claims` como JSON único, injetar conexão no handler.
- [ ] Rate limiting aplicado em login, sincronização, exportação e endpoints de mutação em massa.
- [ ] Logs estruturados sem PII; auditoria imutável em tabela separada.
- [ ] Headers de segurança configurados via middleware.

#### Banco de Dados (PostgreSQL 16 local)

- [ ] RLS habilitado em **todas** as tabelas que armazenam dados de tenant, funcionário, jornada, pagamento ou configuração.
- [ ] Políticas baseadas em `company_id` e `role` do JWT.
- [ ] Uso de funções/SPs para operações sensíveis quando a lógica não puder ser expressa apenas em RLS.
- [ ] Índices apropriados para evitar scan sequencial em políticas RLS.

#### Frontend (Next.js / Oracle Cloud VM)

- [ ] Cookies `HttpOnly`, `Secure`, `SameSite=Strict` para sessão.
- [ ] Sanitização de qualquer conteúdo HTML inserido dinamicamente.
- [ ] CSP configurado e validado em staging/produção.
- [ ] Nenhum secret de servidor exposto em código client-side.

#### DevOps / CI

- [ ] `pip-audit`/`safety` e `bandit` executados em todo PR.
- [ ] Dependabot habilitado para Python e Node.js.
- [ ] Variáveis de ambiente revisadas antes de cada deploy.
- [ ] Checklist pré-deploy preenchido e aprovado.

---

## 3. Gerenciamento de Secrets

### 3.1. Proibições

- **NUNCA** armazenar `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `CONTROL_ID_PASSWORD` ou qualquer outro secret no código-fonte.
- **NUNCA** commitar arquivos `.env`, `.env.local`, `.env.production` ou arquivos de configuração contendo secrets.
- **NUNCA** expor a service role key em endpoints, logs ou no frontend.

### 3.2. Obrigações

- Todos os secrets devem ser armazenados em:
  - **Produção:** arquivo `.env` na VM Oracle Cloud, com permissões `600`, fora do versionamento.
  - **Desenvolvimento local:** arquivo `.env.local` no `.gitignore`.

### 3.3. Lições específicas do PontoJa

- **NUNCA usar `SECRET_KEY` ou `ENCRYPTION_KEY` com valores default** (ex.: `dev-secret-key`, `j6sFvR5Fzq2m1mEJx2fCVh0j0khnj_Q4AhN89WG5f7k=`). Essas chaves devem ser geradas por ambiente e rotacionadas periodicamente.
- **NUNCA hardcoded senhas de dispositivos de terceiros**, como a senha default `admin` do Control iD. A senha do relógio deve ser configurada obrigatoriamente via variável de ambiente e alterada do valor de fábrica antes da primeira sincronização.
- **Toda integração com hardware ou serviço externo** deve ter seu próprio checklist de hardening: troca de credenciais default, uso de TLS, validação de certificado, rotação periódica.
  - **Produção:** arquivo `.env` na VM Oracle Cloud com permissão `600`.
  - **Desenvolvimento local:** arquivo `.env.local` no `.gitignore`.
- Validar no startup do FastAPI que todas as variáveis críticas estão definidas. Caso contrário, a aplicação deve falhar com mensagem clara.
- O frontend nunca acessa o banco diretamente; toda comunicação passa pela API FastAPI com JWT em cookie HttpOnly.

### 3.3. Rotação

- Rotação da service role key e do JWT secret a cada **6 meses**, ou imediatamente se houver suspeita de vazamento.
- Após rotação, invalidar sessões ativas e forçar re-login.
- Documentar a data da última rotação em `.claude/security/secret-rotation.log` ou equivalente.

---

## 4. Autenticação e Autorização

### 4.1. JWT Próprio no FastAPI

- Autenticação implementada no próprio backend FastAPI com **PyJWT**.
- Tabela `users` local armazena: `id`, `email`, `password_hash` (bcrypt/Argon2), `is_active`, `email_verified`, timestamps.
- Tabela `company_users` vincula usuário a empresa com `role`.
- O FastAPI possui endpoints próprios de login, refresh, logout e convite de usuários.
- O backend define o access token em cookie `HttpOnly`/`Secure`/`SameSite=Lax` e o refresh em cookie `HttpOnly`/`Secure`/`SameSite=Strict` com `Path=/api/v1/auth`. O frontend NUNCA lê esses cookies; usa `credentials: 'include'` e renova via `POST /api/v1/auth/refresh`.

### 4.2. Validação de JWT no Backend

- Implementar uma **FastAPI dependency** que:
  1. Extrai o token do cookie `token` (HttpOnly).
  2. Valida a assinatura com `JWT_SECRET`, algoritmo `HS256` (ou `RS256` se futuro), `exp`, `iss` e `aud`.
  3. Extrai `sub`, `email`, `role` e `company_id`.
  4. O `company_id` deve obrigatoriamente estar presente no token. Se estiver ausente, rejeitar com HTTP 401.
  5. Rejeita tokens expirados, malformados ou com assinatura inválida com HTTP 401.
  6. Verifica se o usuário ainda existe e está ativo (`users.is_active = true`); se não, rejeitar com HTTP 401.

### 4.3. Padrão RLS Obrigatório

Em toda operação no banco que dependa de contexto do usuário autenticado, o backend deve seguir o padrão aprovado:

1. **Pool no startup:** o FastAPI cria o pool `asyncpg` no evento de lifespan:
   ```python
   app.state.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
   ```
2. **Não abrir nova conexão por request:** o handler deve obter uma conexão do pool existente (`app.state.db_pool.acquire()`), nunca chamar `asyncpg.connect` diretamente.
3. **Transação explícita:** toda request sensível a empresa deve abrir uma transação (`async with conn.transaction():`), setar o contexto JWT e executar as queries dentro dela.
4. **Claims achatadas no nível raiz:** antes de setar `request.jwt.claims`, achatar as claims em um objeto JSON simples:
   ```python
   flat_claims = {
       "sub": user_id,
       "company_id": str(company_id),
       "role": role,
   }
   await conn.execute(
       "SELECT set_config('request.jwt.claims', $1, true)",
       json.dumps(flat_claims),
   )
   ```
5. **Injeção da conexão no handler:** a dependency deve retornar a conexão com o contexto já configurado para uso exclusivo daquele handler.
6. **Commit/rollback determinístico:** a transação deve ser confirmada apenas após o sucesso da operação; qualquer exceção dispara rollback.

#### Exemplo de Policy RLS

As policies devem ler `company_id` diretamente do nível raiz do objeto JSON configurado:

```sql
CREATE POLICY "isolation_by_company" ON jornadas_processadas
FOR ALL
TO authenticated
USING (
    company_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'company_id')::uuid
);
```

#### Proibições Específicas

- **NUNCA** buscar `company_id` dentro de `app_metadata` diretamente na policy.
- **NUNCA** usar `set_config('request.jwt.claims', ...)` fora de uma transação explícita.
- **NUNCA** abrir uma nova conexão por request (`asyncpg.connect`); sempre usar o pool criado no startup.

### 4.4. Criação de Usuários Administradores

- **NUNCA criar usuários administradores automaticamente com senhas default** (ex.: `admin`/`admin123`, `Tecnova.adm`/`Tec.palmas3225@`).
- Todo administrador deve ser convidado por outro admin/owner via endpoint seguro, recebendo senha temporária aleatória de uso único por canal seguro (e-mail criptografado em trânsito).
- A primeira empresa/owner pode ser criada por um script de bootstrap, mas a senha deve ser gerada aleatoriamente e entregue por canal seguro.

### 4.5. Lock-in do JWT Próprio

- O Vornia implementa autenticação própria com JWT. Não há lock-in de provider externo de auth.
- **Responsabilidades próprias:** emissão, validação, rotação de secret, refresh tokens, invalidação, segurança de hashes.
- **Risco:** vazamento do `JWT_SECRET` compromete todas as sessões. Mitigação: secret longo (≥ 256 bits), armazenado em `.env` com permissão restrita, rotação periódica e imediata em caso de suspeita.
- Backup dos hashes (`users.password_hash`) é suficiente para portabilidade futura.
- **NUNCA** executar queries fora de uma transação com contexto JWT setado quando os dados são sensíveis a empresa.

> **Não é permitido** executar queries fora de uma transação com contexto JWT setado quando os dados são sensíveis a tenant.

### 4.4. Roles e Permissões

As roles iniciais são:

| Role | Escopo | Permissões típicas |
|------|--------|--------------------|
| `admin` | Tenant | Gerenciar usuários, configurações, integrações, exportações, políticas internas. |
| `manager` | Tenant / equipe | Visualizar e editar dados da própria equipe, aprovar ajustes, gerar relatórios. |
| `user` | Próprio usuário | Visualizar própria jornada, solicitar ajustes, visualizar próprios holerites. |

Regras:

- Roles são claims do JWT, definidas na tabela `company_users` e validadas no login.
- O backend **não confia** em role enviada pelo cliente; ela é lida do JWT validado.
- Políticas RLS devem cobrir `SELECT`, `INSERT`, `UPDATE`, `DELETE` de acordo com a role.

---

## 5. Validação de Entrada

### 5.1. Pydantic em Todos os Endpoints

- Todo endpoint FastAPI deve declarar schemas Pydantic v2 para request body, query params e path params.
- Usar `Annotated` com `Field(...)` para restrições explícitas: `min_length`, `max_length`, `regex`, `gt`, `lt`, etc.
- Tratar `ValidationError` retornando HTTP 422 com detalhes de campo, sem expor internals.

### 5.2. Sanitização Adicional

- Remover ou escapar caracteres de controle de strings antes de persistir.
- Validar enumerados via `Literal` ou `Enum` do Pydantic; nunca aceitar strings livres quando o domínio for fechado.
- Limitar tamanho de payload no middleware/nuvem (ex.: 1MB por request padrão, 10MB para upload de arquivo se aplicável).

### 5.3. Upload de Arquivos

- Se houver upload (ex.: importação de funcionários, holerites), validar:
  - Tipo MIME permitido.
  - Extensão correspondente ao conteúdo.
  - Tamanho máximo.
  - Scan anti-malware ou sandbox para arquivos não estruturados.
- Nunca persistir o arquivo com o nome original fornecido pelo usuário.

---

## 6. CSRF, CORS, Cookies e Headers de Segurança

### 6.1. CSRF / Proteção contra Requisições Forjadas

O Vornia usa **JWT em cookie HttpOnly** (emitido pelo FastAPI). Nenhum token é exposto ao JavaScript do navegador:

- **CSRF é mitigado por `SameSite=Lax`/`Strict` nos cookies**; como o refresh usa `Path=/api/v1/auth` e `SameSite=Strict`, um site terceiro não consegue disparar a renovação. Para operações sensíveis (edição manual), exija `reason` e autenticação válida.
- O controle contra requisições forjadas é feito por:
  - CORS restritivo (whitelist de origins).
  - Validação do JWT no backend (assinatura, expiração, `aud`, `iss`).
  - `SameSite=Strict` nos cookies do Next.js (se usados para sessão SSR), nunca `None`.

No MVP, cookies `HttpOnly` + `SameSite` são a defesa adotada; se um fluxo passar a aceitar credenciais cruzadas, reavalie CSRF com token.

### 6.2. CORS

- CORS deve ser **restritivo**:
  - Origens permitidas: domínio de produção da Oracle Cloud (`https://vornia.exemplo.com.br`) e domínios de staging explicitamente listados.
  - **Nunca** usar `*` em produção.
  - Métodos permitidos devem refletir apenas o necessário.
- Revisar a whitelist de origens a cada novo ambiente de preview.

### 6.3. Cookies

- Sessão em cookie `HttpOnly`, `Secure`, `SameSite=Strict`.
- `Max-Age` ou `Expires` adequados; sessão longa apenas com refresh token rotativo.
- Não armazenar tokens em `localStorage` ou `sessionStorage`.

### 6.4. Headers de Segurança

Configurar obrigatoriamente em produção:

| Header | Valor mínimo |
|--------|--------------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |
| `Content-Security-Policy` | Política restritiva, sem `'unsafe-inline'`/`'unsafe-eval'` por padrão. Liberar apenas com justificativa documentada. |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Desabilitar recursos não utilizados (geolocalização, câmera, microfone, etc.). |

Validar headers em staging com ferramenta como Mozilla Observatory ou Security Headers.

---

## 7. Rate Limiting

### 7.1. Endpoints Sensíveis

Aplicar rate limiting em todos os endpoints abaixo, com store compartilhado (Redis local na mesma VM ou banco PostgreSQL):

| Endpoint / Ação | Limite sugerido | Janela |
|-----------------|-----------------|--------|
| Login / refresh token | 5 tentativas | 15 minutos por IP/usuário |
| Solicitação de redefinição de senha | 3 tentativas | 1 hora por e-mail |
| Sincronização de dados (sync) | 30 requisições | 1 hora por tenant |
| Exportação de relatórios | 10 exportações | 1 hora por usuário |
| Importação em massa | 5 uploads | 1 hora por tenant |
| Criação/edição em massa | 100 operações | 1 minuto por tenant |

### 7.2. Regras Gerais

- Rate limiting deve ser baseado em **IP + usuário** quando autenticado, e apenas **IP** quando anônimo.
- Retornar HTTP 429 com header `Retry-After`.
- Logar tentativas excedidas para detecção de abuso.

---

## 8. SQL Injection Prevention

### 8.1. Proibições

- **NUNCA** construir query SQL com f-string, concatenação de string ou interpolação de variáveis do usuário.
- **NUNCA** aceitar nomes de coluna ou tabela diretamente do cliente sem whitelist rigorosa.
- **NUNCA** usar `text()` do SQLAlchemy com strings dinâmicas não parametrizadas.

### 8.2. Obrigações

- Usar ORM/query builders com binds parametrizados (SQLAlchemy 2.0, asyncpg, etc.).
- Para queries raw, usar placeholders e passar valores em dicionário/tupla separada.
- Se for necessário ordenar por coluna dinâmica, validar o nome contra uma whitelist fixa no código.
- Revisar todo código Python com `bandit` (incluindo scripts de migração e notebooks).

---

## 9. XSS Prevention e Sanitização no Frontend

### 9.1. Regras do Next.js

- Renderizar conteúdo de usuário como **texto** por padrão (`{text}`), nunca como HTML.
- Se for inevitável renderizar HTML (ex.: rich text de comunicados internos), sanitizar com biblioteca adequada antes de exibir.
- Não usar `dangerouslySetInnerHTML` com conteúdo não confiável.

### 9.2. Sanitização

- Sanitizar todo input rico no backend antes de persistir, e sanitizar novamente no frontend antes de renderizar (defesa em camadas).
- Lista de tags/attributes permitidas deve ser mínima e revisionada.

### 9.3. CSP

- CSP é a última linha de defesa contra XSS. A política deve ser configurada no lado do servidor e validada.
- Relatar violações de CSP para endpoint de monitoramento.

---

## 10. Logs e Auditoria

### 10.1. O que Nunca Logar

- Senhas, hashes de senha, tokens JWT completos, refresh tokens.
- Dados sensíveis de funcionários: CPF, RG, número de conta bancária completa, endereço, telefone.
- Dados de saúde ou condições médicas, se houver.
- Erros internos que exponham stack trace em logs acessíveis ao cliente.

### 10.2. O que Logar

- Eventos de autenticação: login bem-sucedido, falha de login, logout, redefinição de senha, refresh.
- Alterações de permissão e convites de usuários.
- Operações de exportação, importação e sincronização em massa.
- Alterações em configurações críticas do tenant.
- Acesso a dados sensíveis (visualização de holerite, exportação de jornada).

### 10.3. Auditoria Imutável

- Manter tabela/evento de auditoria separado do banco operacional, com retenção longa.
- Campos mínimos: `timestamp`, `actor_id`, `company_id`, `action`, `resource_type`, `resource_id`, `changes` (JSON), `ip`, `user_agent`.
- Política RLS deve garantir que registros de auditoria sejam **apenas anexados** (append-only); nenhum usuário, incluindo admin, pode editar ou excluir.

---

## 11. Dependências

### 11.1. Scans Obrigatórios

Em todo PR e antes de deploy:

- [ ] `pip-audit` ou `safety check` para dependências Python.
- [ ] `bandit -r .` para identificar padrões inseguros no código Python.
- [ ] `npm audit` ou `pnpm audit` para dependências Node.js.
- [ ] `eslint-plugin-security` no frontend, se aplicável.

### 11.2. Dependabot

- Habilitar Dependabot para Python (`pip`) e Node.js (`npm`) no repositório GitHub.
- Configurar alertas para vulnerabilidades de alta e crítica.
- Estabelecer SLA de correção:
  - Crítica: 24 horas.
  - Alta: 7 dias.
  - Média: 30 dias.

### 11.3. Política de Dependências

- Avaliar nova dependência antes de adicionar: mantenedor ativo, uso amplo, histórico de segurança.
- Fixar versões mínimas no `requirements.txt`/`pyproject.toml` e `package.json`.
- Não usar dependências em versão beta ou fork não revisado sem aprovação.

---

## 12. LGPD (Lei Geral de Proteção de Dados)

### 12.1. Residência dos Dados

- Banco de dados primário na **Oracle Cloud Always Free VM**, localidade escolhida no provisionamento (preferir São Paulo/Brasil, se disponível, para LGPD).
- Backups e réplicas, se houver, devem permanecer em território brasileiro, salvo requisito legal expresso.
- Documentar o mapa de fluxo de dados pessoais (entrada, processamento, armazenamento, saída).

### 12.2. Consentimento e Transparência

- Obter consentimento explícito do titular antes de coletar dados pessoais sensíveis.
- Disponibilizar termos de uso e política de privacidade claros, acessíveis e versionados.
- Registrar versão do termo aceito pelo usuário no momento do cadastro.

### 12.3. Direitos do Titular

Implementar mecanismos para:

- [ ] Acesso aos dados pessoais armazenados.
- [ ] Correção de dados incompletos, inexatos ou desatualizados.
- [ ] Exclusão/anonimização (direito ao esquecimento), respeitando obrigações legais de retenção.
- [ ] Portabilidade dos dados, mediante solicitação.
- [ ] Revogação de consentimento.

### 12.4. Exclusão e Retenção

- Dados excluídos devem ser anonimizados ou removidos de forma irreversível.
- Manter auditoria da exclusão (quem, quando, qual recurso), sem manter o dado pessoal em si.
- Respeitar prazos legais de retenção (ex.: documentos trabalhistas).

### 12.5. Incidentes

- Plano de resposta a incidentes documentado.
- Notificação à autoridade e aos titulares em até 72 horas quando aplicável.
- Canal interno para reporte de vazamentos: `security@vornia.com.br`.

---

## 13. Checklist Pré-Deploy

Antes de qualquer deploy em staging ou produção, o responsável pelo deploy deve confirmar:

### Segurança de Código

- [ ] Nenhum secret hardcoded no diff.
- [ ] Nenhuma query SQL concatenada no diff.
- [ ] Todos os endpoints novos validam entrada via Pydantic.
- [ ] Todos os endpoints novos exigem autenticação, salvo explicitamente documentado como público.
- [ ] RLS habilitado e políticas criadas/alteradas para tabelas novas ou modificadas.
- [ ] Nenhum log novo expondo PII, senha, token ou stack trace ao cliente.

### Scans e Testes

- [ ] `pip-audit`/`safety` sem vulnerabilidades críticas ou altas não mitigadas.
- [ ] `bandit` sem findings críticos.
- [ ] `npm audit` sem vulnerabilidades críticas ou altas não mitigadas.
- [ ] Testes de autenticação e autorização passando.
- [ ] Testes de rate limiting passando.
- [ ] Testes de RLS passando.

### Configuração de Infraestrutura

- [ ] Variáveis de ambiente revisadas e atualizadas.
- [ ] Secrets rotacionados se houver suspeita de exposição.
- [ ] CORS configurado com origens explícitas.
- [ ] Headers de segurança configurados e validados.
- [ ] Rate limiting ativo e com store compartilhado.

### LGPD e Auditoria

- [ ] Fluxo de dados pessoais revisado.
- [ ] Consentimento e termos de uso atualizados, se aplicável.
- [ ] Auditoria imutável operacional.
- [ ] Plano de resposta a incidentes acessível.

### Aprovação

- [ ] Revisão de código aprovada por pelo menos um revisor.
- [ ] Checklist pré-deploy assinado (digitalmente) pelo responsável.
- [ ] Deploy em staging validado antes de produção.

---

## 14. Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Next.js Security](https://nextjs.org/docs/security)
- [LGPD — Lei nº 13.709/2018](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

---

## 15. Histórico de Revisões

| Versão | Data | Autor | Alterações |
|--------|------|-------|------------|
| 1.0 | 2026-11-23 | Security Reviewer ECC | Criação inicial com padrões do Vornia e lições do PontoJa. |
