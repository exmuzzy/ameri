"""Страница «Харнес»: предложения из Исправлений, Правила, Примеры, промпт, история в git."""

from __future__ import annotations

import streamlit as st

from ameri.harness import HarnessRepo, PROMPT_FILE, list_examples, list_rules

from views.common import current_user, display_name, get_settings, get_store
from views.updates import render_update_panel


def _repo() -> HarnessRepo:
    return HarnessRepo(get_settings().harness_dir)


def _proposals() -> None:
    store = get_store()
    proposals = store.list_feedback("proposed")
    st.subheader(f"Ждут утверждения: {len(proposals)}")
    if not proposals:
        st.info("Новых предложений нет. Исправьте ответ в чате и предложите правило или пример — они появятся здесь.")
    for item in proposals:
        with st.container(border=True):
            st.caption(
                f"Исправление #{item.id} · {display_name(item.reviewer)} · чат «{item.chat_id}» "
                f"менеджера {display_name(item.chat_owner)} · {item.created_at[:16].replace('T', ' ')} UTC"
            )
            st.markdown(f"**Вопрос:** {item.question or '—'}")
            with st.expander("Ответ ассистента и исправление"):
                st.markdown("**Было:**\n\n" + item.answer)
                st.markdown("**Стало:**\n\n" + (item.corrected_text or "—"))
                if item.comment:
                    st.markdown(f"**Комментарий:** {item.comment}")
            with st.form(f"proposal-{item.id}"):
                title = st.text_input("Название правила", value=(item.rule_text.splitlines() or ["Правило"])[0][:80])
                rule = st.text_area("Текст правила", value=item.rule_text, height=100)
                as_example = st.checkbox("Добавить пример «вопрос — правильный ответ»", value=item.as_example)
                apply_col, reject_col = st.columns(2)
                apply = apply_col.form_submit_button("Утвердить и сохранить", type="primary", icon=":material/check:")
                reject = reject_col.form_submit_button("Отклонить", icon=":material/close:")
            if apply:
                repo = _repo()
                user = current_user()
                if rule.strip():
                    repo.add_rule(title or "Правило", rule, author=user.name, source=f"исправление #{item.id}")
                if as_example and item.corrected_text:
                    repo.add_example(item.question, item.corrected_text, author=user.name)
                sha, message = repo.commit(f"Харнес: {title or 'пример'} (исправление #{item.id})", author=user)
                store.set_feedback_status(item.id, "applied", sha)
                st.success(message)
                st.rerun()
            if reject:
                store.set_feedback_status(item.id, "rejected")
                st.rerun()


def _files(kind: str, items) -> None:
    st.subheader(f"{kind}: {len(items)}")
    repo = _repo()
    for item in items:
        with st.expander(item.title):
            st.markdown(item.text)
            # Правило и Пример могут называться одинаково, а вкладки рисуются все сразу — ключ с именем папки.
            if st.button("Удалить", key=f"del-{item.path.parent.name}-{item.path.name}"):
                repo.remove(item.path)
                sha, message = repo.commit(f"Харнес: удалено «{item.title}»", author=current_user())
                st.success(message)
                st.rerun()


def _prompt() -> None:
    settings = get_settings()
    st.subheader("Основной промпт ассистента")
    st.caption(f"Файл `harness/{PROMPT_FILE}`. Правила и примеры добавляются к нему автоматически.")
    with st.form("prompt"):
        text = st.text_area(
            "Промпт", value=(settings.harness_dir / PROMPT_FILE).read_text(encoding="utf-8"), height=320,
            label_visibility="collapsed",
        )
        why = st.text_input("Что меняете и зачем")
        if st.form_submit_button("Сохранить в харнес", type="primary"):
            repo = _repo()
            repo.save_prompt(text)
            sha, message = repo.commit(f"Харнес: промпт — {why or 'правка'}", author=current_user())
            st.success(message)


def render() -> None:
    st.title("Харнес")
    repo = _repo()
    version = repo.version()
    st.caption(
        "Харнес — промпт, правила и примеры, по которым работает ассистент. Всё хранится в git-репозитории: "
        f"каждое изменение — коммит с вашим именем, его видно и можно откатить. Текущая версия: `{version or 'не в git'}`."
    )
    tabs = st.tabs(["На утверждении", "Правила", "Примеры", "Промпт", "История изменений", "Обновление"])
    with tabs[0]:
        _proposals()
    with tabs[1]:
        _files("Правила", list_rules(get_settings().harness_dir))
    with tabs[2]:
        _files("Примеры", list_examples(get_settings().harness_dir))
    with tabs[3]:
        _prompt()
    with tabs[4]:
        history = repo.history()
        st.subheader("История изменений")
        if history:
            for entry in history:
                with st.container(border=True):
                    st.text(entry)
        else:
            st.info("История пока пуста: каталог Харнеса не в git.")
    with tabs[5]:
        render_update_panel()
