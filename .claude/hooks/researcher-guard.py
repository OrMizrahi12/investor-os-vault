#!/usr/bin/env python3
"""Guard for the researcher subagent. Runs before each Write or Bash call.

Write: only a report file directly inside Research/.
Bash: only the read or search commands below, with no shell operators.
grep and ls are limited to paths inside this vault.
Exit 2 blocks the call. Any error also blocks, because other exit codes let it through.
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_NAME = re.compile(r"^\d{4}-\d{2}-\d{2} [^/\\]+ (fundamental|strategic)( \d+)?\.md$")
UNSAFE_OUTSIDE_QUOTES = set(";&|<>()`$\\\n\r{}[]*?~!#")
UNSAFE_IN_DOUBLE_QUOTES = set("`$\\")
GREP_FLAG = re.compile(r"^(-[rilLnHhcEFwvs]+|-[ABC]\d{1,3}|--(include|exclude|exclude-dir)=[^/]+)$")
LS_FLAG = re.compile(r"^-[1aAlhRtrS]+$")


def block(reason):
    print(f"researcher guard: {reason}", file=sys.stderr)
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


def allowed_command(argv, cwd):
    if argv[0] in ("grep", "ls"):
        return allowed_search(argv, cwd)
    if argv[:3] == ["agent-reach", "web", "search"]:
        return len(argv) == 6 and not argv[3].startswith("-") and argv[4:] == ["--limit", "5"]
    if argv[:4] == ["uv", "run", "python", "sensors/edgar/edgar.py"]:
        rest = argv[4:]
        if not rest or not re.fullmatch(r"[A-Za-z0-9.]+", rest[0]):
            return False
        return len(rest) == 1 or (len(rest) == 3 and rest[1] == "--document" and bool(re.fullmatch(r"[0-9-]+", rest[2])))
    # jq has no way to write a file without a redirect, and redirects are blocked above.
    return argv[0] == "jq" and "-f" not in argv and "--from-file" not in argv


def check_write(tool_input, cwd):
    path = Path(os.path.realpath(Path(cwd) / tool_input["file_path"]))
    if path.parent != ROOT / "Research" or not REPORT_NAME.match(path.name):
        block("write only Research/YYYY-MM-DD <Company> <fundamental|strategic>.md")


def check_bash(tool_input, cwd):
    command = tool_input["command"].strip()
    if has_shell_syntax(command):
        block("one plain command only, with no operators or substitution")
    argv = shlex.split(command)
    if not argv or not allowed_command(argv, cwd):
        block("Bash allows only agent-reach web search \"<query>\" --limit 5, the edgar sensor, jq, and grep or ls inside this vault")


def main():
    payload = json.load(sys.stdin)
    tool = payload["tool_name"]
    if tool == "Write":
        check_write(payload["tool_input"], payload.get("cwd", ROOT))
    elif tool == "Bash":
        check_bash(payload["tool_input"], payload.get("cwd", ROOT))
    else:
        block(f"unexpected tool {tool}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        block(f"could not check this call ({error})")
