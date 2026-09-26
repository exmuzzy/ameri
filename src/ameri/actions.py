"""Типовые действия, которые Менеджер вызывает в Чате."""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .llm import DeepSeekChat
from .store import Attachment, Message

TEXT_SUFFIXES = {".md", ".txt", ".csv"}
PARSED_SUFFIXES = {".xlsx", ".docx", ".doc"}
DUCT_SUFFIXES = {".md", ".xlsx", ".docx", ".doc", ".csv"}
CONNECTION_TYPES = {"Фланец": "flange", "Раструб": "socket", "Без соединения": "none"}
DUCT_TEMPLATE_NAME = "шаблон расчетки стоимости воздуховодов.xlsx"
MAX_FILE_CHARS = 60_000


@dataclass(frozen=True)
class ActionResult:
    text: str
    files: list[tuple[str, bytes]] = field(default_factory=list)


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


def ask_assistant(
    llm: DeepSeekChat,
    system_prompt: str,
    history: list[Message],
    duct_calc_dir: Path | None,
    names: dict[str, str],
) -> ActionResult:
    """Свободный вопрос: вся переписка Чата с текстом вложений."""

    messages = [{"role": "system", "content": system_prompt}]
    for message in history:
        content = message.content
        if message.role == "user":
            content = f"{names.get(message.author, message.author)}: {content}"
        for attachment in message.attachments:
            content += "\n\n" + attachment_text(attachment, duct_calc_dir)
        messages.append({"role": message.role, "content": content})
    return ActionResult(text=llm.complete(messages))


def duct_calc(
    *,
    spec: Attachment,
    connection_label: str,
    duct_calc_dir: Path,
    base_url: str,
    api_key: str,
    model: str,
) -> ActionResult:
    """Расчётка воздуховодов по вложенной Спецификации (прототип duct-calc)."""

    if not api_key:
        return ActionResult(text="Ключ DeepSeek не задан: Администратору нужно добавить его на сервер.")
    _import_duct_calc(duct_calc_dir)
    from duct_calc.model_client import DeepSeekClient, ModelClientConfig
    from duct_calc.pipeline import PipelineNeedsInput, run_specification_pipeline

    client = DeepSeekClient(ModelClientConfig(base_url=base_url, api_key=api_key, model=model))
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / f"расчетка_{spec.path.stem}.xlsx"
        try:
            if spec.path.suffix.lower() == ".csv":
                from duct_calc.csv_pipeline import run_csv_pipeline

                result = run_csv_pipeline(
                    source_path=spec.path,
                    output_path=output,
                    connection_type=CONNECTION_TYPES[connection_label],
                    template_path=duct_calc_dir / "data" / DUCT_TEMPLATE_NAME,
                    model_client=client,
                )
                summary = f"Позиций: {result.source_item_count}, строк в расчётке: {result.output_row_count}."
            else:
                result = run_specification_pipeline(
                    source_path=spec.path,
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
