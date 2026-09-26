"""Чтение Харнеса: роли и Гранты, промпт Ассистента."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .auth import User


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


def assistant_prompt(harness_dir: Path) -> str:
    """Системный промпт Ассистента: основной текст и все утверждённые Правила."""

    parts = [(harness_dir / "prompts" / "assistant.md").read_text(encoding="utf-8").strip()]
    rules_dir = harness_dir / "rules"
    if rules_dir.is_dir():
        for path in sorted(rules_dir.glob("*.md")):
            parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(part for part in parts if part)
