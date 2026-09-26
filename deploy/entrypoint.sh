#!/bin/sh
# Запуск сайта в контейнере. Если задан AMERI_GIT_URL, Харнес берётся из рабочей копии
# репозитория на постоянном томе: утверждённые правила коммитятся туда и отправляются в GitHub.
set -e

if [ -n "${AMERI_GIT_URL:-}" ]; then
  REPO_DIR="${AMERI_DATA_DIR:-/data}/repo"
  BRANCH="${AMERI_GIT_BRANCH:-master}"
  if [ -d "$REPO_DIR/.git" ]; then
    git -C "$REPO_DIR" remote set-url origin "$AMERI_GIT_URL"
    git -C "$REPO_DIR" pull -q --rebase origin "$BRANCH" || echo "[ameri] git pull не удался, работаю с локальной копией"
  else
    git clone -q --branch "$BRANCH" "$AMERI_GIT_URL" "$REPO_DIR"
  fi
  git -C "$REPO_DIR" config user.name "ameri"
  git -C "$REPO_DIR" config user.email "ameri@localhost"
  export AMERI_HARNESS_DIR="$REPO_DIR/harness"
  export AMERI_SITE_DIR="$REPO_DIR/docs/site"
  export AMERI_GIT_PUSH="${AMERI_GIT_PUSH:-1}"
fi

# Два процесса: сайт (Streamlit) и HTTP API (uvicorn). Если один из них завершился, останавливаем
# и второй и выходим с ошибкой — Docker перезапустит контейнер (restart: unless-stopped).
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true &
SITE_PID=$!
uvicorn --app-dir src ameri.api:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 30 &
API_PID=$!

stop() {
  kill "$SITE_PID" "$API_PID" 2>/dev/null
  wait
}
trap 'stop; exit 0' TERM INT

while kill -0 "$SITE_PID" 2>/dev/null && kill -0 "$API_PID" 2>/dev/null; do
  sleep 5
done
echo "[ameri] процесс сайта или API завершился, перезапуск контейнера"
stop
exit 1
