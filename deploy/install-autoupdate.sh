#!/usr/bin/env bash
# Подключить кнопку «Обновить сайт»: systemd следит за файлом-заявкой, который создаёт сайт.
# Запускать от root; повторный запуск безопасен.
set -euo pipefail
chmod +x /srv/ameri/app/deploy/autoupdate.sh
rm -f /etc/cron.d/ameri-autoupdate   # прежнее обновление по расписанию больше не используется

cat > /etc/systemd/system/ameri-update.service <<UNIT
[Unit]
Description=ameri: обновление из GitHub по кнопке на сайте

[Service]
Type=oneshot
ExecStart=/srv/ameri/app/deploy/autoupdate.sh
StandardOutput=append:/var/log/ameri-update.log
StandardError=append:/var/log/ameri-update.log
UNIT

cat > /etc/systemd/system/ameri-update.path <<UNIT
[Unit]
Description=ameri: заявка на обновление с сайта

[Path]
PathExists=/srv/ameri/data/update-request

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now ameri-update.path >/dev/null
echo "[ameri] Кнопка «Обновить сайт» подключена; журнал /var/log/ameri-update.log"
