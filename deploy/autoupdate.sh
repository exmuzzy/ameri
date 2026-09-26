#!/usr/bin/env bash
# Автообновление ameri из GitHub (запускается cron-ом раз в 5 минут, см. install-autoupdate.sh).
# Харнес и статьи (harness/, docs/) — просто подтягиваются в рабочую копию на томе данных, без перезапуска.
# Любые другие изменения (код, deploy/) — пересборка и перезапуск сайта.
set -euo pipefail

ROOT=/srv/ameri
BRANCH="${AMERI_BRANCH:-master}"
exec 9>/run/ameri-autoupdate.lock
flock -n 9 || exit 0

cd "$ROOT/app"
git fetch -q origin "$BRANCH"
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")
[ "$LOCAL" = "$REMOTE" ] && exit 0

CHANGED=$(git diff --name-only "$LOCAL" "$REMOTE")
git reset -q --hard "origin/$BRANCH"
echo "$(date -Is) обновление ${LOCAL:0:7} → ${REMOTE:0:7}"

# Рабочая копия Харнеса и статей, из которой читает сайт (может содержать утверждённые на сайте коммиты).
if [ -d "$ROOT/data/repo/.git" ]; then
  git -C "$ROOT/data/repo" pull -q --rebase origin "$BRANCH" \
    && echo "  харнес и статьи обновлены" \
    || { git -C "$ROOT/data/repo" rebase --abort 2>/dev/null || true; echo "  ВНИМАНИЕ: конфликт в харнесе, обновите вручную"; }
fi

if echo "$CHANGED" | grep -qvE '^(harness/|docs/|README\.md|CONTEXT\.md)'; then
  echo "  изменился код — пересборка"
  cd "$ROOT/app/deploy" && docker compose up -d --build 2>&1 | tail -n 3
fi
