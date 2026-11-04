#!/usr/bin/env python3
"""The owner's door through the walls. Only the owner runs this, in a terminal or with the ! prefix in Claude Code.
The hook blocks Claude from running it, in any session or routine.

    python3 .claude/hooks/owner-apply.py <file holding the new text> <walled file to replace>

It shows what changes, keeps the old copy in .claude/guardrails/quarantine/, writes the new text and records it.
Typing the command is the yes. It refuses a target outside the walls, since those need no door.
"""
import difflib
import importlib.util
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("guardrails", HERE / "guardrails.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    if not source.is_file():
        sys.exit(f"No such file: {source}")
    cwd = os.getcwd()
    if not (guard.walls_of(target, cwd) or guard.existing_kill_note(target, cwd)):
        sys.exit(f"{target} is not behind a wall, so this door is not needed.")
    new = source.read_text(encoding="utf-8")
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    if new == old:
        sys.exit("No change.")
    sys.stdout.writelines(difflib.unified_diff(old.splitlines(True), new.splitlines(True), f"{target} (old)", f"{target} (new)"))
    print()
    if target.exists():
        rel = target.resolve().relative_to(guard.ROOT).as_posix()
        print(f"Old copy kept: {guard._quarantine(rel, target)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    guard.take_snapshot({"session_id": "owner"}, "owner-apply")  # the new text is the new baseline
    guard.record("owner", "owner-apply: changed by the owner", "owner-apply", target, {"session_id": "owner"})
    print(f"Done: {target}")


if __name__ == "__main__":
    main()
