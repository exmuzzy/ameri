"""Харнес: роли и Гранты, промпт Ассистента, Правила и Примеры в git."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .auth import User

PROMPT_FILE = Path("prompts") / "assistant.md"
RULES_DIR = "rules"
EXAMPLES_DIR = "examples"


@dataclass(frozen=True)
class Access:
    grants: dict[str, frozenset[str]]

    def can(self, user: User, grant: str) -> bool:
        return grant in self.grants.get(user.role, frozenset())


def load_access(harness_dir: Path) -> Access:
    data = yaml.safe_load((harness_dir / "access.yaml").read_text(encoding="utf-8")) or {}
    roles = data.get("roles", {})
    return Access(
        grants={role: frozenset(item.get("grants", [])) for role, item in roles.items()}
    )


@dataclass(frozen=True)
class HarnessFile:
    path: Path
    title: str
    text: str


def _read_dir(harness_dir: Path, name: str) -> list[HarnessFile]:
    folder = harness_dir / name
    if not folder.is_dir():
        return []
    files = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        first = text.splitlines()[0] if text else path.stem
        files.append(HarnessFile(path, first.lstrip("# ").strip(), text))
    return files


def list_rules(harness_dir: Path) -> list[HarnessFile]:
    return _read_dir(harness_dir, RULES_DIR)


def list_examples(harness_dir: Path) -> list[HarnessFile]:
    return _read_dir(harness_dir, EXAMPLES_DIR)


def assistant_prompt(harness_dir: Path) -> str:
    """Системный промпт: основной текст, затем Правила, затем Примеры.

    Порядок стабилен и не зависит от Чата: DeepSeek кэширует одинаковый префикс
    запросов, поэтому неизменная часть Харнеса дешевле при каждом следующем вызове.
    """

    parts = [(harness_dir / PROMPT_FILE).read_text(encoding="utf-8").strip()]
    rules = list_rules(harness_dir)
    if rules:
        parts.append("## Правила, утверждённые руководителем\n\n" + "\n\n".join(r.text for r in rules))
    examples = list_examples(harness_dir)
    if examples:
        parts.append("## Примеры правильных ответов\n\n" + "\n\n".join(e.text for e in examples))
    return "\n\n".join(part for part in parts if part)


def slugify(text: str, fallback: str = "rule") -> str:
    translit = str.maketrans(
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
        "abvgdeejziiklmnoprstufhccss_y_eua",
    )
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().translate(translit)).strip("-")
    return (slug[:48].strip("-") or fallback)


class HarnessRepo:
    """Запись Харнеса в файлы и коммит в git от имени Руководителя."""

    def __init__(self, harness_dir: Path) -> None:
        self.harness_dir = harness_dir

    def _unique(self, folder: str, title: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        target = self.harness_dir / folder / f"{stamp}-{slugify(title)}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def add_rule(self, title: str, text: str, *, author: str, source: str) -> Path:
        path = self._unique(RULES_DIR, title)
        path.write_text(f"### {title.strip()}\n\n{text.strip()}\n\n_Источник: {source}; утвердил: {author}_\n", encoding="utf-8")
        return path

    def add_example(self, question: str, answer: str, *, author: str) -> Path:
        path = self._unique(EXAMPLES_DIR, question[:60] or "example")
        path.write_text(
            f"### Вопрос\n\n{question.strip()}\n\n### Правильный ответ\n\n{answer.strip()}\n\n_Утвердил: {author}_\n",
            encoding="utf-8",
        )
        return path

    def save_prompt(self, text: str) -> Path:
        path = self.harness_dir / PROMPT_FILE
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return path

    def remove(self, path: Path) -> None:
        path.resolve().relative_to(self.harness_dir.resolve())  # только файлы Харнеса
        path.unlink()

    # --- git ---

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.harness_dir), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )

    def is_git(self) -> bool:
        return self._git("rev-parse", "--is-inside-work-tree").returncode == 0

    def version(self) -> str | None:
        result = self._git("log", "-1", "--format=%h", "--", ".")
        return result.stdout.strip() or None if result.returncode == 0 else None

    def history(self, limit: int = 15) -> list[str]:
        result = self._git("log", f"-{limit}", "--format=%h · %ad · %an · %s", "--date=short", "--", ".")
        return result.stdout.splitlines() if result.returncode == 0 else []

    def pull(self) -> str:
        """Подтянуть изменения Харнеса, сделанные в репозитории (например, из ZCode или Cursor)."""

        if not self.is_git():
            return "Каталог Харнеса не в git."
        result = self._git("pull", "--rebase", "origin")
        if result.returncode != 0:
            return f"Не удалось обновить: {(result.stderr or result.stdout).strip()[:300]}"
        return "Харнес обновлён из репозитория: " + (self.version() or "")

    def commit(self, message: str, *, author: User) -> tuple[str | None, str]:
        """Закоммитить все изменения Харнеса. Возвращает (sha, сообщение для интерфейса)."""

        if not self.is_git():
            return None, "Изменение сохранено в файлах, но каталог Харнеса не в git: коммит не создан."
        self._git("add", "-A", ".")
        env_author = f"{author.name} <{author.login}@ameri>"
        result = subprocess.run(
            [
                "git", "-C", str(self.harness_dir),
                "-c", f"user.name={author.name}", "-c", f"user.email={author.login}@ameri",
                "commit", "-m", message, "--author", env_author, "--", ".",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return None, "Нечего коммитить." if "nothing" in result.stdout + result.stderr else result.stderr.strip()
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        if os.environ.get("AMERI_GIT_PUSH") == "1":
            self._git("pull", "--rebase", "origin")
            push = self._git("push", "origin", "HEAD")
            if push.returncode != 0:
                return sha, f"Коммит {sha} создан, но push не удался: {push.stderr.strip()[:200]}"
            return sha, f"Коммит {sha} отправлен в репозиторий."
        return sha, f"Коммит {sha} создан локально (push выключен)."
