# Guia de provisionamento da VM Oracle Cloud (ARM) — Sprint 7

Guia passo a passo para preparar a VM que receberá o Vornia em produção.
Execute **nesta ordem**. Ao final, rode `scripts/check-vm-readiness.sh` — ele é o
portão de entrada para o deploy via GitHub Actions.

Convenções usadas neste documento:

- `<IP_PUBLICO>` = IP público reservado da VM (ex.: `203.0.113.10`)
- `<DOMINIO>` = domínio de teste (ex.: `vornia-teste-203-0-113-10.sslip.io`)
- `<ACME_EMAIL>` = e-mail para o Let's Encrypt (ex.: `devops@tecnova.com.br`)
- Comandosmarked `local` rodam na sua máquina; os demais, na VM via SSH.

---

## 0. Antes de criar a VM (conta Oracle)

1. **Converter a conta para Pay As You Go (PAYG).**
   No console: *Billing → Upgrade / Payment Methods*. Os recursos Always Free
   continuam $0/mês, mas a VM deixa de estar sujeita à política de
   *Idle Reclamation* (desligamento por inatividade).
2. Confirmar que a região escolhida tem capacidade Ampere A1 disponível.
3. Gerar uma **chave SSH exclusiva para deploy** (local), nunca reutilizar chave pessoal:

   ```bash
   ssh-keygen -t ed25519 -C "vornia-deploy" -f ~/.ssh/vornia_deploy
   chmod 600 ~/.ssh/vornia_deploy
   cat ~/.ssh/vornia_deploy.pub   # copiar para o campo "Public Key" da Oracle
   ```

4. Guardar a chave privada também como secret `DEPLOY_SSH_KEY` no GitHub
   (*Settings → Secrets and variables → Actions → New repository secret*).

---

## 1. Criar a instância

1. Oracle Cloud → *Compute → Instances → Create Instance*.
2. **Name:** `vornia-prod`.
3. **Image:** Ubuntu 24.04 LTS (ARM64 / aarch64).
4. **Shape:** `VM.Standard.A1.Flex` — 2 OCPU / 12 GB RAM (Always Free).
5. **SSH key:** colar o conteúdo de `~/.ssh/vornia_deploy.pub`.
6. **Networking:** criar/associar VCN com subnet pública e **reservar IP público**.
7. Criar a instância e anotar `<IP_PUBLICO>`.

Conectar (local):

```bash
ssh -i ~/.ssh/vornia_deploy ubuntu@<IP_PUBLICO>
```

---

## 2. Firewall — Oracle Cloud Security List

No console da Oracle (VCN → subnet → **Security Lists → Default Security List**),
adicionar regras **ingress**:

| Origem | Protocolo | Porta | Finalidade |
|---|---|---|---|
| `0.0.0.0/0` | TCP | **80** | redirect HTTP → HTTPS e desafios ACME |
| `0.0.0.0/0` | TCP | **443** | HTTPS (Caddy) |
| `<SEU_IP>/32` | TCP | 22 | SSH (restringir ao seu IP; Actions usa chave, mas a origem é variável) |

> **Importante:** se o deploy via Actions precisar de SSH de IPs variáveis do GitHub,
> use um bastion ou limite a 22 a uma faixa conhecida. Nunca abra 22 para `0.0.0.0/0`.

Regras **egress** padrão (todo o tráfego saente) já são suficientes para
`apt`, Docker Hub, Let's Encrypt e GitHub.

Também adicionar na própria instância (ver próxima seção) via iptables/ufw.

---

## 3. Sistema base, Docker e Compose (ARM64)

Na VM:

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg git ufw

# Repositório oficial Docker com arquitetura arm64 explícita
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Validar:

```bash
docker --version
docker compose version
docker info | grep -i architecture   # deve mostrar aarch64/arm64
docker run --rm hello-world          # confirma que a ARCH é suportada
```

> Não instalar ReportLab/WeasyPrint: as libs do projeto (openpyxl/fpdf2) são
> puras em Python e evitam wheels nativos em ARM.

---

## 4. Firewall interno (iptables/ufw)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'ACME + redirect'
sudo ufw allow 443/tcp comment 'HTTPS Caddy'
sudo ufw enable
sudo ufw status verbose
```

Regras equivalentes em iptables (caso ufw não seja desejado):

```bash
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

**Nunca** abrir 5432 (Postgres), 6379 (Redis), 8000 (backend) ou 3000 (frontend).
O `docker-compose.prod.yml` já não publica essas portas.

---

## 5. Usuário de deploy e diretório

```bash
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo mkdir -p /opt/vornia
sudo chown -R deploy:deploy /opt/vornia

# Chave SSH do GitHub Actions (mesma chave privada do secret DEPLOY_SSH_KEY)
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy tee /home/deploy/.ssh/authorized_keys > /dev/null <<'EOF'
<COLOAR_A_CHAVE_PUBLICA_AQUI>
EOF
sudo -u deploy chmod 700 /home/deploy/.ssh
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys

sudo -u deploy git clone https://github.com/MapheBR/vornia.git /opt/vornia
```

Testar sem senha (local):

```bash
ssh -i ~/.ssh/vornia_deploy -o StrictHostKeyChecking=accept-new deploy@<IP_PUBLICO> 'cd /opt/vornia && git status --short --branch'
```

> Para `StrictHostKeyChecking=yes` no workflow, obter a impressão digital:
> `ssh-keyscan -H <IP_PUBLICO>` e salvar como secret `DEPLOY_KNOWN_HOSTS`.

---

## 6. `.env` de produção

```bash
sudo -u deploy cp /opt/vornia/.env.example /opt/vornia/.env
sudo -u deploy chmod 600 /opt/vornia/.env
sudo -u deploy nano /opt/vornia/.env
```

Preencher (valores de **exemplo**, trocar pelos reais):

```dotenv
POSTGRES_USER=vornia
POSTGRES_PASSWORD=<senha-forte-gerada>
POSTGRES_DB=vornia
VORNIA_APP_PASSWORD=<senha-forte-app>
VORNIA_AUTH_PASSWORD=<senha-forte-auth>
DATABASE_URL=postgresql://vornia:<senha>@postgres:5432/vornia
DATABASE_URL_APP=postgresql://vornia_app:<senha>@postgres:5432/vornia
DATABASE_URL_BOOTSTRAP=postgresql://vornia_auth:<senha>@postgres:5432/vornia
JWT_SECRET=<openssl rand -hex 32>
COOKIE_SECURE=true
VORNIA_DOMAIN=<DOMINIO>
VORNIA_ACME_EMAIL=<ACME_EMAIL>
CORS_ORIGINS=https://<DOMINIO>
NEXT_PUBLIC_API_URL=https://<DOMINIO>
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://redis:6379/0
BACKUP_DIR=/opt/vornia/backups
```

Gerar secrets fortes:

```bash
openssl rand -hex 32       # JWT_SECRET
openssl rand -base64 24    # senhas
```

> O `check-vm-readiness.sh` falha se `.env` estiver com permissão maior que `600`.

---

## 7. Verificação final da VM

```bash
sudo -u deploy /opt/vornia/scripts/check-vm-readiness.sh /opt/vornia
```

Saída esperada: todas as linhas `OK ...` e **VM pronta para deploy.**
Se houver `FAIL`, corrigir antes de acionar o GitHub Actions.

Checklist manual adicional:

```bash
df -h /opt/vornia            # >= 5 GB livres
free -h                      # >= 8 GB disponíveis
curl -I https://<DOMINIO>    # ainda deve falhar: Caddy sobe no deploy
```

---

## 8. Secrets no GitHub Actions

Criar em *Settings → Secrets and variables → Actions*:

| Secret | Valor |
|---|---|
| `DEPLOY_HOST` | `<IP_PUBLICO>` |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_SSH_KEY` | conteúdo de `~/.ssh/vornia_deploy` (chave privada) |
| `DEPLOY_PATH` | `/opt/vornia` |
| `DEPLOY_PORT` | `22` (opcional) |
| `DEPLOY_KNOWN_HOSTS` | saída de `ssh-keyscan -H <IP_PUBLICO>` (opcional, recomendado) |
| `VORNIA_DOMAIN` | `<DOMINIO>` |
| `VORNIA_ACME_EMAIL` | `<ACME_EMAIL>` |

---

## 9. DNS

No provedor do domínio (ou usando sslip.io, que não exige config):

```
A   <DOMINIO>   -> <IP_PUBLICO>
```

Conferir (local):

```bash
dig +short <DOMINIO>     # deve retornar <IP_PUBLICO>
```

> Com `sslip.io`, use um nome que embuta o IP, ex.:
> `vornia-teste-203-0-113-10.sslip.io`. Nenhum registro manual é necessário.

---

## 10. Deploy e rollback

- **Deploy:** criar tag `v1.0.0` na `main` ou disparar
  *Actions → Deploy → Run workflow* informando a tag.
- **Acompanhar:** `Actions → Deploy` (job `verify` → `deploy`).
- **Validar na VM:** `curl -I https://<DOMINIO>/health` → `200 {"status":"ok"}`.
- **Rollback:** `sudo -u deploy /opt/vornia/scripts/rollback.sh /opt/vornia`.

---

## 11. HTTPS / Caddy

`docker/Caddyfile.prod` usa `{$VORNIA_DOMAIN}` e `{$VORNIA_ACME_EMAIL}` (variáveis
do ambiente, vindas do `.env`). O Caddy:

- obtém o certificado Let's Encrypt automaticamente;
- renova sozinho antes do vencimento;
- redireciona HTTP → HTTPS (`redir https://{host}{uri} permanent`);
- aplica CSP/HSTS e demais headers de segurança.

Verificar certificado:

```bash
echo | openssl s_client -servername <DOMINIO> -connect <DOMINIO>:443 2>/dev/null | openssl x509 -noout -dates -issuer
```

---

## 12. O que vem depois (Fases 2–4)

| Fase | Ação | Status |
|---|---|---|
| 2 | Deploy real via GitHub Actions + HTTPS/ACME | Aguardando VM |
| 3 | Migração PontoJa: `--dry-run` → sua aprovação → `--backup-first --apply` | Aguardando VM |
| 4 | Checklist de Go-Live (17 itens) e aviso à Tecnova | Aguardando Fases 2–3 |

Referências: `docs/MIGRACAO-DRY-RUN.md`, `docs/SPRINT-7-PLANO.md` (se presente),
`.github/workflows/deploy.yml`, `docker-compose.prod.yml`, `docker/Caddyfile.prod`.
