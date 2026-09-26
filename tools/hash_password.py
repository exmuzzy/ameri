"""Хэш пароля для users.toml: python tools/hash_password.py"""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ameri.auth import hash_password  # noqa: E402

print(hash_password(getpass.getpass("Пароль: ")))
