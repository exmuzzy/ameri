"""Страница «Качество»: как работают Менеджеры и Ассистент."""

from __future__ import annotations

import streamlit as st

from views.common import display_name, get_store


def render() -> None:
    st.title("Качество")
    store = get_store()
    rows = store.stats_by_owner()
    if not rows:
        st.info("Данных пока нет: в чатах ещё никто не работал.")
        return

    total_answers = sum(r["answers"] or 0 for r in rows)
    total_likes = sum(r["likes"] for r in rows)
    total_dislikes = sum(r["dislikes"] for r in rows)
    prompt_tokens = sum(r["prompt_tokens"] for r in rows)
    cache_hit = sum(r["cache_hit_tokens"] for r in rows)
    a, b, c, d = st.columns(4)
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
                "👍": r["likes"],
                "👎": r["dislikes"],
                "Исправлено": r["corrections"],
                "Токены (вход/выход)": f"{r['prompt_tokens']:,} / {r['completion_tokens']:,}".replace(",", " "),
                "Последняя активность": (r["last_activity"] or "")[:16].replace("T", " "),
            }
            for r in rows
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Последние плохие ответы")
    bad = [f for f in store.list_feedback() if f.rating < 0][:20]
    if not bad:
        st.caption("Плохих ответов не отмечено.")
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
