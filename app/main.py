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

ROLE_TITLES = {"admin": "Администратор", "leader": "Руководитель", "manager": "Менеджер"}

st.set_page_config(page_title="ameri", page_icon="📐", layout="wide")


def login_page() -> None:
    st.title("ameri")
    st.caption("Рабочее место менеджеров по воздуховодам")
    with st.form("login"):
        login = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти", type="primary")
    if submitted:
        user = authenticate(get_users(), login, password)
        if user is None:
            st.error("Неверный логин или пароль.")
        else:
            st.session_state["user"] = user
            st.rerun()
    about.render(compact=True)


user = st.session_state.get("user")
if user is None:
    login_page()
    st.stop()

with st.sidebar:
    st.markdown(f"**{user.name}**  \n{ROLE_TITLES[user.role]}")
    if st.button("Выйти"):
        st.session_state.clear()
        st.rerun()

access = get_access()
chats_page = st.Page(chats.render, title="Чаты", icon="💬", url_path="chats", default=True)
work = [
    chats_page,
    st.Page(onboarding.render, title="Новому сотруднику", icon="🎓", url_path="onboarding"),
    st.Page(about.render, title="О проекте", icon="📐", url_path="about"),
    st.Page(howto.render, title="Как работать", icon="📖", url_path="howto"),
    st.Page(howto.render_examples, title="Примеры работы", icon="🧩", url_path="examples"),
]
lead = []
if access.can(user, "stats.view"):
    lead.append(st.Page(quality.render, title="Качество", icon="📊", url_path="quality"))
if access.can(user, "harness.edit"):
    lead.append(st.Page(harness_page.render, title="Харнес", icon="🧠", url_path="harness"))
if user.role == "admin":
    lead.append(st.Page(admin.render, title="Настройки", icon="⚙️", url_path="settings"))
st.session_state["pages"] = {"chats": chats_page}
page = st.navigation({"Работа": work, "Руководителю": lead} if lead else work)
page.run()
