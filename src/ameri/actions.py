"""Типовые действия, которые Менеджер вызывает в Чате."""

from __future__ import annotations

import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

import yaml
from dataclasses import dataclass, field
from pathlib import Path

from .llm import DeepSeekChat, key_problem
from .materials import MAX_SECTIONS, Material, find_sections, sections_context
from .store import Attachment, Message, Usage

TEXT_SUFFIXES = {".md", ".txt", ".csv"}
PARSED_SUFFIXES = {".xlsx", ".docx", ".doc"}
DUCT_SUFFIXES = {".md", ".xlsx", ".docx", ".doc", ".csv", ".odt"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
CONNECTION_TYPES = {"Фланец": "flange", "Раструб": "socket", "Без соединения": "none"}
DUCT_TEMPLATE_NAME = "шаблон расчетки стоимости воздуховодов.xlsx"
MAX_FILE_CHARS = 60_000
# Бюджет истории Чата в символах (~40–50 тыс. токенов): старые сообщения отбрасываются первыми.
MAX_HISTORY_CHARS = 150_000
PREVIEW_MAX_CHARS = 20_000
PREVIEW_MAX_ROWS = 200


@dataclass(frozen=True)
class ActionResult:
    text: str
    files: list[tuple[str, bytes]] = field(default_factory=list)
    usage: Usage | None = None


@dataclass(frozen=True)
class AttachmentPreview:
    """Предпросмотр вложения в Чате: без обращения к DeepSeek или прототипу duct-calc."""

    kind: str  # "image" | "pdf" | "text" | "table" | "unsupported"
    text: str = ""
    rows: list[list[str]] = field(default_factory=list)
    truncated: bool = False


def _odt_node_text(node: ET.Element) -> str:
    parts = [node.text or ""]
    for child in node:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "s":
            parts.append(" " * int(next((v for k, v in child.attrib.items() if k.endswith("}c")), "1")))
        elif tag in ("tab", "line-break"):
            parts.append(" ")
        else:
            parts.append(_odt_node_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def odt_text(path: Path) -> str:
    """Текст OpenDocument (.odt): абзац — строка, строка таблицы — ячейки через « | »."""

    root = ET.fromstring(zipfile.ZipFile(path).read("content.xml"))
    lines: list[str] = []

    def walk(node: ET.Element) -> None:
        for child in node:
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "table-row":
                cells = [
                    " ".join(_odt_node_text(cell).split())
                    for cell in child
                    if cell.tag.rsplit("}", 1)[-1] == "table-cell"
                ]
                row = " | ".join(cell for cell in cells if cell)
                if row:
                    lines.append(row)
            elif tag in ("p", "h"):
                text = " ".join(_odt_node_text(child).split())
                if text:
                    lines.append(text)
            else:
                walk(child)

    walk(root)
    return "\n".join(lines)


def duct_calc_available(duct_calc_dir: Path | None) -> bool:
    return bool(
        duct_calc_dir
        and (duct_calc_dir / "src" / "duct_calc").is_dir()
        and (duct_calc_dir / "data" / DUCT_TEMPLATE_NAME).is_file()
    )


def _import_duct_calc(duct_calc_dir: Path) -> None:
    src = str(duct_calc_dir / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def attachment_text(attachment: Attachment, duct_calc_dir: Path | None) -> str:
    """Текст вложения для контекста модели; для неизвестных форматов — только имя."""

    suffix = attachment.path.suffix.lower()
    text = ""
    if suffix in TEXT_SUFFIXES:
        text = attachment.path.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".odt":
        try:
            text = odt_text(attachment.path)
        except (zipfile.BadZipFile, KeyError, ET.ParseError):
            text = ""
    elif suffix in PARSED_SUFFIXES and duct_calc_available(duct_calc_dir):
        _import_duct_calc(duct_calc_dir)
        from duct_calc.document_parser import parse_document

        try:
            text = parse_document(attachment.path).text
        except Exception:  # noqa: BLE001 - файл просто не попадёт в контекст
            text = ""
    if not text:
        return f"[Файл {attachment.name}: содержимое недоступно ассистенту]"
    return f"[Файл {attachment.name}]\n{text[:MAX_FILE_CHARS]}"


def _docx_text(path: Path) -> str:
    from docx import Document

    return "\n".join(p.text for p in Document(path).paragraphs)


def _xlsx_rows(path: Path) -> list[list[str]]:
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        return [
            ["" if cell is None else str(cell) for cell in row]
            for row in sheet.iter_rows(max_row=PREVIEW_MAX_ROWS + 1, values_only=True)
        ]
    finally:
        workbook.close()


def attachment_preview(attachment: Attachment) -> AttachmentPreview:
    """Предпросмотр вложения в Чате, независимо от прототипа duct-calc.

    Картинки и PDF показываются как есть, текстовые форматы и .odt — текстом,
    .xlsx — таблицей; для .doc (старый бинарный формат) и прочего показывается
    только сообщение о недоступности предпросмотра.
    """

    suffix = attachment.path.suffix.lower()
    try:
        if suffix in IMAGE_SUFFIXES:
            return AttachmentPreview(kind="image")
        if suffix == ".pdf":
            return AttachmentPreview(kind="pdf")
        if suffix in TEXT_SUFFIXES:
            text = attachment.path.read_text(encoding="utf-8", errors="replace")
            return AttachmentPreview(kind="text", text=text[:PREVIEW_MAX_CHARS], truncated=len(text) > PREVIEW_MAX_CHARS)
        if suffix == ".odt":
            text = odt_text(attachment.path)
            return AttachmentPreview(kind="text", text=text[:PREVIEW_MAX_CHARS], truncated=len(text) > PREVIEW_MAX_CHARS)
        if suffix == ".docx":
            text = _docx_text(attachment.path)
            return AttachmentPreview(kind="text", text=text[:PREVIEW_MAX_CHARS], truncated=len(text) > PREVIEW_MAX_CHARS)
        if suffix == ".xlsx":
            rows = _xlsx_rows(attachment.path)
            return AttachmentPreview(kind="table", rows=rows[:PREVIEW_MAX_ROWS], truncated=len(rows) > PREVIEW_MAX_ROWS)
    except Exception:  # noqa: BLE001 - предпросмотр не должен ронять страницу
        return AttachmentPreview(kind="unsupported")
    return AttachmentPreview(kind="unsupported")


def ask_assistant(
    llm: DeepSeekChat,
    system_prompt: str,
    history: list[Message],
    duct_calc_dir: Path | None,
    names: dict[str, str],
    materials: list[Material] | None = None,
) -> ActionResult:
    """Свободный вопрос: переписка Чата с текстом вложений в пределах бюджета.

    Системный промпт (Харнес) идёт первым и одинаков для всех Чатов — это
    кэшируемый префикс DeepSeek; переписка добавляется после него. Разделы Материалов
    отрасли, подходящие к двум последним вопросам (и к файлам последнего сообщения),
    дописываются в конец последнего сообщения пользователя: так они не сдвигают
    кэшируемое начало запроса.
    """

    turns: list[dict[str, str]] = []
    files_text = ""  # вложения последнего сообщения пользователя — для подбора Материалов
    for message in history:
        content = message.content
        if message.role == "user":
            content = f"{names.get(message.author, message.author)}: {content}"
        elif message.author != "assistant":
            content = f"[Ответ исправлен руководителем {names.get(message.author, message.author)}]\n{content}"
        attached = [attachment_text(attachment, duct_calc_dir) for attachment in message.attachments]
        for text in attached:
            content += "\n\n" + text
        if message.role == "user":
            files_text = "\n".join(attached)
        turns.append({"role": message.role, "content": content})

    kept: list[dict[str, str]] = []
    budget = MAX_HISTORY_CHARS
    for turn in reversed(turns):
        budget -= len(turn["content"])
        if budget < 0 and kept:
            break
        kept.append(turn)
    kept.reverse()
    if len(kept) < len(turns):
        kept.insert(0, {"role": "user", "content": f"[Ранние сообщения чата ({len(turns) - len(kept)}) опущены из-за длины.]"})

    questions = [m.content for m in history if m.role == "user"][-2:]
    sections = find_sections(materials or [], "\n".join(questions))
    if files_text and len(sections) < MAX_SECTIONS:
        # Сначала — разделы по самому вопросу, остальные места — по тексту приложенного файла.
        extra = [s for s in find_sections(materials or [], files_text) if s not in sections]
        sections += extra[: MAX_SECTIONS - len(sections)]
    if sections:
        reference = sections_context(sections)
        if kept and kept[-1]["role"] == "user":
            kept[-1] = {"role": "user", "content": kept[-1]["content"] + "\n\n" + reference}
        else:
            kept.append({"role": "user", "content": reference})

    text, usage = llm.complete([{"role": "system", "content": system_prompt}, *kept])
    return ActionResult(text=text, usage=usage)


def duct_parse_rules(harness_dir: Path | None) -> str:
    """Правила разбора из Харнеса, которые дописываются к промпту прототипа."""

    if harness_dir is None:
        return ""
    path = harness_dir / "duct_calc" / "parse_rules.md"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def duct_params(harness_dir: Path | None) -> dict:
    if harness_dir is None:
        return {}
    path = harness_dir / "duct_calc" / "params.yaml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.is_file() else {}


_KEYWORD_LISTS = {
    "passthrough_keywords": "PASSTHROUGH_ITEM_KEYWORDS",
    "grid_keywords": "GRID_KEYWORDS",
    "valve_keywords": "VALVE_KEYWORDS",
}


def _install_harness(harness_dir: Path | None) -> None:
    """Подключить Харнес к прототипу duct-calc: правила разбора и ключевые слова расчёта."""

    from duct_calc import pipeline

    original = getattr(pipeline, "_ameri_original_prompt", None) or pipeline.build_system_prompt
    pipeline._ameri_original_prompt = original
    rules = duct_parse_rules(harness_dir)
    pipeline.build_system_prompt = (lambda: original() + "\n\n" + rules) if rules else original

    params = duct_params(harness_dir)
    for key, attr in _KEYWORD_LISTS.items():
        base = getattr(pipeline, f"_ameri_original_{attr}", None) or getattr(pipeline, attr)
        setattr(pipeline, f"_ameri_original_{attr}", base)
        extra = tuple(str(word).lower() for word in params.get(key) or ())
        setattr(pipeline, attr, tuple(base) + extra)


def duct_calc(
    *,
    spec: Attachment,
    connection_label: str,
    duct_calc_dir: Path,
    base_url: str,
    api_key: str,
    model: str,
    harness_dir: Path | None = None,
) -> ActionResult:
    """Расчётка воздуховодов по вложенной Спецификации (прототип duct-calc)."""

    problem = key_problem(api_key)
    if problem:
        return ActionResult(text=problem)
    _import_duct_calc(duct_calc_dir)
    _install_harness(harness_dir)
    from duct_calc.model_client import DeepSeekClient, ModelClientConfig
    from duct_calc.pipeline import PipelineNeedsInput, run_specification_pipeline

    client = DeepSeekClient(ModelClientConfig(base_url=base_url, api_key=api_key, model=model))
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / f"расчетка_{spec.path.stem}.xlsx"
        source = spec.path
        if source.suffix.lower() == ".odt":
            # Прототип не читает OpenDocument: передаём ему текст документа как Markdown.
            source = Path(tmp) / f"{spec.path.stem}.md"
            source.write_text(odt_text(spec.path), encoding="utf-8")
        try:
            if source.suffix.lower() == ".csv":
                from duct_calc.csv_pipeline import run_csv_pipeline

                result = run_csv_pipeline(
                    source_path=source,
                    output_path=output,
                    connection_type=CONNECTION_TYPES[connection_label],
                    template_path=duct_calc_dir / "data" / DUCT_TEMPLATE_NAME,
                    model_client=client,
                )
                summary = f"Позиций: {result.source_item_count}, строк в расчётке: {result.output_row_count}."
            else:
                result = run_specification_pipeline(
                    source_path=source,
                    output_path=output,
                    connection_type=CONNECTION_TYPES[connection_label],
                    template_path=duct_calc_dir / "data" / DUCT_TEMPLATE_NAME,
                    model_client=client,
                )
                summary = f"Позиций: {result.completeness.model_position_count}."
        except PipelineNeedsInput as error:
            return ActionResult(text=f"Нужно уточнение, расчётка не построена: {error}")
        lines = [f"Расчётка по файлу «{spec.name}» готова ({connection_label.lower()}). {summary}"]
        if result.warnings:
            lines.append("Предупреждения: " + "; ".join(result.warnings))
        return ActionResult(text="\n\n".join(lines), files=[(output.name, output.read_bytes())])
