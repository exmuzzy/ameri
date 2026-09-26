"""Страница «Доступ к API»: личные токены для скриптов и агентов."""

from __future__ import annotations

import streamlit as st

from ameri.store import ApiToken

from views.common import current_user, display_name, get_store

TERMS = {"30 дней": 30, "90 дней": 90, "1 год": 365, "Без срока": None}


def _site_url() -> str:
    try:
        host = st.context.headers.get("host")
    except Exception:  # noqa: BLE001 - вне браузера заголовков нет
        host = None
    return f"https://{host}" if host else "https://<адрес сайта>"


def _when(value: str | None) -> str:
    return value[:16].replace("T", " ") if value else "—"


def _token_row(token: ApiToken, show_owner: bool) -> None:
    left, right = st.columns([5, 1], vertical_alignment="center")
    state = "действует" if token.active else ("отозван" if token.revoked_at else "истёк")
    owner = f"{display_name(token.login)} · " if show_owner else ""
    left.markdown(
        f"**{token.name}** · {owner}{state}  \n"
        f"создан {_when(token.created_at)} · до {_when(token.expires_at) if token.expires_at else 'без срока'} · "
        f"последний запрос {_when(token.last_used_at)}"
    )
    if token.active and right.button("Отозвать", key=f"revoke-{token.id}"):
        get_store().revoke_api_token(token.id)
        st.rerun()


def render() -> None:
    user = current_user()
    store = get_store()
    st.title("Доступ к API")
    st.caption(
        "Токен даёт скрипту или агенту (Claude Code, Cursor) те же права, что у вас на сайте: "
        "чаты, вопросы ассистенту, расчётки. Храните его как пароль."
    )

    created = st.session_state.pop("new_api_token", None)
    if created:
        st.success("Токен создан. Скопируйте его сейчас — больше он не покажется.")
        st.code(created, language=None)

    with st.form("new_token", clear_on_submit=True):
        name = st.text_input("Название", placeholder="Например: Claude Code, ноутбук")
        term = st.selectbox("Срок действия", list(TERMS))
        if st.form_submit_button("Создать токен", type="primary"):
            token, _ = store.create_api_token(user.login, name, TERMS[term])
            st.session_state["new_api_token"] = token
            st.rerun()

    url = _site_url()
    with st.expander("Как пользоваться", icon=":material/terminal:"):
        st.markdown(f"Запросы — к `{url}/api/v1/…` с заголовком `Authorization: Bearer <токен>`. Описание — `{url}/api/docs`.")
        st.code(
            f'curl -s {url}/api/v1/chats -H "Authorization: Bearer $AMERI_TOKEN"\n'
            f'curl -s {url}/api/v1/chats/12/messages -H "Authorization: Bearer $AMERI_TOKEN" \\\n'
            '  -F action=duct_calc -F connection=socket -F text="Посчитай" -F files=@spec.xlsx',
            language="bash",
        )

    st.subheader("Ваши токены")
    mine = store.list_api_tokens(user.login)
    if not mine:
        st.caption("Токенов пока нет.")
    for token in mine:
        _token_row(token, show_owner=False)

    if user.role == "admin":
        others = [t for t in store.list_api_tokens() if t.login != user.login]
        if others:
            st.subheader("Токены сотрудников")
            for token in others:
                _token_row(token, show_owner=True)
