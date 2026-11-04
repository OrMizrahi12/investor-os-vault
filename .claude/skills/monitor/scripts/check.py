#!/usr/bin/env python3
"""Do the routines still match? Compares each playbook's prompt with its Desktop task, and the map's IDs across its two files. Writes nothing.
Run from the project root: python3 .claude/skills/monitor/scripts/check.py
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASKS = Path.home() / ".claude" / "scheduled-tasks"
ROUTINES = {"Daily run": "daily-test", "Event run": "event-run", "Monthly hunt": "monthly-hunt", "Weekly thesis check": "weekly-thesis-check", "Quarterly refresh": "quarterly-refresh"}


def prompt_of(playbook):
    found = re.search(r"## The prompt\s+```text\n(.*?)\n```", playbook.read_text(encoding="utf-8"), re.S)
    return found.group(1).strip() if found else None


def task_body(path):
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S).strip()


def map_ids(root=ROOT):
    rule = (root / "Rules/alerts.md").read_text(encoding="utf-8")
    in_rule = set(re.findall(r"^\| ([ROI]\d{1,2}) \|", rule, re.M))
    spec = importlib.util.spec_from_file_location("alertmap", root / "sensors/alerts/alertmap.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return in_rule, {row[0] for row in module.MAP}


def main():
    trouble = 0
    for name, task in ROUTINES.items():
        playbook = ROOT / "Playbooks" / f"{name}.md"
        file = TASKS / task / "SKILL.md"
        prompt = prompt_of(playbook) if playbook.exists() else None
        if prompt is None:
            print(f"{name}: NO PROMPT in the playbook")
            trouble += 1
        elif not file.exists():
            print(f"{name}: no Desktop task named {task}")
            trouble += 1
        elif task_body(file) == prompt:
            print(f"{name}: matches {task}")
        else:
            print(f"{name}: DIFFERS from {task}. The owner pastes the playbook's prompt into Desktop.")
            trouble += 1
    in_rule, in_code = map_ids()
    if in_rule == in_code:
        print(f"The map: the same {len(in_rule)} IDs in Rules/alerts.md and sensors/alerts/alertmap.py")
    else:
        print(f"The map: DIFFERS. Only in the rule: {sorted(in_rule - in_code)}. Only in the code: {sorted(in_code - in_rule)}.")
        trouble += 1
    return 1 if trouble else 0


if __name__ == "__main__":
    sys.exit(main())
