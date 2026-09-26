"""Демо-чаты на рабочем сайте ameri через HTTP API (README → API).

Сценарии — demo/scenarios.yaml, файлы — demo/specs/. Учётные данные — только из окружения:
AMERI_ADMIN_LOGIN / AMERI_ADMIN_PASSWORD (для --setup-users и --update-site), AMERI_DEMO_MANAGER_PASSWORD,
AMERI_DEMO_LEADER_PASSWORD.

    python tools/demo_via_api.py --update-site   # «Обновить сайт из репозитория» и дождаться итога (admin)
    python tools/demo_via_api.py --setup-users   # завести демо-пользователей или сменить им пароли
    python tools/demo_via_api.py                 # все сценарии (чат с таким названием уже есть — пропуск)
    python tools/demo_via_api.py --only 4        # один сценарий
    python tools/demo_via_api.py --only 4 --recreate   # удалить демо-чат сценария и провести заново
    python tools/demo_via_api.py --followup      # ещё по сообщению в чаты, где задан followup
    python tools/demo_via_api.py --report        # что сейчас в демо-чатах (глазами руководителя)
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
import time
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
DEFAULT_URL = "https://159-194-254-146.sslip.io"
POST_TIMEOUT = 600  # расчётка идёт несколько минут
ERROR_PREFIXES = ("Действие завершилось ошибкой", "Не получилось обратиться", "Ключ DeepSeek не задан")


def log(text: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {text}", flush=True)


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        sys.exit(f"Задайте переменную окружения {name}")
    return value


class Api:
    def __init__(self, base_url: str) -> None:
        # httpx сам берёт HTTPS_PROXY и проверяет TLS (SSL_CERT_FILE, если задан).
        self.client = httpx.Client(base_url=base_url.rstrip("/") + "/api/v1", timeout=60, trust_env=True)
        self.tokens: dict[str, str] = {}

    def login(self, login: str, password: str) -> None:
        response = self.client.post("/login", json={"login": login, "password": password})
        if response.status_code != 200:
            sys.exit(f"Вход {login}: {response.status_code} {response.text}")
        self.tokens[login] = response.json()["token"]

    def request(self, who: str, method: str, url: str, **kwargs) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.tokens[who]}"}
        response = self.client.request(method, url, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {url} от {who}: {response.status_code} {response.text}")
        return response

    def get(self, who: str, url: str, **kwargs):
        return self.request(who, "GET", url, **kwargs).json()


def load_scenarios() -> dict:
    return yaml.safe_load((DEMO / "scenarios.yaml").read_text(encoding="utf-8"))


def setup_users(api: Api, config: dict) -> None:
    admin = env("AMERI_ADMIN_LOGIN")
    api.login(admin, env("AMERI_ADMIN_PASSWORD"))
    existing = {u["login"] for u in api.get(admin, "/users")}
    for user in config["users"].values():
        body = {"login": user["login"], "name": user["name"], "role": user["role"], "password": env(user["password_env"])}
        api.request(admin, "POST", "/users", json=body)
        log(f"{user['login']}: {'пароль и имя обновлены' if user['login'] in existing else 'создан'} ({user['role']})")


def update_site(api: Api) -> None:
    admin = env("AMERI_ADMIN_LOGIN")
    api.login(admin, env("AMERI_ADMIN_PASSWORD"))
    before = api.get(admin, "/update")["status"].get("finished_at")
    log("Харнес: " + api.request(admin, "POST", "/update").json()["harness"])
    deadline = time.time() + 20 * 60
    while time.time() < deadline:
        time.sleep(15)
        try:
            state = api.get(admin, "/update")
        except (httpx.HTTPError, RuntimeError) as error:  # сайт перезапускается
            log(f"  жду: {error.__class__.__name__}")
            continue
        status = state["status"]
        log(f"  {status.get('state')}: {status.get('message')} ({status.get('commit')})")
        if state["request_stale"]:
            sys.exit("Служба обновления на сервере не запущена (install-autoupdate.sh)")
        if status.get("finished_at") != before and status.get("state") in ("done", "error"):
            return
    sys.exit("Обновление не закончилось за 20 минут")


def last_answer(api: Api, who: str, chat_id: int) -> dict | None:
    messages = api.get(who, f"/chats/{chat_id}/messages")["messages"]
    answers = [m for m in messages if m["role"] == "assistant" and m["author"] == "assistant"]
    return answers[-1] if answers else None


def short(text: str, limit: int = 400) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def post(api: Api, who: str, chat_id: int, step: dict) -> None:
    data = {"text": step.get("text", ""), "action": step.get("action", "note"), "connection": step.get("connection", "none")}
    files = []
    for name in step.get("files", []):
        path = DEMO / "specs" / name
        files.append(("files", (name, path.read_bytes(), mimetypes.guess_type(name)[0] or "application/octet-stream")))
    log(f"  {who} → {data['action']}{' + ' + ', '.join(step.get('files', [])) if files else ''}: {short(data['text'], 80)}")
    started = time.time()
    body = api.request(who, "POST", f"/chats/{chat_id}/messages", data=data, files=files or None, timeout=POST_TIMEOUT).json()
    answer = body["assistant_message"]
    if answer:
        attached = ", ".join(a["name"] for a in answer["attachments"])
        log(f"  ассистент ({time.time() - started:.0f} с){' 📎 ' + attached if attached else ''}: {short(answer['content'])}")


def feedback(api: Api, who: str, chat_id: int, spec: dict) -> None:
    answer = last_answer(api, who, chat_id)
    if answer is None:
        log("  нет ответа ассистента для оценки — пропуск")
        return
    if answer["content"].startswith(ERROR_PREFIXES):
        log(f"  оценку не ставлю: ответ с ошибкой сайта — {short(answer['content'], 120)}")
        return
    body = api.request(who, "POST", f"/messages/{answer['id']}/feedback", json=spec).json()
    mark = "👍" if spec["rating"] > 0 else "👎"
    status = body["feedback"]["status"]
    log(f"  {who} {mark} ответ #{answer['id']}{' ✏️ исправление в чате' if body['correction'] else ''} (статус {status})")


def run_scenario(api: Api, users: dict, scenario: dict, recreate: bool = False) -> None:
    manager = users["manager"]["login"]
    title = scenario["title"]
    existing = [c for c in api.get(manager, "/chats") if c["title"] == title]
    if existing and recreate:
        for chat in existing:
            api.request(manager, "DELETE", f"/chats/{chat['id']}")
            log(f"#{scenario['id']} «{title}» — чат {chat['id']} удалён")
        existing = []
    if existing:
        log(f"#{scenario['id']} «{title}» уже есть — пропуск")
        return
    for step in scenario["steps"]:
        action = step.get("action")
        who = users[step["as"]]["login"]
        if action and action not in api.get(who, "/me")["actions"]:
            log(f"#{scenario['id']} «{title}»: у {who} нет действия {action} на сайте — сценарий не начат")
            return
    chat = api.request(manager, "POST", "/chats", json={"title": title}).json()
    log(f"#{scenario['id']} «{title}» — чат {chat['id']}")
    for step in scenario["steps"]:
        who = users[step["as"]]["login"]
        words = step.get("when_answer_contains")
        if words:
            answer = last_answer(api, who, chat["id"])
            content = (answer or {}).get("content", "").lower()
            if not any(word.lower() in content for word in words):
                log(f"  шаг пропущен: в ответе нет ни одного из {words}")
                continue
        if "feedback" in step:
            feedback(api, who, chat["id"], step["feedback"])
        else:
            post(api, who, chat["id"], step)


def followup(api: Api, users: dict, scenarios: list[dict]) -> None:
    manager = users["manager"]["login"]
    chats = {c["title"]: c for c in api.get(manager, "/chats")}
    for scenario in scenarios:
        step = scenario.get("followup")
        chat = chats.get(scenario["title"])
        if step and chat:
            log(f"#{scenario['id']} «{scenario['title']}» — продолжение")
            post(api, users[step["as"]]["login"], chat["id"], step)


def report(api: Api, users: dict) -> None:
    leader = users["leader"]["login"]
    for chat in reversed(api.get(leader, "/chats", params={"query": "[Демо]"})):
        print(f"\n=== {chat['title']} (чат {chat['id']}, автор {chat['owner']}, сообщений {chat['message_count']})")
        for message in api.get(leader, f"/chats/{chat['id']}/messages")["messages"]:
            files = ", ".join(f"{a['name']} #{a['id']}" for a in message["attachments"])
            marks = " ".join(("👍" if f["rating"] > 0 else "👎") + f"[{f['status']}]" for f in message["feedback"])
            print(f"--- #{message['id']} {message['author']} · {message['action'] or 'заметка'}{' 📎 ' + files if files else ''} {marks}")
            print(message["content"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=os.environ.get("AMERI_URL", DEFAULT_URL))
    parser.add_argument("--update-site", action="store_true")
    parser.add_argument("--setup-users", action="store_true")
    parser.add_argument("--only", type=int, help="номер сценария")
    parser.add_argument("--recreate", action="store_true", help="удалить существующий демо-чат и провести сценарий заново")
    parser.add_argument("--followup", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    config = load_scenarios()
    api = Api(args.url)
    if args.update_site:
        update_site(api)
        return
    if args.setup_users:
        setup_users(api, config)
        return
    users = config["users"]
    for user in users.values():
        api.login(user["login"], env(user["password_env"]))
    scenarios = config["scenarios"]
    if args.only is not None:
        scenarios = [s for s in scenarios if s["id"] == args.only]
        if not scenarios:
            sys.exit(f"Нет сценария {args.only}")
    if args.report:
        report(api, users)
    elif args.followup:
        followup(api, users, scenarios)
    else:
        for scenario in scenarios:
            run_scenario(api, users, scenario, args.recreate)


if __name__ == "__main__":
    main()
