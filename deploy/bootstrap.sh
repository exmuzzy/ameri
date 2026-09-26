#!/usr/bin/env bash
# Установка ameri на чистую Ubuntu 24.04. Запускать от root; повторный запуск безопасен.
# Необязательные переменные:
#   AMERI_ADMIN_PASSWORD — пароль первого Администратора (логин admin); иначе генерируется
#   AMERI_REPO, AMERI_BRANCH — откуда брать код (по умолчанию GitHub exmuzzy/ameri, master)
#   SITE_ADDRESS — адрес сайта; по умолчанию <ip>.sslip.io
set -euo pipefail

REPO="${AMERI_REPO:-https://github.com/exmuzzy/ameri.git}"
BRANCH="${AMERI_BRANCH:-master}"
ROOT=/srv/ameri
export DEBIAN_FRONTEND=noninteractive

log() { echo "[ameri] $*"; }

log "Пакеты и защита сервера"
apt-get update -q
apt-get install -y -q ca-certificates curl git ufw fail2ban unattended-upgrades python3
ufw allow OpenSSH >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null
systemctl enable --now fail2ban >/dev/null

if ! swapon --show | grep -q /swapfile; then
  log "Swap 2 ГБ"
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

if ! command -v docker >/dev/null; then
  log "Docker"
  curl -fsSL https://get.docker.com | sh
fi

log "Код ${REPO} (${BRANCH})"
mkdir -p "$ROOT"/{data,duct-calc,backups}
chmod 700 "$ROOT/data"
if [ -d "$ROOT/app/.git" ]; then
  git -C "$ROOT/app" fetch -q origin "$BRANCH" && git -C "$ROOT/app" reset -q --hard "origin/$BRANCH"
else
  git clone -q --branch "$BRANCH" "$REPO" "$ROOT/app"
fi

if [ ! -f "$ROOT/data/users.toml" ]; then
  PASSWORD="${AMERI_ADMIN_PASSWORD:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')}"
  HASH=$(PASSWORD="$PASSWORD" python3 -c "import os,sys; sys.path.insert(0,'$ROOT/app/src'); from ameri.auth import hash_password; print(hash_password(os.environ['PASSWORD']))")
  mkdir -p "$ROOT/data"
  printf '[users.admin]\nname = "Администратор"\nrole = "admin"\npassword_hash = "%s"\n' "$HASH" > "$ROOT/data/users.toml"
  chmod 600 "$ROOT/data/users.toml"
  if [ -z "${AMERI_ADMIN_PASSWORD:-}" ]; then
    echo "$PASSWORD" > /root/ameri-admin-password.txt && chmod 600 /root/ameri-admin-password.txt
    log "Пароль admin сохранён в /root/ameri-admin-password.txt"
    ADMIN_NOTE="Логин: admin   Пароль: ${PASSWORD}"
  fi
fi

if [ -z "${SITE_ADDRESS:-}" ]; then
  IP=$(curl -fsS4 https://api.ipify.org || hostname -I | awk '{print $1}')
  SITE_ADDRESS="${IP//./-}.sslip.io"
fi
echo "SITE_ADDRESS=${SITE_ADDRESS}" > "$ROOT/app/deploy/.env"

log "Ночной бэкап"
cat > /etc/cron.d/ameri-backup <<CRON
30 3 * * * root tar -czf $ROOT/backups/ameri-\$(date +\%F).tgz -C $ROOT data && find $ROOT/backups -name 'ameri-*.tgz' -mtime +14 -delete
CRON

bash "$ROOT/app/deploy/install-autoupdate.sh"

log "Запуск"
cd "$ROOT/app/deploy"
docker compose up -d --build
log "Готово: https://${SITE_ADDRESS}"
[ -n "${ADMIN_NOTE:-}" ] && log "$ADMIN_NOTE"
log "Ключ DeepSeek вставьте на странице «Настройки» под admin."
