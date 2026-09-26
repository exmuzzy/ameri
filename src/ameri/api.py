"""HTTP API сайта: те же Чаты, действия и Исправления, что в Streamlit, для скриптов и агентов.

Запуск: ``uvicorn --app-dir src ameri.api:app --port 8000``. Токен — HMAC-подпись логина и
срока действия секретом из ``<data>/secrets/api_secret``; права проверяет ``Access.can``.
"""

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import actions, chat_service, users_service
from .auth import User, authenticate, load_users
from .harness import Access, load_access
from .settings import Settings, load_settings
from .store import Attachment, Chat, Feedback, Message, Store

TOKEN_TTL = 12 * 3600
LOGIN_WINDOW = 15 * 60
LOGIN_MAX_FAILURES = 5
CONNECTIONS = {value: label for label, value in actions.CONNECTION_TYPES.items()}


# --- Токены ---


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def api_secret(settings: Settings) -> bytes:
    """Секрет подписи токенов; создаётся при первом запуске с правами только для владельца."""

    path = settings.data_dir / "secrets" / "api_secret"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o700)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(secrets.token_hex(32), encoding="utf-8")
        tmp.chmod(0o600)
        tmp.replace(path)
    return path.read_text(encoding="utf-8").strip().encode()


def _password_mark(user: User) -> str:
    # Смена пароля отзывает выданные токены: в токен входит отпечаток хэша пароля.
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


def issue_token(secret: bytes, user: User, now: float | None = None) -> tuple[str, int]:
    expires = int((now if now is not None else time.time()) + TOKEN_TTL)
    payload = _b64(json.dumps({"sub": user.login, "exp": expires, "pw": _password_mark(user)}).encode())
    signature = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}", expires


def read_token(secret: bytes, token: str, users: dict[str, User]) -> User | None:
    try:
        payload, signature = token.split(".")
        expected = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_unb64(payload))
    except (ValueError, TypeError):
        return None
    user = users.get(data.get("sub", ""))
    if user is None or data.get("exp", 0) < time.time() or data.get("pw") != _password_mark(user):
        return None
    return user


class LoginLimiter:
    """Не больше LOGIN_MAX_FAILURES неудачных входов за LOGIN_WINDOW с одного адреса или на один логин."""

    def __init__(self) -> None:
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> deque[float]:
        items = self._failures[key]
        while items and items[0] < now - LOGIN_WINDOW:
            items.popleft()
        return items

    def blocked(self, keys: list[str]) -> bool:
        now = time.time()
        with self._lock:
            return any(len(self._recent(key, now)) >= LOGIN_MAX_FAILURES for key in keys)

    def fail(self, keys: list[str]) -> None:
        now = time.time()
        with self._lock:
            for key in keys:
                self._recent(key, now).append(now)


# --- Схемы ---


class LoginIn(BaseModel):
    login: str
    password: str


class ChatIn(BaseModel):
    title: str


class FeedbackIn(BaseModel):
    rating: int
    comment: str = ""
    corrected_text: str = ""
    rule_text: str = ""
    as_example: bool = False


class UserIn(BaseModel):
    login: str
    name: str = ""
    role: str
    password: str


def _user_out(user: User) -> dict:
    return {"login": user.login, "name": user.name, "role": user.role}


def _chat_out(chat: Chat) -> dict:
    return {
        "id": chat.id,
        "title": chat.title,
        "owner": chat.owner,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "message_count": chat.message_count,
    }


def _attachment_out(attachment: Attachment) -> dict:
    return {"id": attachment.id, "name": attachment.name, "size": attachment.size}


def _feedback_out(item: Feedback) -> dict:
    return {
        "id": item.id,
        "reviewer": item.reviewer,
        "rating": item.rating,
        "comment": item.comment,
        "corrected_text": item.corrected_text,
        "rule_text": item.rule_text,
        "as_example": item.as_example,
        "status": item.status,
        "created_at": item.created_at,
    }


def _message_out(message: Message, feedback: list[Feedback] | None = None) -> dict:
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "author": message.author,
        "role": message.role,
        "action": message.action,
        "content": message.content,
        "created_at": message.created_at,
        "attachments": [_attachment_out(a) for a in message.attachments],
        "feedback": [_feedback_out(f) for f in feedback or []],
    }


# --- Приложение ---


def create_app(settings_factory=load_settings) -> FastAPI:
    app = FastAPI(title="ameri API", version="1", docs_url="/api/docs", openapi_url="/api/openapi.json")
    limiter = LoginLimiter()
    state: dict[str, object] = {}

    def get_settings() -> Settings:
        if "settings" not in state:
            state["settings"] = settings_factory()
        return state["settings"]  # type: ignore[return-value]

    def get_store(settings: Annotated[Settings, Depends(get_settings)]) -> Store:
        if "store" not in state:
            state["store"] = Store(settings.db_path, settings.files_dir)
        return state["store"]  # type: ignore[return-value]

    def get_access(settings: Annotated[Settings, Depends(get_settings)]) -> Access:
        # Харнес читается при каждом запросе, как на сайте после обновления: права меняются без перезапуска.
        return load_access(settings.harness_dir)

    def current_user(
        settings: Annotated[Settings, Depends(get_settings)],
        authorization: Annotated[str, Header()] = "",
    ) -> User:
        scheme, _, token = authorization.partition(" ")
        user = None
        if scheme.lower() == "bearer" and token:
            user = read_token(api_secret(settings), token.strip(), load_users(settings.users_file))
        if user is None:
            raise HTTPException(401, "Нужен действующий токен: POST /api/v1/login", headers={"WWW-Authenticate": "Bearer"})
        return user

    SettingsDep = Annotated[Settings, Depends(get_settings)]
    StoreDep = Annotated[Store, Depends(get_store)]
    AccessDep = Annotated[Access, Depends(get_access)]
    UserDep = Annotated[User, Depends(current_user)]

    def require(access: Access, user: User, grant: str) -> None:
        if not access.can(user, grant):
            raise HTTPException(403, f"Нет права {grant}")

    def require_admin(user: User) -> None:
        if user.role != "admin":
            raise HTTPException(403, "Только для администратора")

    def open_chat(store: Store, access: Access, user: User, chat_id: int) -> Chat:
        chat = store.get_chat(chat_id)
        if chat is None:
            raise HTTPException(404, "Чат не найден")
        if not chat_service.can_open(access, user, chat):
            raise HTTPException(403, "Чужой чат")
        return chat

    def names(settings: Settings) -> dict[str, str]:
        return {login: user.name for login, user in load_users(settings.users_file).items()}

    @app.post("/api/v1/login")
    def login(body: LoginIn, request: Request, settings: SettingsDep) -> dict:
        address = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
        keys = ["ip:" + address.split(",")[0].strip(), "login:" + body.login.strip().lower()]
        if limiter.blocked(keys):
            raise HTTPException(429, "Слишком много неудачных попыток входа, подождите 15 минут")
        user = authenticate(load_users(settings.users_file), body.login, body.password)
        if user is None:
            limiter.fail(keys)
            raise HTTPException(401, "Неверный логин или пароль")
        token, expires = issue_token(api_secret(settings), user)
        return {"token": token, "expires_at": datetime.fromtimestamp(expires, timezone.utc).isoformat()}

    @app.get("/api/v1/me")
    def me(user: UserDep, access: AccessDep, settings: SettingsDep) -> dict:
        actions_keys = {label: key for key, label in chat_service.ACTION_KEYS.items()}
        return {
            **_user_out(user),
            "grants": sorted(access.grants.get(user.role, ())),
            "actions": [actions_keys[a] for a in chat_service.available_actions(access, user, settings)],
        }

    @app.get("/api/v1/chats")
    def list_chats(user: UserDep, store: StoreDep, access: AccessDep, query: str = "", author: str | None = None) -> list[dict]:
        return [_chat_out(c) for c in chat_service.visible_chats(store, access, user, query, author or None)]

    @app.post("/api/v1/chats", status_code=201)
    def create_chat(body: ChatIn, user: UserDep, store: StoreDep, access: AccessDep) -> dict:
        require(access, user, "chat.create")
        return _chat_out(store.get_chat(store.create_chat(body.title, user.login)))

    @app.get("/api/v1/chats/{chat_id}/messages")
    def chat_messages(chat_id: int, user: UserDep, store: StoreDep, access: AccessDep) -> dict:
        chat = open_chat(store, access, user, chat_id)
        feedback = store.feedback_for_chat(chat.id)
        return {
            "chat": _chat_out(chat),
            "messages": [_message_out(m, feedback.get(m.id)) for m in store.messages(chat.id)],
        }

    @app.post("/api/v1/chats/{chat_id}/messages", status_code=201)
    def post_message(
        chat_id: int,
        user: UserDep,
        store: StoreDep,
        access: AccessDep,
        settings: SettingsDep,
        text: Annotated[str, Form()] = "",
        action: Annotated[str, Form()] = "note",
        connection: Annotated[str, Form()] = "none",
        files: Annotated[list[UploadFile], File()] = [],  # noqa: B006 - FastAPI копирует значение по умолчанию
    ) -> dict:
        chat = open_chat(store, access, user, chat_id)
        if action not in chat_service.ACTION_KEYS:
            raise HTTPException(422, f"action — одно из: {', '.join(chat_service.ACTION_KEYS)}")
        if connection not in CONNECTIONS:
            raise HTTPException(422, f"connection — одно из: {', '.join(CONNECTIONS)}")
        label = chat_service.ACTION_KEYS[action]
        if label not in chat_service.available_actions(access, user, settings):
            raise HTTPException(403, f"Действие {action} недоступно")
        uploads = [(f.filename or "file", f.file.read()) for f in files]
        posted = chat_service.post_message(
            store,
            settings,
            user,
            chat,
            text=text,
            action=label,
            connection=CONNECTIONS[connection] if label == chat_service.ACTION_DUCT else None,
            files=uploads,
            names=names(settings),
        )
        if posted is None:
            raise HTTPException(422, "Пустое сообщение: нужен текст или файл")
        return {
            "user_message": _message_out(posted.user_message),
            "assistant_message": _message_out(posted.assistant_message) if posted.assistant_message else None,
        }

    @app.get("/api/v1/files/{attachment_id}")
    def download(attachment_id: int, user: UserDep, store: StoreDep, access: AccessDep) -> FileResponse:
        found = store.get_attachment(attachment_id)
        if found is None:
            raise HTTPException(404, "Файл не найден")
        chat_id, attachment = found
        open_chat(store, access, user, chat_id)
        if not attachment.path.is_file():
            raise HTTPException(404, "Файл не найден на диске")
        return FileResponse(attachment.path, filename=attachment.name)

    @app.post("/api/v1/messages/{message_id}/feedback", status_code=201)
    def feedback(message_id: int, body: FeedbackIn, user: UserDep, store: StoreDep, access: AccessDep) -> dict:
        require(access, user, "feedback.review")
        message = store.get_message(message_id)
        if message is None:
            raise HTTPException(404, "Сообщение не найдено")
        chat = open_chat(store, access, user, message.chat_id)
        if message.role != "assistant" or message.author != "assistant":
            raise HTTPException(422, "Оценивать можно только ответы ассистента")
        if body.rating not in (-1, 1):
            raise HTTPException(422, "rating — 1 или -1")
        feedback_id, correction = chat_service.review_message(
            store,
            chat,
            message,
            user,
            rating=body.rating,
            comment=body.comment,
            corrected_text=body.corrected_text,
            rule_text=body.rule_text,
            as_example=body.as_example,
        )
        item = next(f for f in store.feedback_for_chat(chat.id)[message.id] if f.id == feedback_id)
        return {"feedback": _feedback_out(item), "correction": _message_out(correction) if correction else None}

    @app.get("/api/v1/users")
    def list_users(user: UserDep, settings: SettingsDep) -> list[dict]:
        require_admin(user)
        return [_user_out(u) for u in load_users(settings.users_file).values()]

    @app.post("/api/v1/users", status_code=201)
    def save_user(body: UserIn, user: UserDep, settings: SettingsDep) -> dict:
        require_admin(user)
        try:
            saved = users_service.save_user(settings.users_file, body.login, body.name, body.role, body.password)
        except users_service.UserError as error:
            raise HTTPException(422, str(error)) from None
        return _user_out(saved)

    @app.delete("/api/v1/users/{login}", status_code=204)
    def delete_user(login: str, user: UserDep, settings: SettingsDep) -> None:
        require_admin(user)
        try:
            users_service.delete_user(settings.users_file, login, user)
        except users_service.UserError as error:
            raise HTTPException(422, str(error)) from None
        except KeyError:
            raise HTTPException(404, "Пользователь не найден") from None

    return app


app = create_app()
