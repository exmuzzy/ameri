"""Точка входа сайта ameri: вход и навигация."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ameri.auth import authenticate  # noqa: E402
from views import about, admin, chats, harness_page, howto, onboarding, quality  # noqa: E402
from views.common import get_access  # noqa: E402
from views.common import get_users  # noqa: E402
from views.theme import STATIC, apply_theme  # noqa: E402

ROLE_TITLES = {"admin": "Администратор", "leader": "Руководитель", "manager": "Менеджер"}

st.set_page_config(page_title="ameri · Рабочее место", page_icon=str(STATIC / "mark.svg"), layout="wide")
apply_theme()
st.logo(str(STATIC / "wordmark.svg"), size="large")


def login_page() -> None:
    left, center, right = st.columns([1, 1.5, 1])
    with center:
        with st.container(border=True):
            st.image(str(STATIC / "wordmark.svg"), width=158)
            st.subheader("Рабочее место")
            st.caption("Чаты, спецификации и расчётки — в одном месте.")
            with st.form("login"):
                login = st.text_input("Логин")
                password = st.text_input("Пароль", type="password")
                submitted = st.form_submit_button("Войти", type="primary", use_container_width=True)
        st.caption("Для менеджеров по полипропиленовым воздуховодам.")
        with st.expander("Что такое ameri"):
            about.render(compact=True)
    if submitted:
        user = authenticate(get_users(), login, password)
        if user is None:
            st.error("Неверный логин или пароль.")
        else:
            st.session_state["user"] = user
            st.rerun()


user = st.session_state.get("user")
if user is None:
    login_page()
    st.stop()

with st.sidebar:
    st.caption("УЧЁТНАЯ ЗАПИСЬ")
    st.markdown(f"**{user.name}**  \n{ROLE_TITLES[user.role]}")
    if st.button("Выйти", icon=":material/logout:"):
        st.session_state.clear()
        st.rerun()

access = get_access()
chats_page = st.Page(chats.render, title="Чаты", icon=":material/forum:", url_path="chats", default=True)
work = [
    chats_page,
    st.Page(onboarding.render, title="Новому сотруднику", icon=":material/school:", url_path="onboarding"),
    st.Page(about.render, title="О проекте", icon=":material/info:", url_path="about"),
    st.Page(howto.render, title="Как работать", icon=":material/menu_book:", url_path="howto"),
    st.Page(howto.render_examples, title="Примеры работы", icon=":material/description:", url_path="examples"),
]
lead = []
if access.can(user, "stats.view"):
    lead.append(st.Page(quality.render, title="Качество", icon=":material/monitoring:", url_path="quality"))
if access.can(user, "harness.edit"):
    lead.append(st.Page(harness_page.render, title="Харнес", icon=":material/rule:", url_path="harness"))
if user.role == "admin":
    lead.append(st.Page(admin.render, title="Настройки", icon=":material/settings:", url_path="settings"))
st.session_state["pages"] = {"chats": chats_page}
page = st.navigation({"Работа": work, "Руководителю": lead} if lead else work)
page.run()
