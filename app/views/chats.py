"""Страница «Чаты»: история, новый Чат, переписка с Ассистентом."""

from __future__ import annotations

from contextlib import nullcontext

import streamlit as st

from ameri import actions, chat_service
from ameri.chat_service import ACTION_DUCT, ACTION_NOTE
from ameri.store import Chat, Feedback, Message

from views.common import current_user, display_name, get_access, get_settings, get_store, get_users



def _visible_chats(query: str, author: str | None) -> list[Chat]:
    return chat_service.visible_chats(get_store(), get_access(), current_user(), query, author)


def _can_open(chat: Chat) -> bool:
    return chat_service.can_open(get_access(), current_user(), chat)


def _select(chat_id: int) -> None:
    st.query_params["chat"] = str(chat_id)


def _history_column() -> None:
    user = current_user()
    with st.popover("➕ Новый чат", use_container_width=True, disabled=not get_access().can(user, "chat.create")):
        with st.form("new_chat", clear_on_submit=True):
            title = st.text_input("Название", placeholder="Объект, заказ или задача")
            if st.form_submit_button("Создать", type="primary"):
                _select(get_store().create_chat(title, user.login))
                st.rerun()

    query = st.text_input("Поиск", placeholder="Название или текст", label_visibility="collapsed")
    author = None
    if get_access().can(user, "chat.view_all"):
        logins = sorted(get_users())
        choice = st.selectbox(
            "Автор", ["Все"] + logins, format_func=lambda x: x if x == "Все" else display_name(x)
        )
        author = None if choice == "Все" else choice

    chats = _visible_chats(query, author)
    if not chats:
        st.caption("Чатов пока нет.")
    selected = st.query_params.get("chat")
    for chat in chats:
        label = chat.title
        caption = f"{display_name(chat.owner)} · {chat.updated_at[:16].replace('T', ' ')} · {chat.message_count} сообщ."
        if st.button(
            label,
            key=f"chat-{chat.id}",
            help=caption,
            use_container_width=True,
            type="primary" if selected == str(chat.id) else "secondary",
        ):
            _select(chat.id)
            st.rerun()


def _feedback_badges(items: list[Feedback]) -> str:
    marks = []
    for item in items:
        mark = "👍" if item.rating > 0 else "👎"
        if item.corrected_text:
            mark += "✏️"
        if item.status == "proposed":
            mark += " (правило на утверждении)"
        elif item.status == "applied":
            mark += f" (в харнесе {item.commit_sha or ''})"
        marks.append(f"{mark} {display_name(item.reviewer)}")
    return " · ".join(marks)


def _review_controls(chat: Chat, message: Message) -> None:
    """Оценка и Исправление ответа Ассистента Руководителем."""

    store = get_store()
    user = current_user()
    col_like, col_dislike, col_fix = st.columns([1, 1, 6])
    if col_like.button("👍", key=f"like-{message.id}", help="Хороший ответ"):
        store.add_feedback(message.id, reviewer=user.login, rating=1)
        st.rerun()
    if col_dislike.button("👎", key=f"dislike-{message.id}", help="Плохой ответ"):
        store.add_feedback(message.id, reviewer=user.login, rating=-1)
        st.rerun()
    with col_fix.popover("✏️ Исправить и научить"):
        with st.form(f"fix-{message.id}", clear_on_submit=True):
            corrected = st.text_area("Как надо было ответить", value=message.content, height=200)
            comment = st.text_input("Что было не так (для истории)")
            rule = st.text_area(
                "Правило, которое надо запомнить (необязательно)",
                placeholder="Например: клапан считать как 2 метра прямого участка того же сечения.",
            )
            as_example = st.checkbox("Сохранить вопрос и правильный ответ как пример для ассистента")
            if st.form_submit_button("Исправить", type="primary"):
                chat_service.review_message(
                    store,
                    chat,
                    message,
                    user,
                    rating=-1,
                    comment=comment,
                    corrected_text=corrected,
                    rule_text=rule,
                    as_example=as_example,
                )
                if rule.strip() or as_example:
                    st.toast("Исправление отправлено в чат; правило ждёт утверждения на странице «Харнес».")
                st.rerun()


def _render_message(chat: Chat, message: Message, feedback: list[Feedback], can_review: bool) -> None:
    avatar = "📐" if message.role == "assistant" else None
    with st.chat_message(message.role, avatar=avatar):
        meta = f"**{display_name(message.author)}** · {message.created_at[:16].replace('T', ' ')} UTC"
        if message.action:
            meta += f" · {message.action}"
        st.caption(meta)
        st.markdown(message.content)
        for attachment in message.attachments:
            if attachment.path.is_file():
                st.download_button(
                    f"📎 {attachment.name} ({attachment.size // 1024 + 1} КБ)",
                    data=attachment.path.read_bytes(),
                    file_name=attachment.name,
                    key=f"file-{attachment.id}",
                )
        if feedback:
            st.caption(_feedback_badges(feedback))
        if can_review and message.role == "assistant" and message.author == "assistant":
            _review_controls(chat, message)


def _chat_column(chat: Chat) -> None:
    user = current_user()
    access = get_access()
    settings = get_settings()
    st.subheader(chat.title)
    st.caption(f"Автор: {display_name(chat.owner)} · создан {chat.created_at[:16].replace('T', ' ')} UTC")

    feedback = get_store().feedback_for_chat(chat.id)
    can_review = access.can(user, "feedback.review")
    for message in get_store().messages(chat.id):
        _render_message(chat, message, feedback.get(message.id, []), can_review)

    options = chat_service.available_actions(access, user, settings)
    left, right = st.columns([2, 1])
    action = left.radio("Действие", options, horizontal=True)
    connection = None
    if action == ACTION_DUCT:
        connection = right.selectbox("Тип соединения", list(actions.CONNECTION_TYPES))

    submitted = st.chat_input(
        "Сообщение",
        accept_file="multiple",
        file_type=["md", "txt", "csv", "xlsx", "docx", "doc", "odt", "pdf", "png", "jpg", "jpeg"],
    )
    if submitted:
        files = [(f.name, f.getvalue()) for f in submitted.files]
        with st.spinner("Ассистент работает…") if action != ACTION_NOTE else nullcontext():
            posted = chat_service.post_message(
                get_store(),
                settings,
                user,
                chat,
                text=submitted.text or "",
                action=action,
                connection=connection,
                files=files,
                names={login: u.name for login, u in get_users().items()},
            )
        if posted is not None:
            st.rerun()


def render() -> None:
    st.title("Чаты")
    history, current = st.columns([1, 3], gap="large")
    with history:
        _history_column()
    with current:
        chat_id = st.query_params.get("chat")
        chat = get_store().get_chat(int(chat_id)) if chat_id and chat_id.isdigit() else None
        if chat is None or not _can_open(chat):
            st.info("Выберите чат слева или начните новый.")
            return
        _chat_column(chat)
