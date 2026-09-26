import shutil
import subprocess
from pathlib import Path

from ameri.auth import User
from ameri.harness import HarnessRepo, list_rules, slugify

HARNESS = Path(__file__).resolve().parents[1] / "harness"
BOSS = User("boss", "Руководитель", "leader", "")


def test_commit_rule_to_git(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    harness = tmp_path / "harness"
    shutil.copytree(HARNESS, harness)
    repo = HarnessRepo(harness)
    sha, _ = repo.commit("Начальный Харнес", author=BOSS)
    assert sha
    path = repo.add_rule("Отвод", "Отвод без градусов — 90°.", author="boss", source="опрос")
    sha2, message = repo.commit("Правило: отвод", author=BOSS)
    assert sha2 and sha2 != sha and "создан" in message
    assert [r.path for r in list_rules(harness)] == [path]
    assert repo.history()[0].endswith("Правило: отвод")
    log = subprocess.run(["git", "-C", str(tmp_path), "log", "-1", "--format=%an"], capture_output=True, text=True)
    assert log.stdout.strip() == "Руководитель"
    assert repo.commit("пусто", author=BOSS)[0] is None


def test_no_git(tmp_path):
    harness = tmp_path / "harness"
    shutil.copytree(HARNESS, harness)
    sha, message = HarnessRepo(harness).commit("x", author=BOSS)
    assert sha is None and "не в git" in message


def test_slugify():
    assert slugify("Клапан = 2 метра!") == "klapan-2-metra"
    assert slugify("!!!") == "rule"
