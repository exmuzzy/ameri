from ameri.store import Store, safe_file_name


def make_store(tmp_path):
    return Store(tmp_path / "db.sqlite3", tmp_path / "files")


def test_chat_messages_and_attachments(tmp_path):
    store = make_store(tmp_path)
    chat_id = store.create_chat("Объект Лесная", "anna")
    msg = store.add_message(
        chat_id, author="anna", role="user", content="спецификация", files=[("../spec.md", b"1. d=200")]
    )
    assert msg.attachments[0].name == "spec.md"
    assert msg.attachments[0].path.read_bytes() == b"1. d=200"
    assert msg.attachments[0].path.is_relative_to(tmp_path / "files")
    store.add_message(chat_id, author="assistant", role="assistant", content="готово", action="Вопрос")
    messages = store.messages(chat_id)
    assert [m.role for m in messages] == ["user", "assistant"]
    assert store.get_chat(chat_id).message_count == 2


def test_list_filters(tmp_path):
    store = make_store(tmp_path)
    a = store.create_chat("Первый", "anna")
    store.create_chat("Второй", "boris")
    store.add_message(a, author="anna", role="user", content="тройник 500")
    assert [c.owner for c in store.list_chats(owner="anna")] == ["anna"]
    assert [c.id for c in store.list_chats(query="тройник")] == [a]
    assert len(store.list_chats()) == 2


def test_safe_file_name():
    assert safe_file_name("../../etc/passwd") == "passwd"
    assert safe_file_name("расчётка.xlsx") == "расчётка.xlsx"
    assert safe_file_name("") == "file"


def test_feedback_and_stats(tmp_path):
    store = make_store(tmp_path)
    chat_id = store.create_chat("t", "anna")
    store.add_message(chat_id, author="anna", role="user", content="вопрос")
    answer = store.add_message(chat_id, author="assistant", role="assistant", content="ответ")
    store.add_feedback(answer.id, reviewer="boss", rating=-1, corrected_text="верно так", rule_text="правило")
    store.add_feedback(answer.id, reviewer="boss", rating=1)
    proposed = store.list_feedback("proposed")
    assert len(proposed) == 1 and proposed[0].question == "вопрос" and proposed[0].chat_owner == "anna"
    store.set_feedback_status(proposed[0].id, "applied", "abc123")
    assert store.list_feedback("applied")[0].commit_sha == "abc123"
    stats = store.stats_by_owner()[0]
    assert (stats["owner"], stats["answers"], stats["likes"], stats["dislikes"], stats["corrections"]) == ("anna", 1, 1, 1, 1)
    assert set(store.feedback_for_chat(chat_id)) == {answer.id}


def test_onboarding(tmp_path):
    store = make_store(tmp_path)
    store.set_onboarding("anna", "login", True)
    store.set_onboarding("anna", "login", True)
    assert store.onboarding_done("anna") == {"login"}
    store.set_onboarding("anna", "login", False)
    assert store.onboarding_done("anna") == set()
