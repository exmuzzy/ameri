"""Замеры «до/после обучения» Харнеса на рабочем сайте через HTTP API (prompts/industry-research.md).

Сценарии — demo/training/scenarios.yaml: пользователи, спецификации (каталог с spec.* и, если есть, expected.yaml),
справочные вопросы и витринные чаты. Пароли — из окружения: AMERI_TRAINING_MANAGER_PASSWORD,
AMERI_TRAINING_LEADER_PASSWORD; завести пользователей — `setup-users` (нужны AMERI_ADMIN_LOGIN, AMERI_ADMIN_PASSWORD).

    python tools/training_via_api.py setup-users              # завести пользователей замеров или сменить им пароли
    python tools/training_via_api.py run --phase before       # чаты «[До обучения] …»: расчётки и вопросы
    python tools/training_via_api.py run --phase after        # то же в чатах «[После обучения] …»
    python tools/training_via_api.py measure --phase before   # XLSX → красные строки → demo/training/results/
    python tools/training_via_api.py showcase                 # витринные чаты «[Витрина] …»
    python tools/training_via_api.py note --chat "<название>" --text "…" [--as leader]
    python tools/training_via_api.py like --chat "<название>" --comment "…"   # 👍 последнему ответу
    python tools/training_via_api.py report                   # таблица «до/после» в Markdown

Чат с таким названием уже есть — шаг пропускается (повторный запуск безопасен).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
from io import BytesIO
from pathlib import Path

import openpyxl
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demo_via_api import DEFAULT_URL, POST_TIMEOUT, Api, env, last_answer, log, short  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "demo" / "training"
RESULTS = TRAINING / "results"
PREFIX = {"before": "[До обучения]", "after": "[После обучения]", "showcase": "[Витрина]"}
ACTIONS = {"ask": "Вопрос ассистенту", "duct_calc": "Расчётка воздуховодов", "note": None}


def load_config() -> dict:
    return yaml.safe_load((TRAINING / "scenarios.yaml").read_text(encoding="utf-8"))


def spec_file(item: dict) -> Path:
    folder = ROOT / item["dir"]
    return next(p for p in sorted(folder.iterdir()) if p.stem == "spec")


def expected(item: dict) -> dict | None:
    path = ROOT / item["dir"] / "expected.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None


def setup_users(api: Api, config: dict) -> None:
    admin = env("AMERI_ADMIN_LOGIN")
    api.login(admin, env("AMERI_ADMIN_PASSWORD"))
    for user in config["users"].values():
        body = {"login": user["login"], "name": user["name"], "role": user["role"], "password": env(user["password_env"])}
        api.request(admin, "POST", "/users", json=body)
        log(f"{user['login']}: сохранён ({user['role']})")


def login_all(api: Api, config: dict) -> dict[str, str]:
    logins = {}
    for role, user in config["users"].items():
        api.login(user["login"], env(user["password_env"]))
        logins[role] = user["login"]
    return logins


def find_chat(api: Api, who: str, title: str) -> dict | None:
    return next((c for c in api.get(who, "/chats", params={"query": title}) if c["title"] == title), None)


def post(api: Api, who: str, chat_id: int, *, text: str, action: str, connection: str = "none", files: list[Path] = ()) -> dict:
    data = {"text": text, "action": action, "connection": connection}
    upload = [("files", (p.name, p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream")) for p in files]
    log(f"  {who} → {action}{' + ' + ', '.join(p.name for p in files) if files else ''}: {short(text, 80)}")
    body = api.request(who, "POST", f"/chats/{chat_id}/messages", data=data, files=upload or None, timeout=POST_TIMEOUT).json()
    if body["assistant_message"]:
        log(f"  ассистент: {short(body['assistant_message']['content'])}")
    return body


def new_chat(api: Api, who: str, title: str) -> dict | None:
    if find_chat(api, who, title):
        log(f"«{title}» уже есть — пропуск")
        return None
    chat = api.request(who, "POST", "/chats", json={"title": title}).json()
    log(f"«{title}» — чат {chat['id']}")
    return chat


def run_phase(api: Api, users: dict[str, str], config: dict, phase: str) -> None:
    manager = users["manager"]
    for item in config["specs"]:
        chat = new_chat(api, manager, f"{PREFIX[phase]} {item['title']}")
        if chat:
            post(api, manager, chat["id"], text=item["intro"], action="note")
            post(api, manager, chat["id"], text=item["request"], action="duct_calc", connection=item["connection"], files=[spec_file(item)])
    for item in config["questions"]:
        chat = new_chat(api, manager, f"{PREFIX[phase]} {item['title']}")
        if chat:
            post(api, manager, chat["id"], text=item["text"], action="ask")


def run_showcase(api: Api, users: dict[str, str], config: dict) -> None:
    for item in config.get("showcase", []):
        chat = new_chat(api, users["manager"], f"{PREFIX['showcase']} {item['title']}")
        if not chat:
            continue
        for step in item["steps"]:
            who = users[step["as"]]
            if "feedback" in step:
                answer = last_answer(api, who, chat["id"])
                if answer:
                    api.request(who, "POST", f"/messages/{answer['id']}/feedback", json=step["feedback"])
                    log(f"  {who} 👍 ответ #{answer['id']}")
                continue
            files = [ROOT / f for f in step.get("files", [])]
            post(api, who, chat["id"], text=step["text"], action=step["action"], connection=step.get("connection", "none"), files=files)


# --- замер ---


def _red(font) -> bool:
    color = font.color if font else None
    if color is None:
        return False
    if color.type == "rgb" and isinstance(color.rgb, str) and len(color.rgb) >= 6:
        red, green, blue = (int(color.rgb[-6:][i : i + 2], 16) for i in (0, 2, 4))
        return red >= 0xC0 and green <= 0x60 and blue <= 0x60
    return color.type == "indexed" and color.indexed in (2, 10)


def analyze_xlsx(data: bytes) -> dict:
    """Строки с данными и строки, где хоть одна непустая ячейка набрана красным шрифтом."""

    book = openpyxl.load_workbook(BytesIO(data))
    sheets = {}
    for sheet in book.worksheets:
        rows, red = [], []
        for row in sheet.iter_rows():
            cells = [c for c in row if c.value not in (None, "")]
            if not cells:
                continue
            text = " | ".join(str(c.value) for c in cells)
            rows.append(text)
            if any(_red(c.font) for c in cells):
                red.append(text)
        sheets[sheet.title] = {"rows": len(rows), "red": red, "text": rows}
    return sheets


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def compare(expected_data: dict | None, table: dict | None, answer: str) -> dict | None:
    """Совпадение с expected.yaml: найдена ли позиция и совпадает ли «красность»."""

    if not expected_data:
        return None
    rows = table["text"] if table else []
    red_rows = {_norm(r) for r in (table["red"] if table else [])}
    found = matched = 0
    misses = []
    for item in expected_data["positions"]:
        line = _norm(item["line"])
        hits = [r for r in rows if line in _norm(r)]
        in_answer = line in _norm(answer)
        if not hits and not in_answer:
            misses.append(f"«{item['line']}»: нет в расчётке")
            continue
        found += 1
        is_red = any(_norm(r) in red_rows for r in hits) or (not hits and in_answer)
        if "red" in item and is_red != item["red"]:
            misses.append(f"«{item['line']}»: {'красная' if is_red else 'не красная'}, ожидалась {'красная' if item['red'] else 'обычная'}")
        else:
            matched += 1
    return {"total": len(expected_data["positions"]), "found": found, "matched": matched, "misses": misses}


def main_table(sheets: dict) -> dict | None:
    return max(sheets.values(), key=lambda s: s["rows"]) if sheets else None


def measure(api: Api, users: dict[str, str], config: dict, phase: str) -> dict:
    leader = users["leader"]
    result = {"phase": phase, "specs": {}, "questions": {}}
    for item in config["specs"]:
        title = f"{PREFIX[phase]} {item['title']}"
        chat = find_chat(api, leader, title)
        if not chat:
            log(f"нет чата «{title}»")
            continue
        messages = api.get(leader, f"/chats/{chat['id']}/messages")["messages"]
        answers = [m for m in messages if m["author"] == "assistant" and m["action"] == ACTIONS["duct_calc"]]
        answer = answers[-1] if answers else None
        text = answer["content"] if answer else ""
        xlsx = next((a for a in (answer or {}).get("attachments", []) if a["name"].endswith(".xlsx")), None)
        sheets = analyze_xlsx(api.request(leader, "GET", f"/files/{xlsx['id']}").content) if xlsx else {}
        table = main_table(sheets)
        warnings = re.findall(r"Предупреждения: (.*)", text)
        result["specs"][item["key"]] = {
            "chat_id": chat["id"],
            "title": title,
            "answer": text,
            "xlsx": xlsx["name"] if xlsx else None,
            "sheets": {name: {"rows": s["rows"], "red": s["red"]} for name, s in sheets.items()},
            "table_rows": table["rows"] if table else 0,
            "red_rows": len(table["red"]) if table else 0,
            "needs_input": text.startswith("Нужно уточнение"),
            "warnings": warnings[0].split("; ") if warnings else [],
            "expected": compare(expected(item), table, text),
        }
        log(f"{item['key']}: строк {result['specs'][item['key']]['table_rows']}, красных {result['specs'][item['key']]['red_rows']}")
    for item in config["questions"]:
        title = f"{PREFIX[phase]} {item['title']}"
        chat = find_chat(api, leader, title)
        answer = last_answer(api, leader, chat["id"]) if chat else None
        result["questions"][item["key"]] = {"chat_id": chat["id"] if chat else None, "title": title, "answer": answer["content"] if answer else None}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{phase}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"→ {RESULTS / f'{phase}.json'}")
    return result


def report() -> str:
    phases = {p: json.loads((RESULTS / f"{p}.json").read_text(encoding="utf-8")) for p in ("before", "after") if (RESULTS / f"{p}.json").is_file()}
    lines = ["| Спецификация | Строк до → после | Красных до → после | Совпадение с expected.yaml до → после | Предупреждений до → после |", "|---|---|---|---|---|"]
    keys = list((phases.get("before") or phases.get("after") or {"specs": {}})["specs"])
    for key in keys:
        cells = {}
        for phase, data in phases.items():
            spec = data["specs"].get(key)
            if not spec:
                continue
            exp = spec["expected"]
            cells[phase] = (
                "уточнение" if spec["needs_input"] else str(spec["table_rows"]),
                str(spec["red_rows"]),
                f"{exp['matched']}/{exp['total']}" if exp else "—",
                str(len(spec["warnings"])),
            )
        before, after = cells.get("before", ("—",) * 4), cells.get("after", ("—",) * 4)
        lines.append(f"| {key} | " + " | ".join(f"{b} → {a}" for b, a in zip(before, after)) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["setup-users", "run", "measure", "showcase", "note", "like", "report"])
    parser.add_argument("--phase", choices=["before", "after"], default="before")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--chat")
    parser.add_argument("--text", default="")
    parser.add_argument("--comment", default="")
    parser.add_argument("--as", dest="who", choices=["manager", "leader"], default="leader")
    args = parser.parse_args()

    if args.command == "report":
        print(report())
        return
    api = Api(args.url)
    config = load_config()
    if args.command == "setup-users":
        setup_users(api, config)
        return
    users = login_all(api, config)
    if args.command == "run":
        run_phase(api, users, config, args.phase)
    elif args.command == "measure":
        measure(api, users, config, args.phase)
    elif args.command == "showcase":
        run_showcase(api, users, config)
    else:
        who = users[args.who]
        chat = find_chat(api, users["leader"], args.chat)
        if not chat:
            sys.exit(f"Нет чата «{args.chat}»")
        if args.command == "note":
            post(api, who, chat["id"], text=args.text, action="note")
        else:
            answer = last_answer(api, who, chat["id"])
            api.request(who, "POST", f"/messages/{answer['id']}/feedback", json={"rating": 1, "comment": args.comment})
            log(f"👍 ответ #{answer['id']} в «{args.chat}»")


if __name__ == "__main__":
    main()
