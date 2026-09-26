"""Страница «Новому сотруднику»: чек-лист и учебный Чат."""

from __future__ import annotations

import streamlit as st

from views.common import current_user, get_settings, get_store
from views.theme import article

STEPS = [
    ("read_about", "Прочитать «О проекте»: что делает ameri и главный принцип «модель не калькулятор»."),
    ("read_howto", "Прочитать «Как работать»: чаты, действия, уточнения."),
    ("sandbox", "Открыть учебный чат и задать ассистенту вопрос по учебной спецификации."),
    ("duct_calc", "Построить в учебном чате расчётку по учебной спецификации и скачать XLSX."),
    ("rules", "Запомнить: никаких клиентских ФИО, телефонов, почт и паспортов в чатах."),
    ("first_real", "Создать первый рабочий чат по своей задаче."),
]
SANDBOX_TITLE = "Учебный чат"


def _open_sandbox() -> None:
    store = get_store()
    user = current_user()
    existing = [c for c in store.list_chats(owner=user.login) if c.title == SANDBOX_TITLE]
    if existing:
        chat_id = existing[0].id
    else:
        chat_id = store.create_chat(SANDBOX_TITLE, user.login)
        sample = get_settings().site_dir / "sample_spec.md"
        store.add_message(
            chat_id,
            author="assistant",
            role="assistant",
            action="Онбординг",
            content=(
                "Это учебный чат: здесь можно пробовать всё без последствий.\n\n"
                "1. Выберите действие **Вопрос ассистенту** и спросите: «Какие позиции в учебной спецификации?»\n"
                "2. Скачайте файл ниже, выберите **Расчётка воздуховодов**, тип соединения **Фланец**, "
                "приложите файл скрепкой и отправьте.\n"
                "3. Посмотрите предупреждения в ответе и скачайте XLSX."
            ),
            files=[(sample.name, sample.read_bytes())] if sample.is_file() else [],
        )
    get_store().set_onboarding(user.login, "sandbox", True)
    st.switch_page(st.session_state["pages"]["chats"], query_params={"chat": str(chat_id)})


def render() -> None:
    user = current_user()
    store = get_store()
    st.title("Новому сотруднику")
    st.caption("Первые шаги · 15–20 минут")
    article((get_settings().site_dir / "onboarding.md").read_text(encoding="utf-8"))

    done = store.onboarding_done(user.login)
    st.progress(len(done & {k for k, _ in STEPS}) / len(STEPS), text=f"Выполнено {len(done)} из {len(STEPS)}")
    st.subheader("Ваш чек-лист")
    for key, text in STEPS:
        checked = st.checkbox(text, value=key in done, key=f"onb-{key}")
        if checked != (key in done):
            store.set_onboarding(user.login, key, checked)
            st.rerun()
    if st.button("Открыть учебный чат", type="primary", icon=":material/forum:"):
        _open_sandbox()
