"""Страница «Качество»: как работают Менеджеры и Ассистент."""

from __future__ import annotations

import streamlit as st

from views.common import display_name, get_store


def render() -> None:
    st.title("Качество")
    st.caption("Ответы ассистента, оценки и активность команды")
    store = get_store()
    rows = store.stats_by_owner()
    if not rows:
        st.info("Пока нет данных. После первых ответов ассистента здесь появятся оценки и статистика по менеджерам.")
        return

    total_answers = sum(r["answers"] or 0 for r in rows)
    total_likes = sum(r["likes"] for r in rows)
    total_dislikes = sum(r["dislikes"] for r in rows)
    prompt_tokens = sum(r["prompt_tokens"] for r in rows)
    cache_hit = sum(r["cache_hit_tokens"] for r in rows)
    a, b, c, d = st.columns(4, gap="small")
    a.metric("Ответов ассистента", total_answers)
    b.metric("Оценено", total_likes + total_dislikes)
    c.metric("Доля хороших", f"{total_likes / (total_likes + total_dislikes):.0%}" if total_likes + total_dislikes else "—")
    d.metric("Попадание в кэш DeepSeek", f"{cache_hit / prompt_tokens:.0%}" if prompt_tokens else "—")

    st.subheader("По менеджерам")
    st.dataframe(
        [
            {
                "Менеджер": display_name(r["owner"]),
                "Чатов": r["chats"],
                "Сообщений": r["user_messages"] or 0,
                "Ответов ассистента": r["answers"] or 0,
                "Верно": r["likes"],
                "Ошибки": r["dislikes"],
                "Исправлено": r["corrections"],
                "Вход, токены": r["prompt_tokens"],
                "Выход, токены": r["completion_tokens"],
                "Последняя активность": (r["last_activity"] or "")[:16].replace("T", " "),
            }
            for r in rows
        ],
        column_config={
            name: st.column_config.NumberColumn(name, format="%d", width="small")
            for name in ("Чатов", "Сообщений", "Ответов ассистента", "Верно", "Ошибки", "Исправлено", "Вход, токены", "Выход, токены")
        },
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Ответы, требующие внимания")
    bad = [f for f in store.list_feedback() if f.rating < 0][:20]
    if not bad:
        st.info("Ответов с ошибками пока нет. Отмечайте их в чате, чтобы улучшать работу ассистента.")
    for item in bad:
        with st.container(border=True):
            st.caption(
                f"{display_name(item.chat_owner)} · {item.created_at[:16].replace('T', ' ')} UTC · "
                f"статус: {({'reviewed': 'отмечено', 'proposed': 'правило на утверждении', 'applied': 'в харнесе', 'rejected': 'отклонено'})[item.status]}"
            )
            st.markdown(f"**Вопрос:** {item.question or '—'}")
            if item.comment:
                st.markdown(f"**Что не так:** {item.comment}")
            st.markdown(f"[Открыть чат](/chats?chat={item.chat_id})")
