"""Страница «Настройки» для Администратора: ключ DeepSeek и пользователи."""

from __future__ import annotations

import re

import streamlit as st

from ameri.auth import ROLES, User, hash_password, load_users, save_users

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
    st.write("Статус: " + ("✅ задан" if settings.api_key() else "❌ не задан"))
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
            login = login.strip().lower()
            if not re.fullmatch(r"[a-z0-9._-]{2,32}", login):
                st.error("Логин: 2–32 символа, латиница, цифры, точка, дефис, подчёркивание.")
            elif len(password) < 8:
                st.error("Пароль не короче 8 символов.")
            else:
                users[login] = User(login, name.strip() or login, role, hash_password(password))
                save_users(settings.users_file, users)
                get_users.clear()
                st.success(f"Пользователь {login} сохранён.")
                st.rerun()
    removable = [u for u in users if u != st.session_state["user"].login]
    if removable:
        with st.form("remove"):
            victim = st.selectbox("Удалить пользователя", removable)
            if st.form_submit_button("Удалить"):
                users.pop(victim)
                save_users(settings.users_file, users)
                get_users.clear()
                st.rerun()


def render() -> None:
    st.title("Настройки")
    render_update_panel()
    st.divider()
    _key_section()
    st.divider()
    _users_section()
