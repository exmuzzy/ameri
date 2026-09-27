"""Кнопка «Обновить сайт»: харнес и статьи — сразу, код — через службу обновления на сервере."""

from __future__ import annotations

import streamlit as st

from ameri.updates import request_stale, request_update, update_in_progress, update_status

from views.common import current_user, get_settings


def _start_update() -> None:
    """Колбэк кнопки: выполняется до перерисовки, поэтому кнопка сразу становится неактивной."""

    settings = get_settings()
    if update_in_progress(settings):  # двойной клик или соседняя вкладка
        return
    st.session_state["update_message"] = request_update(settings, current_user().name)


def render_update_panel() -> None:
    st.subheader("Обновление сайта")
    st.caption(
        "Берёт последнюю версию из GitHub (ветка master). Харнес и статьи обновляются сразу, "
        "без перезапуска. Если изменился код, сервер пересоберёт сайт — это займёт несколько минут; "
        "во время пересборки (1–2 минуты) страница может показать «Connection error» или 502 — это нормально: "
        "подождите и обновите страницу. Чаты и пользователи при обновлении сохраняются."
    )
    _update_status_block()


@st.fragment(run_every=5)
def _update_status_block() -> None:
    settings = get_settings()
    busy = update_in_progress(settings)

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
    message = st.session_state.pop("update_message", None)
    if message:
        st.success(f"{message}. Заявка на обновление кода отправлена.")

    st.button(
        "Идёт обновление…" if busy else "Обновить сайт из репозитория",
        type="primary",
        icon=":material/hourglass_top:" if busy else ":material/sync:",
        disabled=busy,
        on_click=_start_update,
        key="update_site",
    )
    if busy:
        st.caption("Кнопка станет доступна, когда обновление закончится; статус обновляется сам.")
