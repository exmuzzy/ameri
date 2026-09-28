"""Страницы сайта в Streamlit AppTest: ссылки на Материалы отрасли из чата и сама страница материалов."""

import shutil
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from ameri.auth import User
from ameri.store import Store

from test_materials import CHEMISTRY, NAMES

ROOT = Path(__file__).resolve().parents[1]
ANNA = User("anna", "Анна", "manager", "x")


@pytest.fixture
def site(tmp_path, monkeypatch):
    harness = tmp_path / "harness"
    shutil.copytree(ROOT / "harness", harness)
    shutil.rmtree(harness / "materials", ignore_errors=True)
    (harness / "materials").mkdir()
    (harness / "materials" / "20-chemical-resistance.md").write_text(CHEMISTRY, encoding="utf-8")
    (harness / "materials" / "10-nomenclature.md").write_text(NAMES, encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "users.toml").write_text('[users.anna]\nname = "Анна"\nrole = "manager"\npassword_hash = "x"\n', encoding="utf-8")
    monkeypatch.setenv("AMERI_DATA_DIR", str(data))
    monkeypatch.setenv("AMERI_HARNESS_DIR", str(harness))
    st.cache_resource.clear()
    st.cache_data.clear()
    yield Store(data / "ameri.sqlite3", data / "files")
    st.cache_resource.clear()
    st.cache_data.clear()


def open_app(page: str | None = None, **params: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=60)
    at.session_state["user"] = ANNA
    if page:
        at.run()
        at._page_hash = next(h for h, i in at._registered_pages.items() if i.get("url_pathname") == page)
    for key, value in params.items():
        at.query_params[key] = value
    return at.run()


def test_chat_answer_links_open_material_sections(site):
    chat_id = site.create_chat("Кислоты", "anna")
    site.add_message(chat_id, author="anna", role="user", content="Выдержит ли ПП серную кислоту?")
    site.add_message(
        chat_id,
        author="assistant",
        role="assistant",
        content="Стоек. Подробнее — [Кислоты](/materials?doc=chemical-resistance&section=acids).",
    )
    at = open_app(chat=str(chat_id))
    assert not at.exception
    assert any(m.value == "Стоек. Подробнее — «Кислоты»." for m in at.markdown)
    links = [(p.proto.label, p.proto.page, p.proto.query_string) for p in at.get("page_link")]
    assert ("Кислоты", "materials", "doc=chemical-resistance&section=acids") in links


def test_attachment_has_download_and_preview(site):
    chat_id = site.create_chat("Спецификация", "anna")
    site.add_message(
        chat_id,
        author="anna",
        role="user",
        content="вопрос",
        files=[("note.txt", "привет мир".encode("utf-8"))],
    )
    at = open_app(chat=str(chat_id))
    assert not at.exception
    assert [d.label for d in at.download_button] == ["note.txt (1 КБ)"]
    preview_bodies = [
        child.proto.body
        for block in at.get("popover")
        for child in block.children.values()
        if hasattr(child.proto, "body")
    ]
    assert "привет мир" in preview_bodies


def test_materials_page_shows_linked_section(site):
    at = open_app("materials", doc="chemical-resistance", section="acids")
    assert not at.exception
    assert [(h.value, h.proto.anchor) for h in at.header] == [("Кислоты", "acids"), ("Щёлочи и аммиак", "alkalis")]
    assert "РАЗДЕЛ ПО ССЫЛКЕ" in [c.value for c in at.caption]
    at.text_input[0].input("колено").run()
    assert any(b.label == "Отводы · Как называют изделия" for b in at.button)


def test_assistant_article_page(site):
    at = open_app("assistant")
    assert not at.exception
    text = "\n".join(m.value for m in at.markdown)
    assert "### Отраслевые источники" in text and "## Текущие правила" in text
    links = [(p.proto.label, p.proto.page) for p in at.get("page_link")]
    assert ("Открыть материалы отрасли", "materials") in links


def test_roadmap_article_page(site):
    at = open_app("roadmap")
    assert not at.exception
    text = "\n".join(m.value for m in at.markdown)
    assert "## Где хранятся файлы" in text and "## Теги и облако тегов" in text
    assert "## Ассистент пообещал файл, который не мог прислать" in text
    assert "10 · [Как проверяем изменения](#am-section-10)" in text


def test_calculation_questions_page_for_leader_only(site):
    at = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=60)
    at.session_state["user"] = User("boss", "Руководитель", "leader", "x")
    at.run()
    pages = {i.get("url_pathname"): h for h, i in at._registered_pages.items()}
    assert "questions" in pages
    at._page_hash = pages["questions"]
    at.run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Q37. Нарезка метража" in text and "Q51" in text

    manager = open_app()
    assert "questions" not in {i.get("url_pathname") for i in manager._registered_pages.values()}
