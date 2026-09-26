import re
import shutil
from pathlib import Path

from ameri import actions, materials
from ameri.harness import assistant_prompt
from ameri.store import Store, Usage

HARNESS = Path(__file__).resolve().parents[1] / "harness"

CHEMISTRY = """# Химическая стойкость

_Обновлено: 2026-09-26._ Таблицы для жидкостей.

## Кислоты {#acids}

Серная кислота 10 % при 20 °C — стоек.

### Оговорки
Пары и конденсат — уточнять у технолога.

Источник: [Каталог](https://example.com/chem.pdf)

## Щёлочи и аммиак {#alkalis}

Гидроксид натрия — стоек. Источник: [Каталог](https://example.com/chem.pdf)
"""

NAMES = """# Как называют изделия

_Обновлено: 2026-09-26._

## Отводы

Колено, поворот, угол — это отвод. Источник: [Прайс](https://example.com/price)
"""


class FakeLlm:
    def __init__(self):
        self.messages = None

    def complete(self, messages, **_):
        self.messages = messages
        return "ответ", Usage(prompt_tokens=10, completion_tokens=2, cache_hit_tokens=8)


def make_harness(tmp_path: Path) -> Path:
    harness = tmp_path / "harness"
    shutil.copytree(HARNESS, harness)
    folder = harness / "materials"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir()
    (folder / "20-chemical-resistance.md").write_text(CHEMISTRY, encoding="utf-8")
    (folder / "10-nomenclature.md").write_text(NAMES, encoding="utf-8")
    (folder / "README.md").write_text("# Как устроены материалы\n", encoding="utf-8")
    return harness


def test_parse_material_sections_and_ids(tmp_path):
    loaded = materials.load_materials(make_harness(tmp_path))
    assert [m.id for m in loaded] == ["nomenclature", "chemical-resistance"]
    chemistry = loaded[1]
    assert chemistry.title == "Химическая стойкость"
    assert "Обновлено" in chemistry.intro
    assert [s.id for s in chemistry.sections] == ["acids", "alkalis"]
    assert chemistry.sections[0].title == "Кислоты"
    assert "### Оговорки" in chemistry.sections[0].text
    assert chemistry.sections[0].link == "/materials?doc=chemical-resistance&section=acids"
    assert loaded[0].sections[0].id == "otvody"  # без {#id} — транслитерация заголовка


def test_find_sections_matches_word_forms(tmp_path):
    loaded = materials.load_materials(make_harness(tmp_path))
    found = materials.find_sections(loaded, "Выдержит ли ПП серную кислоту?")
    assert found and found[0].id == "acids"
    assert materials.find_sections(loaded, "клиент пишет «колено ф250»")[0].id == "otvody"
    assert materials.find_sections(loaded, "сколько стоит доставка") == []


def test_prompt_lists_materials_after_examples(tmp_path):
    harness = make_harness(tmp_path)
    (harness / "examples").mkdir(exist_ok=True)
    (harness / "examples" / "x.md").write_text("### Вопрос\n\nq\n\n### Правильный ответ\n\na\n", encoding="utf-8")
    prompt = assistant_prompt(harness)
    assert prompt.index("Примеры правильных") < prompt.index("## Материалы отрасли")
    assert "[Кислоты](/materials?doc=chemical-resistance&section=acids)" in prompt
    assert "2026-09-26" not in prompt  # в неизменной части промпта нет дат
    assert prompt == assistant_prompt(harness)


def test_ask_assistant_appends_sections_to_last_question(tmp_path):
    loaded = materials.load_materials(make_harness(tmp_path))
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    store.add_message(chat_id, author="anna", role="user", content="Выдержит ли ПП пары серной кислоты?")
    llm = FakeLlm()
    actions.ask_assistant(llm, "sys", store.messages(chat_id), None, {"anna": "Анна"}, materials=loaded)
    assert llm.messages[0] == {"role": "system", "content": "sys"}
    last = llm.messages[-1]
    assert last["role"] == "user" and last["content"].startswith("Анна: Выдержит ли ПП")
    assert "[Кислоты](/materials?doc=chemical-resistance&section=acids)" in last["content"]
    assert "Серная кислота 10 %" in last["content"]

    store.add_message(chat_id, author="anna", role="user", content="сколько стоит доставка")
    actions.ask_assistant(llm, "sys", store.messages(chat_id), None, {}, materials=loaded)
    assert "Материалы отрасли" in llm.messages[-1]["content"]  # тема предыдущего вопроса ещё действует
    actions.ask_assistant(llm, "sys", store.messages(chat_id)[-1:], None, {}, materials=loaded)
    assert "Материалы отрасли" not in llm.messages[-1]["content"]


def test_split_links_keeps_only_existing_sections(tmp_path):
    loaded = materials.load_materials(make_harness(tmp_path))
    text = (
        "ПП стоек, подробнее — [Кислоты](/materials?doc=chemical-resistance&section=acids) "
        "и ещё раз [Кислоты](/materials?doc=chemical-resistance&section=acids); "
        "[Выдуманный](/materials?doc=chemical-resistance&section=nope), [Весь материал](/materials?doc=nomenclature)."
    )
    shown, links = materials.split_links(text, loaded)
    assert "/materials?" not in shown
    assert "«Кислоты»" in shown and "Выдуманный" in shown
    assert links == [
        materials.MaterialLink("Кислоты", "chemical-resistance", "acids"),
        materials.MaterialLink("Весь материал", "nomenclature", None),
    ]


def test_repository_materials_are_valid():
    """Материалы Харнеса: у каждого раздела явный id и источник; ссылки в Харнесе ведут на существующие разделы."""

    loaded = materials.load_materials(HARNESS)
    ids = [m.id for m in loaded]
    assert len(ids) == len(set(ids))
    for material in loaded:
        text = material.path.read_text(encoding="utf-8")
        assert text.startswith("# "), material.path
        assert re.search(r"Обновлено: \d{4}-\d{2}-\d{2}", material.intro), f"{material.path}: нет даты обновления"
        section_ids = [s.id for s in material.sections]
        assert section_ids and len(section_ids) == len(set(section_ids)), material.path
        for section in material.sections:
            assert f"{{#{section.id}}}" in text, f"{material.path}: у раздела «{section.title}» нет явного {{#id}}"
            assert re.search(r"https?://", section.text), f"{material.path}: у раздела «{section.title}» нет источника"
    for path in [*HARNESS.glob("rules/*.md"), *HARNESS.glob("examples/*.md"), *HARNESS.glob("prompts/*.md")]:
        for label, url in re.findall(r"\[([^\]]+)\]\((/materials\?[^)\s]+)\)", path.read_text(encoding="utf-8")):
            shown, links = materials.split_links(f"[{label}]({url})", loaded)
            assert links, f"{path.name}: ссылка {url} ведёт на несуществующий раздел"


def test_ask_assistant_uses_attached_spec_for_materials(tmp_path):
    loaded = materials.load_materials(make_harness(tmp_path))
    store = Store(tmp_path / "db.sqlite3", tmp_path / "files")
    chat_id = store.create_chat("t", "anna")
    store.add_message(
        chat_id, author="anna", role="user", content="Что тут может смутить производство?",
        files=[("spec.md", "Колено ф250 — 2 шт".encode())],
    )
    llm = FakeLlm()
    actions.ask_assistant(llm, "sys", store.messages(chat_id), None, {}, materials=loaded)
    assert "[Отводы](/materials?doc=nomenclature&section=otvody)" in llm.messages[-1]["content"]
