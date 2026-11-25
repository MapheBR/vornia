# Provisionamento da VM Oracle Cloud (ARM) — Sprint 7

## 1. Conta e instância

1. **Converter a conta para PAYG** antes de qualquer coisa: Always Free continua $0/mês,
   mas a VM deixa de sofrer *Idle Reclamation*.
2. Criar instância ARM (Ampere A1, 2 OCPU / 12 GB RAM), Ubuntu 24.04 ARM64.
3. Chave SSH própria (nunca reutilizar chave de dev), IP público reservado.
4. `ssh -i ~/.ssh/vornia_deploy ubuntu@<IP>` para conectar.

## 2. Docker + Compose (ARM)

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker deploy
```

Validar: `docker --version`, `docker compose version`, `docker info`.

## 3. Firewall

Oracle Cloud (Security List): abrir **80** e **443**; bloquear todo o resto.
No sistema: `sudo ufw allow 80/tcp`, `sudo ufw allow 443/tcp`, `sudo ufw enable`.
Postgres/Redis/backend/frontend **nunca** publicados — ver `docker-compose.prod.yml`.

## 4. Usuário e diretório de deploy

```bash
sudo adduser --disabled-password deploy
sudo mkdir -p /opt/vornia && sudo chown deploy:deploy /opt/vornia
sudo -u deploy git clone https://github.com/MapheBR/vornia.git /opt/vornia
```

## 5. `.env` de produção

`sudo -u deploy cp /opt/vornia/.env.example /opt/vornia/.env`
Editar com `JWT_SECRET` forte, senhas das roles, `DATABASE_URL*`, `VORNIA_DOMAIN`
(ex.: `vornia-test.<ip>.sslip.io`) e `VORNIA_ACME_EMAIL`.
`chmod 600 /opt/vornia/.env` — o check de prontidão falha se estiver mais aberto.

## 6. Verificação

```bash
sudo -u deploy /opt/vornia/scripts/check-vm-readiness.sh /opt/vornia
```

Se imprimir **VM pronta para deploy.**, a VM está preparada. Só então o GitHub
Actions de deploy pode rodar.

## 7. Deploy

- Tag `v*` ou `workflow_dispatch` com a tag em `.github/workflows/deploy.yml`.
- Secrets necessários no repositório: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`,
  `DEPLOY_PATH`, `VORNIA_DOMAIN`, `VORNIA_ACME_EMAIL`, `DEPLOY_PORT` (opcional).
- Rollback: `sudo -u deploy /opt/vornia/scripts/rollback.sh /opt/vornia`.

## 8. Domínio/HTTPS

O Caddy (`docker/Caddyfile.prod`) usa `{$VORNIA_DOMAIN}` — variável, não fixa.
Para testes iniciais, use `sslip.io`/`nip.io` apontando para o IP da VM.
O Caddy obtém e renova o certificado Let's Encrypt automaticamente; a porta 80
serve apenas o redirect para HTTPS e os desafios ACME.
