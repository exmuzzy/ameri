import inspect
import io
import json
import shutil
import time
from dataclasses import replace
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

from ameri import api, chat_service
from ameri.auth import User, hash_password, load_users, save_users
from ameri.settings import load_settings
from ameri.store import Store, Usage

HARNESS = Path(__file__).resolve().parents[1] / "harness"
PASSWORD = "секретный-пароль"


class FakeLlm:
    calls: list = []

    def __init__(self, **_):
        pass

    def complete(self, messages, **_):
        FakeLlm.calls.append(messages)
        return "ответ ассистента", Usage(prompt_tokens=10, completion_tokens=2, cache_hit_tokens=8)


@pytest.fixture
def env(tmp_path, monkeypatch):
    harness = tmp_path / "harness"
    shutil.copytree(HARNESS, harness)
    settings = replace(
        load_settings(),
        data_dir=tmp_path / "data",
        users_file=tmp_path / "data" / "users.toml",
        harness_dir=harness,
        duct_calc_dir=None,
        deepseek_api_key="test",
    )
    save_users(
        settings.users_file,
        {
            login: User(login, name, role, hash_password(PASSWORD))
            for login, name, role in [
                ("anna", "Анна", "manager"),
                ("boris", "Борис", "manager"),
                ("boss", "Руководитель", "leader"),
                ("root", "Админ", "admin"),
            ]
        },
    )
    FakeLlm.calls = []
    monkeypatch.setattr(chat_service, "DeepSeekChat", FakeLlm)
    client = TestClient(api.create_app(lambda: settings))
    return client, settings


def login(client, name):
    response = client.post("/api/v1/login", json={"login": name, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_login_and_me(env):
    client, _ = env
    assert client.get("/api/v1/me").status_code == 401
    headers = login(client, "anna")
    me = client.get("/api/v1/me", headers=headers).json()
    assert me["login"] == "anna" and me["role"] == "manager"
    assert "chat.create" in me["grants"]
    assert me["actions"] == ["ask", "note"]  # без прототипа расчётки нет


def test_wrong_password_and_rate_limit(env):
    client, _ = env
    for _ in range(api.LOGIN_MAX_FAILURES):
        assert client.post("/api/v1/login", json={"login": "anna", "password": "нет"}).status_code == 401
    blocked = client.post("/api/v1/login", json={"login": "anna", "password": PASSWORD})
    assert blocked.status_code == 429


def test_expired_and_forged_tokens(env):
    client, settings = env
    secret = api.api_secret(settings)
    assert (settings.data_dir / "secrets" / "api_secret").stat().st_mode & 0o777 == 0o600
    anna = load_users(settings.users_file)["anna"]
    expired, _ = api.issue_token(secret, anna, now=time.time() - api.TOKEN_TTL - 10)
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401

    forged, _ = api.issue_token(b"other-secret", anna)
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401

    # Подмена логина в полезной нагрузке ломает подпись.
    good, _ = api.issue_token(secret, anna)
    payload, signature = good.split(".")
    data = json.loads(api._unb64(payload))
    data["sub"] = "boss"
    tampered = api._b64(json.dumps(data).encode()) + "." + signature
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {good}"}).status_code == 200


def test_manager_cannot_see_foreign_chat(env):
    client, _ = env
    anna, boris, boss = login(client, "anna"), login(client, "boris"), login(client, "boss")
    chat = client.post("/api/v1/chats", json={"title": "Заказ Анны"}, headers=anna).json()
    assert client.get(f"/api/v1/chats/{chat['id']}/messages", headers=boris).status_code == 403
    assert client.post(f"/api/v1/chats/{chat['id']}/messages", data={"text": "x"}, headers=boris).status_code == 403
    assert [c["title"] for c in client.get("/api/v1/chats", headers=boris).json()] == []
    assert [c["title"] for c in client.get("/api/v1/chats", headers=boss).json()] == ["Заказ Анны"]
    assert client.get("/api/v1/chats?author=boris", headers=boss).json() == []


def test_note_does_not_call_assistant(env):
    client, _ = env
    anna = login(client, "anna")
    chat = client.post("/api/v1/chats", json={"title": "t"}, headers=anna).json()
    response = client.post(f"/api/v1/chats/{chat['id']}/messages", data={"text": "заметка", "action": "note"}, headers=anna)
    assert response.status_code == 201
    assert response.json()["assistant_message"] is None
    assert response.json()["user_message"]["action"] is None
    assert FakeLlm.calls == []
    assert client.post(f"/api/v1/chats/{chat['id']}/messages", data={"action": "note"}, headers=anna).status_code == 422
    assert client.post(f"/api/v1/chats/{chat['id']}/messages", data={"text": "x", "action": "duct_calc"}, headers=anna).status_code == 403


def test_ask_with_file_and_download(env):
    client, _ = env
    anna = login(client, "anna")
    chat = client.post("/api/v1/chats", json={"title": "t"}, headers=anna).json()
    response = client.post(
        f"/api/v1/chats/{chat['id']}/messages",
        data={"text": "что тут?", "action": "ask"},
        files=[("files", ("spec.md", "Воздуховод ф200 — 5 мп".encode(), "text/markdown"))],
        headers=anna,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["assistant_message"]["content"] == "ответ ассистента"
    assert body["user_message"]["action"] == chat_service.ACTION_ASK
    assert "Анна: что тут?" in FakeLlm.calls[0][1]["content"]
    assert "ф200" in FakeLlm.calls[0][1]["content"]

    attachment = body["user_message"]["attachments"][0]
    assert attachment["name"] == "spec.md"
    downloaded = client.get(f"/api/v1/files/{attachment['id']}", headers=anna)
    assert downloaded.status_code == 200 and "ф200" in downloaded.content.decode()
    assert client.get(f"/api/v1/files/{attachment['id']}", headers=login(client, "boris")).status_code == 403
    assert client.get("/api/v1/files/999", headers=anna).status_code == 404


def test_download_xlsx_answer(env):
    client, settings = env
    anna = login(client, "anna")
    chat = client.post("/api/v1/chats", json={"title": "t"}, headers=anna).json()
    book = openpyxl.Workbook()
    book.active["A1"] = "расчётка"
    data = io.BytesIO()
    book.save(data)
    store = Store(settings.db_path, settings.files_dir)
    store.add_message(chat["id"], author="assistant", role="assistant", content="готово", files=[("r.xlsx", data.getvalue())])
    messages = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=anna).json()["messages"]
    file_id = messages[0]["attachments"][0]["id"]
    content = client.get(f"/api/v1/files/{file_id}", headers=anna).content
    assert openpyxl.load_workbook(io.BytesIO(content)).active["A1"].value == "расчётка"


def test_feedback_only_for_leader(env):
    client, _ = env
    anna, boss = login(client, "anna"), login(client, "boss")
    chat = client.post("/api/v1/chats", json={"title": "t"}, headers=anna).json()
    answer = client.post(
        f"/api/v1/chats/{chat['id']}/messages", data={"text": "вопрос", "action": "ask"}, headers=anna
    ).json()["assistant_message"]
    url = f"/api/v1/messages/{answer['id']}/feedback"
    assert client.post(url, json={"rating": 1}, headers=anna).status_code == 403
    assert client.post(url, json={"rating": 1}, headers=boss).json()["correction"] is None

    fixed = client.post(
        url,
        json={"rating": -1, "comment": "не так", "corrected_text": "правильно", "rule_text": "Новое правило"},
        headers=boss,
    ).json()
    assert fixed["feedback"]["status"] == "proposed"
    assert fixed["correction"]["action"] == "Исправление руководителя"
    assert fixed["correction"]["author"] == "boss"
    messages = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=anna).json()["messages"]
    assert [m["content"] for m in messages] == ["вопрос", "ответ ассистента", "правильно"]
    assert len(messages[1]["feedback"]) == 2
    # Исправление руководителя само не оценивается.
    assert client.post(f"/api/v1/messages/{fixed['correction']['id']}/feedback", json={"rating": 1}, headers=boss).status_code == 422


def test_users_admin_only(env):
    client, _ = env
    root = login(client, "root")
    for name in ("anna", "boss"):
        headers = login(client, name)
        assert client.get("/api/v1/users", headers=headers).status_code == 403
        assert client.post("/api/v1/users", json={"login": "x1", "role": "manager", "password": "12345678"}, headers=headers).status_code == 403
        assert client.delete("/api/v1/users/boris", headers=headers).status_code == 403

    users = client.get("/api/v1/users", headers=root).json()
    assert {"login": "anna", "name": "Анна", "role": "manager"} in users
    assert all("password_hash" not in u for u in users)

    bad = [
        {"login": "Я", "role": "manager", "password": "12345678"},
        {"login": "ok.user", "role": "manager", "password": "short"},
        {"login": "ok.user", "role": "boss", "password": "12345678"},
    ]
    for body in bad:
        assert client.post("/api/v1/users", json=body, headers=root).status_code == 422

    created = client.post(
        "/api/v1/users", json={"login": "New.User", "name": "Новый", "role": "leader", "password": "длинный-пароль"}, headers=root
    )
    assert created.json() == {"login": "new.user", "name": "Новый", "role": "leader"}
    token = client.post("/api/v1/login", json={"login": "new.user", "password": "длинный-пароль"}).json()["token"]
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).json()["role"] == "leader"

    # Смена пароля отзывает старый токен.
    client.post("/api/v1/users", json={"login": "new.user", "name": "Новый", "role": "leader", "password": "другой-пароль"}, headers=root)
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    assert client.delete("/api/v1/users/root", headers=root).status_code == 422
    assert client.delete("/api/v1/users/nobody", headers=root).status_code == 404
    assert client.delete("/api/v1/users/new.user", headers=root).status_code == 204
    assert client.post("/api/v1/login", json={"login": "new.user", "password": "другой-пароль"}).status_code == 401


def test_site_and_api_share_send_function():
    from views import admin, chats

    assert "chat_service.post_message(" in inspect.getsource(chats._chat_column)
    assert "chat_service.review_message(" in inspect.getsource(chats._review_controls)
    assert "chat_service.post_message(" in inspect.getsource(api.create_app)
    assert "chat_service.review_message(" in inspect.getsource(api.create_app)
    assert chats.chat_service is api.chat_service
    assert "save_user(" in inspect.getsource(admin._users_section)
    assert "delete_user(" in inspect.getsource(admin._users_section)
