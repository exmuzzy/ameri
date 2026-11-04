"""Склейка чертёжной спецификации (лист по ГОСТ 21.110) в плоскую таблицу.

Шаг 1 из двух, без модели: код приводит чертёжный лист к виду «одна позиция — одна строка»
и отдаёт `.xlsx` на проверку. Менеджер правит его руками и сам шлёт на расчётку как обычную
таблицу (шаг 2). Длину прямика, размеры зонта и количество здесь не придумываем (Q48):
в колонке «Кол-во» остаётся то, что написано в чертеже.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path

NOTE = "Собранная спецификация. Проверьте и отправьте на расчётку как обычную таблицу."
FLAT_HEADER = ["Наименование", "Кол-во", "Ед."]

_SYSTEM_HEADING = re.compile(r"^система\s+\S+", re.IGNORECASE)
_STAMP = re.compile(r"взам\.?\s*инв|подпись и дата|инв\.\s*n", re.IGNORECASE)
_POS_NUM = re.compile(r"^\s*\d+\.(?:\d+)?\s*")
_SUBITEM = re.compile(r"^\s*\d+\.\d+\s*")
_NUMBER = re.compile(r"^\d+(?:[.,]\d+)?$")
_DIAMETER_SIGN = re.compile(r"[∅⌀øØÆф]\s*\d", re.IGNORECASE)
_UNIT_DOT = re.compile(r"^[а-яa-z]+\.$", re.IGNORECASE)
_MARK_DOUBLE_HYPHEN = re.compile(r"-\s*-\s*(?=\S)")
_DIAMETER_PREFIXES = ("∅", "⌀", "ø", "Ø", "ф", "Ф")


class DrawingSpecError(ValueError):
    """Файл не читается как чертёжная спецификация; текст ошибки показывается менеджеру."""


@dataclass(frozen=True)
class DrawingPosition:
    system: str
    name: str
    qty: int | float
    unit: str


@dataclass
class _Draft:
    system: str
    name: str
    qty: str = ""
    unit: str = ""
    marks: list[str] = field(default_factory=list)


def _cell(value: object) -> str:
    return "" if value is None else " ".join(str(value).split())


def _is_header(cells: list[str]) -> bool:
    joined = " ".join(cell.lower() for cell in cells if cell)
    return "наименование" in joined and ("кол" in joined or "единиц" in joined or joined.startswith("ед"))


def _header_map(row: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for index, cell in enumerate(row):
        low = cell.lower()
        if "наименование" in low:
            mapping["name"] = index
        elif "марка" in low or low.startswith("тип"):
            mapping["mark"] = index
        elif "единиц" in low or low.startswith("ед"):
            mapping["unit"] = index
        elif "кол" in low:
            mapping["qty"] = index
    return mapping


def _field(row: list[str], columns: dict[str, int], key: str) -> str:
    index = columns.get(key)
    return row[index] if index is not None and index < len(row) else ""


def _strip_number(name: str) -> str:
    return _POS_NUM.sub("", name, count=1).strip(" .")


def _join_marks(marks: list[str]) -> str:
    """Марка в чертеже рвётся по строкам на дефисе: «ХИМВЕНТ-ПП-БС-» + «-125-110-» — одна марка."""

    result = ""
    for part in marks:
        part = part.strip()
        if not part:
            continue
        if not result:
            result = part
        elif result.endswith("-") or part.startswith("-"):
            result = _MARK_DOUBLE_HYPHEN.sub("-", result + part)
        else:
            result = f"{result} {part}"
    return result


def _with_mark(name: str, marks: list[str]) -> str:
    mark = _join_marks(marks)
    if not mark or mark.lower() in name.lower():
        return name
    if _NUMBER.fullmatch(mark):
        # Голое число в колонке марки («315» у шумоглушителя) — сечение, а не количество.
        return name if _DIAMETER_SIGN.search(name) else f"{name} ⌀{mark}"
    return f"{name} {mark}"


def _quantity(text: str) -> int | float:
    value = float(text.replace(",", "."))
    return int(value) if value == int(value) else value


def _unit(text: str) -> str:
    text = text.strip()
    if not text:
        return "шт"
    return text[:-1] if _UNIT_DOT.fullmatch(text) else text


def assemble_positions(path: Path) -> list[DrawingPosition]:
    """Позиции чертёжной спецификации с первой вкладки `.xlsx`, склеенные в одну строку на позицию."""

    import openpyxl

    try:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as error:  # noqa: BLE001 - любой нечитаемый файл — понятная ошибка менеджеру
        raise DrawingSpecError(f"Не получилось открыть файл как Excel: {error.__class__.__name__}.") from error
    try:
        rows = [[_cell(value) for value in row] for row in book.worksheets[0].iter_rows(values_only=True)]
    finally:
        book.close()

    columns: dict[str, int] | None = None
    system = ""
    pending: _Draft | None = None  # начало позиции без количества: «7. Воздуховод пластиковый»
    current: _Draft | None = None
    drafts: list[_Draft] = []

    def flush() -> None:
        nonlocal current
        if current is not None:
            drafts.append(current)
            current = None

    for raw in rows:
        cells = [cell for cell in raw if cell and not _STAMP.search(cell)]
        if not cells:
            continue
        if _is_header(cells):
            columns = _header_map(raw)  # шапка повторяется на каждом листе чертежа
            continue
        if columns is None:
            if _SYSTEM_HEADING.match(cells[0]):
                system = cells[0]
            continue

        name = _field(raw, columns, "name")
        mark = _field(raw, columns, "mark")
        unit = _field(raw, columns, "unit")
        qty = _field(raw, columns, "qty").replace(",", ".")
        name = "" if _STAMP.search(name) else name
        mark = "" if _STAMP.search(mark) else mark
        if name and _SYSTEM_HEADING.match(name):
            flush()
            pending = None
            system = name
            continue
        has_qty = _NUMBER.fullmatch(qty) is not None
        if not name and not mark and not has_qty:
            continue

        if not has_qty:
            if name and _POS_NUM.match(name):
                # Номер без количества — начало позиции (родитель «8. Воздуховод …» или имя, перенесённое на строку).
                flush()
                pending = _Draft(system, _strip_number(name), marks=[mark] if mark else [])
            elif current is not None:
                current.name = f"{current.name} {name}".strip()
                if mark:
                    current.marks.append(mark)
            elif pending is not None:
                pending.name = f"{pending.name} {name}".strip()
                if mark:
                    pending.marks.append(mark)
            continue

        flush()
        clean = _strip_number(name) if name else mark
        marks = [mark] if name and mark else []
        subitem = bool(_SUBITEM.match(name)) if name else False
        if pending is not None and (subitem or not _POS_NUM.match(name)):
            clean = f"{pending.name} {clean}".strip()
            marks = pending.marks + marks
        if not subitem:
            pending = None  # родитель «8. Воздуховод …» действует на все подпункты 8.1, 8.2, …
        if not clean:
            continue
        current = _Draft(system, clean, qty=qty, unit=unit, marks=marks)
    flush()

    if columns is None:
        raise DrawingSpecError(
            "Не нашёл шапку таблицы («Наименование … Кол-во») на первой вкладке: "
            "это не чертёжная спецификация. Для обычной таблицы выберите вид «Обычная таблица»."
        )
    if not drafts:
        raise DrawingSpecError("В файле нет ни одной позиции с количеством.")
    return [
        DrawingPosition(
            system=draft.system,
            name=" ".join(_with_mark(draft.name, draft.marks).split()),
            qty=_quantity(draft.qty),
            unit=_unit(draft.unit),
        )
        for draft in drafts
    ]


def flat_xlsx(positions: list[DrawingPosition]) -> bytes:
    """Плоский лист, который читает обычный конвертер: «Система …», шапка, «Наименование | Кол-во | Ед.»."""

    import openpyxl

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Спецификация"
    sheet.append([NOTE])
    last_system: str | None = None
    for position in positions:
        if position.system != last_system:
            last_system = position.system
            if position.system:
                sheet.append([])
                sheet.append([position.system])
            if position.system or sheet.max_row == 1:
                sheet.append(FLAT_HEADER)
        sheet.append([position.name, position.qty, position.unit])
    sheet.column_dimensions["A"].width = 90
    sheet.column_dimensions["B"].width = 12
    sheet.column_dimensions["C"].width = 10
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def flat_name(source_name: str) -> str:
    """Имя файла сборки не «расчетка_…», чтобы не спутать с КП."""

    return f"спецификация_{Path(source_name).stem}.xlsx"
