"""Обновление сайта из GitHub: заявка для службы на сервере и её статус (кнопка на сайте и API)."""

from __future__ import annotations

import json
import time
from datetime import datetime

from .harness import HarnessRepo
from .settings import Settings

STALE_REQUEST_SECONDS = 120
# Если служба упала посреди пересборки, статус «running» перестаёт блокировать кнопку через 30 минут.
RUNNING_MAX_SECONDS = 30 * 60


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


def update_in_progress(settings: Settings) -> bool:
    """Обновление идёт: заявка ждёт службу (и служба жива) или служба пишет статус «running»."""

    request = settings.data_dir / "update-request"
    if request.exists() and not request_stale(settings):
        return True
    status = update_status(settings)
    if status.get("state") != "running":
        return False
    try:
        started = datetime.fromisoformat(status.get("finished_at", "")).timestamp()
    except ValueError:
        return False
    return time.time() - started < RUNNING_MAX_SECONDS


def request_update(settings: Settings, requested_by: str) -> str:
    """Подтянуть харнес и статьи сразу и оставить заявку на обновление кода службе ameri-update."""

    pulled = HarnessRepo(settings.harness_dir).pull()
    (settings.data_dir / "update-request").write_text(requested_by, encoding="utf-8")
    return pulled
