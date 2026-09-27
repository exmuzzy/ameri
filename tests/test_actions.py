from pathlib import Path

from ameri import actions
from ameri.harness import assistant_prompt, load_access
from ameri.auth import User
from ameri.store import Store, Usage

HARNESS = Path(__file__).resolve().parents[1] / "harness"


class FakeLlm:
    def __init__(self):
        self.messages = None

    def complete(self, messages, **_):
        self.messages = messages
        return "ответ", Usage(prompt_tokens=10, completion_tokens=2, cache_hit_tokens=8)


def test_ask_assistant_includes_history_and_files(tmp_path):
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    store.add_message(chat_id, author="anna", role="user", content="что тут?", files=[("spec.md", b"d=200")])
    llm = FakeLlm()
    result = actions.ask_assistant(llm, "sys", store.messages(chat_id), None, {"anna": "Анна"})
    assert result.text == "ответ"
    assert llm.messages[0] == {"role": "system", "content": "sys"}
    assert "Анна: что тут?" in llm.messages[1]["content"]
    assert "d=200" in llm.messages[1]["content"]


def test_duct_calc_unavailable_without_prototype(tmp_path):
    assert not actions.duct_calc_available(None)
    assert not actions.duct_calc_available(tmp_path)


def test_harness_files_load():
    access = load_access(HARNESS)
    manager = User("m", "M", "manager", "")
    leader = User("l", "L", "leader", "")
    assert access.can(manager, "action.duct_calc")
    assert not access.can(manager, "chat.view_all")
    assert access.can(leader, "chat.view_all")
    assert "ameri" in assistant_prompt(HARNESS)


def test_history_budget_keeps_latest(tmp_path, monkeypatch):
    monkeypatch.setattr(actions, "MAX_HISTORY_CHARS", 50)
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    for i in range(5):
        store.add_message(chat_id, author="anna", role="user", content=f"сообщение номер {i}")
    llm = FakeLlm()
    result = actions.ask_assistant(llm, "sys", store.messages(chat_id), None, {})
    contents = [m["content"] for m in llm.messages]
    assert result.usage.cache_hit_tokens == 8
    assert "сообщение номер 4" in contents[-1]
    assert "опущены" in contents[1]
    assert not any("номер 0" in c for c in contents)


def test_prompt_order_is_static_first(tmp_path):
    import shutil
    from ameri.harness import HarnessRepo

    harness = tmp_path / "harness"
    shutil.copytree(HARNESS, harness)
    repo = HarnessRepo(harness)
    repo.add_rule("Клапан", "Клапан считать как 2 метра прямого участка.", author="boss", source="исправление #1")
    repo.add_example("Сколько стоит отвод?", "Цену считает расчётка.", author="boss")
    prompt = assistant_prompt(harness)
    assert prompt.index("Ты — ассистент") < prompt.index("Правила, утверждённые") < prompt.index("Примеры правильных")


def test_odt_text(tmp_path):
    import zipfile

    content = (
        '<office:document-content xmlns:office="o" xmlns:text="t" xmlns:table="tb"><office:body><office:text>'
        "<text:p>Тема: Воздуховоды</text:p>"
        "<table:table><table:table-row><table:table-cell><text:p>Воздуховод ПП ф160 L1000</text:p></table:table-cell>"
        "<table:table-cell><text:p>2</text:p></table:table-cell><table:table-cell><text:p>шт</text:p></table:table-cell>"
        "</table:table-row></table:table>"
        "</office:text></office:body></office:document-content>"
    )
    path = tmp_path / "spec.odt"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("content.xml", content)
    assert actions.odt_text(path) == "Тема: Воздуховоды\nВоздуховод ПП ф160 L1000 | 2 | шт"


def test_non_ascii_key_gives_clear_message():
    import pytest
    from ameri.llm import BAD_KEY_MESSAGE, DeepSeekChat, LlmError, key_problem

    assert key_problem("sk-abc123") is None
    assert key_problem("sk-ключ") == BAD_KEY_MESSAGE
    assert key_problem("sk-abc 123") == BAD_KEY_MESSAGE
    with pytest.raises(LlmError, match="недопустимые символы"):
        DeepSeekChat(base_url="https://x", api_key="sk-вставьте ключ", model="m")


def test_spec_lines_from_tables(tmp_path):
    md = tmp_path / "s.md"
    md.write_text(
        "# Приток П2\n\n| № | Наименование | Кол-во | Ед. |\n|---|---|---|---|\n"
        "| 1 | Воздуховод ПП 400×300 δ=4 | 8 | м |\n| 2 | Отвод 90° ПП ф160 | 2 | шт |\n",
        encoding="utf-8",
    )
    assert actions.spec_lines_text(md).splitlines() == [
        "Приток П2",
        "1. Воздуховод ПП 400×300 δ=4 — 8 м; кол-во: 8",
        "2. Отвод 90° ПП ф160 — 2 шт; кол-во: 2",
    ]
    csv_file = tmp_path / "s.csv"
    csv_file.write_text("№;Наименование;Кол-во;Ед. изм.\n1;Воздуховод ПП ф160 (В1);10;мп\n2;Хомут ф160;4;шт\n", encoding="utf-8")
    assert actions.spec_lines_text(csv_file).splitlines() == [
        "1. Воздуховод ПП ф160 (В1) — 10 мп; кол-во: 10",
        "2. Хомут ф160 — 4 шт; кол-во: 4",
    ]
    assert actions.spec_lines_text(tmp_path / "x.xlsx") is None


def test_spec_lines_from_odt_keeps_system_headings():
    demo = Path(__file__).resolve().parents[1] / "demo" / "specs" / "06-ceh-pokraski-v1-p1.odt"
    lines = actions.spec_lines_text(demo).splitlines()
    assert lines[0] == "Цех покраски, объект «Восточная площадка»"
    assert "1. Воздуховод ПП ∅400 δ=4 — 14 мп; система В1; кол-во: 14" in lines
    assert "9. Решётка ПП 500×400 — 2 шт; система П1; кол-во: 2" in lines
    assert not any(line.startswith("Система") for line in lines)
    assert not any("Наименование" in line for line in lines)


def test_red_positions_from_result(tmp_path):
    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([None, 1, "Воздуховод ПП ф315\t10\tмп\tКол-во: 10 мп — отрезки по 1500 мм"])
    sheet.append([None, 2, "Переход ПП ф315\t2\tшт\tКол-во: 2 шт (проблема: Позиция 5: не указан размер d_out)"])
    sheet.append([None, 3, "Отвод 90° ПП\t3\tшт (проблема: Позиция 6: тип не распознан)"])
    path = tmp_path / "r.xlsx"
    book.save(path)
    assert actions.red_positions(path) == [
        "«Переход ПП ф315 · 2 · шт» — не указан второй диаметр (выход)",
        "«Отвод 90° ПП · 3 · шт» — тип не распознан",
    ]
    assert actions.red_positions(tmp_path / "нет.xlsx") == []


def test_assistant_prompt_includes_parse_rules():
    prompt = assistant_prompt(HARNESS)
    assert "Как расчётка понимает строки спецификаций" in prompt
    assert "Тройник без размера ответвления" in prompt
    assert prompt.index("Как расчётка понимает") < prompt.index("Примеры правильных")
