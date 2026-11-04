"""Склейка чертёжной спецификации (ГОСТ 21.110) в плоскую таблицу — шаг 1 из двух, без модели."""

from __future__ import annotations

import io

import openpyxl
import pytest

from ameri import actions, drawing_spec

HEADER = [None, None, "Позиция", "Наименование и техническая характеристика", "Тип, марка, обозначение документа",
          "Единица измерения", "Коли- чество"]


def _drawing(tmp_path, rows, name="чертёж.xlsx"):
    """Короткая синтетическая копия чертёжного листа: колонки A, B — штамп, D — наименование, E — марка."""

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append(HEADER)
    for row in rows:
        sheet.append(row)
    path = tmp_path / name
    book.save(path)
    return path


def _row(name="", mark="", unit="", qty="", stamp=""):
    return [stamp or None, None, None, name or None, mark or None, unit or None, qty or None]


def _flat(positions):
    return [(p.system, p.name, p.qty, p.unit) for p in positions]


def test_wrapped_name_and_stamp_become_one_position(tmp_path):
    path = _drawing(tmp_path, [
        _row("Система В5"),
        _row("4. Переход пластиковый, тип центральный,", "ХИМВЕНТ-ПП-БС-125-110-", "шт.", "2"),
        _row(stamp="Взам. инв. N"),
        _row("∅125 / ∅110", "-100-3-ММ"),
        _row("5.  Отвод 90 град пластиковый ∅110", "ХИМВЕНТ-ПП-БС-110-3-ММ", "шт.", "4"),
    ])

    positions = drawing_spec.assemble_positions(path)

    assert _flat(positions) == [
        ("Система В5", "Переход пластиковый, тип центральный, ∅125 / ∅110 ХИМВЕНТ-ПП-БС-125-110-100-3-ММ", 2, "шт"),
        ("Система В5", "Отвод 90 град пластиковый ∅110 ХИМВЕНТ-ПП-БС-110-3-ММ", 4, "шт"),
    ]
    assert all("Взам" not in p.name and "инв" not in p.name for p in positions)


def test_stamp_in_mark_column_is_dropped_and_leading_number_removed(tmp_path):
    path = _drawing(tmp_path, [
        _row("6.  Отвод 90 град пластиковый ∅110", "Подпись и дата", "шт.", "4"),
    ])

    (position,) = drawing_spec.assemble_positions(path)

    assert position.name == "Отвод 90 град пластиковый ∅110"


def test_duct_subitems_get_parent_type_and_mark_with_length(tmp_path):
    path = _drawing(tmp_path, [
        _row("Система В5"),
        _row("8.  Воздуховод пластиковый"),
        _row("8.1                                          ∅110", "ХИМВЕНТ-ПП-БС-110*2,3", "шт.", "1"),
        _row(mark="-2000-ФМ"),
        _row("8.2                                          ∅110", "ХИМВЕНТ-ПП-БС-110*2,3", "шт.", "5"),
        _row(mark="-2000-ММ"),
        _row("9.  Заглушка пластиковая ∅315", "ХИМВЕНТ-ПП-БС-315-3-М", "шт.", "1"),
    ])

    positions = drawing_spec.assemble_positions(path)

    assert _flat(positions) == [
        ("Система В5", "Воздуховод пластиковый ∅110 ХИМВЕНТ-ПП-БС-110*2,3-2000-ФМ", 1, "шт"),
        ("Система В5", "Воздуховод пластиковый ∅110 ХИМВЕНТ-ПП-БС-110*2,3-2000-ММ", 5, "шт"),
        ("Система В5", "Заглушка пластиковая ∅315 ХИМВЕНТ-ПП-БС-315-3-М", 1, "шт"),
    ]


def test_parent_type_does_not_leak_into_next_item(tmp_path):
    path = _drawing(tmp_path, [
        _row("7.  Воздуховод пластиковый"),
        _row("7.1                                          ∅250", "", "шт.", "2"),
        _row("8.  Зонт вытяжной пластиковый", "ХИМВЕНТ-ПП-БС-", "шт.", "2"),
        _row(mark="600х600х500-∅250-М"),
    ])

    positions = drawing_spec.assemble_positions(path)

    assert [p.name for p in positions] == [
        "Воздуховод пластиковый ∅250",
        "Зонт вытяжной пластиковый ХИМВЕНТ-ПП-БС-600х600х500-∅250-М",
    ]


def test_bare_number_in_mark_is_diameter_not_quantity(tmp_path):
    """Шумоглушитель длиной 1000 мм: «315» в колонке марки — сечение, а не количество."""

    path = _drawing(tmp_path, [
        _row("4. Шумоглушитель длиной 1000мм", "315", "шт.", "1"),
        _row("5. Отвод ∅200", "200", "шт.", "3"),
    ])

    positions = drawing_spec.assemble_positions(path)

    assert [(p.name, p.qty) for p in positions] == [
        ("Шумоглушитель длиной 1000мм ⌀315", 1),
        ("Отвод ∅200", 3),
    ]


def test_systems_are_sections_and_do_not_stick_to_previous_position(tmp_path):
    path = _drawing(tmp_path, [
        _row("Система В5"),
        _row("1. Отвод 90 град пластиковый ∅110", "", "шт.", "4"),
        _row("Система В18 (В18’)"),
        _row("1. Отвод 90 град пластиковый ∅315", "", "шт.", "2"),
    ])

    positions = drawing_spec.assemble_positions(path)

    assert _flat(positions) == [
        ("Система В5", "Отвод 90 град пластиковый ∅110", 4, "шт"),
        ("Система В18 (В18’)", "Отвод 90 град пластиковый ∅315", 2, "шт"),
    ]


def test_clean_file_without_mark_column_still_assembles(tmp_path):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append(["Позиция", "Наименование", "Единица измерения", "Количество"])
    sheet.append([None, "Система В9", None, None])
    sheet.append([None, "1. Заглушка пластиковая ∅315", "шт.", 1])
    sheet.append([None, "2. Переход пластиковый,", "шт.", 2])
    sheet.append([None, "∅315 / ∅200", None, None])
    path = tmp_path / "чистая.xlsx"
    book.save(path)

    positions = drawing_spec.assemble_positions(path)

    assert _flat(positions) == [
        ("Система В9", "Заглушка пластиковая ∅315", 1, "шт"),
        ("Система В9", "Переход пластиковый, ∅315 / ∅200", 2, "шт"),
    ]


def test_repeated_header_on_next_sheet_page_is_not_a_continuation(tmp_path):
    path = _drawing(tmp_path, [
        _row("1. Отвод 90 град пластиковый ∅110", "", "шт.", "4"),
        HEADER,
        _row("2. Заглушка пластиковая ∅315", "", "шт.", "1"),
    ])

    positions = drawing_spec.assemble_positions(path)

    assert [p.name for p in positions] == ["Отвод 90 град пластиковый ∅110", "Заглушка пластиковая ∅315"]


def test_duct_length_is_not_invented(tmp_path):
    """Q48: воздуховод в штуках без длины остаётся «1 шт» — метры ставит менеджер."""

    path = _drawing(tmp_path, [
        _row("8.  Воздуховод пластиковый"),
        _row("8.1                                          ∅110", "", "шт.", "1"),
    ])

    (position,) = drawing_spec.assemble_positions(path)

    assert position.qty == 1 and position.unit == "шт"
    assert "L" not in position.name and "мм" not in position.name


def test_file_without_header_is_not_a_drawing(tmp_path):
    book = openpyxl.Workbook()
    book.active.append(["Просто текст"])
    path = tmp_path / "x.xlsx"
    book.save(path)

    with pytest.raises(drawing_spec.DrawingSpecError, match="шапк"):
        drawing_spec.assemble_positions(path)


def test_header_without_positions_is_an_error(tmp_path):
    path = _drawing(tmp_path, [_row("Система В5")])

    with pytest.raises(drawing_spec.DrawingSpecError, match="позиц"):
        drawing_spec.assemble_positions(path)


def test_flat_xlsx_is_read_by_the_ordinary_converter(tmp_path):
    """Шаг 2: собранный файл — обычная плоская таблица для того же spec_lines_text."""

    path = _drawing(tmp_path, [
        _row("Система В5"),
        _row("4. Переход пластиковый, тип центральный,", "ХИМВЕНТ-ПП-БС-125-110-", "шт.", "2"),
        _row("∅125 / ∅110", "-100-3-ММ"),
        _row("5.  Отвод 90 град пластиковый ∅110", "", "шт.", "4"),
        _row("Система В9"),
        _row("1. Заглушка пластиковая ∅315", "", "шт.", "1"),
    ])
    flat = tmp_path / "спецификация.xlsx"
    flat.write_bytes(drawing_spec.flat_xlsx(drawing_spec.assemble_positions(path)))

    text = actions.spec_lines_text(flat)

    lines = text.splitlines()
    assert lines[0] == drawing_spec.NOTE
    assert lines[1:] == [
        "1. Переход пластиковый, тип центральный, ∅125 / ∅110 ХИМВЕНТ-ПП-БС-125-110-100-3-ММ"
        " — 2 шт; система В5; кол-во: 2",
        "2. Отвод 90 град пластиковый ∅110 — 4 шт; система В5; кол-во: 4",
        "3. Заглушка пластиковая ∅315 — 1 шт; система В9; кол-во: 1",
    ]


def test_flat_xlsx_has_one_sheet_with_note_system_and_header(tmp_path):
    positions = [drawing_spec.DrawingPosition("Система В5", "Отвод ∅110", 4, "шт")]

    book = openpyxl.load_workbook(io.BytesIO(drawing_spec.flat_xlsx(positions)))

    assert len(book.worksheets) == 1
    cells = [[c for c in row if c is not None] for row in book.active.iter_rows(values_only=True)]
    cells = [row for row in cells if row]
    assert cells == [
        [drawing_spec.NOTE],
        ["Система В5"],
        ["Наименование", "Кол-во", "Ед."],
        ["Отвод ∅110", 4, "шт"],
    ]


def test_positions_count_is_declined_in_the_chat_answer():
    words = {n: actions._positions_word(n) for n in (1, 2, 4, 5, 11, 12, 14, 21, 22, 25, 111, 231)}

    assert words == {
        1: "позиция", 2: "позиции", 4: "позиции", 5: "позиций", 11: "позиций", 12: "позиций", 14: "позиций",
        21: "позиция", 22: "позиции", 25: "позиций", 111: "позиций", 231: "позиция",
    }


def test_assembled_name_for_download_is_not_a_calculation_name():
    assert drawing_spec.flat_name("Заявка на химстойкую вентиляцию.xlsx") == "спецификация_Заявка на химстойкую вентиляцию.xlsx"
