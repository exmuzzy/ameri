#!/usr/bin/env bash
# Включить автообновление ameri из GitHub раз в 5 минут. Запускать от root; повторный запуск безопасен.
set -euo pipefail
chmod +x /srv/ameri/app/deploy/autoupdate.sh
cat > /etc/cron.d/ameri-autoupdate <<CRON
*/5 * * * * root /srv/ameri/app/deploy/autoupdate.sh >> /var/log/ameri-update.log 2>&1
CRON
echo "[ameri] Автообновление включено: раз в 5 минут, журнал /var/log/ameri-update.log"
