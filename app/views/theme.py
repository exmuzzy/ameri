"""Общая тема интерфейса Streamlit и оформленные статьи."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

STATIC = Path(__file__).resolve().parents[1] / "static"


def apply_theme() -> None:
    """Подключить локальные стили один раз на каждом проходе Streamlit."""
    st.markdown(f"<style>{(STATIC / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def article(text: str, *, toc: bool = False) -> None:
    """Статья с необязательным оглавлением на основе Markdown-заголовков."""
    if toc:
        headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
        if headings:
            with st.expander("Содержание", expanded=True, icon=":material/list:"):
                for index, heading in enumerate(headings, 1):
                    st.markdown(f"{index:02d} · [{heading}](#am-section-{index})")
            for index, heading in enumerate(headings, 1):
                text = text.replace(f"## {heading}", f'<span id="am-section-{index}"></span>\n\n## {heading}', 1)
    # Markdown из собственного каталога docs/site, а не пользовательский ввод.
    st.markdown(text, unsafe_allow_html=toc)