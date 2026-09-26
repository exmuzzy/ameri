"""Отправка сообщения в Чат и Исправление ответа: общее для сайта (Streamlit) и HTTP API."""

from __future__ import annotations

from dataclasses import dataclass

from . import actions
from .auth import User
from .harness import Access, HarnessRepo, assistant_prompt
from .llm import DeepSeekChat, LlmError
from .settings import Settings
from .store import Chat, Message, Store

ACTION_ASK = "Вопрос ассистенту"
ACTION_DUCT = "Расчётка воздуховодов"
ACTION_NOTE = "Без ассистента"
ACTION_CORRECTION = "Исправление руководителя"

# Короткие имена действий для API и их Гранты (у «Без ассистента» Гранта нет).
ACTION_KEYS = {"ask": ACTION_ASK, "duct_calc": ACTION_DUCT, "note": ACTION_NOTE}
ACTION_GRANTS = {ACTION_ASK: "action.ask", ACTION_DUCT: "action.duct_calc"}


@dataclass(frozen=True)
class PostResult:
    user_message: Message
    assistant_message: Message | None


def can_open(access: Access, user: User, chat: Chat) -> bool:
    return chat.owner == user.login or access.can(user, "chat.view_all")


def can_delete(user: User, chat: Chat) -> bool:
    """Удалить Чат может его автор или Администратор."""

    return chat.owner == user.login or user.role == "admin"


def visible_chats(store: Store, access: Access, user: User, query: str = "", author: str | None = None) -> list[Chat]:
    if access.can(user, "chat.view_all"):
        return store.list_chats(owner=author, query=query)
    return store.list_chats(owner=user.login, query=query)


def available_actions(access: Access, user: User, settings: Settings) -> list[str]:
    """Действия, которые пользователь может выбрать в Чате, в порядке кнопок на сайте."""

    options = []
    if access.can(user, ACTION_GRANTS[ACTION_ASK]):
        options.append(ACTION_ASK)
    if access.can(user, ACTION_GRANTS[ACTION_DUCT]) and actions.duct_calc_available(settings.duct_calc_dir):
        options.append(ACTION_DUCT)
    options.append(ACTION_NOTE)
    return options


def run_action(
    store: Store,
    settings: Settings,
    chat: Chat,
    message: Message,
    action: str,
    connection: str | None,
    names: dict[str, str],
) -> Message:
    """Выполнить действие по сообщению пользователя и записать ответ Ассистента в Чат."""

    try:
        if action == ACTION_DUCT:
            specs = [a for a in message.attachments if a.path.suffix.lower() in actions.DUCT_SUFFIXES]
            if not specs:
                result = actions.ActionResult(
                    "Для расчётки приложите файл спецификации: .md, .xlsx, .docx, .doc, .odt или .csv."
                )
            else:
                result = actions.duct_calc(
                    spec=specs[0],
                    connection_label=connection or "Без соединения",
                    duct_calc_dir=settings.duct_calc_dir,
                    base_url=settings.deepseek_base_url,
                    api_key=settings.api_key(),
                    model=settings.deepseek_model,
                    harness_dir=settings.harness_dir,
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
                names,
            )
    except LlmError as error:
        result = actions.ActionResult(f"Не получилось обратиться к модели: {error}")
    except Exception as error:  # noqa: BLE001 - ошибка показывается в чате и не роняет страницу
        result = actions.ActionResult(f"Действие завершилось ошибкой: {error.__class__.__name__}: {error}")
    return store.add_message(
        chat.id,
        author="assistant",
        role="assistant",
        content=result.text,
        action=action,
        files=result.files,
        usage=result.usage,
        harness_version=HarnessRepo(settings.harness_dir).version(),
    )


def post_message(
    store: Store,
    settings: Settings,
    user: User,
    chat: Chat,
    *,
    text: str,
    action: str,
    connection: str | None,
    files: list[tuple[str, bytes]],
    names: dict[str, str],
) -> PostResult | None:
    """То, что делает кнопка отправки в Чате: сообщение пользователя, затем действие Ассистента.

    Возвращает None, если нечего отправлять (нет ни текста, ни файлов).
    """

    text = text.strip()
    if not text and not files:
        return None
    message = store.add_message(
        chat.id,
        author=user.login,
        role="user",
        content=text or "(файлы)",
        action=None if action == ACTION_NOTE else action,
        files=files,
    )
    answer = None
    if action != ACTION_NOTE:
        answer = run_action(store, settings, chat, message, action, connection, names)
    return PostResult(message, answer)


def review_message(
    store: Store,
    chat: Chat,
    message: Message,
    reviewer: User,
    *,
    rating: int,
    comment: str = "",
    corrected_text: str = "",
    rule_text: str = "",
    as_example: bool = False,
) -> tuple[int, Message | None]:
    """Оценка ответа Ассистента; с исправленным текстом — ещё и «Исправление руководителя» в Чат.

    Правило и Пример только предлагаются (status = proposed): в Харнес их вносит
    Руководитель кнопкой на странице «Харнес».
    """

    feedback_id = store.add_feedback(
        message.id,
        reviewer=reviewer.login,
        rating=rating,
        comment=comment,
        corrected_text=corrected_text,
        rule_text=rule_text,
        as_example=as_example,
    )
    correction = None
    if corrected_text.strip():
        correction = store.add_message(
            chat.id, author=reviewer.login, role="assistant", content=corrected_text, action=ACTION_CORRECTION
        )
    return feedback_id, correction
