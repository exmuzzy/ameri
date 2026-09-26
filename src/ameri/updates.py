"""Обновление сайта из GitHub: заявка для службы на сервере и её статус (кнопка на сайте и API)."""

from __future__ import annotations

import json
import time

from .harness import HarnessRepo
from .settings import Settings

STALE_REQUEST_SECONDS = 120


def update_status(settings: Settings) -> dict:
    """Итог последнего обновления из data/update-status.json (пишет deploy/autoupdate.sh)."""

    path = settings.data_dir / "update-status.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def request_stale(settings: Settings) -> bool:
    """Заявка висит дольше двух минут — служба обновления на сервере не запущена."""

    request = settings.data_dir / "update-request"
    return request.exists() and time.time() - request.stat().st_mtime > STALE_REQUEST_SECONDS


def request_update(settings: Settings, requested_by: str) -> str:
    """Подтянуть харнес и статьи сразу и оставить заявку на обновление кода службе ameri-update."""

    pulled = HarnessRepo(settings.harness_dir).pull()
    (settings.data_dir / "update-request").write_text(requested_by, encoding="utf-8")
    return pulled
