#!/usr/bin/env python3
"""The guardrail hook. One file, standard library only, for Mac, Windows and Linux.

It runs for every session in this project, because a deny rule cannot tell a routine from a person.

Before a call (PreToolUse):
  - A file tool may not write inside a wall.
  - A shell command that names a walled path may only read it.
  - Nothing that looks like placing a trade or talking to a broker goes out.
After a shell call (PostToolUse, PostToolUseFailure):
  - A walled file that changed anyway, say through a script, is put back. The changed copy goes to
    .claude/guardrails/quarantine/, so nothing is lost.

Exit 2 blocks. Any error also blocks, because other exit codes let a call through.
Page: guardrails.html. Tests: sensors/guardrails/.
"""
import datetime as dt
import fnmatch
import glob
import hashlib
import json
import os
import posixpath
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".claude" / "guardrails"
LOG = STATE / "blocked.jsonl"

# ---- the walls: rule id, name, relative path in lower case. A path ending in / is a folder. First match wins. ----
WALLS = [
    ("W4", "the alert map", "rules/alerts.md"),
    ("W4", "the alert map", "sensors/alerts/alertmap.py"),
    ("W4", "the alert map", ".claude/skills/monitor/"),
    ("W3", "the method", "rules/when-to-buy.md"),
    ("W3", "the method", "rules/when-to-trim.md"),
    ("W3", "the method", "rules/sizing.md"),
    ("W3", "the method", "rules/cash.md"),
    ("W3", "the method", ".claude/skills/valuation/"),
    ("W3", "the method", ".claude/skills/portfolio-manager/"),
    ("W3", "the method", "sensors/base/model.py"),
    ("W3", "the method", "sensors/strategic/model.py"),
    ("W3", "the method", "sensors/valuation/save.py"),
    ("W3", "the method", "sensors/valuation/runs/"),
    ("W1", "my rules", "rules/"),
    ("W1", "my rules", "rules.md"),
    ("W1", "my rules", "claude.md"),
    ("W1", "my rules", "claude.local.md"),
    ("W2", "my portfolio", "portfolio/"),
    ("W5", "the guardrails", ".claude/"),
    ("W5", "the guardrails", ".mcp.json"),
    ("W5", "the guardrails", "sensors/guardrails/"),
]
# The kill lines the map reads. A new thesis may add a note, but a saved one stays as it is. The hook alone holds this.
KILL_NOTES = "research/*kill criteria*.md"
# Scripts may add new files here. Existing ones may not change.
MAY_ADD = ("sensors/valuation/runs/", "sensors/guardrails/runs/")
# Where a run's own output goes, so never watched.
NOT_WATCHED = ("sensors/guardrails/runs/", ".claude/guardrails/")
HOME_WALLS = re.compile(r"/\.claude/(settings[^/]*\.json|hooks(/|$)|agents(/|$)|skills(/|$)|commands(/|$)|scheduled-tasks(/|$))")

# ---- what looks like a trade or a broker ----
HOSTS = (r"alpaca\.markets|interactivebrokers\.[a-z.]+|ibkr\.com|ibllc\.com|schwab\.com|schwabapi\.com|fidelity\.com|vanguard\.com|"
         r"robinhood\.com|etrade\.com|tdameritrade\.com|tradestation\.com|tastytrade\.com|tastyworks\.com|webull\.com|merrilledge\.com|"
         r"firstrade\.com|tradier\.com|moomoo\.com|futunn\.com|saxobank\.com|degiro\.[a-z.]+|trading212\.com|plus500\.com|etoro\.com|"
         r"questrade\.com|lightspeed\.com|tradezero\.[a-z.]+|kraken\.com|coinbase\.com|binance\.[a-z.]+")
HOST = re.compile(rf"(?<![\w-])(?:[\w-]+\.)*(?:{HOSTS})", re.I)
SDK = (r"alpaca[-_][\w-]+|alpaca_trade_api|ib_insync|ib_async|ibapi|ibgateway|ib-gateway|tws-?api|robin_stocks|schwab-py|schwabdev|tda-api|pyetrade|ccxt|APCA_[A-Z_]+")
CALLS = (r"(?:place|submit|create|cancel|modify|replace|send)_?(?:bracket_?|market_?|limit_?)?order|order_(?:buy|sell|stock|target|market|limit)\w*|"
         r"placeOrder|submitOrder|createOrder|cancelOrder|modifyOrder|replaceOrder|buy_market|sell_market")
GATEWAY = r"(?:localhost|127\.0\.0\.1)[: ]+(?:7496|7497|4001|4002)\b"
CODE_API = re.compile(rf"(?<![\w-])(?:{SDK}|{CALLS})(?![\w-])|{GATEWAY}|(?:^|\n)\s*(?:import|from)\s+(?:alpaca|robinhood|webull|tradier|moomoo|firstrade|tastytrade|tradestation)\b", re.I)
API = re.compile(rf"(?<![\w-])(?:{SDK}|{CALLS}|alpaca|ibkr|robinhood|tradestation|tastytrade|tastyworks|webull|moomoo|firstrade|tradier)(?![\w-])|{GATEWAY}", re.I)
NAMES = (r"schwab|fidelity|vanguard|robinhood|interactive brokers|ibkr|alpaca|e\*?-?trade|merrill edge|td ameritrade|tradestation|tastytrade|webull|moomoo|"
         r"firstrade|tradier|saxo|degiro|trading ?212|my broker(?:age)?|brokerage account")
ACTIONS = r"log ?in|logon|sign ?in|account|order|trade|trading|api|password|credential|oauth|token|session|buy|sell"
NAME_ACTION = re.compile(rf"\b(?:{NAMES})\b.{{0,60}}\b(?:{ACTIONS})\b|\b(?:{ACTIONS})\b.{{0,60}}\b(?:{NAMES})\b", re.I | re.S)
ORDER_SHAPES = [
    re.compile(r"\b(?:buy|sell|short|cover)\s+\d[\d,.]*\s*(?:shares?|contracts?|lots?|units?)\b", re.I),
    re.compile(r"\b(?:BUY|SELL|buy|sell)\s+\d[\d,.]*\s+[A-Z]{1,5}\b"),
    re.compile(r"\b(?:BUY|SELL|buy|sell)\s+[A-Z]{1,5}\s+\d"),
    re.compile(r"\b(?:market|limit|stop|stop[- ]limit|bracket|trailing[- ]stop)[ -]order\b", re.I),
    re.compile(r"\b(?:side|action)[\"'\s:=]+(?:buy|sell)\b", re.I),
    re.compile(r"(?:-X\s*(?:POST|PUT|DELETE|PATCH)|--request\s+(?:POST|PUT|DELETE|PATCH)|--data|\s-d\s|requests\.(?:post|put|delete)|method=.(?:POST|PUT|DELETE))[^\n]{0,200}/(?:orders?|trades?)\b", re.I),
    re.compile(r"/(?:orders?|trades?)\b[^\n]{0,200}(?:-X\s*(?:POST|PUT|DELETE|PATCH)|--request\s+(?:POST|PUT|DELETE|PATCH)|--data|\s-d\s)", re.I),
    re.compile(r"\b(?:place|submit|send|execute)\s+(?:an?\s+|the\s+)?(?:order|trade)\b", re.I),
    re.compile(r"\bbroker(?:age)?\b", re.I),
]
# Tools that act through a signed-in browser or the desktop. A click names no host, so they are closed whole.
SCREEN_TOOLS = re.compile(r"^mcp__(?:computer-use|claude-in-chrome|claude_browser|remote-devices)", re.I)
BROKER_TOOL = re.compile(r"^mcp__.*(?:broker|alpaca|ibkr|schwab|fidelity|robinhood|etrade|webull|tradier|tastytrade|trad(?:e|ing)|order)", re.I)
CODE_FILE = re.compile(r"\.(?:py|pyw|sh|bash|zsh|ps1|psm1|bat|cmd|js|mjs|cjs|ts|rb|pl|php|go|rs|java|ipynb)$", re.I)

READ_ONLY = {"cat", "grep", "egrep", "fgrep", "rg", "ls", "head", "tail", "wc", "diff", "stat", "file", "jq", "echo", "printf", "cd", "pwd", "date", "basename", "dirname",
             "realpath", "readlink", "du", "df", "sha256sum", "shasum", "md5sum", "cut", "uniq", "tr", "nl", "test", "[", "true", "false", "which", "type", "column", "less", "more",
             "sed", "awk", "gawk", "find", "sort", "git", "get-content", "select-string", "get-childitem", "test-path", "gc", "dir", "findstr", "resolve-path", "get-item", "measure-object"}
GIT_READ = {"diff", "log", "show", "status", "blame", "rev-parse", "ls-files"}
FIND_WRITES = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls", "-fprint0"}
DESTROYERS = {"rm", "rmdir", "mv", "cp", "rsync", "chmod", "chown", "ln", "unzip", "shred", "truncate", "del", "erase", "rd", "move", "copy", "xcopy", "robocopy", "remove-item", "move-item", "copy-item"}


# Tools that only read or talk inside this session.
NOT_OUTGOING = {"Read", "Grep", "Glob", "LS", "TodoWrite", "TaskOutput", "TaskStop", "ToolSearch", "AskUserQuestion", "SubagentHandback", "SendMessage", "ListAgents",
                "ReportFindings", "Monitor", "ExitPlanMode", "EnterPlanMode", "SendFeedback", "ScheduleWakeup", "EndConversation"}


class Blocked(Exception):
    def __init__(self, rule, reason):
        super().__init__(reason)
        self.rule, self.reason = rule, reason


# ---- paths ----

def _norm(raw):
    """A path as text in one form, whatever the system: forward slashes, lower case, no .. steps."""
    text = str(raw).replace("\\", "/")
    drive = re.match(r"^/([a-zA-Z])/(.*)$", text)  # Git Bash writes C:\Users as /c/Users
    if drive:
        text = f"{drive.group(1)}:/{drive.group(2)}"
    return text.casefold()


def _is_absolute(text):
    return text.startswith("/") or bool(re.match(r"^[a-z]:/", text))


def relative(raw, cwd, root=ROOT):
    """The path relative to the project in lower case, or None if it lies outside."""
    text, base = _norm(raw), _norm(root)
    if text.startswith("~"):
        text = _norm(Path.home()) + text[1:]
    if not _is_absolute(text):
        text = _norm(cwd).rstrip("/") + "/" + text
    text, base = posixpath.normpath(text), posixpath.normpath(base)
    if text == base:
        return ""
    return text[len(base) + 1:] if text.startswith(base + "/") else None


def wall_of_relative(rel):
    if rel is None:
        return None
    for rule, name, pattern in WALLS:
        if rel == pattern.rstrip("/") or (pattern.endswith("/") and rel.startswith(pattern)):
            return None if rel.startswith("sensors/guardrails/runs/") else (rule, name)
    return None


def walls_of(raw, cwd, root=ROOT):
    """Which wall a path lies behind, checking both its words and where a link really leads."""
    found = wall_of_relative(relative(raw, cwd, root))
    if found:
        return found
    if HOME_WALLS.search(_norm(os.path.expanduser(str(raw)))) and _home_path(raw, cwd):
        return "W5", "the guardrails"
    try:
        real = os.path.realpath(Path(cwd) / os.path.expanduser(str(raw)))
    except (OSError, ValueError):
        return None
    if real != str(raw):
        found = wall_of_relative(relative(real, cwd, root))
        if found:
            return found
        if HOME_WALLS.search(_norm(real)) and _home_path(real, cwd):
            return "W5", "the guardrails"
    return None


def _home_path(raw, cwd):
    text = _norm(os.path.expanduser(str(raw)))
    if not _is_absolute(text):
        text = _norm(cwd).rstrip("/") + "/" + text
    return posixpath.normpath(text).startswith(posixpath.normpath(_norm(Path.home())) + "/.claude/")


def existing_kill_note(raw, cwd, root=ROOT):
    rel = relative(raw, cwd, root)
    if rel is None or not fnmatch.fnmatchcase(rel, KILL_NOTES):
        return False
    return (Path(cwd) / os.path.expanduser(str(raw))).exists()


# ---- shell commands ----

CONTROL_PREFIX = {"do", "then", "else", "elif", "if", "while", "until", "!", "{", "time"}
CONTROL_ONLY = {"done", "fi", "esac", "}", "for", "case", "select", "function"}
WRAPPERS = {"env", "nohup", "exec", "nice", "ionice", "timeout", "command", "sudo", "stdbuf", "setsid", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "pwsh", "powershell", "cmd"}
SHELL_FLAG = {"-c", "-lc", "-ic", "-command", "/c", "/k", "-encodedcommand", "-ec", "-e"}
CODE_RUNNERS = {"python", "python3", "py", "pypy", "pypy3", "node", "ruby", "perl", "php", "osascript"}
CODE_FLAG = {"-c", "-e", "-r", "--eval", "-p", "--print", "-pe", "-ne", "-pi", "-i"}
LAST_IS_TARGET = {"cp", "copy", "copy-item", "xcopy", "robocopy", "install", "ln", "rsync"}
WRITERS = {"tee", "touch", "mkdir", "dd", "patch", "ed", "ex", "vi", "vim", "nano", "emacs", "set-content", "add-content", "out-file", "new-item", "clear-content", "sponge", "xargs", "parallel", "find"} | DESTROYERS
WRITE_SIGNAL = re.compile(r"""open\s*\([^)]*['"][wax+]|\.write|write_text|write_bytes|\.unlink|\.rename|os\.(?:remove|rename|replace|unlink|system|rmdir|chmod|truncate)|shutil\.|subprocess|\.touch|\.mkdir|\.rmdir|writeFile|appendFile|rmSync|unlinkSync|File\.(?:write|delete)|\bunlink\b|\brename\b|sed\s+-i|>\s*['"\w./]""", re.I)


def parse_shell(command):
    """Cut a command into segments at unquoted operators. Each has its words, redirect targets and any heredoc text. Text inside $() and backticks is cut too."""
    segments, extra = [], []
    token, started, quote, i = "", False, None, 0
    current = {"tokens": [], "redirects": [], "body": ""}
    pending = []

    def end_token():
        nonlocal token, started
        if started:
            current["tokens"].append(token)
        token, started = "", False

    def end_segment():
        nonlocal current
        end_token()
        if current["tokens"] or current["redirects"] or current["body"]:
            segments.append(current)
        current = {"tokens": [], "redirects": [], "body": ""}

    n = len(command)
    while i < n:
        c = command[i]
        if quote == "'":
            if c == "'":
                quote = None
            else:
                token += c
        elif quote == '"':
            if c == '"':
                quote = None
            elif c == "\\" and i + 1 < n and command[i + 1] in '"\\$`':
                token += command[i + 1]
                i += 1
            elif c == "`" or command.startswith("$(", i):
                inner, i = _substitution(command, i)
                extra.append(inner)
                token += "$SUB"
                continue
            else:
                token += c
        elif c in "'\"":
            quote, started = c, True
        elif c == "\\" and i + 1 < n:
            if command[i + 1] != "\n":
                token += "\\" + command[i + 1] if command[i + 1] not in " '\"" else command[i + 1]
                started = True
            i += 1
        elif c == "`" or command.startswith("$(", i):
            inner, i = _substitution(command, i)
            extra.append(inner)
            token, started = token + "$SUB", True
            continue
        elif command.startswith("<<<", i):
            end_token()
            word, i = _word(command, _skip_spaces(command, i + 3))
            current["body"] += word + "\n"
            continue
        elif command.startswith("<<", i):
            end_token()
            i += 2
            if command[i:i + 1] in ("-", "~"):
                i += 1
            word, i = _word(command, _skip_spaces(command, i))
            pending.append((word, current))
            continue
        elif c == ">" or (c in "12&" and command[i + 1:i + 2] == ">" and not started):
            end_token()
            i += 1 if c == ">" else 2
            while i < n and command[i] in ">|&":
                i += 1
            target, i = _word(command, _skip_spaces(command, i))
            current["redirects"].append(target)
            continue
        elif c == "<":
            end_token()
            _, i = _word(command, _skip_spaces(command, i + 1))
            continue
        elif c == "\n" and pending:
            end_segment()
            i += 1
            for word, owner in pending:
                body, i = _heredoc(command, i, word)
                owner["body"] += body
            pending = []
            continue
        elif c in ";|&\n()":
            end_segment()
        elif c in " \t\r":
            end_token()
        elif c == "#" and not started:
            while i < n and command[i] != "\n":
                i += 1
            continue
        else:
            token += c
            started = True
        i += 1
    end_segment()
    for inner in extra:
        segments += parse_shell(inner)
    return segments


def _skip_spaces(command, i):
    while i < len(command) and command[i] in " \t":
        i += 1
    return i


def _heredoc(command, i, word):
    lines = []
    while i < len(command):
        end = command.find("\n", i)
        end = len(command) if end < 0 else end
        line = command[i:end]
        i = end + 1
        if line.strip() == word:
            break
        lines.append(line)
    return "\n".join(lines) + "\n", i


def _substitution(command, i):
    if command[i] == "`":
        end = command.find("`", i + 1)
        end = len(command) if end < 0 else end
        return command[i + 1:end], end + 1
    depth, j = 1, i + 2
    while j < len(command) and depth:
        depth += command[j] == "("
        depth -= command[j] == ")"
        j += 1
    return command[i + 2:j - 1], j


def _word(command, i):
    out, quote = "", None
    while i < len(command):
        c = command[i]
        if quote:
            if c == quote:
                quote = None
            else:
                out += c
        elif c in "'\"":
            quote = c
        elif c in " \t\n;|&<>()":
            break
        else:
            out += c
        i += 1
    return out, i


def base_name(word):
    return word.replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")


def plain_tokens(tokens):
    """The words of a segment with shell keywords, VAR=value and wrappers such as nohup taken off."""
    tokens = list(tokens)
    while tokens:
        first = tokens[0]
        name = base_name(first)
        if first in CONTROL_PREFIX or re.fullmatch(r"[A-Za-z_]\w*=.*", first):
            tokens = tokens[1:]
        elif name in WRAPPERS:
            tokens = tokens[1:]
            while tokens and (tokens[0].startswith("-") or re.fullmatch(r"\d+[smhd]?", tokens[0]) or re.fullmatch(r"[A-Za-z_]\w*=.*", tokens[0])):
                tokens = tokens[1:]
        else:
            break
    return tokens


def tokens_read_only(tokens):
    tokens = plain_tokens(tokens)
    if not tokens or tokens[0] in CONTROL_ONLY:
        return True
    name, args = base_name(tokens[0]), tokens[1:]
    if name == "xargs":
        rest = [a for a in args if not a.startswith("-")]
        return bool(rest) and base_name(rest[0]) in READ_ONLY - {"sed", "awk", "gawk", "find", "sort", "git"}
    if name not in READ_ONLY:
        return False
    if name == "sed":
        return not any(re.match(r"^(-[a-zA-Z]*i|--in-place)", a) for a in args)
    if name in ("awk", "gawk"):
        return not any("system(" in a or "getline" in a or re.search(r"(print|printf)[^;}]*>", a) or a.startswith("-i") or a == "--inplace" for a in args)
    if name == "find":
        for index, arg in enumerate(args):
            low = arg.lower()
            if low in ("-exec", "-execdir", "-ok", "-okdir"):
                if index + 1 >= len(args) or base_name(args[index + 1]) not in READ_ONLY - {"sed", "awk", "gawk", "find", "sort", "git"}:
                    return False
            elif low in FIND_WRITES:
                return False
        return True
    if name == "sort":
        return not any(a.startswith("-o") or a.startswith("--output") for a in args)
    if name == "git":
        return bool(args) and args[0] in GIT_READ
    return True


def segment_reads_only(segment):
    return tokens_read_only(segment["tokens"])


def _clean_for_mentions(command, root):
    """Lower case, forward slashes, no .. steps, and the project's own folder dropped, so every way of naming a path reads the same."""
    text = command.replace("\\", "/").replace('"', " ").replace("'", " ").casefold()
    text = re.sub(r"/([a-z])/(?=users/)", r"\1:/", text)
    for base in {_norm(root), _norm(os.path.realpath(root))}:
        text = text.replace(base.rstrip("/") + "/", "./")
    text = re.sub(r"\$\{?\w+\}?/", "./", text)  # $PWD/Rules, ${CLAUDE_PROJECT_DIR}/Rules
    while True:
        cut = re.sub(r"(?:[^\s/:=(),;|&.][^\s/:=(),;|&]*/)\.\./", "", text)
        cut = re.sub(r"(?<=[\s=(,;|&+])\./", "", cut)
        if cut == text:
            break
        text = cut
    return text


def mentions(text, root=ROOT):
    """Walled paths named anywhere in a text, even inside quotes or code."""
    clean = " " + _clean_for_mentions(text, root)
    found = []
    for rule, name, pattern in WALLS:
        needle = pattern.rstrip("/")
        if re.search(rf"[\s=(,:;|&<>\[{{+](?:\./)*{re.escape(needle)}(?:/|(?=[\s,;:)|&\]}}]|$))", clean):
            found.append((rule, name, needle))
    if re.search(r"kill criteria[^\n]*\.md", clean):
        found.append(("W4", "the alert map", "a saved kill line note"))
    if re.search(r"\.claude/(?:settings[^/\s]*\.json|hooks\b|agents\b|skills\b|commands\b|scheduled-tasks\b)", clean):
        found.append(("W5", "the guardrails", ".claude settings or hooks"))
    return found


def code_mentions(code, root=ROOT):
    """Walled paths in code. Only a quoted string that starts with the path counts, so a sentence that names a rule in passing does not."""
    found = []
    for quoted in re.findall(r"""'([^'\n]{1,160})'|"([^"\n]{1,160})\"""", code):
        text = quoted[0] or quoted[1]
        if "/" not in text and "\\" not in text and "." not in text:
            continue  # a bare word such as "Portfolio" is a title more often than a path. The after-check still stands.
        found += [m for m in mentions(text, root) if _starts_with_wall(text, m, root)]
    return found


def _starts_with_wall(text, mention, root):
    clean = _clean_for_mentions(text, root).strip()
    while clean.startswith("./"):
        clean = clean[2:]
    return clean.startswith(mention[2]) or mention[2] == "a saved kill line note" or ".claude/" in clean[:60]


def _expand(token, cwd):
    """What a glob in an argument would really reach."""
    if not re.search(r"[*?\[]", token):
        return [token]
    pattern = os.path.expanduser(token)
    if not os.path.isabs(pattern):
        pattern = os.path.join(str(cwd), pattern)
    return glob.glob(pattern, include_hidden=True)[:2000] or [token]


def contains_wall(raw, cwd, root):
    """True if a path is the project or a folder holding walled files, such as `.` or `sensors`."""
    rel = relative(raw, cwd, root)
    if rel is None:
        return False
    return rel == "" or any(p.startswith(rel + "/") for _, _, p in WALLS)


def _resolve_vars(token, values):
    def swap(match):
        return values.get(match.group(1) or match.group(2), match.group(0))
    return re.sub(r"\$(?:\{(\w+)\}|(\w+))", swap, token)


def _inline_code(tokens, body):
    """The code an interpreter gets from -c, -e or a heredoc, or None."""
    args = tokens[1:]
    for index, arg in enumerate(args):
        if arg.lower() in CODE_FLAG and index + 1 < len(args):
            return args[index + 1]
        if not arg.startswith("-"):
            break
    if body and (not args or args[-1] == "-" or all(a.startswith("-") for a in args)):
        return body
    return None


def check_shell(command, cwd, root=ROOT):
    values = {"PWD": str(cwd), "HOME": str(Path.home()), "CLAUDE_PROJECT_DIR": str(root)}
    segments = parse_shell(command)
    tainted, earlier = {}, []
    for segment in segments:
        tokens = [_resolve_vars(t, values) for t in segment["tokens"]]
        for token in tokens:
            hit = re.fullmatch(r"([A-Za-z_]\w*)=(.*)", token, re.S)
            if not hit:
                break
            values[hit.group(1)] = hit.group(2)
            if mentions(hit.group(2), root):
                tainted[hit.group(1)] = mentions(hit.group(2), root)[0]
        if len(tokens) > 3 and tokens[0] in ("for", "select") and tokens[2] == "in":
            found = [m for t in tokens[3:] for m in mentions(t, root)]
            if found:
                tainted[tokens[1]] = found[0]
        for target in segment["redirects"]:
            target = _resolve_vars(target, values)
            wall = walls_of(target, cwd, root)
            if wall:
                raise Blocked(wall[0], f"a shell redirect would write to {wall[1]} ({target})")
            if existing_kill_note(target, cwd, root):
                raise Blocked("W4", f"a shell redirect would change a saved kill line note ({target})")
        tokens = plain_tokens(tokens)
        if not tokens:
            continue
        name = base_name(tokens[0])
        if name == "cd" and len(tokens) > 1 and "$" not in tokens[1]:
            cwd = os.path.normpath(os.path.join(str(cwd), os.path.expanduser(tokens[1])))
            continue
        if tokens_read_only(tokens):
            earlier += [m for t in tokens[1:] for m in mentions(t, root)]
            continue
        if name in SHELLS or name == "eval":
            inner = " ".join(tokens[1:]) if name == "eval" else _flag_value(tokens, SHELL_FLAG) or segment["body"]
            if inner:
                check_shell(inner, cwd, root)
                continue
        if name in CODE_RUNNERS:
            code = _inline_code(tokens, segment["body"])
            if code is not None:
                found = code_mentions(code, root)
                if found and WRITE_SIGNAL.search(code):
                    raise Blocked(found[0][0], f"this code names {found[0][1]} ({found[0][2]}) and looks like it writes")
                if not any(re.fullmatch(r"-[a-zA-Z]*i[a-zA-Z]*", t) for t in tokens[1:]):  # perl -pi edits the files it is given
                    continue
            if _plain_walled_run(tokens, root, cwd):
                continue
        args = tokens[1:]
        if name in LAST_IS_TARGET and args:
            flagged = [a for i, a in enumerate(args) if i and args[i - 1] in ("-t", "--target-directory")]
            args = flagged or [a for a in args if not a.startswith("-")][-1:]
        for token in args:
            if token.startswith("-") and not re.search(r"[*?\[]", token):
                continue
            for path in _expand(token, cwd):
                wall = walls_of(path, cwd, root)
                if wall:
                    raise Blocked(wall[0], f"this command may change {wall[1]} ({path})")
                if existing_kill_note(path, cwd, root):
                    raise Blocked("W4", f"this command may change a saved kill line note ({path})")
                if name in DESTROYERS | {"find"} and contains_wall(path, cwd, root):
                    raise Blocked("W1", f"{name} on {path} would reach walled folders")
        if name in WRITERS:
            for var, mention in tainted.items():
                if any(re.search(rf"\$\{{?{var}\b", t) for t in args):
                    raise Blocked(mention[0], f"${var} holds {mention[1]} ({mention[2]}) and {name} may change it")
            if name in ("xargs", "parallel") and earlier:
                raise Blocked(earlier[0][0], f"{name} is fed from {earlier[0][1]} ({earlier[0][2]}) and may change it")


def _flag_value(tokens, flags):
    for index, token in enumerate(tokens[1:-1], start=1):
        if token.lower() in flags:
            return " ".join(tokens[index + 1:])
    return None


def _plain_walled_run(tokens, root, cwd):
    """python <script inside a wall>, such as value.py. Walled code is safe to run and the after-check still stands."""
    args = tokens[1:]
    while args and args[0] in ("-I", "-B", "-u", "-E", "-s", "-S"):
        args = args[1:]
    if not args or args[0].startswith("-"):
        return False
    rel = relative(args[0], cwd, root)
    if rel is None or rel.startswith(".claude/hooks/"):
        return False
    return bool(wall_of_relative(rel))


# ---- trades and brokers ----

def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from strings_in(item)


def trade_hit(text, phrases=False):
    hit = HOST.search(text)
    if hit:
        return "T1", hit.group(0)
    hit = API.search(text)
    if hit:
        return "T2", hit.group(0)
    hit = NAME_ACTION.search(text)
    if hit:
        return "T3", hit.group(0)[:80]
    if phrases:
        for pattern in ORDER_SHAPES:
            hit = pattern.search(text)
            if hit:
                return "T4", hit.group(0)[:80]
    return None


def code_hit(text):
    """In a file of code, a broker's address or order call counts. A saved link to a news story on a broker's site does not."""
    for match in HOST.finditer(text):
        after = text[match.end():match.end() + 6].casefold()
        if not (match.group(0).casefold().startswith("news.") or after.startswith("/news")):
            return "T1", match.group(0)
    hit = CODE_API.search(text)
    return ("T2", hit.group(0)) if hit else None


TRADE_NAMES = {"T1": "a broker's site", "T2": "a broker's software or an order call", "T3": "a broker named with an action", "T4": "the shape of an order"}


def _raise_trade(hit, where):
    raise Blocked(hit[0], f"{where} looks like {TRADE_NAMES[hit[0]]}: {hit[1]!r}. Claude never trades or talks to a broker. Give the owner the recommendation instead.")


def scan_script(tokens, cwd, root):
    """A script a command runs is read first, so a trade written by another route is caught before it runs."""
    for token in tokens[1:]:
        if token.startswith("-"):
            continue
        path = Path(cwd) / os.path.expanduser(token)
        rel = relative(path, cwd, root)
        if rel is not None and rel.startswith(("sensors/guardrails/", ".claude/hooks/")):
            return  # these hold the patterns themselves, and they are walled
        try:
            if path.is_file() and path.stat().st_size < 2_000_000:
                hit = code_hit(path.read_text(encoding="utf-8", errors="replace"))
                if hit:
                    _raise_trade(hit, f"the script {token}")
        except OSError:
            pass
        return


def check_trade_in_shell(command, cwd, root=ROOT):
    segments = parse_shell(command)
    if not segments:
        return
    if all(segment_reads_only(s) and not s["redirects"] and not s["body"] for s in segments):
        return  # reading saved notes that name a broker is not talking to one
    parts = []
    any_outgoing = any(not segment_reads_only(s) for s in segments)
    for segment in segments:
        tokens = plain_tokens(segment["tokens"])
        if not tokens:
            continue
        name = base_name(tokens[0])
        if name == "cd":
            cwd = os.path.normpath(os.path.join(str(cwd), os.path.expanduser(tokens[1]))) if len(tokens) > 1 and "$" not in tokens[1] else cwd
            continue
        if name in CODE_RUNNERS or name in SHELLS:
            scan_script(tokens, cwd, root)
        if segment["body"] and any(CODE_FILE.search(t) for t in segment["redirects"]):
            hit = code_hit(segment["body"])
            if hit:
                _raise_trade(hit, "this code")
        if not segment_reads_only(segment):
            parts.append(" ".join(tokens if name not in CODE_RUNNERS else [t for t in tokens if len(t) < 300]))
            if name in SHELLS and segment["body"]:
                parts.append(segment["body"])
            elif name in CODE_RUNNERS:
                code = _inline_code(tokens, segment["body"]) or ""
                hit = code_hit(code) or (("T4", "an order's side") if ORDER_SHAPES[4].search(code) else None)
                if hit:
                    _raise_trade(hit, "this code")
        elif name in ("echo", "printf") and any_outgoing:
            parts.append(" ".join(tokens))
    hit = trade_hit("\n".join(parts), phrases=True)
    if hit:
        _raise_trade(hit, "this command")


# ---- one call ----

def text_of_write(tool, tool_input):
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        return tool_input.get("new_string", "")
    if tool == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    return tool_input.get("new_source", "")


def check_call(tool, tool_input, cwd, root=ROOT):
    if tool in NOT_OUTGOING:
        return
    if SCREEN_TOOLS.match(tool):
        raise Blocked("T5", f"{tool} acts through a signed-in browser or the desktop, where a click names no site. Closed here.")
    if BROKER_TOOL.match(tool):
        raise Blocked("T5", f"{tool} looks like a broker or order tool.")
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        wall = walls_of(path, cwd, root)
        if wall:
            raise Blocked(wall[0], f"{wall[1]} is walled off ({path}). No run may change it. Write a proposal for the owner instead.")
        if existing_kill_note(path, cwd, root):
            raise Blocked("W4", f"a saved kill line note is walled off ({path}). Write a proposal for the owner instead.")
        if CODE_FILE.search(str(path)):
            hit = code_hit(text_of_write(tool, tool_input))
            if hit:
                _raise_trade(hit, f"code for {path}")
        hit = trade_hit(Path(str(path).replace("\\", "/")).name)
        if hit and hit[0] == "T2":
            _raise_trade(hit, "this file's name")
        return
    if tool in ("Bash", "PowerShell"):
        command = tool_input.get("command", "")
        check_shell(command, cwd, root)
        check_trade_in_shell(command, cwd, root)
        return
    text = "\n".join(strings_in(tool_input))
    hit = trade_hit(text)
    if hit:
        _raise_trade(hit, tool)


# ---- the record ----

def record(rule, how, tool, target, payload):
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        entry = {"when": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "rule": rule, "how": how, "tool": tool,
                 "target": str(target)[:200], "session": payload.get("session_id", ""), "agent": payload.get("agent_type", ""), "mode": payload.get("permission_mode", "")}
        with open(LOG, "a", encoding="utf-8") as out:
            out.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # a full disk must not open the wall


# ---- the check after a shell call ----

MANIFEST = STATE / "manifest.json"
SHADOW = STATE / "shadow"
QUARANTINE = STATE / "quarantine"
LOCAL_SETTINGS = ".claude/settings.local.json"


def watched_files(root=ROOT):
    out = {}
    root = Path(root)

    def add(path):
        rel = path.relative_to(root).as_posix()
        low = rel.casefold()
        if "__pycache__" in low or low.endswith(".pyc") or any(low.startswith(x) for x in NOT_WATCHED):
            return
        out[rel] = path

    for top in ("Rules", "Portfolio", ".claude", "sensors/guardrails", "sensors/valuation/runs"):
        folder = root / top
        if folder.is_dir():
            for base, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for name in files:
                    add(Path(base) / name)
    for name in ("rules.md", "CLAUDE.md", "CLAUDE.local.md", ".mcp.json", "sensors/alerts/alertmap.py", "sensors/base/model.py", "sensors/strategic/model.py", "sensors/valuation/save.py"):
        if (root / name).is_file():
            add(root / name)
    research = root / "Research"
    if research.is_dir():
        for path in research.glob("*kill criteria*.md"):
            add(path)
    return out


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stat(path):
    info = path.stat()
    return [info.st_size, info.st_mtime_ns]


def _shadow_path(rel):
    return SHADOW / hashlib.sha256(rel.encode()).hexdigest()


def _load_manifest():
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_manifest(manifest):
    STATE.mkdir(parents=True, exist_ok=True)
    temp = MANIFEST.with_name(f"manifest.{os.getpid()}.tmp")
    temp.write_text(json.dumps(manifest), encoding="utf-8")
    os.replace(temp, MANIFEST)


def take_snapshot(payload, tool):
    """Before a shell call. A change since the last call is not undone, since it may be the owner's own edit. It is written down."""
    SHADOW.mkdir(parents=True, exist_ok=True)
    manifest, first = _load_manifest(), not MANIFEST.exists()
    files, changed = watched_files(), False
    for rel, path in files.items():
        now, known = _stat(path), manifest.get(rel)
        if known and known[:2] == now:
            continue
        digest = _digest(path)
        if known and known[2] == digest:
            manifest[rel] = now + [digest]
            changed = True
            continue
        if known and not first:
            record("W?", "changed between calls, not undone", tool, rel, payload)
        shutil.copy2(path, _shadow_path(rel))
        manifest[rel] = now + [digest]
        changed = True
    for rel in [r for r in manifest if r not in files]:
        record("W?", "removed between calls, not undone", tool, rel, payload)
        del manifest[rel]
        changed = True
    if changed or first:
        _save_manifest(manifest)


def _only_allow_list_changed(old_bytes, new_bytes):
    """Claude Code writes "always allow" clicks here itself. Only the allow list may move, and it cannot beat a deny."""
    try:
        old, new = json.loads(old_bytes or b"{}"), json.loads(new_bytes)
    except ValueError:
        return False
    for side in (old, new):
        side.get("permissions", {}).pop("allow", None)
        if not side.get("permissions"):
            side.pop("permissions", None)
    return old == new


def _quarantine(rel, path):
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    keep = QUARANTINE / day / rel
    keep.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, keep)
    return keep


def check_after(payload, tool):
    """After a shell call. Put back any walled file that changed, and keep the changed copy."""
    manifest = _load_manifest()
    if not manifest:
        return []
    files, undone, dirty = watched_files(), [], False
    for rel, path in files.items():
        now, known = _stat(path), manifest.get(rel)
        if known and known[:2] == now:
            continue
        if known and known[2] == _digest(path):
            manifest[rel] = now + [known[2]]
            dirty = True
            continue
        low = rel.casefold()
        if known is None:
            if low == LOCAL_SETTINGS and _only_allow_list_changed(b"", path.read_bytes()):
                continue
            if any(low.startswith(x) for x in MAY_ADD) or fnmatch.fnmatchcase(low, KILL_NOTES):
                continue
            keep = _quarantine(rel, path)
            path.unlink()
            undone.append((rel, "new file removed", keep))
            continue
        shadow = _shadow_path(rel)
        if low == LOCAL_SETTINGS and _only_allow_list_changed(shadow.read_bytes(), path.read_bytes()):
            manifest[rel] = now + [_digest(path)]
            shutil.copy2(path, shadow)
            dirty = True
            continue
        keep = _quarantine(rel, path)
        shutil.copy2(shadow, path)
        manifest[rel] = _stat(path) + [known[2]]
        dirty = True
        undone.append((rel, "changed, put back", keep))
    for rel in [r for r in manifest if r not in files]:
        target, shadow = Path(ROOT) / rel, _shadow_path(rel)
        if shadow.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(shadow, target)
            manifest[rel] = _stat(target) + [manifest[rel][2]]
            undone.append((rel, "deleted, put back", None))
            dirty = True
    if dirty:
        _save_manifest(manifest)
    for rel, what, _ in undone:
        wall = wall_of_relative(rel.casefold()) or ("W4", "a saved kill line note")
        record(wall[0], f"after-check: {what}", tool, rel, payload)
    return undone


def main():
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    event = payload.get("hook_event_name", "PreToolUse")
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if event in ("PostToolUse", "PostToolUseFailure"):
        if tool in ("Bash", "PowerShell"):
            undone = check_after(payload, tool)
            if undone:
                names = "; ".join(f"{rel} ({what})" for rel, what, _ in undone)
                print(f"guardrails: this command changed walled files. Undone: {names}. Do not try another way.", file=sys.stderr)
                sys.exit(2)
        return
    try:
        check_call(tool, tool_input, cwd)
    except Blocked as stop:
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("command") or tool_input.get("url") or tool_input.get("query") or tool_input.get("prompt") or tool
        record(stop.rule, "before the call", tool, target, payload)
        print(f"guardrails [{stop.rule}]: {stop.reason} Do not try another way.", file=sys.stderr)
        sys.exit(2)
    if tool in ("Bash", "PowerShell"):
        take_snapshot(payload, tool)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        print(f"guardrails: could not check this call, so it is blocked ({type(error).__name__}: {error})", file=sys.stderr)
        sys.exit(2)
