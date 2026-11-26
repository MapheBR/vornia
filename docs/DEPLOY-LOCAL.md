# Deploy local (Self-hosting) com Tailscale — Vornia

Este é o guia oficial de deploy **sem custo de nuvem**: o Vornia roda em um
computador da Tecnova ligado 24h, e o acesso remoto é feito apenas pela
**Tailscale** (VPN mesh gratuita). **Nenhuma porta é aberta no roteador** e o
sistema **não é exposto à internet pública**.

## 1. Visão geral

```
[Funcionário] -- Tailscale --> 100.x.y.z:8080 --> Caddy --> Next.js / FastAPI
                                                      \--> PostgreSQL + Redis (redes internas)
```

- Custo: **R$ 0** (Docker Compose + Tailscale plano gratuito).
- Acesso: somente dispositivos autenticados no *tailnet* da Tecnova.
- HTTPS: opcional, com certificado emitido pelo próprio Tailscale (`*.ts.net`).
- Deploy: `git pull` + `docker compose up -d --build` no computador local.
- O GitHub Actions de deploy remoto está **pausado** (`deploy.yml` com `if: false`).

## 2. Requisitos do computador servidor

| Item | Mínimo recomendado |
|---|---|
| Sistema | Windows 10/11 Pro com WSL2 **ou** Linux (Ubuntu 24.04) |
| CPU | 4 núcleos (2 OCPU equivalente) |
| RAM | 8 GB (12 GB confortável) |
| Disco | 40 GB livres (SSD recomendado) |
| Rede | Conectado ao roteador da Tecnova, IP local fixo (reserva DHCP) |
| Energia | Ligado 24h; desativar suspensão/hibernação |

## 3. Instalação do Docker

### Linux (Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
docker --version && docker compose version && docker run --rm hello-world
```

### Windows

1. Habilitar virtualização na BIOS e o recurso **Windows Subsystem for Linux**.
2. Instalar **Docker Desktop for Windows** (backend WSL2).
3. Em *Settings → Resources*: CPUs ≥ 4, Memory ≥ 8 GB, Disk ≥ 40 GB.
4. Validar no PowerShell:

```powershell
docker --version
docker compose version
docker run --rm hello-world
```

>(no PowerShell, use `docker compose ...` comum; evite `&&` — use `;` para separar comandos.)

## 4. Tailscale no servidor

1. Criar conta gratuita em <https://tailscale.com> e escolher um *tailnet* (ex.: `tecnova`).
2. Instalar:
   - **Windows:** baixar o instalador em <https://tailscale.com/download/windows> e executar.
   - **Linux:**
     ```bash
     curl -fsSL https://tailscale.com/install.sh | sh
     sudo tailscale up --ssh
     ```
3. Autenticar com a conta Google/Microsoft da Tecnova no link mostrado.
4. Anotar o **IP virtual** (ex.: `100.74.12.9`):

```bash
tailscale ip -4
```

5. Habilitar **MagicDNS** no console do Tailscale (*DNS → MagicDNS*). Isso dá um nome
   tipo `vornia-servidor.tail123456.ts.net` — útil para o certificado HTTPS opcional.

## 5. Tailscale nos dispositivos dos funcionários

1. Instalar o cliente Tailscale (Windows/macOS/iOS/Android) com a **mesma conta**
   e o mesmo tailnet da Tecnova.
2. Aprovar os dispositivos no console (*Machines → Approve*), se a aprovação estiver ativa.
3. Conferir que o equipamento recebeu um IP `100.x.y.z` e que consegue pingar o servidor:

```bash
ping 100.74.12.9
```

4. **Acesso restrito:** no console, *Access Controls*, liberar apenas usuários/grupos
   autorizados para a tag do servidor. Exemplo (ACL):

```json
{
  "groups": { "group:funcionarios": ["ana@tecnova.com.br", "joao@tecnova.com.br"] },
  "acls": [
    { "action": "accept", "src": ["group:funcionarios"], "dst": ["tag:vornia:8080"] }
  ],
  "tagOwners": { "tag:vornia": ["admin@tecnova.com.br"] }
}
```

5. No servidor, aplicar a tag:

```bash
sudo tailscale up --advertise-tags=tag:vornia   # Linux
```

No Windows, use *Tailscale → Properties → Machine tags* (ou o comando equivalente no Prompt).

**Nunca** abrir portas no roteador. O Tailscale cria a conexão de saída; não há
port forwarding e nem IP público.

## 6. Firewall local

- **Linux (ufw):** liberar apenas a interface Tailscale na porta 8080:

```bash
sudo ufw allow in on tailscale0 to any port 8080 proto tcp
```

  Se a distro usar firewalld: `sudo firewall-cmd --permanent --add-port=8080/tcp --zone=trusted`.

- **Windows:** o Defender bloqueia por padrão conexões de redes "Públicas".
  Marcar a rede como **Privada** e criar regra de entrada para a porta 8080
  apenas para o adaptador `Tailscale`:

```powershell
New-NetFirewallRule -DisplayName "Vornia Tailscale 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -InterfaceAlias "Tailscale*" -Action Allow
```

## 7. Caddy na rede local (sem domínio público)

O `docker/Caddyfile.prod` foi adaptado: **`auto_https off`**, escuta `:80`,
**não exige `VORNIA_DOMAIN`** e não faz desafios ACME. O `docker-compose.local.yml`
publica **8080** (e **8443** no modo HTTPS opcional) e derruba as portas internas
de Postgres/Redis/backend/frontend:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

Os funcionários acessam:

```
http://100.74.12.9:8080
```

ou, com MagicDNS:

```
http://vornia-servidor.tail123456.ts.net:8080
```

### HTTPS opcional com certificado do Tailscale

O Tailscale emite certificados gratuitos para nomes `*.ts.net`:

```bash
sudo tailscale cert vornia-servidor.tail123456.ts.net
# gera: vornia-servidor.tail123456.ts.net.crt e .key
```

1. Coloque os arquivos em `docker/certs/` (o compose já monta esse diretório em
   `/etc/caddy/certs`).
2. Em `docker-compose.local.yml`, troque a linha do volume do Caddy por:

```yaml
- ./docker/Caddyfile.tailscale-https:/etc/caddy/Caddyfile:ro
```

3. Configure o `.env`:

```dotenv
VORNIA_TLS_CERT=/etc/caddy/certs/vornia-servidor.tail123456.ts.net.crt
VORNIA_TLS_KEY=/etc/caddy/certs/vornia-servidor.tail123456.ts.net.key
COOKIE_SECURE=true
```

O acesso passa a ser `https://vornia-servidor.tail123456.ts.net:8443`
(porta 8443 publicada pelo compose local). O HTTP na 8080 redireciona para HTTPS.

> Com HTTP puro na VPN mantenha `COOKIE_SECURE=false` — o tráfego já está
> criptografado pelo Tailscale. Use `COOKIE_SECURE=true` apenas no modo HTTPS.

## 8. Preparar o código e o `.env`

```bash
# Linux
sudo mkdir -p /opt/vornia && sudo chown $USER:$USER /opt/vornia
git clone https://github.com/MapheBR/vornia.git /opt/vornia
```

```powershell
# Windows (PowerShell)
git clone https://github.com/MapheBR/vornia.git C:\vornia
cd C:\vornia
```

Copiar e editar o `.env`:

```bash
cp .env.example .env
chmod 600 .env     # Linux
```

Ajustar no mínimo: senhas do Postgres/roles, `JWT_SECRET` (`openssl rand -hex 32`),
`COOKIE_SECURE`, `BACKUP_DIR` e, se usar HTTPS, `VORNIA_TLS_CERT`/`VORNIA_TLS_KEY`.
**Não é necessário definir `VORNIA_DOMAIN`** no modo HTTP (padrão).

> O frontend usa caminhos relativos `/api/v1/...`, então funciona tanto em
> `localhost:8080` quanto no IP do Tailscale sem precisar de `NEXT_PUBLIC_API_URL`.

## 9. Deploy / atualização (sem GitHub Actions)

```bash
cd /opt/vornia
git pull --ff-only origin main
docker compose -f docker-compose.yml -f docker-compose.local.yml pull
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose exec -T backend alembic upgrade head
curl -fsS http://localhost:8080/health
```

No Windows, o comando é idêntico no PowerShell (sem `&&`, use `;`).

Validação de prontidão:

```bash
chmod +x scripts/check-local-readiness.sh   # apenas na primeira vez (Linux)
./scripts/check-local-readiness.sh          # Linux/WSL
# Windows: bash scripts/check-local-readiness.sh
```

## 10. Acesso dos funcionários — resumo

| Passo | Funcionário |
|---|---|
| 1 | Instalar Tailscale e entrar com a conta da Tecnova |
| 2 | Aguardar aprovação do dispositivo no console |
| 3 | Abrir `http://100.74.12.9:8080` (ou o nome MagicDNS/HTTPS) |
| 4 | Fazer login com e-mail/senha fornecidos pelo gestor |

## 11. Backup local

```bash
BACKUP_DIR=/opt/vornia/backups ./scripts/backup-postgres.sh
# restaurar (teste):
./scripts/backup-postgres.sh --restore /opt/vornia/backups/<arquivo>.sql.gz
```

Manter cópias também em um disco externo ou outro dispositivo do tailnet.

## 12. Checklist de go-live local

- [ ] Docker e Compose funcionando (`hello-world`)
- [ ] Tailscale no servidor com IP `100.x.y.z`
- [ ] Dispositivos dos funcionários aprovados e ACL aplicada
- [ ] Nenhuma porta aberta no roteador
- [ ] `check-local-readiness.sh` verde
- [ ] `http://100.x.y.z:8080/health` responde `{"status":"ok"}`
- [ ] Login/registro e refresh funcionando
- [ ] Migration `head` aplicada
- [ ] Backup + restore testados localmente
- [ ] Migração PontoJa: `--dry-run` conferido e `--backup-first --apply` executado
- [ ] Aviso à Tecnova com o endereço de acesso

## 13. Diferenças em relação ao plano Oracle (arquivado)

| Item | Oracle (arquivado) | Local (atual) |
|---|---|---|
| Custo | $0 (Always Free PAYG) | R$ 0 |
| Acesso | HTTPS público + domínio | Tailscale, sem internet pública |
| Deploy | Actions → SSH por tag | `git pull` + `docker compose up -d --build` |
| Certificado | Let's Encrypt | Opcional: `tailscale cert` (`*.ts.net`) |
| Firewall | Security List + iptables/ufw | Firewall local + Tailscale ACL |

Referência histórica: `docs/DEPLOY-VM.md` (mantido apenas como registro).
