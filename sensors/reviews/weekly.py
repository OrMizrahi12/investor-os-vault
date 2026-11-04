"""Weekly thesis check, the plain-script parts. No advice. The prompt is in Playbooks/Weekly thesis check.md.

Run from the project root:
    .venv/bin/python sensors/reviews/weekly.py start        open a run: which companies, since when, what to search, K9's reading
    .venv/bin/python sensors/reviews/weekly.py sec <url>    save one sec.gov document as plain text, through the EDGAR client
    .venv/bin/python sensors/reviews/weekly.py finish       check the report, add it to the end of today's Journal, close the run

Writes only under sensors/reviews/ and at the end of today's Journal. It sends nothing and never asks Yahoo.
"""

import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "sensors" / "daily"))
import quarterly  # noqa: E402
from collect import plain_text  # noqa: E402
from publish import ADVICE, DATE, MOVE, SOURCE  # noqa: E402

RUNS = HERE / "runs"
STATE = HERE / "weekly-state.json"
RULE = re.compile(r"\b[RO]\d{1,2}\b")


class Refused(Exception):
    pass


def theses():
    return tomllib.loads((HERE / "theses.toml").read_text())


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"last": None, "alerts": []}


def has_kill_lines(path):
    """Owner's ruling, Nov. 4, 2026: only notes with kill lines count."""
    return path.exists() and bool(re.search(r"^\| \*\*K\d+\*\* \|", path.read_text(), re.M))


def report_shell(companies, since, today):
    out = [f"# Weekly thesis check, {today}", "", f"New since {since}. Facts only. Recommends nothing.", ""]
    for c in companies:
        out += [f'## {c["name"]}', "", "| Id | New this week? | What it says, or \"nothing new\" | Source and date |", "|---|---|---|---|"]
        out += [f"| {i} |  |  |  |" for i in c["claims"] + c["lines"]]
        out += ["", "### Red", "", "- Nothing.", "", "### Orange", "", "- Nothing.", "", "### Info", "", "- Nothing.", "", "### Unread leads", "", "- Nothing.", ""]
    return "\n".join(out)


def start(today=None, k9=quarterly.k9_reading):
    today = today or dt.date.today().isoformat()
    s, cfg = state(), theses()
    since = s["last"] or (dt.date.fromisoformat(today) - dt.timedelta(days=7)).isoformat()
    known = {c["kill"] for c in cfg["company"]}
    companies = [c for c in cfg["company"] if has_kill_lines(ROOT / c["kill"])]
    problems = [f'{c["name"]} is listed, but its kill note has no kill lines, so it is skipped.' for c in cfg["company"] if c not in companies]
    problems += [f"{p.relative_to(ROOT)} has no entry in sensors/reviews/theses.toml, so this run does not cover it."
                for p in sorted((ROOT / "Research").glob("* kill criteria.md")) if str(p.relative_to(ROOT)) not in known]
    if not companies:
        print("NO COMPANY WITH A THESIS.")
        return None
    run = RUNS / f"weekly-{today}"
    (run / "docs").mkdir(parents=True, exist_ok=True)
    inbox = {}
    for c in companies:
        inbox[c["name"]] = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "Inbox").glob(f'* {c["ticker"]} *.md')) if p.name[:10] >= since]
    try:
        reading = k9()
    except Exception as err:  # the search can still run
        reading = {"problem": f"{type(err).__name__}: {err}"[:200]}
    order = {"today": today, "since": since, "companies": companies, "open_domains": cfg["open_domains"], "new_inbox": inbox, "k9": reading,
             "already_alerted": s["alerts"][-30:], "problems": problems, "report": str((run / "report.md").relative_to(ROOT))}
    (run / "order.json").write_text(json.dumps(order, indent=1) + "\n")
    if not (run / "report.md").exists():
        (run / "report.md").write_text(report_shell(companies, since, today))
    print(f'OPEN: {(run / "order.json").relative_to(ROOT)}')
    return run


def open_run():
    runs = sorted((p for p in RUNS.glob("weekly-*") if (p / "order.json").exists() and not (p / "closed.json").exists()), reverse=True)
    if not runs:
        raise Refused("No open run. Run start first.")
    return runs[0]


def save_sec(url):
    parts = urlparse(url)
    if parts.netloc != "www.sec.gov" or not parts.path.startswith("/Archives/"):
        raise Refused("Only www.sec.gov/Archives documents go through here.")
    run = open_run()
    settings = quarterly.edgar.load_settings()
    client = quarterly.edgar.SecClient(settings["user_agent"], settings["rate"])
    path = run / "docs" / (re.sub(r"\W+", "-", parts.path.split("/data/")[-1])[:120] + ".txt")
    path.write_text(plain_text(client.get(url)))
    print(path.relative_to(ROOT))


def part(text, name):
    m = re.search(rf"^### {name}\s*\n(.*?)(?=^#{{2,3}} |\Z)", text, re.S | re.M)
    return [] if not m else [ln for ln in m.group(1).splitlines() if ln.startswith("- ") and ln.strip() != "- Nothing."]


def check_report(text, order):
    problems = []
    for company in order["companies"]:
        for i in company["claims"] + company["lines"]:
            row = re.search(rf"^\| {i} \|(.*)\|\s*$", text, re.M)
            cells = [c.strip() for c in row.group(1).split("|")] if row else []
            if not row or not all(cells[:2]):
                problems.append(f"{i} has no reading. Fill its row, even with \"nothing new\".")
    for line in text.splitlines():
        hit = ADVICE.search(line)
        if hit:
            problems.append(f'Reads as advice ("{hit.group(0)}"): {line[:90]}')
        if re.search(r"\b(close|share price|stock price)\b", line, re.I) and MOVE.search(line):
            problems.append(f"Shows a price move: {line[:90]}")
    for level in ("Red", "Orange"):
        for line in part(text, level):
            if not RULE.search(line):
                problems.append(f"No rule ID from Rules/alerts.md: {line[:90]}")
            if not SOURCE.search(line):
                problems.append(f"No source: {line[:90]}")
            if not DATE.search(line):
                problems.append(f"No date: {line[:90]}")
            if level == "Red" and re.search(r"\bR2\b", line) and "appears broken" not in line:
                problems.append(f'An R2 says "appears broken". The owner rules: {line[:90]}')
    return problems


def finish():
    run = open_run()
    order = json.loads((run / "order.json").read_text())
    text = (run / "report.md").read_text()
    problems = check_report(text, order)
    if problems:
        print("REFUSED. Fix these in the report and run finish again:")
        for p in problems:
            print("  " + p)
        return 1
    red, orange, info, unread = (part(text, n) for n in ("Red", "Orange", "Info", "Unread leads"))
    today, name = order["today"], ", ".join(c["name"] for c in order["companies"])
    alerts = ""
    if red:
        alerts += "\n**Red**\n\n" + "\n".join(red) + "\n"
    if orange:
        alerts += "\n**Orange**\n\n" + "\n".join(orange) + "\n"
    if not alerts:
        alerts = "\nNo Orange and no Red.\n"
    left = [f"- {len(unread)} lead(s) not read, so they raised nothing. List: `{order['report']}`."] if unread else []
    left += [f"- {p}" for p in order["problems"]]
    journal = quarterly.JOURNAL / f"{today}.md"
    old = journal.read_text() if journal.exists() else f"# {today}\n"
    block = (f"## Session: weekly thesis check, {name}\n\n### What we did\n\n- Checked each claim and kill line against what is new since {order['since']}. "
             f"{len(info)} Info line(s) and every reading are in `{order['report']}`.\n{alerts}\n### What we decided\n\n- Nothing. The run recommends nothing and made no investing decision.\n\n"
             f"### What we left open\n\n" + ("\n".join(left) if left else "- Nothing.") + "\n")
    temp = journal.with_name(journal.name + ".tmp")
    temp.write_text(old.rstrip("\n") + "\n\n" + block)
    temp.replace(journal)
    s = state()
    s["last"] = today
    s["alerts"] += [ln[:300] for ln in red + orange]
    STATE.write_text(json.dumps(s, indent=1) + "\n")
    (run / "closed.json").write_text(json.dumps({"closed": today}) + "\n")
    print(f"Done. Journal/{today}.md: {len(red)} Red, {len(orange)} Orange.")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "start":
            start()
            return 0
        if cmd == "sec" and len(sys.argv) == 3:
            save_sec(sys.argv[2])
            return 0
        if cmd == "finish":
            return finish()
        print(__doc__)
        return 2
    except Refused as err:
        print("STOPPED: " + str(err))
        return 1


if __name__ == "__main__":
    sys.exit(main())
