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

exec streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
