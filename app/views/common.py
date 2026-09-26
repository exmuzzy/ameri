"""Общие ресурсы страниц: настройки, хранилище, пользователи, Харнес."""

from __future__ import annotations

import streamlit as st

from ameri.auth import User, load_users
from ameri.harness import Access, load_access
from ameri.materials import Material, load_materials
from ameri.settings import Settings, load_settings
from ameri.store import Store


@st.cache_resource
def get_settings() -> Settings:
    return load_settings()


@st.cache_resource
def get_store() -> Store:
    settings = get_settings()
    return Store(settings.db_path, settings.files_dir)


@st.cache_data(ttl=60)
def get_users() -> dict[str, User]:
    return load_users(get_settings().users_file)


@st.cache_data(ttl=60)
def get_access() -> Access:
    return load_access(get_settings().harness_dir)


@st.cache_data(ttl=60)
def get_materials() -> list[Material]:
    return load_materials(get_settings().harness_dir)


def current_user() -> User:
    return st.session_state["user"]


def display_name(login: str) -> str:
    if login == "assistant":
        return "Ассистент"
    user = get_users().get(login)
    return user.name if user else login
