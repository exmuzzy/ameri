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
