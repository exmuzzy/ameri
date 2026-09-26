"""Страница «Чаты»: история, новый Чат, переписка с Ассистентом."""

from __future__ import annotations

import streamlit as st

from ameri import actions
from ameri.harness import assistant_prompt
from ameri.llm import DeepSeekChat, LlmError
from ameri.store import Chat, Message

from views.common import current_user, display_name, get_access, get_settings, get_store, get_users

ACTION_ASK = "Вопрос ассистенту"
ACTION_DUCT = "Расчётка воздуховодов"
ACTION_NOTE = "Без ассистента"


def _visible_chats(query: str, author: str | None) -> list[Chat]:
    user = current_user()
    store = get_store()
    if get_access().can(user, "chat.view_all"):
        return store.list_chats(owner=author, query=query)
    return store.list_chats(owner=user.login, query=query)


def _can_open(chat: Chat) -> bool:
    user = current_user()
    return chat.owner == user.login or get_access().can(user, "chat.view_all")


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


def _render_message(message: Message) -> None:
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


def _run_action(chat: Chat, message: Message, action: str, connection: str | None) -> None:
    settings = get_settings()
    store = get_store()
    try:
        if action == ACTION_DUCT:
            specs = [a for a in message.attachments if a.path.suffix.lower() in actions.DUCT_SUFFIXES]
            if not specs:
                result = actions.ActionResult(
                    "Для расчётки приложите файл спецификации: .md, .xlsx, .docx, .doc или .csv."
                )
            else:
                result = actions.duct_calc(
                    spec=specs[0],
                    connection_label=connection or "Без соединения",
                    duct_calc_dir=settings.duct_calc_dir,
                    base_url=settings.deepseek_base_url,
                    api_key=settings.api_key(),
                    model=settings.deepseek_model,
                )
        else:
            llm = DeepSeekChat(
                base_url=settings.deepseek_base_url,
                api_key=settings.api_key(),
                model=settings.deepseek_model,
            )
            result = actions.ask_assistant(
                llm,
                assistant_prompt(settings.harness_dir),
                store.messages(chat.id),
                settings.duct_calc_dir,
                {login: user.name for login, user in get_users().items()},
            )
    except LlmError as error:
        result = actions.ActionResult(f"Не получилось обратиться к модели: {error}")
    except Exception as error:  # noqa: BLE001 - ошибка показывается в чате и не роняет страницу
        result = actions.ActionResult(f"Действие завершилось ошибкой: {error.__class__.__name__}: {error}")
    store.add_message(
        chat.id, author="assistant", role="assistant", content=result.text, action=action, files=result.files
    )


def _chat_column(chat: Chat) -> None:
    user = current_user()
    access = get_access()
    settings = get_settings()
    st.subheader(chat.title)
    st.caption(f"Автор: {display_name(chat.owner)} · создан {chat.created_at[:16].replace('T', ' ')} UTC")

    for message in get_store().messages(chat.id):
        _render_message(message)

    options = []
    if access.can(user, "action.ask"):
        options.append(ACTION_ASK)
    if access.can(user, "action.duct_calc") and actions.duct_calc_available(settings.duct_calc_dir):
        options.append(ACTION_DUCT)
    options.append(ACTION_NOTE)
    left, right = st.columns([2, 1])
    action = left.radio("Действие", options, horizontal=True)
    connection = None
    if action == ACTION_DUCT:
        connection = right.selectbox("Тип соединения", list(actions.CONNECTION_TYPES))

    submitted = st.chat_input(
        "Сообщение",
        accept_file="multiple",
        file_type=["md", "txt", "csv", "xlsx", "docx", "doc", "pdf", "png", "jpg", "jpeg"],
    )
    if submitted:
        text = (submitted.text or "").strip()
        files = [(f.name, f.getvalue()) for f in submitted.files]
        if not text and not files:
            return
        message = get_store().add_message(
            chat.id,
            author=user.login,
            role="user",
            content=text or "(файлы)",
            action=None if action == ACTION_NOTE else action,
            files=files,
        )
        if action != ACTION_NOTE:
            with st.spinner("Ассистент работает…"):
                _run_action(chat, message, action, connection)
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
