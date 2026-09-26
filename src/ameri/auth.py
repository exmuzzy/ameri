"""Учётные записи и проверка паролей (scrypt из стандартной библиотеки)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROLES = ("admin", "leader", "manager")
_N, _R, _P = 2**14, 8, 1


@dataclass(frozen=True)
class User:
    login: str
    name: str
    role: str
    password_hash: str


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return "scrypt${}${}${}${}${}".format(
        _N, _R, _P, base64.b64encode(salt).decode(), base64.b64encode(digest).decode()
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = password_hash.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest)
        actual = hashlib.scrypt(
            password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def load_users(path: Path) -> dict[str, User]:
    """Прочитать users.toml: [users.<login>] name, role, password_hash."""

    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    users: dict[str, User] = {}
    for login, item in data.get("users", {}).items():
        role = item.get("role", "manager")
        if role not in ROLES:
            raise ValueError(f"Неизвестная роль {role!r} у пользователя {login!r}")
        users[login] = User(
            login=login,
            name=item.get("name", login),
            role=role,
            password_hash=item["password_hash"],
        )
    return users


def authenticate(users: dict[str, User], login: str, password: str) -> User | None:
    user = users.get(login.strip())
    if user is None:
        # Тратим то же время, что и на проверку, чтобы не раскрывать существующие логины.
        verify_password(password, hash_password("x"))
        return None
    return user if verify_password(password, user.password_hash) else None


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # строка JSON — корректная базовая строка TOML


def save_users(path: Path, users: dict[str, User]) -> None:
    """Записать users.toml атомарно, с правами только для владельца."""

    lines: list[str] = []
    for login in sorted(users):
        user = users[login]
        lines += [
            f"[users.{_toml_string(login)}]",
            f"name = {_toml_string(user.name)}",
            f"role = {_toml_string(user.role)}",
            f"password_hash = {_toml_string(user.password_hash)}",
            "",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)
