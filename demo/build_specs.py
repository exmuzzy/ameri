"""Собрать файлы спецификаций для демо-чатов (demo/specs/). Все данные вымышлены.

Запуск: ``python demo/build_specs.py``. Метаданные файлов (автор, компания) пустые,
даты фиксированы, чтобы повторная сборка давала те же файлы.
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import docx
import openpyxl

OUT = Path(__file__).resolve().parent / "specs"
FIXED_DATE = datetime(2026, 1, 1)


def xlsx(name: str, title: str, header: list[str], rows: list[tuple]) -> None:
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Спецификация"
    sheet.append([title])
    sheet.append(header)
    for row in rows:
        sheet.append(list(row))
    sheet.column_dimensions["A"].width = 60
    props = book.properties
    props.creator = props.lastModifiedBy = props.title = props.company = ""  # type: ignore[attr-defined]
    props.created = props.modified = FIXED_DATE
    book.save(OUT / name)


def docx_file(name: str, paragraphs: list[str], table: list[tuple] | None = None) -> None:
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    if table:
        grid = document.add_table(rows=0, cols=len(table[0]))
        for row in table:
            cells = grid.add_row().cells
            for cell, value in zip(cells, row):
                cell.text = str(value)
    core = document.core_properties
    for field in ("author", "last_modified_by", "title", "subject", "keywords", "comments", "category"):
        setattr(core, field, "")
    core.created = core.modified = FIXED_DATE
    core.revision = 1
    document.save(OUT / name)


def odt(name: str, blocks: list[tuple[str, list[tuple] | None]]) -> None:
    """Минимальный OpenDocument: заголовок раздела и таблица позиций под ним."""

    body = []
    for heading, rows in blocks:
        body.append(f"<text:p>{escape(heading)}</text:p>")
        if rows:
            cols = len(rows[0])
            body.append(f'<table:table table:name="t{len(body)}"><table:table-column table:number-columns-repeated="{cols}"/>')
            for row in rows:
                cells = "".join(
                    f'<table:table-cell office:value-type="string"><text:p>{escape(str(v))}</text:p></table:table-cell>'
                    for v in row
                )
                body.append(f"<table:table-row>{cells}</table:table-row>")
            body.append("</table:table>")
    ns = (
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"'
    )
    content = (
        f'<?xml version="1.0" encoding="UTF-8"?><office:document-content {ns} office:version="1.2">'
        f"<office:body><office:text>{''.join(body)}</office:text></office:body></office:document-content>"
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        "</manifest:manifest>"
    )
    stamp = FIXED_DATE.timetuple()[:6]
    with zipfile.ZipFile(OUT / name, "w") as archive:
        archive.writestr(zipfile.ZipInfo("mimetype", stamp), "application/vnd.oasis.opendocument.text")
        info = zipfile.ZipInfo("content.xml", stamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)
        info = zipfile.ZipInfo("META-INF/manifest.xml", stamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, manifest)


def text(name: str, content: str) -> None:
    (OUT / name).write_text(content.strip() + "\n", encoding="utf-8")


def big_csv() -> str:
    """Сценарий 7: 50 позиций трёх систем — прямые участки, отводы, переходы, тройники, решётки."""

    rows: list[tuple] = []
    n = 0

    def add(item: str, qty: object, unit: str) -> None:
        nonlocal n
        n += 1
        rows.append((n, item, qty, unit))

    for system, diameters in (("В1", (160, 200, 250, 315)), ("В2", (200, 250, 315, 400)), ("В3", (110, 125, 160))):
        for d in diameters:
            add(f"Воздуховод ПП ф{d} δ=3 мм ({system})", (d // 20) + 2, "мп")
        for d in diameters:
            add(f"Отвод 90° ПП ф{d} ({system})", 2 if d < 300 else 1, "шт")
        for big, small in zip(diameters[1:], diameters):
            add(f"Переход ПП ф{big}/ф{small} L-300мм ({system})", 1, "шт")
        for big, small in zip(diameters[1:], diameters):
            add(f"Тройник ПП ф{big}-ф{small} ({system})", 1, "шт")
    add("Отвод 45° ПП ф250 (В2)", 4, "шт")
    add("Заглушка ПП ф400 (В2)", 1, "шт")
    add("Зонт крышный ф400 (В2)", 1, "шт")
    add("Решётка ПП ф315 (В1)", 2, "шт")
    add("Ниппель ПП ф200 (В1)", 3, "шт")
    add("Ниппель ПП ф160 (В3)", 2, "шт")
    add("Дроссель-клапан ПП ф250 (В2)", 2, "шт")
    add("Дроссель-клапан ПП ф125 (В3)", 1, "шт")
    add("Воздуховод прямоугольный ПП 400×300 δ=4 (В2)", 6, "мп")
    add("Отвод 90° прямоугольный ПП 400×300 (В2)", 2, "шт")
    add("Переход ПП 400×300/ф315 L-400мм (В2)", 1, "шт")
    add("Гибкая вставка ф315 (В1)", 2, "шт")
    add("Гибкая вставка ф400 (В2)", 2, "шт")
    add("Хомут ф315 (В1)", 8, "шт")
    add("Хомут ф160 (В3)", 6, "шт")
    add("Виброизолятор под вентилятор (В2)", 4, "шт")
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["№", "Наименование", "Кол-во", "Ед. изм."])
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> None:
    OUT.mkdir(exist_ok=True)

    # 1. Excel в погонных метрах (раструб).
    xlsx(
        "01-severnyj-ceh-v2.xlsx",
        "Вытяжка В2, Северный цех. ",
        ["Наименование", "Кол-во", "Ед."],
        [
            ("Воздуховод из полипропилена ⌀200", 8, "мп"),
            ("Воздуховод из полипропилена ⌀315", 12, "мп"),
            ("Отвод 90° ⌀200", 3, "шт"),
            ("Тройник ⌀315-⌀200 под углом 90 гр.", 2, "шт"),
            ("Ниппель ⌀315", 1, "шт"),
            ("Зонт круглый 315", 1, "шт"),
            ("Защитная сетка ⌀315 (выброс)", 1, "шт"),
            ("Гибкая вставка ф315", 2, "шт"),
            ("Хомут ф315 с резинкой", 6, "шт"),
        ],
    )

    # 2. Word с «б=» и «δ=», тройники без ответвления, дроссель-клапаны.
    docx_file(
        "02-reagent-zakaz.docx",
        [
            "Заявка на воздуховоды, участок реагентов",
            "Воздуховод круглый из ПП б=3 мм ф250 – 18 м",
            "Воздуховод круглый из ПП б=3 мм ф160 – 9 м",
            "Воздуховод прямоугольный из ПП б=5 мм 600х400 – 2 м",
            "Переход из ПП δ=3 ∅250/∅160 – 3 шт.",
            "Тройник из ПП ф250 – 4 шт.",
            "Тройник из ПП ф160 – 2 шт.",
            "Отвод 90° из ПП ф160 – 6 шт.",
            "Дроссель-клапан круглый ПП ф250 – 3 шт.",
            "Дроссель-клапан круглый ПП ф160 – 5 шт.",
        ],
    )

    # 3. Прямоугольная система на фланцах.
    text(
        "03-pritok-p2-flanec.md",
        """
# Приток П2, административный корпус (фланцевое соединение)

| № | Наименование | Кол-во | Ед. |
|---|---|---|---|
| 1 | Воздуховод прямоугольный ПП 1000×600 δ=6 | 4 | м |
| 2 | Воздуховод прямоугольный ПП 800×500 δ=5 | 6 | м |
| 3 | Воздуховод прямоугольный ПП 600×400 δ=4 | 10 | м |
| 4 | Воздуховод прямоугольный ПП 400×300 δ=4 | 8 | м |
| 5 | Отвод 90° прямоугольный ПП 800×500 | 2 | шт |
| 6 | Отвод 90° прямоугольный ПП 400×300 | 3 | шт |
| 7 | Переход прямоугольный ПП 1000×600/800×500 L-500мм | 1 | шт |
| 8 | Переход прямоугольный ПП 800×500/600×400 L-500мм | 1 | шт |
| 9 | Переход прямоугольный ПП 600×400/400×300 L-400мм | 2 | шт |
| 10 | Тройник прямоугольный ПП 600×400/400×300 | 2 | шт |
| 11 | Заглушка прямоугольная ПП 400×300 | 2 | шт |
""",
    )

    # 3а. Та же система в Excel: менеджер пересохраняет таблицу, когда прямые из .md ушли в красные.
    xlsx(
        "03-pritok-p2-flanec.xlsx",
        "Приток П2, административный корпус (фланцевое соединение)",
        ["Наименование", "Кол-во", "Ед."],
        [
            ("Воздуховод прямоугольный ПП 1000×600 δ=6", 4, "мп"),
            ("Воздуховод прямоугольный ПП 800×500 δ=5", 6, "мп"),
            ("Воздуховод прямоугольный ПП 600×400 δ=4", 10, "мп"),
            ("Воздуховод прямоугольный ПП 400×300 δ=4", 8, "мп"),
            ("Отвод 90° прямоугольный ПП 800×500", 2, "шт"),
            ("Отвод 90° прямоугольный ПП 400×300", 3, "шт"),
            ("Переход прямоугольный ПП 1000×600/800×500 L-500мм", 1, "шт"),
            ("Переход прямоугольный ПП 800×500/600×400 L-500мм", 1, "шт"),
            ("Переход прямоугольный ПП 600×400/400×300 L-400мм", 2, "шт"),
            ("Тройник прямоугольный ПП 600×400/400×300", 2, "шт"),
            ("Заглушка прямоугольная ПП 400×300", 2, "шт"),
        ],
    )

    # 4. «Красные» позиции: нет второго сечения у перехода, нет размера у отвода.
    docx_file(
        "04-sklad-v3.docx",
        ["Склад готовой продукции, система В3"],
        [
            ("Наименование", "Кол-во", "Ед."),
            ("Воздуховод ПП ф315", "10", "мп"),
            ("Воздуховод ПП ф250", "6", "мп"),
            ("Переход ПП ф315", "2", "шт"),
            ("Отвод 90° ПП", "3", "шт"),
            ("Тройник ПП ф315-ф250", "1", "шт"),
            ("Заглушка ПП ф250", "1", "шт"),
        ],
    )
    docx_file(
        "04-sklad-v3-utochnenie.docx",
        ["Склад готовой продукции, система В3 (уточнено у клиента)"],
        [
            ("Наименование", "Кол-во", "Ед."),
            ("Воздуховод ПП ф315", "10", "мп"),
            ("Воздуховод ПП ф250", "6", "мп"),
            ("Переход ПП ф315/ф250 L-300мм", "2", "шт"),
            ("Отвод 90° ПП ф250", "3", "шт"),
            ("Тройник ПП ф315-ф250", "1", "шт"),
            ("Заглушка ПП ф250", "1", "шт"),
        ],
    )

    # 6. Две системы в одном .odt.
    odt(
        "06-ceh-pokraski-v1-p1.odt",
        [
            ("Цех покраски, объект «Восточная площадка»", None),
            ("Система В1", [
                ("Наименование", "Кол-во", "Ед."),
                ("Воздуховод ПП ∅400 δ=4", "14", "мп"),
                ("Воздуховод ПП ∅315 δ=3", "8", "мп"),
                ("Отвод 90° ПП ∅400", "4", "шт"),
                ("Переход ПП ∅400/∅315 L-400мм", "1", "шт"),
                ("Зонт крышный ф400", "1", "шт"),
            ]),
            ("Система П1", [
                ("Наименование", "Кол-во", "Ед."),
                ("Воздуховод прямоугольный ПП 500×400 δ=4", "12", "мп"),
                ("Отвод 90° прямоугольный ПП 500×400", "3", "шт"),
                ("Переход ПП 500×400/∅400 L-500мм", "1", "шт"),
                ("Решётка ПП 500×400", "2", "шт"),
            ]),
        ],
    )

    # 7. Большой CSV.
    text("07-tri-sistemy-50-pozicij.csv", big_csv())
    # 7а. Тот же список в Excel: менеджер пересохраняет, когда CSV не прочитался.
    rows = list(csv.reader(io.StringIO(big_csv()), delimiter=";"))
    xlsx(
        "07-tri-sistemy-50-pozicij.xlsx",
        "Системы В1, В2, В3 — выгрузка из проекта",
        ["Наименование", "Кол-во", "Ед."],
        [(name, int(qty), unit) for _, name, qty, unit in rows[1:]],
    )

    # 10. Учебная спецификация.
    text(
        "10-uchebnaya.md",
        """
# Учебная спецификация: вытяжка из мойки

| Наименование | Кол-во | Ед. |
|---|---|---|
| Воздуховод ПП ф160 | 5 | мп |
| Отвод 90° ПП ф160 | 2 | шт |
| Тройник ПП ф160 | 1 | шт |
| Переход ПП ф160/ф125 | 1 | шт |
| Зонт круглый 160 | 1 | шт |
| Хомут ф160 | 4 | шт |
""",
    )


if __name__ == "__main__":
    main()
