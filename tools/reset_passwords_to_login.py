"""Сбросить пароли всех пользователей на их логин.

    python tools/reset_passwords_to_login.py [путь к users.toml] [--yes]

Без пути берётся AMERI_USERS_FILE или var/users.toml (см. settings.py).
ВНИМАНИЕ: после сброса пароль совпадает с логином — это временная мера
(например, до первой смены пароля новыми сотрудниками), не постоянный режим.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ameri.auth import User, hash_password, load_users, save_users  # noqa: E402

DEFAULT_PATH = Path(os.environ.get("AMERI_USERS_FILE", Path("var") / "users.toml"))


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--yes"]
    confirmed = "--yes" in argv
    path = Path(args[0]) if args else DEFAULT_PATH

    users = load_users(path)
    if not users:
        print(f"Пользователи не найдены: {path}")
        return 1

    print(f"Файл: {path}")
    for login in sorted(users):
        print(f"  {login} -> пароль станет {login!r}")

    if not confirmed:
        answer = input("Сбросить пароли всех пользователей выше на их логин? [yes/N] ")
        if answer.strip().lower() != "yes":
            print("Отменено.")
            return 1

    updated = {
        login: User(
            login=user.login,
            name=user.name,
            role=user.role,
            password_hash=hash_password(login),
        )
        for login, user in users.items()
    }
    save_users(path, updated)
    print(f"Готово: {len(updated)} пользователь(ей) обновлено в {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
