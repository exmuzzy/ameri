from __future__ import annotations

import streamlit as st

from views.common import get_settings
from views.theme import article


def render(compact: bool = False) -> None:
    text = (get_settings().site_dir / "about.md").read_text(encoding="utf-8")
    if compact:
        st.divider()
        # На странице входа заголовок уже есть.
        text = text.split("\n", 1)[1]
    article(text)
