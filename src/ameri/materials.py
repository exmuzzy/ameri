"""Материалы отрасли: справочник в harness/materials/*.md, его страница на сайте и ссылки из ответов.

Файл материала — Markdown: первая строка «# Название», затем вводный текст, затем разделы
«## Название раздела {#id}». Идентификатор раздела — часть ссылки
/materials?doc=<материал>&section=<раздел>, на которую ссылаются ответы ассистента, поэтому
его не меняют. Материал без номера-префикса в имени файла: «10-nomenclature.md» → «nomenclature».
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import snowballstemmer

from .harness import slugify

MATERIALS_DIR = "materials"
PAGE_PATH = "materials"
PROMPT_FILE = Path("prompts") / "materials.md"
# Сколько разделов и текста подкладывать к вопросу ассистенту.
MAX_SECTIONS = 3
MAX_SECTION_CHARS = 3_500
# Порог — доля от оценки раздела, где одно редкое слово вопроса встречается один раз.
MIN_SCORE = 0.6

_HEADING = re.compile(r"^## +(.+?)\s*(?:\{#([a-z0-9][a-z0-9-]*)\})?\s*$")
_LINK = re.compile(r"\[([^\]\n]+)\]\((/" + PAGE_PATH + r"\?[^)\s]+)\)")
_WORD = re.compile(r"[a-zа-я0-9]+")
_STOP = frozenset(
    "а без бы в во вам вас весь все всё вы где да для до его ее её если есть же за и из или им их к как "
    "ко когда кто ли либо мне мы на над не нет нужно о об однако он она они оно от по под при про с со "
    "так там то тоже только у уже чем что чтобы это этот эта эти я можно ну ещё еще какой какая какие "
    "каких".split()
)
# Основы слов, которые есть почти в любом вопросе к ассистенту и ничего не говорят о теме.
_STOP_STEMS = frozenset("расчетк посчита клиент менеджер ассистент подскаж скаж ответ вопрос пишет присла спрашива".split())


@dataclass(frozen=True)
class Section:
    doc_id: str
    doc_title: str
    id: str
    title: str
    text: str

    @property
    def link(self) -> str:
        return section_link(self.doc_id, self.id)


@dataclass(frozen=True)
class Material:
    id: str
    title: str
    intro: str
    sections: tuple[Section, ...]
    path: Path

    @property
    def link(self) -> str:
        return section_link(self.id)

    def section(self, section_id: str) -> Section | None:
        return next((s for s in self.sections if s.id == section_id), None)


def section_link(doc_id: str, section_id: str | None = None) -> str:
    query = {"doc": doc_id} | ({"section": section_id} if section_id else {})
    return f"/{PAGE_PATH}?{urlencode(query)}"


def material_id(path: Path) -> str:
    return re.sub(r"^\d+-", "", path.stem)


def parse_material(path: Path) -> Material:
    """Разобрать файл материала: заголовок, вводный текст и разделы «## …»."""

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    doc_id = material_id(path)
    title = lines[0].lstrip("# ").strip() if lines else doc_id
    intro: list[str] = []
    sections: list[tuple[str, str, list[str]]] = []
    for line in lines[1:]:
        match = _HEADING.match(line)
        if match:
            name = match.group(1).strip()
            sections.append((match.group(2) or slugify(name, "section"), name, []))
        elif sections:
            sections[-1][2].append(line)
        else:
            intro.append(line)
    return Material(
        id=doc_id,
        title=title,
        intro="\n".join(intro).strip(),
        sections=tuple(
            Section(doc_id, title, section_id, name, "\n".join(body).strip())
            for section_id, name, body in sections
        ),
        path=path,
    )


def load_materials(harness_dir: Path | None) -> list[Material]:
    """Все материалы Харнеса в порядке имён файлов (порядок стабилен — это часть промпта)."""

    folder = harness_dir / MATERIALS_DIR if harness_dir else None
    if folder is None or not folder.is_dir():
        return []
    return [parse_material(path) for path in sorted(folder.glob("*.md")) if path.name != "README.md"]


def find_material(materials: list[Material], doc_id: str | None) -> Material | None:
    return next((m for m in materials if m.id == doc_id), None)


# --- промпт ассистента ---


def materials_index(harness_dir: Path, materials: list[Material] | None = None) -> str:
    """Оглавление материалов со ссылками на разделы — неизменная часть системного промпта."""

    materials = load_materials(harness_dir) if materials is None else materials
    if not materials:
        return ""
    prompt = harness_dir / PROMPT_FILE
    lines = ["## Материалы отрасли"]
    if prompt.is_file():
        lines += ["", prompt.read_text(encoding="utf-8").strip()]
    lines.append("")
    for material in materials:
        lines.append(f"- {material.title}: " + "; ".join(f"[{s.title}]({s.link})" for s in material.sections))
    return "\n".join(lines)


def _stem_word(word: str) -> str:
    stem = _stemmer().stemWord(word)
    # Беглая гласная: «фланец» / «фланцы», «уголок» / «уголки».
    if len(stem) > 4 and stem.endswith(("ец", "ок")):
        stem = stem[:-2] + stem[-1]
    return stem


@lru_cache(maxsize=1)
def _stemmer():
    return snowballstemmer.stemmer("russian")


def tokens(text: str) -> list[str]:
    words = _WORD.findall(text.lower().replace("ё", "е"))
    stems = (_stem_word(word) for word in words if word not in _STOP and (len(word) > 1 or word.isdigit()))
    return [stem for stem in stems if stem not in _STOP_STEMS]


def find_sections(
    materials: list[Material], query: str, limit: int = MAX_SECTIONS, min_score: float = MIN_SCORE
) -> list[Section]:
    """Разделы, ближе всего подходящие к вопросу (BM25 по словам с учётом окончаний)."""

    sections = [s for m in materials for s in m.sections]
    query_terms = set(tokens(query))
    if not sections or not query_terms:
        return []
    docs = [Counter(tokens(f"{s.doc_title} {s.title} {s.title} {s.title} {s.text}")) for s in sections]
    average = sum(sum(d.values()) for d in docs) / len(docs)
    k1, b = 1.5, 0.75

    def idf(containing: int) -> float:
        return math.log(1 + (len(docs) - containing + 0.5) / (containing + 0.5))

    scored = []
    for section, counts in zip(sections, docs):
        length = sum(counts.values())
        score = 0.0
        for term in query_terms:
            frequency = counts.get(term, 0)
            if frequency:
                weight = idf(sum(1 for d in docs if term in d))
                score += weight * frequency * (k1 + 1) / (frequency + k1 * (1 - b + b * length / average))
        score /= idf(1)  # оценка не зависит от размера справочника
        if score >= min_score:
            scored.append((score, section))
    scored.sort(key=lambda pair: -pair[0])
    return [section for _, section in scored[:limit]]


def sections_context(sections: list[Section]) -> str:
    """Текст найденных разделов для последнего сообщения в запросе к модели."""

    parts = ["[Материалы отрасли к вопросу. Если опираешься на них — дай ссылку на раздел, как указано.]"]
    for section in sections:
        text = section.text
        if len(text) > MAX_SECTION_CHARS:
            text = text[:MAX_SECTION_CHARS].rsplit("\n", 1)[0] + "\n…"
        parts.append(f"### {section.doc_title} → {section.title}\nСсылка: [{section.title}]({section.link})\n\n{text}")
    return "\n\n".join(parts)


# --- ссылки в ответах ---


@dataclass(frozen=True)
class MaterialLink:
    label: str
    doc_id: str
    section_id: str | None


def split_links(text: str, materials: list[Material]) -> tuple[str, list[MaterialLink]]:
    """Ссылки на материалы в тексте ответа: текст без адресов и список ссылок для кнопок сайта.

    Ссылка на несуществующий материал или раздел остаётся обычным текстом без кнопки.
    """

    links: list[MaterialLink] = []

    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        query = parse_qs(urlsplit(match.group(2)).query)
        material = find_material(materials, (query.get("doc") or [None])[0])
        section_id = (query.get("section") or [None])[0]
        if material and (section_id is None or material.section(section_id)):
            link = MaterialLink(label, material.id, section_id)
            if link not in links:
                links.append(link)
            return f"«{label}»"
        return label

    return _LINK.sub(replace, text), links
