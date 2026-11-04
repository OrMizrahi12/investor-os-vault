#!/usr/bin/env python3
"""Guard for the coach subagent. Runs before each Read, Write, Edit, Bash or Skill call.

The order is the point. Until a decision file with "stage: view written" exists, the
only call allowed is the Write that creates one, holding the owner's view and nothing
else. After that:

Write: a new file in Journal/decisions/, or JSON in the session scratchpad. No overwrite.
Edit: only a file in Journal/decisions/, and never its "## My view" section.
Bash: grep, ls and jq inside this vault, pm.py and date, with no shell operators.
Skill: only portfolio-manager.

Read stays open once the gate is, since the skill must read the vault.
Exit 2 blocks the call. Any error also blocks, because other exit codes let it through.
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "Journal" / "decisions"
FILE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2} [^/\\]+\.md$")
OPEN_STAGE = re.compile(r"^stage: view written$", re.M)
SCRATCH_JSON = re.compile(r"^/tmp/claude-[^/]+/.+/scratchpad/[^/]+\.json$")
PM = ".claude/skills/portfolio-manager/scripts/pm.py"
UNSAFE_OUTSIDE_QUOTES = set(";&|<>()`$\\\n\r{}[]*?~!#")
UNSAFE_IN_DOUBLE_QUOTES = set("`$\\")
GREP_FLAG = re.compile(r"^(-[rilLnHhcEFwvs]+|-[ABC]\d{1,3}|--(include|exclude|exclude-dir)=[^/]+)$")
LS_FLAG = re.compile(r"^-[1aAlhRtrS]+$")
VIEW_SECTION = re.compile(r"^## My view\n.*?(?=^## |\Z)", re.M | re.S)
ONLY_THE_VIEW = re.compile(r"^## ", re.M)


def block(reason):
    print(f"coach guard: {reason}", file=sys.stderr)
    sys.exit(2)


def has_shell_syntax(command):
    """True if the shell would do more than run one plain command."""
    quote = None
    for char in command:
        if quote == "'":
            quote = None if char == "'" else quote
        elif quote == '"':
            if char == '"':
                quote = None
            elif char in UNSAFE_IN_DOUBLE_QUOTES:
                return True
        elif char in "'\"":
            quote = char
        elif char in UNSAFE_OUTSIDE_QUOTES:
            return True
    return quote is not None


def inside_vault(path, cwd):
    """True if the path, with links followed, is this vault or lies inside it."""
    root = os.path.realpath(ROOT)
    real = os.path.realpath(Path(cwd) / path)
    return real == root or real.startswith(root + os.sep)


def view_is_on_file():
    """True if some decision file holds a written view not yet compared."""
    if not DECISIONS.is_dir():
        return False
    return any(OPEN_STAGE.search(p.read_text()) for p in DECISIONS.glob("*.md"))


def decision_path(tool_input, cwd):
    """The real path if it is a decision file's name directly in the folder, else None."""
    path = Path(os.path.realpath(Path(cwd) / tool_input["file_path"]))
    return path if path.parent == Path(os.path.realpath(DECISIONS)) and FILE_NAME.match(path.name) else None


def check_first_write(path, content):
    """The first write holds the owner's view and nothing else."""
    if not OPEN_STAGE.search(content):
        block('a new decision file starts with "stage: view written"')
    if ONLY_THE_VIEW.findall(content) != ["## "] or "## My view" not in content:
        block('a new decision file holds only the "## My view" section')


def check_write(tool_input, cwd):
    raw = str(tool_input["file_path"])
    if SCRATCH_JSON.match(os.path.realpath(raw)):
        if not view_is_on_file():
            block("write the owner's view first")
        return
    path = decision_path(tool_input, cwd)
    if path is None:
        block("write only Journal/decisions/YYYY-MM-DD <Company>.md, or JSON in the scratchpad")
    if path.exists():
        block("a decision file is written once: add a new name, or use Edit below the owner's view")
    check_first_write(path, tool_input["content"])


def check_edit(tool_input, cwd):
    path = decision_path(tool_input, cwd)
    if path is None or not path.exists():
        block("edit only an existing file in Journal/decisions/")
    text = path.read_text()
    old, new = tool_input["old_string"], tool_input["new_string"]
    section = VIEW_SECTION.search(text)
    if section is None:
        block('this file has no "## My view" section to protect')
    if tool_input.get("replace_all"):
        block("no replace_all in a decision file")
    if "## My view" in new:
        block('the "## My view" section cannot be added to or moved')
    start = text.find(old)
    if old == "" or start < 0:
        block("the text to edit is not in the file")
    if start < section.end() and start + len(old) > section.start():
        # One exception: adding new sections straight after the view, with the view's
        # words kept exactly. Nothing else in the file can anchor that first addition.
        added = new[len(old):] if new.startswith(old) else None
        at_the_end = text[start + len(old):section.end()].strip() == ""
        if added is None or not at_the_end or not added.lstrip().startswith("## "):
            block('the "## My view" section is fixed once written')


def allowed_search(argv, cwd):
    """grep PATTERN PATH... or ls [PATH...], both read-only and inside the vault."""
    flag = GREP_FLAG if argv[0] == "grep" else LS_FLAG
    rest = [arg for arg in argv[1:] if not flag.match(arg)]
    if any(arg.startswith("-") for arg in rest):
        return False
    if argv[0] == "grep":
        # The first is the pattern. A path is required, so grep never waits on input.
        rest = rest[1:] if len(rest) >= 2 else ["/"]
    return all(inside_vault(path, cwd) for path in rest or [cwd])


def allowed_pm(argv):
    """.venv/bin/python -I pm.py INPUTS.json, with only the script's read-only options."""
    if argv[:2] != [".venv/bin/python", "-I"] or len(argv) < 4 or argv[2] != PM:
        return False
    if not (SCRATCH_JSON.match(os.path.realpath(argv[3])) or argv[3].startswith(".claude/skills/portfolio-manager/assets/")):
        return False
    if ".." in argv[3]:
        return False
    rest = argv[4:]
    while rest:
        if rest[0] == "--json":
            rest = rest[1:]
        elif rest[0] == "--portfolio" and len(rest) >= 2 and rest[1].startswith("Portfolio/") and ".." not in rest[1]:
            rest = rest[2:]
        elif rest[0] == "--what-if-size" and len(rest) >= 2 and re.fullmatch(r"\d+(\.\d+)?", rest[1]):
            rest = rest[2:]
        else:
            return False
    return True


def allowed_command(argv, cwd):
    if argv[0] in ("grep", "ls"):
        return allowed_search(argv, cwd)
    if argv[0] == "date":
        return len(argv) == 1 or (len(argv) == 2 and bool(re.fullmatch(r"\+[%A-Za-z-]+", argv[1])))
    if argv[0] == "jq":
        # jq has no way to write a file without a redirect, and redirects are blocked above.
        return "-f" not in argv and "--from-file" not in argv
    return allowed_pm(argv)


def check_bash(tool_input, cwd):
    command = tool_input["command"].strip()
    if has_shell_syntax(command):
        block("one plain command only, with no operators or substitution")
    argv = shlex.split(command)
    if not argv or not allowed_command(argv, cwd):
        block("Bash allows only grep, ls and jq inside this vault, date, and pm.py on an input file")


def main():
    payload = json.load(sys.stdin)
    tool = payload["tool_name"]
    tool_input = payload["tool_input"]
    cwd = payload.get("cwd", ROOT)
    if tool == "Write":
        check_write(tool_input, cwd)
        return
    if tool == "Edit":
        # Not gated: a coach that closes the stage must still reach its own file.
        # check_edit needs an existing decision file and keeps the owner's view fixed.
        check_edit(tool_input, cwd)
        return
    if not view_is_on_file():
        block("write the owner's view to Journal/decisions/ first, or return the three questions")
    if tool == "Bash":
        check_bash(tool_input, cwd)
    elif tool == "Skill":
        if tool_input.get("skill") != "portfolio-manager":
            block("the only skill the coach runs is portfolio-manager")
    elif tool != "Read":
        block(f"unexpected tool {tool}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        block(f"could not check this call ({error})")
