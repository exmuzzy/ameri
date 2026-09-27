import json
import os
import time
from datetime import datetime, timedelta, timezone

from ameri import updates
from ameri.settings import load_settings


def settings_for(tmp_path, monkeypatch):
    monkeypatch.setenv("AMERI_DATA_DIR", str(tmp_path))
    return load_settings()


def write_status(settings, state, age_seconds=0):
    stamp = (datetime.now(timezone.utc) - timedelta(seconds=age_seconds)).isoformat(timespec="seconds")
    (settings.data_dir / "update-status.json").write_text(
        json.dumps({"state": state, "finished_at": stamp}), encoding="utf-8"
    )


def test_in_progress_states(tmp_path, monkeypatch):
    settings = settings_for(tmp_path, monkeypatch)
    assert not updates.update_in_progress(settings)

    request = settings.data_dir / "update-request"
    request.write_text("Админ", encoding="utf-8")
    assert updates.update_in_progress(settings)            # заявка ждёт службу
    old = time.time() - updates.STALE_REQUEST_SECONDS - 5
    os.utime(request, (old, old))
    assert not updates.update_in_progress(settings)        # служба не запущена — кнопку не блокируем
    request.unlink()

    write_status(settings, "running")
    assert updates.update_in_progress(settings)            # идёт пересборка
    write_status(settings, "running", age_seconds=updates.RUNNING_MAX_SECONDS + 5)
    assert not updates.update_in_progress(settings)        # служба упала посреди пересборки
    write_status(settings, "done")
    assert not updates.update_in_progress(settings)
    write_status(settings, "error")
    assert not updates.update_in_progress(settings)


def test_button_is_disabled_while_busy():
    import inspect

    from views import updates as view

    source = inspect.getsource(view)
    assert "disabled=busy" in source and "on_click=_start_update" in source
    assert "update_in_progress(settings)" in inspect.getsource(view._start_update)
