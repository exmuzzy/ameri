#!/usr/bin/env bash
# Установка ameri на VPS Beget, где маркетплейс оставил недоустановленный Coolify.
# Убирает только контейнеры Coolify (они заняли порты 80 и 443) и запускает bootstrap.sh.
#   curl -fsSL https://raw.githubusercontent.com/exmuzzy/ameri/master/deploy/beget.sh | bash
set -euo pipefail

if command -v docker >/dev/null; then
  ids=$(docker ps -aq --filter "name=coolify" || true)
  if [ -n "$ids" ]; then
    echo "[ameri] Убираю контейнеры Coolify: $(docker ps -a --filter name=coolify --format '{{.Names}}' | tr '\n' ' ')"
    docker rm -f $ids >/dev/null
  fi
fi

curl -fsSL https://raw.githubusercontent.com/exmuzzy/ameri/master/deploy/bootstrap.sh -o /root/ameri-bootstrap.sh
bash /root/ameri-bootstrap.sh
