"""Sends Red lines from the daily run and the event run to the owner's phone through a Telegram bot. Red only, each one once.

Plain Python and the standard library. No model and no session. It reads files the runs already wrote.

Run from the project root, in your own terminal:
    .venv/bin/python sensors/phone/phone.py setup     asks for the token without showing it, finds your chat, saves both
    .venv/bin/python sensors/phone/phone.py test      sends one made-up Red marked TEST, through the same path, and proves a second pass sends nothing
    .venv/bin/python sensors/phone/phone.py check     checks that the token stays out of the vault, transcripts and shell history
    .venv/bin/python sensors/phone/phone.py send      one pass: sends what is waiting. The two runs call this at their end
    .venv/bin/python sensors/phone/phone.py send --every 900     the same pass every 15 minutes, for retries and dead runs

The token lives only in ~/.config/investor-os/telegram.env, outside the vault, readable only by you. Nothing here prints it,
passes it on a command line or writes it elsewhere. Page: phone.html.
"""
import contextlib
import datetime as dt
import fcntl
import getpass
import json
import os
import re
import stat
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECRET = Path.home() / ".config" / "investor-os" / "telegram.env"
API = "https://api.telegram.org"
TOKEN_SHAPE = re.compile(rb"(?<![\w:/.-])\d{8,10}:[A-Za-z0-9_-]{35}(?![\w-])")  # a bot token's form. Once saved, the exact token is searched for too.
ACCESSION = re.compile(r"\b\d{10}-\d{2}-\d{6}\b|\b\d{18}\b")
LIMIT = 3900  # Telegram stops at 4096 characters
STALE_HOURS = 2  # a run that has not briefed a digest by then is taken as dead, so its presumed Reds go out unread
SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules"}
OUTSIDE = [Path.home() / ".claude" / "projects", Path.home() / ".claude" / "scheduled-tasks", Path.home() / ".claude" / "history.jsonl", Path.home() / ".bash_history"]


class PhoneError(Exception):
    """Its message has been through scrub(), so it is safe to print."""


def scrub(text, token=None):
    text = str(text)
    if token:
        text = text.replace(token, "[token hidden]")
    return TOKEN_SHAPE.sub(b"[token hidden]", text.encode()).decode()


# ---- the token ----

def read_secret(path=SECRET, root=ROOT):
    path = Path(path)
    if not path.exists():
        raise PhoneError("No bot set up yet. Run: .venv/bin/python sensors/phone/phone.py setup")
    if path.resolve().is_relative_to(Path(root).resolve()):
        raise PhoneError("The token file is inside the vault. Move it out. Nothing sent.")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise PhoneError("Others can read the token file. Run setup again. Nothing sent.")
    out = dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)
    if not out.get("TOKEN") or not out.get("CHAT_ID"):
        raise PhoneError("The token file is incomplete. Run setup again. Nothing sent.")
    return out


def write_secret(token, chat_id, path=SECRET, root=ROOT):
    path = Path(path)
    if path.resolve().is_relative_to(Path(root).resolve()):
        raise PhoneError("Refused: that place is inside the vault.")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(f"TOKEN={token}\nCHAT_ID={chat_id}\nVAULT={Path(root).resolve()}\n")
    temp.replace(path)


def call(token, method, data=None, api=API):
    """One request. The token goes in the URL because Telegram requires it, so no error from here may carry the URL."""
    body = urllib.parse.urlencode(data or {}).encode()
    try:
        with urllib.request.urlopen(f"{api}/bot{token}/{method}", data=body, timeout=30) as r:
            out = json.loads(r.read())
    except urllib.error.HTTPError as err:
        try:
            said = json.loads(err.read()).get("description", "")
        except ValueError:
            said = ""
        raise PhoneError(scrub(f"Telegram said {err.code}: {said}", token)) from None
    except (OSError, ValueError) as err:
        raise PhoneError(scrub(f"Could not reach Telegram: {type(err).__name__}", token)) from None
    if not out.get("ok"):
        raise PhoneError(scrub(f'Telegram refused: {out.get("description", "")}', token))
    return out["result"]


# ---- finding Red lines ----

def keys_of(line):
    found = sorted({a.replace("-", "") for a in ACCESSION.findall(line)})
    return found or ["line:" + re.sub(r"\W+", " ", line).strip().lower()[:200]]


def red_lines(text):
    """The bullets under a heading Red, in either form the runs write."""
    out, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        if re.fullmatch(r"#+\s*\w.*|\*\*\w+\*\*", s):
            inside = bool(re.fullmatch(r"#+\s*Red\s*|\*\*Red\*\*", s))
        elif inside and line.startswith("- ") and s.rstrip(".") != "- Nothing":
            out.append(s)
    return out


def from_daily(root, now):
    out = []
    for path in sorted((root / "sensors/daily/runs").glob("*.json")):
        try:
            d = json.loads(path.read_text())
        except ValueError:
            continue
        where = f'Daily run, Journal/{d.get("today")}.md'
        brief = root / d.get("brief_path", "")
        lines = red_lines(brief.read_text()) if d.get("briefed") and brief.is_file() else []
        out += [{"keys": keys_of(x), "lines": [x], "where": where} for x in lines]
        covered = {k for x in lines for k in keys_of(x)}
        dead = now - path.stat().st_mtime > STALE_HOURS * 3600
        for item in d.get("items", []):
            if item.get("level") != "Red" or item["id"].replace("-", "") in covered or not (d.get("briefed") or dead):
                continue
            items = ", ".join(item.get("items") or [])
            out.append({"keys": keys_of(item["id"]), "where": f'{where}. The run did not finish, so nobody has read this', "lines": [
                f'- **{item.get("company", "")}, {item.get("rule", "")}.** Presumed Red from the item number alone, not read: {item.get("form", "")} items {items}. [{item.get("form", "")}, filed {item.get("filed", "")}]({item.get("url", "")}), {item["id"]}.']})
    return out


def from_events(root):
    out = []
    for run in sorted((root / "sensors/hunt/runs").glob("events-*")):
        report, order = run / "report.md", run / "order.json"
        if not report.is_file() or not order.is_file() or json.loads(order.read_text()).get("replay"):
            continue
        out += [{"keys": keys_of(x), "lines": [x], "where": f"Event run, sensors/hunt/runs/{run.name}/report.md"} for x in red_lines(report.read_text())]
    return out


def waiting(root, sent, now):
    """One event, one alert: lines that share a filing become one message. A line goes out unless all its filings have gone."""
    alerts = []
    for red in from_daily(root, now) + from_events(root):
        if all(k in sent for k in red["keys"]):
            continue
        twin = next((a for a in alerts if set(a["keys"]) & set(red["keys"])), None)
        if twin:
            twin["keys"] = sorted(set(twin["keys"]) | set(red["keys"]))
            twin["lines"] += [x for x in red["lines"] if x not in twin["lines"]]
        else:
            alerts.append(red)
    return alerts


def plain(line):
    text = re.sub(r"^- ", "", line)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"\1: \2", text)
    return re.sub(r"\*\*|`", "", text)


def message(alert, token=None):
    body = "\n\n".join(plain(x) for x in alert["lines"])
    tail = f'\n\n{alert["where"]}. An alert states a condition. It gives no advice.'
    if len(body) + len(tail) > LIMIT:
        body = body[:LIMIT - len(tail) - 30].rstrip() + " ... Rest in the source below."
    return scrub(f"RED ALERT\n\n{body}{tail}", token)


# ---- one pass ----

def load_sent(root):
    path = root / "sensors/phone/sent.json"
    return json.loads(path.read_text()) if path.exists() else {}


def save_sent(root, sent):
    path = root / "sensors/phone/sent.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(sent, indent=1) + "\n")
    temp.replace(path)


def note_failure(root, why):
    """A failed send is Orange under O16: one line a day in the Journal, and never on the phone."""
    today = dt.date.today().isoformat()
    path = root / "Journal" / f"{today}.md"
    old = path.read_text() if path.exists() else f"# {today}\n"
    if "Phone send FAILED" in old:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(old.rstrip("\n") + f"\n\nPhone send FAILED, O16: {why}\n")
    temp.replace(path)


@contextlib.contextmanager
def one_at_a_time(root):
    """The retry loop and a run's last step can meet. The second waits, then finds the Red already sent."""
    path = root / "sensors/phone/.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def send_pass(root=ROOT, secret=SECRET, api=API, now=None, any_root=False):
    """Marks a Red as sent only after Telegram says yes, so a failed send is retried. No Red waiting means no network at all."""
    root = Path(root)
    with one_at_a_time(root):
        return _send_pass(root, secret, api, now, any_root)


def _send_pass(root, secret, api, now, any_root):
    sent = load_sent(root)
    alerts = waiting(root, sent, now or time.time())
    if not alerts:
        return {"sent": 0, "waiting": 0, "error": None}
    try:
        cfg = read_secret(secret, root)
    except PhoneError as err:
        if not any_root:
            note_failure(root, f"{len(alerts)} Red waiting. {err}")
        return {"sent": 0, "waiting": len(alerts), "error": str(err)}
    if not any_root and cfg.get("VAULT") != str(root.resolve()):  # a scratch copy never reaches the phone
        return {"sent": 0, "waiting": len(alerts), "error": "This is not the vault named in the token file. Nothing sent."}
    done = 0
    for alert in alerts:
        try:
            call(cfg["TOKEN"], "sendMessage", {"chat_id": cfg["CHAT_ID"], "text": message(alert, cfg["TOKEN"]), "disable_web_page_preview": "true"}, api)
        except PhoneError as err:
            note_failure(root, f"{len(alerts) - done} Red waiting and will be retried. {err}")
            return {"sent": done, "waiting": len(alerts) - done, "error": str(err)}
        stamp = dt.datetime.now().isoformat(timespec="seconds")
        sent.update({k: {"at": stamp, "where": alert["where"]} for k in alert["keys"]})
        save_sent(root, sent)
        done += 1
        if done < len(alerts):
            time.sleep(1.1)  # Telegram asks for no more than one message a second in a chat
    return {"sent": done, "waiting": 0, "error": None}


def after_run(root=ROOT, secret=SECRET, api=API):
    """What the two runs call at their end. It never stops a run, and says nothing on a day with nothing to say."""
    try:
        out = send_pass(root, secret, api)
        if out["sent"] or out["error"]:
            print(f'Phone: {out["sent"]} Red sent, {out["waiting"]} waiting.' + (f' {out["error"]}' if out["error"] else ""))
        hits = scan_vault(root, secret)
        if hits:
            note_failure(root, f"Something shaped like a bot token is in {', '.join(hits[:5])}. Run phone.py check.")
            print(f"Phone: token check FAILED in {len(hits)} file(s). Run phone.py check.")
    except Exception as err:  # noqa: BLE001 a phone problem must never stop a run
        print(scrub(f"Phone: failed, {type(err).__name__}."))


# ---- keeping the token out ----

def holds_token(path, token=None):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return False
    return bool((token and token.encode() in data) or TOKEN_SHAPE.search(data))


def walk(top):
    top = Path(top)
    if top.is_file():
        yield top
        return
    for folder, dirs, files in os.walk(top):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield Path(folder) / name


def known_token(secret):
    try:
        return next((x.split("=", 1)[1] for x in Path(secret).read_text().splitlines() if x.startswith("TOKEN=")), None)
    except OSError:
        return None


def scan_vault(root=ROOT, secret=SECRET):
    token = known_token(secret)
    return [str(p.relative_to(root)) for p in walk(root) if holds_token(p, token)]


def check(root=ROOT, secret=SECRET, outside=None):
    """Prints file names only, never what matched. Returns 1 if anything is wrong."""
    secret, bad = Path(secret), []
    def line(ok, text):
        print(("ok   " if ok else "FAIL ") + text)
        if not ok:
            bad.append(text)
    if secret.exists():
        mode = stat.S_IMODE(secret.stat().st_mode)
        line(not secret.resolve().is_relative_to(Path(root).resolve()), "the token file is outside the vault")
        line(not mode & 0o077, f"only you can read the token file (mode {mode:o})")
        line(not stat.S_IMODE(secret.parent.stat().st_mode) & 0o077, "only you can open its folder")
    else:
        print("note no token file yet, so this checks for anything shaped like a token, not for your token")
    hits = scan_vault(root, secret)
    line(not hits, f"no token in the vault ({sum(1 for _ in walk(root))} files read, .venv skipped)")
    for name in hits:
        print(f"     found in {name}")
    token = known_token(secret)
    for place in (OUTSIDE if outside is None else outside):
        if not Path(place).exists():
            continue
        found = [p for p in walk(place) if holds_token(p, token)]
        line(not found, f"no token in {str(place).replace(str(Path.home()), '~')}")
        for p in found:
            print(f"     found in {str(p).replace(str(Path.home()), '~')}")
    return 1 if bad else 0


# ---- setup and the test ----

def setup(secret=SECRET):
    if not sys.stdin.isatty():
        print("Refused: run this in your own terminal, so the token is never in a session or a log.")
        return 2
    token = getpass.getpass("Paste the bot token (nothing shows as you paste): ").strip()
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{30,}", token):
        print("That does not look like a bot token. Nothing saved. Copy it again from BotFather.")
        return 1
    try:
        bot = call(token, "getMe")
        print(f'Found your bot: @{bot.get("username")}.')
        input(f'On your phone, open @{bot.get("username")}, tap Start, then press Enter here.')
        chats = [u["message"]["chat"] for u in call(token, "getUpdates") if u.get("message", {}).get("chat", {}).get("type") == "private"]
    except PhoneError as err:
        print(err)
        return 1
    if not chats:
        print("No message reached the bot yet. Tap Start, send it any word, and run setup again. Nothing saved.")
        return 1
    chat = chats[-1]
    if input(f'Send alerts to the Telegram account named "{chat.get("first_name", "")}"? y/n: ').strip().lower() != "y":
        print("Nothing saved.")
        return 1
    write_secret(token, chat["id"], secret)
    print("Saved outside the vault, readable only by you. Next: .venv/bin/python sensors/phone/phone.py test")
    return 0


TEST_LINE = ("- **TEST, made up, R1.** TEST ONLY. NOT A REAL ALERT. No kill line was crossed and no such filing exists. "
             "[Made-up 8-K, filed {day}](https://www.sec.gov/), 0000000000-00-000000.")


def test_root(folder, day):
    """A made-up run in a throwaway folder, so the test Red never touches the Journal or the real sent list."""
    root = Path(folder)
    runs = root / "sensors/daily/runs"
    runs.mkdir(parents=True)
    (runs / "test.brief.md").write_text("### Red\n\n" + TEST_LINE.format(day=day) + "\n\n### Orange\n\n- A made-up Orange that must not be sent.\n\n### Info\n\n- A made-up Info line that must not be sent.\n")
    (runs / "test.json").write_text(json.dumps({"today": day, "briefed": True, "brief_path": "sensors/daily/runs/test.brief.md", "items": []}))
    return root


def run_test(secret=SECRET, api=API):
    with tempfile.TemporaryDirectory() as folder:
        root = test_root(folder, dt.date.today().isoformat())
        first = send_pass(root, secret, api, any_root=True)
        second = send_pass(root, secret, api, any_root=True)
    if first["error"] or second["error"]:
        print(first["error"] or second["error"])
        return 1
    print(f'First pass sent {first["sent"]}. Second pass sent {second["sent"]}.')
    if (first["sent"], second["sent"]) != (1, 0):
        print("FAIL: expected 1 and then 0.")
        return 1
    print("Your phone should now show one message that starts RED ALERT and says TEST. Only your phone can confirm it arrived.")
    return 0


def main():
    args = sys.argv[1:]
    if args == ["setup"]:
        return setup()
    if args == ["test"]:
        return run_test()
    if args == ["check"]:
        return check()
    if args == ["send"]:
        out = send_pass()
        print(f'{out["sent"]} Red sent, {out["waiting"]} waiting.' + (f' {out["error"]}' if out["error"] else ""))
        return 1 if out["error"] else 0
    if len(args) == 3 and args[:2] == ["send", "--every"] and args[2].isdigit():
        while True:
            after_run()
            time.sleep(max(int(args[2]), 60))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
