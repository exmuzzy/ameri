"""Сценарии замеров и примеров переписок (demo/training, demo/examples): файлы на месте, шаги корректны."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = {"ask", "duct_calc", "note"}
CONNECTIONS = {"flange", "socket", "none"}


def chats() -> list[tuple[str, dict]]:
    training = yaml.safe_load((ROOT / "demo" / "training" / "scenarios.yaml").read_text(encoding="utf-8"))
    examples = yaml.safe_load((ROOT / "demo" / "examples" / "scenarios.yaml").read_text(encoding="utf-8"))
    return [(f"showcase: {c['title']}", c) for c in training["showcase"]] + [
        (f"example: {c['title']}", c) for c in examples["examples"]
    ]


def test_twenty_examples_with_unique_titles():
    examples = yaml.safe_load((ROOT / "demo" / "examples" / "scenarios.yaml").read_text(encoding="utf-8"))["examples"]
    titles = [c["title"] for c in examples]
    assert len(titles) == 20 and len(set(titles)) == 20


@pytest.mark.parametrize(("name", "chat"), chats(), ids=[n for n, _ in chats()])
def test_steps_are_valid(name, chat):
    assert chat["steps"], name
    for step in chat["steps"]:
        assert step["as"] in {"manager", "leader"}, name
        if "feedback" in step:
            assert step["feedback"]["rating"] in (1, -1), name
            continue
        assert step["action"] in ACTIONS and step["text"].strip(), name
        if step["action"] == "duct_calc":
            assert step["connection"] in CONNECTIONS and step.get("files"), name
        for path in step.get("files", []):
            assert (ROOT / path).is_file(), f"{name}: нет файла {path}"
