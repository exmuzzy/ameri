from pathlib import Path

from ameri import actions
from ameri.harness import assistant_prompt, load_access
from ameri.auth import User
from ameri.store import Attachment, Store, Usage

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
    admin = User("a", "A", "admin", "")
    assert access.can(manager, "action.duct_calc")
    assert not access.can(manager, "chat.view_all")
    assert not access.can(manager, "harness.edit")
    assert not access.can(manager, "feedback.review")
    assert access.can(leader, "chat.view_all")
    assert access.can(leader, "harness.edit")
    assert access.can(leader, "feedback.review")
    assert access.can(admin, "harness.edit")
    assert access.can(admin, "feedback.review")
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


def _attachment(path: Path) -> Attachment:
    return Attachment(id=1, name=path.name, path=path, size=path.stat().st_size if path.exists() else 0)


def test_attachment_preview_text(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("привет мир", encoding="utf-8")
    preview = actions.attachment_preview(_attachment(path))
    assert preview.kind == "text"
    assert preview.text == "привет мир"
    assert not preview.truncated


def test_attachment_preview_markdown(tmp_path):
    path = tmp_path / "spec.md"
    path.write_text("# Заголовок\n\n| A | B |\n|---|---|\n| 1 | 2 |", encoding="utf-8")
    preview = actions.attachment_preview(_attachment(path))
    assert preview.kind == "markdown"
    assert preview.text == "# Заголовок\n\n| A | B |\n|---|---|\n| 1 | 2 |"
    assert not preview.truncated


def test_attachment_preview_image_and_pdf_by_suffix(tmp_path):
    image = tmp_path / "photo.png"
    image.write_bytes(b"\x89PNG\r\n")
    assert actions.attachment_preview(_attachment(image)).kind == "image"

    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    assert actions.attachment_preview(_attachment(pdf)).kind == "pdf"


def test_attachment_preview_unsupported_for_legacy_doc(tmp_path):
    path = tmp_path / "старый.doc"
    path.write_bytes(b"\xd0\xcf\x11\xe0")
    assert actions.attachment_preview(_attachment(path)).kind == "unsupported"


def test_attachment_preview_docx(tmp_path):
    from docx import Document

    path = tmp_path / "spec.docx"
    document = Document()
    document.add_paragraph("Раздел 1")
    document.add_paragraph("Воздуховод ф160")
    document.save(path)
    preview = actions.attachment_preview(_attachment(path))
    assert preview.kind == "text"
    assert preview.text == "Раздел 1\nВоздуховод ф160"


def test_attachment_preview_xlsx(tmp_path):
    from openpyxl import Workbook

    path = tmp_path / "spec.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Наименование", "Кол-во"])
    sheet.append(["Воздуховод ф160", 2])
    workbook.save(path)
    preview = actions.attachment_preview(_attachment(path))
    assert preview.kind == "table"
    assert preview.rows == [["Наименование", "Кол-во"], ["Воздуховод ф160", "2"]]
    assert not preview.truncated


def test_attachment_preview_odt(tmp_path):
    import zipfile

    content = (
        '<office:document-content xmlns:office="o" xmlns:text="t"><office:body><office:text>'
        "<text:p>Тема: Воздуховоды</text:p>"
        "</office:text></office:body></office:document-content>"
    )
    path = tmp_path / "spec.odt"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("content.xml", content)
    preview = actions.attachment_preview(_attachment(path))
    assert preview.kind == "text"
    assert preview.text == "Тема: Воздуховоды"


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


# --- Q38 и Q39 поверх прототипа (прототипа в репозитории нет: проверяем на его подобии) ---

from dataclasses import dataclass as _dc, field as _field
from types import SimpleNamespace as _NS


@_dc(frozen=True)
class _Question:
    code: str
    text: str


@_dc(frozen=True)
class _Position:
    source_no: str
    source_text: str
    element_type: str | None = None
    qty: float | None = None
    length_mm: float | None = None
    size: dict = _field(default_factory=dict)
    questions: tuple = ()


def test_round_umbrella_single_size_gets_dome_neck_plus_1000():
    # Решение 09.10.2026: купол = патрубок + 2 × 500 (вылет), как в скилле; было 2 × патрубок.
    position = _Position("1", "Зонт круглый 250", "umbrella_round", 1, size={"d": 250},
                         questions=(_Question("missing_size_d_dome", "Не указан диаметр купола"),))
    fixed = actions.umbrella_with_dome(position)
    assert fixed.size["d_neck"] == 250 and fixed.size["d_dome"] == 1250
    assert fixed.questions == ()
    explicit = _Position("2", "Зонт", "umbrella_round", 1, size={"d_neck": 250, "d_dome": 450})
    assert actions.umbrella_with_dome(explicit).size["d_dome"] == 450
    square = _Position("3", "Зонт 300х300", "umbrella_square", 1, size={"side_neck": 300})
    assert actions.umbrella_with_dome(square) is square


def test_section_heading_detection():
    def heading(text, **fields):
        return actions.is_section_heading(text, _Position("1", text, **fields))

    assert heading("Вытяжка из химлаборатории.")
    assert heading("Спецификация\tНаименование\tКол-во\tЕд.")
    assert heading("Приток П2, административный корпус")
    assert not heading("Переход ф315/ф250")
    assert not heading("Уголок 45х45х4")
    assert not heading("Скотч\t2\tшт")
    assert not heading("Отвод", size={"d": 200})
    assert not heading("Хомут", qty=2)


def test_preview_without_headings_rechecks_completeness():
    from dataclasses import replace

    heading = _Position("1", "Вытяжка из химлаборатории")
    duct = _Position("2", "Воздуховод ⌀200 — 2 шт", "straight_round", 2, 1500, {"d": 200})
    lost = _NS(source_no="3", source_text="Что-то непонятное", position=None, status="problem")
    item = lambda p: _NS(source_no=p.source_no, source_text=p.source_text, position=p, status="ready")  # noqa: E731
    message = "В разборе есть позиции без корректного количества"
    completeness = _NS(source_position_count=3, source_quantity_sum=None, message=message)

    @_dc(frozen=True)
    class Preview:
        positions: tuple
        response: object
        completeness: object
        source_position_count: int = 3
        model_position_count: int = 2
        model_quantity_sum: float = 2
        completeness_message: str | None = message
        warnings: tuple = (message, "другое")

    @_dc(frozen=True)
    class Response:
        positions: tuple

    def compare(source, response):
        count = len(response.positions)
        ok = all(p.qty is not None for p in response.positions)
        return _NS(source_position_count=source.position_count, model_position_count=count,
                   model_quantity_sum=sum(p.qty or 0 for p in response.positions),
                   message=None if ok and count == source.position_count else "расхождение")

    preview = Preview((item(heading), item(duct), lost), Response((heading, duct)), completeness)
    fixed = actions.preview_without_headings(preview, compare)
    assert [p.source_no for p in fixed.positions] == ["2", "3"]  # неразобранная строка не пропала
    assert fixed.response.positions == (duct,)
    # Источник: 3 строки минус заголовок = 2, модель вернула 1 позицию — расхождение видно.
    assert fixed.completeness.source_position_count == 2
    assert fixed.warnings == ("другое", "расхождение")
    assert actions.preview_without_headings(replace(preview, positions=(item(duct),)), compare).positions == (item(duct),)


def test_xlsx_without_index_column_becomes_numbered_lines(tmp_path):
    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append(["Вытяжка В2, Северный цех. "])
    sheet.append(["Наименование", "Кол-во", "Ед."])
    sheet.append(["Воздуховод из полипропилена ⌀200", 8, "мп"])
    sheet.append(["Зонт круглый 315", 1, "шт"])
    plain = tmp_path / "plain.xlsx"
    book.save(plain)
    assert actions.spec_lines_text(plain).splitlines() == [
        "Вытяжка В2, Северный цех.",
        "1. Воздуховод из полипропилена ⌀200 — 8 мп; кол-во: 8",
        "2. Зонт круглый 315 — 1 шт; кол-во: 1",
    ]
    sheet.insert_cols(1)
    sheet["A2"] = "№"
    numbered = tmp_path / "numbered.xlsx"
    book.save(numbered)
    assert actions.spec_lines_text(numbered) is None  # с «№» позиции делит сам прототип


def test_unit_column_before_quantity_gives_number_then_unit(tmp_path):
    """Прототип узнаёт метраж только как «54.8 м»: при «м. 54.8» прямой участок не режется по 1500,
    а модель ставит 54,8 шт по 54 800 мм. Колонка «Ед.» перед «Кол-вом» — частый вид спецификаций."""

    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([None, None, "Система Во 1.1"])
    sheet.append([None, None, "Скруббер STRADA CLEAN C 18-35-750", "ХИМВЕНТ-Н-О-810", None, None, "шт.", 1])
    sheet.append([None, None, "Воздуховод из полипропилена ø150, толщ. 3,0 мм", None, None, None, "м.", 54.8])
    sheet.append([None, None, "Воздуховод из полипропилена ø900, толщ. 5,0 мм", None, None, None, "м.", 0.5])
    path = tmp_path / "unit_first.xlsx"
    book.save(path)
    assert actions.spec_lines_text(path).splitlines() == [
        "1. Скруббер STRADA CLEAN C 18-35-750 — ХИМВЕНТ-Н-О-810 1 шт.; система Во 1.1; кол-во: 1",
        "2. Воздуховод из полипропилена ø150, толщ. 3,0 мм — 54.8 м.; система Во 1.1; кол-во: 54.8",
        "3. Воздуховод из полипропилена ø900, толщ. 5,0 мм — 0.5 м.; система Во 1.1; кол-во: 0.5",
    ]


def test_request_in_copy_of_our_calc_template_keeps_only_name_quantity_unit(tmp_path):
    """Заявка 09.10.2026 пришла в копии нашей расчётки: шапка «Номенклатура … S элемента, м2» с цифрой
    становилась позицией № 1 и сдвигала номера, а нули и #DIV/0! расчётных колонок попадали в каждую строку."""

    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append(["Номенклатура ", "Кол-во", "Ед.изм.", "Толщина материала в мм", "S элемента, м2", "S общ ",
                  "Цена  кг  ", "Плотность", "% на раскрой", "К/эф", "Цена за шт без соединения, руб",
                  "ИТОГО без соединения", "СОЕДИНЕНИЕ", "Цена за шт с соединением, руб",
                  "ИТОГО с соединением, руб", "Масса воздуховодов всего, с креплением, кг *"])
    sheet.append(["Дроссель клапан  ПП  400х250 фф", 2, "шт", *[None] * 10, 0, 0, "#DIV/0!"])
    sheet.append(["Шумоглушитель ПП ф500 L 900 фф", 1, "шт", *[None] * 10, 0, 0, "#DIV/0!"])
    path = tmp_path / "client.xlsx"
    book.save(path)
    assert actions.spec_lines_text(path).splitlines() == [
        "1. Дроссель клапан ПП 400х250 фф — 2 шт; кол-во: 2",
        "2. Шумоглушитель ПП ф500 L 900 фф — 1 шт; кол-во: 1",
    ]


def fake_prototype(tmp_path, error: str) -> Path:
    """Минимальный duct-calc: pipeline падает с ValueError, как прототип на файле без позиций."""

    package = tmp_path / "proto" / "src" / "duct_calc"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "model_client.py").write_text(
        "class ModelClientConfig:\n"
        "    last = None\n"
        "    def __init__(self, **kw):\n"
        "        ModelClientConfig.last = kw\n"
        "class DeepSeekClient:\n    def __init__(self, config): pass\n",
        encoding="utf-8",
    )
    (package / "pipeline.py").write_text(
        "PASSTHROUGH_ITEM_KEYWORDS = ()\nGRID_KEYWORDS = ()\nVALVE_KEYWORDS = ()\n"
        "def build_system_prompt(): return ''\n"
        "def with_umbrella_optional_neck_key(*a, **kw): return a[0] if a else None\n"
        "def preview_specification(*a, **kw): return None\n"
        "def compare_completeness(*a, **kw): return None\n"
        "class PipelineNeedsInput(ValueError): pass\n"
        f"def run_specification_pipeline(**kw): raise ValueError({error!r})\n",
        encoding="utf-8",
    )
    (tmp_path / "proto" / "data").mkdir()
    return tmp_path / "proto"


def test_duct_calc_explains_spec_without_positions(tmp_path, monkeypatch):
    import sys

    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        monkeypatch.delitem(sys.modules, name)
    proto = fake_prototype(tmp_path, "Нельзя сформировать расчётку без позиций")
    monkeypatch.setattr(sys, "path", list(sys.path))
    spec_path = tmp_path / "spec.docx"
    spec_path.write_bytes(b"")
    spec = Attachment(id=1, name="spec.docx", path=spec_path, size=0)
    result = actions.duct_calc(
        spec=spec, connection_label="Раструб", duct_calc_dir=proto, base_url="u", api_key="sk-test", model="m"
    )
    assert result.text == actions.NO_POSITIONS_TEXT
    from duct_calc.model_client import ModelClientConfig

    assert ModelClientConfig.last["timeout_seconds"] == 7 * 60
    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        del sys.modules[name]


def test_duct_calc_text_wraps_chat_message(monkeypatch, tmp_path):
    captured = {}

    def fake_duct_calc(**kwargs):
        captured["name"] = kwargs["spec"].name
        captured["text"] = kwargs["spec"].path.read_text(encoding="utf-8")
        return actions.ActionResult("Расчётка по файлу «позиции-из-чата.md» готова.")

    monkeypatch.setattr(actions, "duct_calc", fake_duct_calc)
    result = actions.duct_calc_text(
        text="Шибер 160 — 2 шт",
        connection_label="Фланец",
        duct_calc_dir=tmp_path,
        base_url="u",
        api_key="sk-test",
        model="m",
    )
    assert captured == {"name": "позиции-из-чата.md", "text": "Шибер 160 — 2 шт\n"}
    assert result.text.startswith("Расчётка по тексту из чата")


def test_line_without_connection_is_not_overridden_by_chat_choice():
    plain = "Отвод 90 круглый без соединения из полипропилена СМП-ППС-_/_-О90-400"
    assert actions.names_no_connection(plain)
    assert actions.names_no_connection("Переход ПП ф200, соединение отсутствует")
    assert actions.names_no_connection("Воздуховод ф250, соединение не требуется")
    assert actions.names_no_connection("Отвод ф200 без фланцев и без раструбов")
    assert not actions.names_no_connection("Отвод 90 ПП ф400 муфтовое соединение")
    assert not actions.names_no_connection("Воздуховод круглый из полипропилена ф 355 L-2000 мм")


def test_coupling_wording_is_socket_not_a_separate_product():
    assert actions.is_coupling_item("Муфта из полипропилена СМП-ППС-М-355")
    assert actions.is_coupling_item("Муфта соединительная для круглых воздуховодов полипропиленовая 315")
    assert not actions.is_coupling_item("Отвод 90 круглый без соединения из полипропилена СМП-ППС-_/_-О90-400")
    assert not actions.is_coupling_item("Воздуховод круглый из полипропилена ф 355 муфтовое соединение L-2000")
    assert actions.names_socket_connection("Отвод 90 ПП ф400 муфтовое соединение")
    assert not actions.names_socket_connection("Отвод 90 круглый без соединения из полипропилена")


def test_install_counts_coupling_as_one_socket(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        monkeypatch.delitem(sys.modules, name)
    proto = fake_prototype(tmp_path, "не важно")
    monkeypatch.setattr(sys, "path", [str(proto / "src"), *sys.path])
    from duct_calc import pipeline

    seen = {}

    def original_nipple(text):
        return "ниппел" in text.lower()

    def original_global(position, connection_type):
        seen["connection"] = connection_type
        return position

    pipeline._is_nipple_text = original_nipple
    pipeline.with_global_connection = original_global
    actions._install_harness(None)
    assert pipeline._is_nipple_text("Муфта из полипропилена СМП-ППС-М-355")
    assert pipeline._is_nipple_text("ниппель 400")
    assert not pipeline._is_nipple_text("Отвод 90 круглый без соединения")
    pipeline.with_global_connection(SimpleNamespace(source_text="Отвод 90 ПП ф400 муфтовое соединение"), "none")
    assert seen["connection"] == "socket"
    pipeline.with_global_connection(SimpleNamespace(source_text="Отвод 90 круглый без соединения"), "flange")
    assert seen["connection"] == "none"
    pipeline.with_global_connection(SimpleNamespace(source_text="Воздуховод ф400"), "flange")
    assert seen["connection"] == "flange"
    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        del sys.modules[name]


def test_harness_keeps_prototype_meter_cutting_q37(tmp_path, monkeypatch):
    """Q37 (а): метраж режет сам прототип — 1500 мм и остаток; Харнес не подменяет его нарезку."""

    import sys

    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        monkeypatch.delitem(sys.modules, name)
    proto = fake_prototype(tmp_path, "не важно")
    monkeypatch.setattr(sys, "path", [str(proto / "src"), *sys.path])
    from duct_calc import pipeline

    def prototype_cutting(*args, **kwargs):
        return "нарезка прототипа"

    pipeline._meter_segment_rows = prototype_cutting
    actions._install_harness(None)
    assert pipeline._meter_segment_rows is prototype_cutting
    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        del sys.modules[name]


def test_result_notes_umbrella_and_flange20(tmp_path):
    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([None, 1, "Зонт круглый 315\t1\tшт"])
    sheet.append([None, 2, "Переход ф450/600х300 — труба/фланец20"])
    sheet.append([None, 3, "Отвод ф200 (проблема: Позиция 3: тип не распознан)"])
    sheet.append([None, 4, "Воздуховод ф200 — 2 шт по 1000 мм"])
    path = tmp_path / "r.xlsx"
    book.save(path)
    notes = actions.result_notes(path, "Раструб")
    assert len(notes) == 2
    assert "Проверьте зонты вручную" in notes[0] and "Зонт круглый 315 · 1 · шт" in notes[0]
    assert "шинорейка 20" in notes[1] and "«раструб»" in notes[1] and "фланец20" in notes[1]
    assert "стандартным фланцем" in actions.result_notes(path, "Фланец")[1]
    assert not actions.FLANGE_20.search("Воздуховод ф200")


def test_umbrella_note_depends_on_type(tmp_path):
    """У вытяжного (островного) зонта купола нет — подпись «купол = патрубок + 1000» его вводила в заблуждение."""

    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([None, 4, "Зонт вытяжной ПП 1400х1000 Н300 врезка ф315 площадка 700х500 ф — 3 шт; кол-во: 3"])
    sheet.append([None, 5, "Зонт крышный ПП ф500 ф — 1 шт; кол-во: 1"])
    path = tmp_path / "r.xlsx"
    book.save(path)
    island, roof = actions.result_notes(path, "Фланец")[0].splitlines()[1:]
    assert island.startswith("- «Зонт вытяжной ПП 1400х1000 Н300 врезка ф315 площадка 700х500 ф» — островной")
    assert "врезка — L200 и 1 фланец" in island and "купол" not in island
    assert roof == "- «Зонт крышный ПП ф500 ф» — купол взят как патрубок + 1000 мм, если не указан"


def test_manager_message_drops_model_warnings_keeps_code_ones():
    """Свободный текст модели («element_type = null…») — её промежуточный шаг, менеджеру он не нужен;
    сигнал кода о полноте разбора остаётся."""

    @_dc(frozen=True)
    class Preview:
        response: object
        warnings: tuple

    model = "Позиции «Шумоглушитель» — вне каталога типов: element_type = null."
    code = "В разборе есть позиции без корректного количества"
    preview = Preview(_NS(warnings=(model,)), (model, code))
    assert actions.without_model_warnings(preview).warnings == (code,)
    assert actions.manager_warning("Коэффициент L для нестандарт фасон взят из скилла") == (
        "Раскрой нестандартных изделий (зонты, клапаны, шумоглушители) — 1,5 (в шаблоне «от 1,5, уточнять»)."
    )
    assert actions.manager_warning(code) == code


def test_himvent_and_lone_connection_are_read_from_the_line():
    """ХИМВЕНТ на названном элементе считается. Отдельный фланец берёт размер и количество из строки."""

    assert actions.is_himvent_duct("Воздуховод аналог ХИМВЕНТ ø250 L1500")
    assert actions.is_himvent_duct("Отвод 90-ПП-110-3-ММ ХИМВЕНТ")
    assert actions.is_himvent_duct("Переход ХИМВЕНТ-ПП-250/200-3-ММ")
    assert actions.is_himvent_duct("Прямой участок ХИМВЕНТ ф250")
    assert not actions.is_himvent_duct("ХИМВЕНТ-Н-О-1130-ПП-БС-У2-30/1000-ПО")
    assert not actions.is_himvent_duct("Вентилятор ХИМВЕНТ-Н-К-О-225")
    assert not actions.is_himvent_duct("Скруббер ХИМВЕНТ")

    assert actions.lone_connection_kind("фланец 355") == "flange"
    assert actions.lone_connection_kind("фланцы 355 — 4 шт") == "flange"
    assert actions.lone_connection_kind("фланец ПП 600х300") == "flange"
    assert actions.lone_connection_kind("фланец 200") == "flange"
    assert actions.lone_connection_kind("раструб 315") == "socket"
    assert actions.lone_connection_kind("фланец 20") is None
    assert actions.lone_connection_kind("ф20") is None
    assert actions.lone_connection_kind("Отвод 90 ф315 фланец") is None

    assert actions.lone_connection_section("фланец 355") == ("round", (355.0,))
    assert actions.lone_connection_section("фланец 355 — 4 шт") == ("round", (355.0,))
    assert actions.lone_connection_section("фланец ПП 600х300") == ("rect", (600.0, 300.0))
    assert actions.stated_piece_quantity(None, "фланец 355") == 1
    assert actions.stated_piece_quantity(None, "фланец 355 — 4 шт") == 4
    assert actions.stated_piece_quantity(4, "фланец 355") == 4
    assert actions.stated_piece_quantity("4", "фланец 355") == 4
    assert actions.stated_piece_quantity("4", "фланец 355 — 2 шт") == 4
    assert actions.stated_piece_quantity("нет", "фланец 355 — 4 шт") == 4


def test_install_prices_lone_connection_and_keeps_named_himvent(tmp_path, monkeypatch):
    """Обёртка поверх старого прототипа: воздуховод с ХИМВЕНТ не покупной, фланец 355 — одно соединение."""

    import sys

    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        monkeypatch.delitem(sys.modules, name)
    proto = fake_prototype(tmp_path, "не важно")
    monkeypatch.setattr(sys, "path", [str(proto / "src"), *sys.path])
    from duct_calc import pipeline

    pipeline.PASSTHROUGH_ITEM_KEYWORDS = ("скруббер", "химвент", "вентилятор")

    def old_scrubber(source_text: str) -> bool:
        lower = source_text.lower().replace("ё", "е")
        return any(word in lower for word in pipeline.PASSTHROUGH_ITEM_KEYWORDS)

    def old_rules(position):
        return position

    def old_row(position, coefficients, *args, system=None, connection_type=None, **kwargs):
        return _NS(passthrough=True, connection_type=connection_type, text=position.source_text)

    pipeline._is_scrubber_text = old_scrubber
    pipeline.with_special_catalog_rules = old_rules
    pipeline.position_to_output_row = old_row

    calls = []

    def fake_cost(kind, shape, dimensions):
        calls.append((kind, shape, dimensions))
        return "one"

    monkeypatch.setattr(actions, "connection_unit_cost", fake_cost)
    monkeypatch.setattr(actions, "_output_row", lambda **kwargs: _NS(**kwargs))
    actions._install_harness(None)
    actions._install_harness(None)

    assert not pipeline._is_scrubber_text("Воздуховод аналог ХИМВЕНТ ø250 L1500")
    assert not pipeline._is_scrubber_text("Отвод 90-ПП-110-3-ММ ХИМВЕНТ")
    assert pipeline._is_scrubber_text("ХИМВЕНТ-Н-О-1130-ПП-БС-У2-30/1000-ПО")
    assert pipeline._is_scrubber_text("Вентилятор ХИМВЕНТ-Н-К-О-225")
    assert pipeline._is_scrubber_text("Скруббер ХИМВЕНТ")
    assert pipeline._is_scrubber_text("Воздуховод скруббер ХИМВЕНТ ф250")

    @_dc(frozen=True)
    class Position:
        source_no: str
        source_text: str
        element_type: str | None
        qty: float | None
        length_mm: float | None
        size: dict
        ends: tuple
        questions: tuple

    def position(text, **kwargs):
        data = dict(
            source_no="1",
            source_text=text,
            element_type=None,
            qty=None,
            length_mm=None,
            size={},
            ends=(),
            questions=(("unknown_type", "Тип не распознан"),),
        )
        data.update(kwargs)
        return Position(**data)

    ready = pipeline.with_special_catalog_rules(position("фланец 355"))
    assert ready.questions == ()
    assert ready.qty == 1
    assert ready.element_type is None
    assert ready.size == {"d": 355.0}
    elbow = position("Отвод 90 ф315 фланец", element_type="elbow_round", qty=1, questions=(("keep", "остаётся"),))
    assert pipeline.with_special_catalog_rules(elbow) is elbow

    one = pipeline.position_to_output_row(position("фланец 355"), None, connection_type="socket")
    assert one.purchased is True
    assert one.area_m2 is None
    assert one.quantity == 1
    assert one.connection_cost == "one"
    assert calls == [("flange", "round", (355.0,))]

    from_text_qty = pipeline.position_to_output_row(position("фланец 355", qty="4"), None, connection_type="socket")
    assert from_text_qty.quantity == 4
    assert from_text_qty.purchased is True
    assert from_text_qty.connection_cost == "one"
    assert calls[-1] == ("flange", "round", (355.0,))

    four = pipeline.position_to_output_row(position("фланец 355 — 4 шт"), None, connection_type="none")
    assert four.quantity == 4
    assert calls == [
        ("flange", "round", (355.0,)),
        ("flange", "round", (355.0,)),
        ("flange", "round", (355.0,)),
    ]

    socket = pipeline.position_to_output_row(position("раструб 315"), None, connection_type="flange")
    assert socket.quantity == 1
    assert calls[-1] == ("socket", "round", (315.0,))

    rect = pipeline.position_to_output_row(position("фланец ПП 600х300"), None, connection_type="socket")
    assert rect.quantity == 1
    assert calls[-1] == ("flange", "rect", (600.0, 300.0))

    before = len(calls)
    assert pipeline.position_to_output_row(position("фланец 20"), None, connection_type="flange").passthrough is True
    assert pipeline.position_to_output_row(
        position("Отвод 90 ф315 фланец", element_type="elbow_round", qty=1), None, connection_type="socket"
    ).passthrough is True
    assert len(calls) == before

    for name in [n for n in sys.modules if n == "duct_calc" or n.startswith("duct_calc.")]:
        del sys.modules[name]
