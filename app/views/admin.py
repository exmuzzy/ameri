"""Страница «Настройки» для Администратора: ключ DeepSeek и пользователи."""

from __future__ import annotations

import streamlit as st

from ameri.auth import ROLES, load_users
from ameri.users_service import UserError, delete_user, save_user

from views.common import get_settings, get_users
from views.updates import render_update_panel

ROLE_TITLES = {"admin": "Администратор", "leader": "Руководитель", "manager": "Менеджер"}


def _key_section() -> None:
    settings = get_settings()
    st.subheader("Ключ DeepSeek")
    if settings.deepseek_api_key:
        st.success("Ключ задан переменной окружения на сервере.")
        return
    st.caption("Ключ хранится только на сервере, в файле с доступом для владельца. На странице он не показывается.")
    st.write("Статус: " + ("ключ задан" if settings.api_key() else "ключ не задан"))
    with st.form("api_key", clear_on_submit=True):
        key = st.text_input("Новый ключ", type="password", placeholder="sk-…")
        if st.form_submit_button("Сохранить ключ", type="primary") and key.strip():
            settings.save_api_key(key)
            st.success("Ключ сохранён.")


def _users_section() -> None:
    settings = get_settings()
    users = load_users(settings.users_file)
    st.subheader("Пользователи")
    st.dataframe(
        [{"Логин": u.login, "Имя": u.name, "Роль": ROLE_TITLES[u.role]} for u in users.values()],
        hide_index=True,
        use_container_width=True,
    )
    with st.form("user", clear_on_submit=True):
        st.markdown("**Добавить пользователя или сменить пароль**")
        login = st.text_input("Логин (латиница, цифры, точка, дефис)")
        name = st.text_input("Имя")
        role = st.selectbox("Роль", ROLES, index=2, format_func=ROLE_TITLES.get)
        password = st.text_input("Пароль (не короче 8 символов)", type="password")
        if st.form_submit_button("Сохранить", type="primary"):
            try:
                saved = save_user(settings.users_file, login, name, role, password)
            except UserError as error:
                st.error(str(error))
            else:
                get_users.clear()
                st.success(f"Пользователь {saved.login} сохранён.")
                st.rerun()
    removable = [u for u in users if u != st.session_state["user"].login]
    if removable:
        with st.form("remove"):
            victim = st.selectbox("Удалить пользователя", removable)
            if st.form_submit_button("Удалить"):
                delete_user(settings.users_file, victim, st.session_state["user"])
                get_users.clear()
                st.rerun()


def render() -> None:
    st.title("Настройки")
    st.caption("Управление обновлениями, ключом ассистента и учётными записями")
    render_update_panel()
    st.divider()
    _key_section()
    st.divider()
    _users_section()
