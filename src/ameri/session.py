"""«Запомнить вход» на сайте: подписанная cookie на 30 дней.

Токен устроен как токены API (HMAC, отпечаток хэша пароля — смена пароля отзывает вход),
но подписывается отдельным секретом и имеет отдельное назначение, поэтому cookie сайта
нельзя использовать как токен API и наоборот.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path

from .auth import User

COOKIE_NAME = "ameri_session"
SESSION_TTL = 30 * 24 * 3600


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def session_secret(data_dir: Path) -> bytes:
    path = data_dir / "secrets" / "session_secret"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o700)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(secrets.token_hex(32), encoding="utf-8")
        tmp.chmod(0o600)
        tmp.replace(path)
    return path.read_text(encoding="utf-8").strip().encode()


def _password_mark(user: User) -> str:
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


def issue(secret: bytes, user: User, now: float | None = None) -> str:
    expires = int((now if now is not None else time.time()) + SESSION_TTL)
    payload = _b64(
        json.dumps({"aud": "site", "sub": user.login, "exp": expires, "pw": _password_mark(user)}).encode()
    )
    signature = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def read(secret: bytes, token: str | None, users: dict[str, User]) -> User | None:
    if not token:
        return None
    try:
        payload, signature = token.split(".")
        expected = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_unb64(payload))
    except (ValueError, TypeError):
        return None
    user = users.get(data.get("sub", ""))
    if (
        user is None
        or data.get("aud") != "site"
        or data.get("exp", 0) < time.time()
        or data.get("pw") != _password_mark(user)
    ):
        return None
    return user


def cookie_script(token: str | None) -> str:
    """JS для скрытого компонента: поставить cookie (token) или стереть её (None)."""

    if token is None:
        value = f"{COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax"
    else:
        value = f"{COOKIE_NAME}={token}; Max-Age={SESSION_TTL}; Path=/; SameSite=Lax"
    secure = "; Secure" if token is not None else ""
    return (
        "<script>(function(){var d=window.parent.document;"
        f"var s=(d.location.protocol==='https:')?'{secure}':'';"
        f"d.cookie={json.dumps(value)}+s;}})();</script>"
    )
