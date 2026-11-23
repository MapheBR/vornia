# ECC — Guia de Uso no Projeto Vornia

> Versão do ECC: **2.2.3**  
> Harness: **OpenCode** (adaptado do plugin oficial `ecc-universal`)  
> Canal de instalação: `npm install ecc-universal@2.2.3` (fonte oficial)  
> Repositório oficial: https://github.com/affaan-m/ECC  
> npm: https://www.npmjs.com/package/ecc-universal  

---

## 1. Instalação realizada

- **Node.js**: v22.14.0 ✅
- **npm**: 10.9.2 ✅
- **Python**: 3.11.0rc2 ✅
- **Git**: 2.53.0.windows.2 ✅
- **ECC**: instalado localmente via `npm install ecc-universal@2.2.3 --save`
- **Configuração OpenCode**: `opencode.json` na raiz referenciando o plugin `ecc-universal`, instruções, agentes e comandos.
- **Assets copiados** para o projeto:
  - `.opencode/commands/` — templates dos comandos slash
  - `.opencode/prompts/` — prompts dos agentes
  - `.opencode/instructions/INSTRUCTIONS.md` — regras consolidadas do OpenCode
  - `AGENTS.md` e `CONTRIBUTING.md` na raiz

> **Nota sobre `/ecc-guide`**: esse comando é nativo do **Claude Code**. No OpenCode, o equivalente é usar a skill `ecc-guide` (carregada automaticamente quando o contexto é sobre o ECC) ou consultar este documento. Os comandos slash disponíveis no OpenCode são listados abaixo.
>
> **Teste de operacionalidade**: o subagente `planner` foi executado com sucesso como teste e confirmou que o ECC está operacional no OpenCode para o projeto Vornia.

---

## 2. Agentes disponíveis (subagentes ECC)

| Agente | Propósito | Quando usar |
|--------|-----------|-------------|
| `planner` | Planejamento de implementação | Recursos complexos, refatorações, decisões de escopo |
| `architect` | Arquitetura de sistemas | Decisões técnicas, escalabilidade, padrões |
| `tdd-guide` | TDD (testes primeiro) | Novos recursos, correções de bugs, refatoração |
| `code-reviewer` | Revisão de código | Imediatamente após escrever/alterar código |
| `security-reviewer` | Segurança | Antes de commits; código com auth, input sensível, API, dados pessoais |
| `build-error-resolver` | Resolver erros de build/type | Quando build falhar |
| `e2e-runner` | Testes E2E com Playwright | Fluxos críticos do usuário |
| `refactor-cleaner` | Limpeza de código morto | Manutenção, remoção de duplicatas |
| `doc-updater` | Documentação e codemaps | Atualização de docs |
| `python-reviewer` | Revisão Python | Código Python do Vornia |
| `database-reviewer` | PostgreSQL/SQLite | Schemas, queries, migrações |
| `code-explorer` | Mapeamento de codebases desconhecidas | Diagnóstico do projeto antigo PontoJa |
| `spec-miner` | Extração de specs de brownfield | Levantar regras de negócio do PontoJa |

### Agentes adicionais no catálogo ECC

O repositório oficial conta com **68 agentes** especializados, incluindo:
`go-reviewer`, `go-build-resolver`, `java-reviewer`, `java-build-resolver`, `kotlin-reviewer`, `rust-reviewer`, `typescript-reviewer`, `react-reviewer`, `vue-reviewer`, `django-reviewer`, `fastapi-reviewer`, `php-reviewer`, `cpp-reviewer`, `csharp-reviewer`, `flutter-reviewer`, `swift-reviewer`, `performance-optimizer`, `silent-failure-hunter`, `spec-miner`, `loop-operator`, `harness-optimizer`, `rag-pipeline-reviewer`, `mle-reviewer`, `opensource-forker`, `opensource-sanitizer`, `opensource-packager`, entre outros.

---

## 3. Skills disponíveis (seleção relevante para o Vornia)

O ECC possui **293 skills**. As principais para este projeto estão abaixo.

| Skill | Descrição | Quando usar |
|-------|-----------|-------------|
| `tdd-workflow` | Desenvolvimento test-first com 80%+ cobertura | Sempre para features/bugs/refactor |
| `security-review` | Checklist e padrões de segurança | Auth, input, endpoints, dados sensíveis |
| `coding-standards` | Convenções de código gerais | Revisão de qualidade e nomenclatura |
| `python-patterns` | Idiomas Python, PEP 8, type hints | Código Python do backend |
| `python-testing` | pytest, mocks, fixtures, cobertura | Testes Python |
| `backend-patterns` | APIs REST, camadas, repository/service, middleware | Backend Flask/FastAPI do Vornia |
| `api-design` | Design de endpoints REST, status codes, paginação, versionamento | APIs do Vornia |
| `frontend-patterns` | React/Next.js, estado, performance | Frontend do Vornia |
| `e2e-testing` | Playwright, Page Object Model, flaky tests | Testes E2E |
| `verification-loop` | Verificação em 6 fases (build, lint, testes, segurança, diff) | Antes de PRs/merges |
| `strategic-compact` | Gerenciamento de context window | Sessões longas |
| `eval-harness` | Eval-driven development | Garantir critérios de aceite |
| `architecture-decision-records` | Capturar ADRs | Decisões arquiteturais |
| `database-migrations` | Migrações seguras de banco | Evolução do schema |
| `postgres-patterns` / `mysql-patterns` | Padrões de banco | Otimização de queries |
| `git-workflow` | Branches, commits convencionais | Workflow do time |
| `deployment-patterns` | CI/CD, Docker, health checks | Preparar deploy |
| `lgpd` / `hipaa-compliance` | Conformidade de dados | Documentação LGPD do Vornia |
| `design-system` | Tokens, consistência visual | Identidade visual Vornia |

### Skills carregadas por padrão no OpenCode

As seguintes skills são carregadas automaticamente via `opencode.json`:

- `tdd-workflow`
- `security-review`
- `coding-standards`
- `frontend-patterns`
- `backend-patterns`
- `e2e-testing`
- `verification-loop`
- `api-design`
- `strategic-compact`
- `eval-harness`

Outras skills são ativadas automaticamente quando o contexto da conversa corresponde à sua descrição (trigger table).

---

## 4. Comandos slash disponíveis no OpenCode

| Comando | Agente/Skill | Uso |
|---------|--------------|-----|
| `/plan "descrição"` | `planner` | Criar plano de implementação |
| `/tdd` | `tdd-guide` | Workflow TDD |
| `/code-review` | `code-reviewer` | Revisar código recente |
| `/security` | `security-reviewer` | Revisão de segurança |
| `/build-fix` | `build-error-resolver` | Corrigir erros de build |
| `/e2e` | `e2e-runner` | Testes E2E |
| `/refactor-clean` | `refactor-cleaner` | Remover código morto |
| `/orchestrate` | `planner` | Orquestrar múltiplos agentes |
| `/update-docs` | `doc-updater` | Atualizar documentação |
| `/test-coverage` | `tdd-guide` | Análise de cobertura |

> No Claude Code, os comandos usam prefixo `/ecc:` (ex.: `/ecc:plan`). No OpenCode, usam a forma curta (`/plan`).

---

## 5. Mapeamento ECC por fase do projeto Vornia

| Fase | Objetivo | Agente / Skill / Comando ECC recomendado |
|------|----------|------------------------------------------|
| **FASE 0** — Instalar e aprender ECC | Configurar ECC e documentar uso | `configure-ecc` skill, este `ECC-USO.md` |
| **FASE 1** — Diagnóstico do projeto antigo | Ler e auditar `PontoJa` sem alterar | `/code-review` + `security-reviewer`, `spec-miner` |
| **FASE 2** — Arquitetura e padrões | Definir camadas, nomeação, commits | `/plan` (planner) + `architect` + `architecture-decision-records` |
| **FASE 3** — Plano e MVP | Roadmap de sprints e critérios de aceite | `/plan` (planner) + `product-capability` + `eval-harness` |
| **FASE 4** — Identidade visual | Logo, paleta, site de apresentação | `design-system` + `frontend-patterns` + geração de imagem |
| **FASE 5** — Implementação | Codificar MVP, corrigir defeitos, segurança | `/tdd` + `/code-review` + `/security` + `python-reviewer` + `database-reviewer` |
| **FASE 6** — Documentação | Docs completas em `/docs` | `/update-docs` + `doc-updater` + `architecture-decision-records` |

### Uso recomendado por tipo de tarefa

- **Feature nova**: `/plan` → `/tdd` → `/code-review` → `/security`
- **Bug**: `/tdd` (reproduzir com teste falhando) → implementar → `/code-review`
- **Refatoração**: `/plan` (se grande) → `/refactor-clean` → `/tdd` → `/code-review`
- **Antes de commit/merge**: `/security` + `/code-review` + `verification-loop`
- **Decisão arquitetural**: `architect` + `architecture-decision-records`
- **Dúvida sobre qual agente/skill usar**: skill `ecc-guide` ou `prompt-optimizer`

---

## 6. Como o ECC escolhe skills e agentes automaticamente

O ECC usa **trigger tables** e **descrições das skills/agentes** para ativar o recurso certo:

1. **Descrição da skill/agente** (`description` no frontmatter ou config) é comparada ao contexto da conversa.
2. **Palavras-chave e frases** nas skills definem quando ativar. Exemplos:
   - "auth", "senha", "input", "endpoint" → ativa `security-review`
   - "test", "tdd", "coverage" → ativa `tdd-workflow`
   - "deploy", "CI/CD", "Docker" → ativa `deployment-patterns`
3. **Agent orchestration** no `AGENTS.md`: regras como "Complex feature requests → planner" guiam a escolha.
4. **OpenCode carrega skills** listadas em `opencode.json` e descobre outras via `skills.paths`.
5. **Hooks** (quando suportados): `PreToolUse` pode sugerir skills, revisões e gates de segurança. No OpenCode, hooks automatizados são limitados; ações de segurança e formatação devem ser feitas manualmente.

### Recomendação operacional

Não depender exclusivamente da ativação automática. Para cada fase do projeto, usar explicitamente o comando/agente/skill indicado na tabela acima.

---

## 7. Controles de runtime

| Variável | Função |
|----------|--------|
| `ECC_HOOK_PROFILE=minimal\|standard\|strict` | Perfil de rigor dos hooks |
| `ECC_DISABLED_HOOKS=id1,id2` | Desabilitar hooks específicos |
| `ECC_CONTEXT_WINDOW_TOKENS=200000` | Tamanho da janela de contexto para `strategic-compact` |

No OpenCode, hooks são parcialmente suportados pelo plugin `ecc-universal`. Verificações de segurança, formatação e testes devem ser executadas manualmente antes de commits.

---

## 8. Checklist de segurança obrigatória (ECC)

Antes de **qualquer commit**:

- [ ] Nenhum segredo hardcoded (API keys, senhas, tokens)
- [ ] Todas as entradas de usuário validadas
- [ ] Queries parametrizadas (prevenção SQL injection)
- [ ] XSS sanitizado
- [ ] CSRF habilitado
- [ ] Autenticação/autorização verificadas
- [ ] Rate limiting em endpoints
- [ ] Mensagens de erro não vazam dados sensíveis

Se encontrar problema de segurança: **PARAR** → usar `security-reviewer` → corrigir CRITICAL → rotacionar segredos expostos → revisar código similar.

---

## 9. Links úteis

- README oficial (pt-BR): https://github.com/affaan-m/ECC/blob/main/docs/pt-BR/README.md
- OpenCode plugin README: `node_modules/ecc-universal/.opencode/README.md`
- Repositório: https://github.com/affaan-m/ECC
- npm: https://www.npmjs.com/package/ecc-universal
- Site: https://ecc.tools

---

*Documento gerado na FASE 0 do projeto Vornia. Aguardando aprovação para seguir para a FASE 1.*
