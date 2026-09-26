"""Страница «Материалы отрасли»: справочник из harness/materials с поиском и ссылками на разделы."""

from __future__ import annotations

import streamlit as st

from ameri.materials import Material, find_material, find_sections

from views.common import get_materials


def _open(doc_id: str, section_id: str | None = None) -> None:
    st.query_params.clear()
    st.query_params["doc"] = doc_id
    if section_id:
        st.query_params["section"] = section_id


def _sidebar(materials: list[Material], current: Material) -> None:
    query = st.text_input("Поиск", placeholder="Например: серная кислота, колено, фланец 20")
    if query.strip():
        found = find_sections(materials, query, limit=8, min_score=0.3)
        st.caption(f"Найдено разделов: {len(found)}" if found else "Ничего не нашлось — попробуйте другое слово.")
        for section in found:
            if st.button(f"{section.title} · {section.doc_title}", key=f"found-{section.doc_id}-{section.id}", use_container_width=True):
                _open(section.doc_id, section.id)
                st.rerun()
        st.divider()
    st.caption("МАТЕРИАЛЫ")
    for material in materials:
        if st.button(
            material.title,
            key=f"doc-{material.id}",
            use_container_width=True,
            type="primary" if material.id == current.id else "secondary",
        ):
            _open(material.id)
            st.rerun()


def _document(material: Material, section_id: str | None) -> None:
    st.subheader(material.title)
    if material.intro:
        st.markdown(material.intro)
    linked = material.section(section_id) if section_id else None
    if linked:
        with st.container(border=True):
            st.caption("РАЗДЕЛ ПО ССЫЛКЕ")
            st.markdown(f"#### {linked.title}")
            st.markdown(linked.text)
    with st.expander("Содержание", expanded=linked is None, icon=":material/list:"):
        for index, section in enumerate(material.sections, 1):
            st.markdown(f"{index:02d} · [{section.title}](#{section.id})")
    for section in material.sections:
        st.header(section.title, anchor=section.id, divider="gray")
        st.markdown(section.text)
        st.caption(f"Ссылка на раздел: `{section.link}`")


def render() -> None:
    st.title("Материалы отрасли")
    st.caption(
        "Справочник для работы с клиентами: как называют изделия, нормативы, типовые размеры, химстойкость. "
        "Собран из открытых источников — у каждого раздела есть ссылки. Ассистент отвечает по нему и даёт ссылки на разделы."
    )
    materials = get_materials()
    if not materials:
        st.info("Материалов пока нет: они появятся после обновления харнеса.")
        return
    current = find_material(materials, st.query_params.get("doc")) or materials[0]
    left, right = st.columns([1, 2.6], gap="large")
    with left:
        _sidebar(materials, current)
    with right:
        _document(current, st.query_params.get("section"))
