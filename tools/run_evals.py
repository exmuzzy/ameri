"""Прогон Эталонов из harness/evals через прототип duct-calc с текущим Харнесом.

Переменные: DEEPSEEK_API_KEY (или DEEPSEEK_API_KEY_FILE), AMERI_DUCT_CALC_DIR.
  python tools/run_evals.py [--no-harness] [имя_эталона ...]
Код выхода 1, если хоть одна проверка не прошла.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ameri import actions  # noqa: E402
from ameri.settings import load_settings  # noqa: E402

RED = {"needs_input", "problem"}


def run_case(case_dir: Path, settings, use_harness: bool) -> tuple[int, int, list[str]]:
    from duct_calc.model_client import DeepSeekClient, ModelClientConfig
    from duct_calc.pipeline import preview_specification

    expected = yaml.safe_load((case_dir / "expected.yaml").read_text(encoding="utf-8"))
    spec = next(p for p in case_dir.iterdir() if p.stem == "spec")
    actions._install_harness(settings.harness_dir if use_harness else None)
    client = DeepSeekClient(
        ModelClientConfig(
            base_url=settings.deepseek_base_url, api_key=settings.api_key(), model=settings.deepseek_model
        )
    )
    # Как на сайте (actions.duct_calc): таблицы прототип получает пронумерованными строками.
    lines_text = actions.spec_lines_text(spec)
    with tempfile.TemporaryDirectory() as tmp:
        source = spec
        if lines_text is not None:
            source = Path(tmp) / "spec.md"
            source.write_text(lines_text, encoding="utf-8")
        preview = preview_specification(
            source_path=source, connection_type=expected.get("connection", "none"), model_client=client
        )
    lines, passed, total = [], 0, 0
    for item in expected["positions"]:
        found = [p for p in preview.positions if item["line"] in p.source_text]
        total += 1
        if not found:
            if item.get("heading"):
                passed += 1  # заголовок раздела в расчётку не попадает (Q39)
            else:
                lines.append(f"  ✗ «{item['line']}»: позиция не найдена")
            continue
        position = found[0]
        problems = []
        if "red" in item and (position.status in RED) != item["red"]:
            problems.append(f"статус {position.status}" + (f" ({position.issue})" if position.issue else ""))
        if "type" in item and position.element_type != item["type"]:
            problems.append(f"тип {position.element_type}, ожидался {item['type']}")
        if problems:
            lines.append(f"  ✗ «{item['line']}»: " + "; ".join(problems))
        else:
            passed += 1
    red_total = sum(1 for p in preview.positions if p.status in RED)
    lines.insert(0, f"  позиций: {len(preview.positions)}, красных: {red_total}")
    return passed, total, lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-harness", action="store_true", help="без правил Харнеса — для сравнения")
    parser.add_argument("cases", nargs="*")
    args = parser.parse_args()

    settings = load_settings()
    if not actions.duct_calc_available(settings.duct_calc_dir):
        print("Нужен прототип duct-calc: задайте AMERI_DUCT_CALC_DIR")
        return 2
    sys.path.insert(0, str(settings.duct_calc_dir / "src"))
    cases = sorted(d for d in (settings.harness_dir / "evals").iterdir() if (d / "expected.yaml").is_file())
    if args.cases:
        cases = [d for d in cases if d.name in args.cases]

    all_passed = all_total = 0
    for case in cases:
        passed, total, lines = run_case(case, settings, not args.no_harness)
        all_passed += passed
        all_total += total
        print(f"{'✓' if passed == total else '✗'} {case.name}: {passed}/{total}")
        print("\n".join(lines))
    mode = "без Харнеса" if args.no_harness else "с Харнесом"
    print(f"\nИтого {mode}: {all_passed}/{all_total}")
    return 0 if all_passed == all_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
