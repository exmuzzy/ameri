"""Кнопка «Обновить сайт»: харнес и статьи — сразу, код — через службу обновления на сервере."""

from __future__ import annotations

import streamlit as st

from ameri.updates import request_stale, request_update, update_status

from views.common import current_user, get_settings


def render_update_panel() -> None:
    settings = get_settings()
    st.subheader("Обновление сайта")
    st.caption(
        "Берёт последнюю версию из GitHub (ветка master). Харнес и статьи обновляются сразу, "
        "без перезапуска. Если изменился код, сервер пересоберёт сайт — это займёт несколько минут, "
        "страница переподключится сама. Чаты и пользователи при обновлении сохраняются."
    )

    status = update_status(settings)
    if status:
        label = {"done": "Готово", "running": "Выполняется", "error": "Ошибка"}.get(status.get("state"), "Статус")
        st.write(
            f"**{label}** · {status.get('message', '')} · версия `{status.get('commit', '?')}` · "
            f"{status.get('finished_at', '')[:16].replace('T', ' ')} · запросил: {status.get('requested_by', '—')}"
        )
    if request_stale(settings):
        st.warning(
            "Заявка на обновление висит больше двух минут: служба обновления на сервере не запущена. "
            "Администратору нужно один раз выполнить на сервере `bash /srv/ameri/app/deploy/install-autoupdate.sh`."
        )

    if st.button("Обновить сайт из репозитория", type="primary", icon=":material/sync:"):
        pulled = request_update(settings, current_user().name)
        st.success(f"{pulled}. Заявка на обновление кода отправлена.")
        st.rerun()
