from __future__ import annotations

import streamlit as st

from views.common import get_settings
from views.theme import article


SAMPLE_CALC_INPUT = "sample_calc_input.xlsx"
SAMPLE_CALC_INPUT_NAME = "Образец правильного файла для расчета.xlsx"


def render() -> None:
    site_dir = get_settings().site_dir
    article((site_dir / "howto.md").read_text(encoding="utf-8"), toc=True)
    sample = site_dir / SAMPLE_CALC_INPUT
    if sample.is_file():
        st.download_button(
            "Скачать образец входного файла для расчётки",
            data=sample.read_bytes(),
            file_name=SAMPLE_CALC_INPUT_NAME,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            icon=":material/download:",
            key="sample-calc-input",
        )


def render_examples() -> None:
    article((get_settings().site_dir / "examples.md").read_text(encoding="utf-8"), toc=True)


def render_questions() -> None:
    article((get_settings().site_dir / "questions.md").read_text(encoding="utf-8"), toc=True)


def render_roadmap() -> None:
    article((get_settings().site_dir / "roadmap.md").read_text(encoding="utf-8"), toc=True)


def render_assistant() -> None:
    article((get_settings().site_dir / "assistant.md").read_text(encoding="utf-8"), toc=True)
    st.page_link(
        st.session_state["pages"]["materials"],
        label="Открыть материалы отрасли",
        icon=":material/library_books:",
    )
