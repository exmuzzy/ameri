"""Настройки сайта из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_secret(env_name: str) -> str:
    """Значение из переменной или из файла, указанного в <ИМЯ>_FILE (docker secrets)."""

    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    file_path = os.environ.get(f"{env_name}_FILE", "").strip()
    if file_path and Path(file_path).is_file():
        return Path(file_path).read_text(encoding="utf-8").strip()
    return ""


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    users_file: Path
    harness_dir: Path
    site_dir: Path
    duct_calc_dir: Path | None
    deepseek_base_url: str
    deepseek_model: str
    deepseek_api_key: str

    @property
    def db_path(self) -> Path:
        return self.data_dir / "ameri.sqlite3"

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "files"

    @property
    def key_file(self) -> Path:
        """Ключ DeepSeek, заданный Администратором на странице «Настройки»."""
        return self.data_dir / "secrets" / "deepseek_api_key"

    def api_key(self) -> str:
        """Ключ из окружения или из файла на сервере; читается при каждом вызове."""
        if self.deepseek_api_key:
            return self.deepseek_api_key
        if self.key_file.is_file():
            return self.key_file.read_text(encoding="utf-8").strip()
        return ""

    def save_api_key(self, key: str) -> None:
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self.key_file.parent.chmod(0o700)
        tmp = self.key_file.with_suffix(".tmp")
        tmp.write_text(key.strip(), encoding="utf-8")
        tmp.chmod(0o600)
        tmp.replace(self.key_file)


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("AMERI_DATA_DIR", REPO_ROOT / "var"))
    duct_calc_dir = os.environ.get("AMERI_DUCT_CALC_DIR", "").strip()
    return Settings(
        data_dir=data_dir,
        users_file=Path(os.environ.get("AMERI_USERS_FILE", data_dir / "users.toml")),
        harness_dir=Path(os.environ.get("AMERI_HARNESS_DIR", REPO_ROOT / "harness")),
        site_dir=Path(os.environ.get("AMERI_SITE_DIR", REPO_ROOT / "docs" / "site")),
        duct_calc_dir=Path(duct_calc_dir) if duct_calc_dir else None,
        deepseek_base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
        deepseek_api_key=_read_secret("DEEPSEEK_API_KEY"),
    )
