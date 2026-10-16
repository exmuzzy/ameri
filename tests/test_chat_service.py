from dataclasses import replace
from pathlib import Path

from ameri import actions, chat_service
from ameri.settings import load_settings
from ameri.store import Store

HARNESS = Path(__file__).resolve().parents[1] / "harness"


def _settings(tmp_path):
    return replace(
        load_settings(),
        data_dir=tmp_path / "data",
        users_file=tmp_path / "data" / "users.toml",
        harness_dir=HARNESS,
        duct_calc_dir=tmp_path / "proto",
        deepseek_api_key="sk-test",
    )


def test_duct_action_uses_text_when_file_missing(tmp_path, monkeypatch):
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    message = store.add_message(
        chat_id,
        author="anna",
        role="user",
        content="Обратный клапан ПП ф315 L300 раструб/раструб — 1 шт",
        action=chat_service.ACTION_DUCT,
    )
    chat = store.list_chats(owner="anna")[0]
    captured: dict[str, str] = {}

    def fake_duct_calc_text(**kwargs):
        captured["text"] = kwargs["text"]
        captured["connection"] = kwargs["connection_label"]
        return actions.ActionResult("ok")

    monkeypatch.setattr(actions, "duct_calc_text", fake_duct_calc_text)

    answer = chat_service.run_action(store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, "Раструб", {})
    assert answer.content == "ok"
    assert captured == {
        "text": "Обратный клапан ПП ф315 L300 раструб/раструб — 1 шт",
        "connection": "Раструб",
    }


def test_duct_action_explains_how_to_send_spec_without_file_or_text(tmp_path):
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    message = store.add_message(chat_id, author="anna", role="user", content="(файлы)", action=chat_service.ACTION_DUCT)
    chat = store.list_chats(owner="anna")[0]

    answer = chat_service.run_action(store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, "Фланец", {})
    assert "Для расчётки приложите файл спецификации" in answer.content
    assert "или напишите список позиций" in answer.content
