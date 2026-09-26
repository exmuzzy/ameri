from __future__ import annotations

import streamlit as st

from views.common import get_settings


def render() -> None:
    st.markdown((get_settings().site_dir / "howto.md").read_text(encoding="utf-8"))


def render_examples() -> None:
    st.markdown((get_settings().site_dir / "examples.md").read_text(encoding="utf-8"))
