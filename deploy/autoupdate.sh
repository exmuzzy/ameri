#!/usr/bin/env bash
# Обновление ameri из GitHub по кнопке «Обновить сайт» (сайт создаёт /srv/ameri/data/update-request,
# systemd-юнит ameri-update.path запускает этот скрипт). Можно запустить и вручную.
# Харнес и статьи (harness/, docs/) подтягиваются без перезапуска; код — пересборка и перезапуск сайта.
set -uo pipefail

ROOT=/srv/ameri
BRANCH="${AMERI_BRANCH:-master}"
STATUS="$ROOT/data/update-status.json"
REQUEST="$ROOT/data/update-request"
exec 9>/run/ameri-autoupdate.lock
flock -n 9 || exit 0

requested_by=$(cat "$REQUEST" 2>/dev/null || echo "вручную")
rm -f "$REQUEST"

status() {  # status <state> <message>
  printf '{"state": "%s", "message": "%s", "commit": "%s", "requested_by": "%s", "finished_at": "%s"}\n' \
    "$1" "$2" "$(git -C "$ROOT/app" rev-parse --short HEAD)" "$requested_by" "$(date -Is)" > "$STATUS.tmp"
  mv "$STATUS.tmp" "$STATUS"
}

cd "$ROOT/app"
status running "Проверяю обновления"
if ! git fetch -q origin "$BRANCH"; then
  status error "Не удалось связаться с GitHub"; exit 1
fi
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ -d "$ROOT/data/repo/.git" ]; then
  git -C "$ROOT/data/repo" pull -q --rebase origin "$BRANCH" \
    || { git -C "$ROOT/data/repo" rebase --abort 2>/dev/null; status error "Конфликт в харнесе: правило изменили и на сайте, и в репозитории"; exit 1; }
fi

if [ "$LOCAL" = "$REMOTE" ]; then
  status done "Уже последняя версия"; exit 0
fi

CHANGED=$(git diff --name-only "$LOCAL" "$REMOTE")
git reset -q --hard "origin/$BRANCH"
if echo "$CHANGED" | grep -qvE '^(harness/|docs/|README\.md|CONTEXT\.md)'; then
  status running "Изменился код — пересобираю сайт, это займёт несколько минут"
  # Резервная копия базы перед пересборкой (последние 10 копий).
  mkdir -p "$ROOT/backups"
  python3 -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d)" \
    "$ROOT/data/ameri.sqlite3" "$ROOT/backups/ameri-before-update-$(date +%F-%H%M%S).sqlite3" 2>/dev/null || true
  ls -1t "$ROOT"/backups/ameri-before-update-*.sqlite3 2>/dev/null | tail -n +11 | xargs -r rm -f
  if (cd "$ROOT/app/deploy" && docker compose up -d --build) >> /var/log/ameri-update.log 2>&1; then
    status done "Сайт пересобран и перезапущен"
  else
    status error "Пересборка не удалась, см. /var/log/ameri-update.log"; exit 1
  fi
else
  status done "Харнес и статьи обновлены"
fi
