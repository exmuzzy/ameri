from __future__ import annotations

import streamlit as st

from views.common import get_settings
from views.theme import article


def render() -> None:
    article((get_settings().site_dir / "howto.md").read_text(encoding="utf-8"), toc=True)


def render_examples() -> None:
    article((get_settings().site_dir / "examples.md").read_text(encoding="utf-8"), toc=True)
