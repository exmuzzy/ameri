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


def test_ask_action_says_no_connection_without_prefix(tmp_path, monkeypatch):
    from ameri.llm import NO_CONNECTION_MESSAGE, LlmError, NoConnectionError

    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    message = store.add_message(chat_id, author="anna", role="user", content="Какая толщина?", action=chat_service.ACTION_ASK)
    chat = store.list_chats(owner="anna")[0]

    def lost(*args, **kwargs):
        raise NoConnectionError()

    monkeypatch.setattr(actions, "ask_assistant", lost)
    answer = chat_service.run_action(store, _settings(tmp_path), chat, message, chat_service.ACTION_ASK, None, {})
    assert answer.content == NO_CONNECTION_MESSAGE

    def refused(*args, **kwargs):
        raise LlmError("DeepSeek ответил ошибкой 401")

    monkeypatch.setattr(actions, "ask_assistant", refused)
    answer = chat_service.run_action(store, _settings(tmp_path), chat, message, chat_service.ACTION_ASK, None, {})
    assert answer.content == "Не получилось обратиться к модели: DeepSeek ответил ошибкой 401"


def _drawing_bytes() -> bytes:
    import io

    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([None, None, "Позиция", "Наименование и техническая характеристика", "Тип, марка", "Единица измерения", "Количество"])
    sheet.append([None, None, None, "Система В5", None, None, None])
    sheet.append([None, None, None, "4. Переход пластиковый,", "ХИМВЕНТ-ПП-БС-125-110-", "шт.", 2])
    sheet.append(["Взам. инв. N", None, None, "∅125 / ∅110", "-100-3-ММ", None, None])
    sheet.append([None, None, None, "5. Отвод 90 град пластиковый ∅110", None, "шт.", 4])
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def _drawing_message(tmp_path, content="(файлы)", files=None):
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    message = store.add_message(
        chat_id,
        author="anna",
        role="user",
        content=content,
        action=chat_service.ACTION_DUCT,
        files=[("Заявка химвент.xlsx", _drawing_bytes())] if files is None else files,
    )
    return store, store.list_chats(owner="anna")[0], message


def test_drawing_layout_only_assembles_and_never_calls_model_or_calc(tmp_path, monkeypatch):
    """Шаг 1: «Спецификация с чертежа» — склейка кодом, ни расчётка, ни DeepSeek не вызываются, ключ не нужен."""

    store, chat, message = _drawing_message(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("модель и расчётка на чертёжном листе не вызываются")

    monkeypatch.setattr(actions, "duct_calc", forbidden)
    monkeypatch.setattr(actions, "duct_calc_text", forbidden)
    monkeypatch.setattr(actions, "ask_assistant", forbidden)
    settings = replace(_settings(tmp_path), deepseek_api_key="")

    answer = chat_service.run_action(
        store, settings, chat, message, chat_service.ACTION_DUCT, None, {}, spec_layout="drawing"
    )

    assert answer.content.startswith("Собрали плоскую спецификацию (2 позиции) из файла «Заявка химвент.xlsx».")
    assert "Модель его не разбирала и не считала" in answer.content
    assert "«Обычная таблица»" in answer.content
    assert [a.name for a in answer.attachments] == ["спецификация_Заявка химвент.xlsx"]
    assert answer.action == chat_service.ACTION_DUCT


def test_drawing_layout_result_is_read_by_the_ordinary_calc_converter(tmp_path):
    store, chat, message = _drawing_message(tmp_path)

    answer = chat_service.run_action(
        store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, None, {}, spec_layout="drawing"
    )

    text = actions.spec_lines_text(answer.attachments[0].path)
    assert text.splitlines()[1:] == [
        "1. Переход пластиковый, ∅125 / ∅110 ХИМВЕНТ-ПП-БС-125-110-100-3-ММ — 2 шт; система В5; кол-во: 2",
        "2. Отвод 90 град пластиковый ∅110 — 4 шт; система В5; кол-во: 4",
    ]


def test_drawing_layout_without_xlsx_asks_for_the_file(tmp_path):
    store, chat, message = _drawing_message(tmp_path, content="Переход ∅125 — 2 шт", files=[])

    answer = chat_service.run_action(
        store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, None, {}, spec_layout="drawing"
    )

    assert "приложите чертёжную спецификацию в формате .xlsx" in answer.content
    assert not answer.attachments


def test_drawing_layout_with_ordinary_table_explains_the_mistake(tmp_path):
    import io

    import openpyxl

    book = openpyxl.Workbook()
    book.active.append(["Просто текст"])
    buffer = io.BytesIO()
    book.save(buffer)
    store, chat, message = _drawing_message(tmp_path, files=[("обычная.xlsx", buffer.getvalue())])

    answer = chat_service.run_action(
        store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, None, {}, spec_layout="drawing"
    )

    assert "Не нашёл шапку таблицы" in answer.content
    assert "«Обычная таблица»" in answer.content
    assert not answer.attachments


def test_plain_layout_keeps_the_calc_path(tmp_path, monkeypatch):
    """Обычная таблица (и значение по умолчанию) — расчётка как раньше."""

    store, chat, message = _drawing_message(tmp_path)
    seen = {}

    def fake_duct_calc(**kwargs):
        seen["connection"] = kwargs["connection_label"]
        return actions.ActionResult("посчитано")

    monkeypatch.setattr(actions, "duct_calc", fake_duct_calc)

    for layout in ({}, {"spec_layout": "plain"}):
        seen.clear()
        answer = chat_service.run_action(
            store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, "Раструб", {}, **layout
        )
        assert answer.content == "посчитано"
        assert seen == {"connection": "Раструб"}


def test_duct_action_explains_how_to_send_spec_without_file_or_text(tmp_path):
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    message = store.add_message(chat_id, author="anna", role="user", content="(файлы)", action=chat_service.ACTION_DUCT)
    chat = store.list_chats(owner="anna")[0]

    answer = chat_service.run_action(store, _settings(tmp_path), chat, message, chat_service.ACTION_DUCT, "Фланец", {})
    assert "Для расчётки приложите файл спецификации" in answer.content
    assert "или напишите список позиций" in answer.content
