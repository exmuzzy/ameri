"""Кнопка «Обновить сайт»: харнес и статьи — сразу, код — через службу обновления на сервере."""

from __future__ import annotations

import json
import time

import streamlit as st

from ameri.harness import HarnessRepo

from views.common import current_user, get_settings

STALE_REQUEST_SECONDS = 120


def _status() -> dict:
    path = get_settings().data_dir / "update-status.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def render_update_panel() -> None:
    settings = get_settings()
    request = settings.data_dir / "update-request"
    st.subheader("Обновление сайта")
    st.caption(
        "Берёт последнюю версию из GitHub (ветка master). Харнес и статьи обновляются сразу, "
        "без перезапуска. Если изменился код, сервер пересоберёт сайт — это займёт несколько минут, "
        "страница переподключится сама. Чаты и пользователи при обновлении сохраняются."
    )

    status = _status()
    if status:
        icon = {"done": "✅", "running": "⏳", "error": "⚠️"}.get(status.get("state"), "ℹ️")
        st.write(
            f"{icon} {status.get('message', '')} · версия `{status.get('commit', '?')}` · "
            f"{status.get('finished_at', '')[:16].replace('T', ' ')} · запросил: {status.get('requested_by', '—')}"
        )
    if request.exists() and time.time() - request.stat().st_mtime > STALE_REQUEST_SECONDS:
        st.warning(
            "Заявка на обновление висит больше двух минут: служба обновления на сервере не запущена. "
            "Администратору нужно один раз выполнить на сервере `bash /srv/ameri/app/deploy/install-autoupdate.sh`."
        )

    if st.button("🔄 Обновить сайт из репозитория", type="primary"):
        pulled = HarnessRepo(settings.harness_dir).pull()
        request.write_text(current_user().name, encoding="utf-8")
        st.success(f"{pulled}. Заявка на обновление кода отправлена.")
        st.rerun()
