"""Управление пользователями (форма «Пользователи» на странице «Настройки» и HTTP API)."""

from __future__ import annotations

import re
from pathlib import Path

from .auth import ROLES, User, hash_password, load_users, save_users

LOGIN_PATTERN = re.compile(r"[a-z0-9._-]{2,32}")
MIN_PASSWORD = 8


class UserError(ValueError):
    """Ошибка проверки: текст показывается пользователю как есть."""


def save_user(users_file: Path, login: str, name: str, role: str, password: str) -> User:
    """Добавить пользователя или сменить пароль, имя и роль существующего."""

    login = login.strip().lower()
    if not LOGIN_PATTERN.fullmatch(login):
        raise UserError("Логин: 2–32 символа, латиница, цифры, точка, дефис, подчёркивание.")
    if len(password) < MIN_PASSWORD:
        raise UserError(f"Пароль не короче {MIN_PASSWORD} символов.")
    if role not in ROLES:
        raise UserError(f"Роль — одна из: {', '.join(ROLES)}.")
    users = load_users(users_file)
    users[login] = User(login, name.strip() or login, role, hash_password(password))
    save_users(users_file, users)
    return users[login]


def delete_user(users_file: Path, login: str, actor: User) -> None:
    if login == actor.login:
        raise UserError("Нельзя удалить самого себя.")
    users = load_users(users_file)
    if login not in users:
        raise KeyError(login)
    users.pop(login)
    save_users(users_file, users)
