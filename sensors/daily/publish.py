"""Daily run, part 2: check the brief, put it at the top of today's Journal, then file what is new in Inbox/.

Run from the project root, with no arguments:
    .venv/bin/python sensors/daily/publish.py

It works on the newest digest not yet briefed. On a quiet digest it writes the one line itself. It refuses a brief
that recommends, shows a price move, lacks a source or date, leaves out a Red or Orange item, or moves a presumed Red
out of Red. It only ever adds to the Journal: the earlier text stays exactly as it was.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE), str(ROOT / "sensors" / "phone")]
from collect import RUNS, nice  # noqa: E402
import phone  # noqa: E402

JOURNAL = ROOT / "Journal"
INBOX = ROOT / "Inbox"
DATE = re.compile(r"\b(Jan|Feb|Mar|March|Apr|April|May|June|July|Aug|Sept|Oct|Nov|Dec)\.? \d{1,2}, \d{4}\b|\b\d{4}-\d{2}-\d{2}\b")
SOURCE = re.compile(r"\]\((https?://|[^)]+\.\w+\))|`[^`]+\.\w+`")
ADVICE = re.compile(r"\b(recommend\w*|suggest\w*|should|consider|you may want|worth (buying|selling)|(buy|sell|trim|hold)(?![-\w]))\b", re.I)
MOVE = re.compile(r"\b(rose|fell|jumped|dropped|gained|lost|up|down)\b|%", re.I)


class Refused(Exception):
    pass


def newest_open():
    for path in sorted(RUNS.glob("*.json"), reverse=True):
        digest = json.loads(path.read_text())
        if not digest.get("briefed"):
            return path, digest
    raise Refused("No digest waiting. Run collect.py first.")


def quiet_line(d):
    s = d["stands"]
    since = f'the brief of {nice(d["since"])}' if d.get("since") else "the last radar run"
    fetched = nice(d["sec_list"]["fetched"]) if d["sec_list"].get("fetched") else "date unknown"
    return (f'**Daily brief, {nice(d["today"])}: nothing needs me.** Since {since}: no new filing, no line crossed on a saved close, no date moved '
            f'([SEC filing list, fetched {fetched}]({d["sec_list"].get("url")}); [last saved close, {nice(s["date"])}, {s["source_label"]}]({s["source_url"]}); '
            f'`{d["radar_report"]}`, {nice(d["today"])}). {d["not_read"]}')


def sections(text):
    parts, current = {}, None
    for line in text.splitlines():
        m = re.fullmatch(r"#+\s*(Red|Orange|Info)\s*", line.strip())
        if m:
            current = m.group(1)
            parts[current] = []
        elif current:
            parts[current].append(line)
    return parts


def check(text, d):
    problems = []
    parts = sections(text)
    if list(parts) != ["Red", "Orange", "Info"]:
        problems.append("The brief needs three parts in this order: ### Red, ### Orange, ### Info.")
        return problems
    bullets = [line for body in parts.values() for line in body if line.startswith("- ") and line.strip() != "- Nothing."]
    if not bullets:
        problems.append("The digest is not quiet, but the brief has no line.")
    for line in bullets:
        if not SOURCE.search(line):
            problems.append(f"No source: {line[:90]}")
        if not DATE.search(line):
            problems.append(f"No date: {line[:90]}")
    for line in text.splitlines():
        hit = ADVICE.search(line)
        if hit:
            problems.append(f'Reads as advice ("{hit.group(0)}"): {line[:90]}')
        if re.search(r"\bclose\b", line, re.I) and MOVE.search(line):
            problems.append(f"Shows a price move: {line[:90]}")
    for item in d["items"]:
        if item["level"] == "Info":
            continue
        token = item.get("token") or item["id"].split(":", 1)[-1]
        if token not in text and token.replace("-", "") not in text:
            problems.append(f'{item["level"]} item left out, name it by "{token}": {item["summary"][:70]}')
        red = "\n".join(parts["Red"])
        if item["rule"] == "R3" and token not in red and token.replace("-", "") not in red:
            problems.append(f"{token} is presumed Red until the owner rules. It stays in Red.")
    return problems


def add_to_journal(block, record, day):
    """Under the date heading, then the session record at the end. Earlier text is kept byte for byte."""
    path = JOURNAL / f"{day}.md"
    old = path.read_text() if path.exists() else f"# {day}\n"
    first, _, rest = old.partition("\n")
    new = f"{first}\n\n{block.strip()}\n\n{rest.lstrip(chr(10))}".rstrip("\n") + "\n\n" + record.strip() + "\n"
    if rest.strip() not in new:
        raise Refused("The Journal's earlier text would change. Nothing written.")
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(new)
    temp.replace(path)
    return path


def session_record(d, quiet):
    ran = ", ".join(f'{r["name"]} {"ok" if r["ok"] else "FAILED"}' for r in d["sensors"])
    time = d["run_local"][11:16]
    left = "- Nothing." if quiet else "- What the brief above lists, for me to read."
    return (f"## Session: daily run, {time}\n\n### What we did\n\n- Ran the daily run: {ran}. Digest: `sensors/daily/runs/{d['stem']}.json`. {d['not_read']}\n\n"
            f"### What we decided\n\n- Nothing. The run recommends nothing and made no investing decision.\n\n### What we left open\n\n{left}")


def inbox_note(item):
    ticker = item.get("ticker") or "GLW"
    form = str(item["form"]).replace("/", "-")
    tail = f'{item["filed"]}' if item.get("roll_up") else item["id"]
    path = INBOX / f'{item["filed"]} {ticker} {form} {tail}.md'
    if path.exists():
        return None
    lines = ["---", f"ticker: {ticker}", f'company: "{item.get("company", "")}"', f'form: "{item["form"]}"', f'filed: "{item["filed"]}"']
    if not item.get("roll_up"):
        lines.append(f'accession: {item["id"]}')
    lines += ["sources:", f'  - "{item["url"]}"', "---", "", f'# {item.get("company", "")} {item["form"]}, filed {nice(item["filed"])}', "",
              f'*Written by `sensors/daily/publish.py`. Company: [[{item.get("company", "")}]]. Source: [{item["form"]}, filed {nice(item["filed"])}]({item["url"]}).*', "",
              "A dated record that the filing came. Not a view on the company.", "", item["summary"], ""]
    if item.get("lines"):
        lines += [f"- {line}" for line in item["lines"]] + [""]
    path.write_text("\n".join(lines))
    return path.name


def publish():
    path, d = newest_open()
    day = d["today"]
    journal = JOURNAL / f"{day}.md"
    already = journal.exists() and re.search(r"^(\*\*|## )Daily brief, ", journal.read_text(), re.M)
    if d["quiet"]:
        if already:  # a second quiet run the same day adds no second line
            block = None
        else:
            block = quiet_line(d)
    else:
        brief = ROOT / d["brief_path"]
        if not brief.exists():
            raise Refused(f'Write the brief to {d["brief_path"]} first.')
        text = brief.read_text()
        problems = check(text, d)
        if problems:
            raise Refused("\n".join(problems))
        block = f'## Daily brief, {nice(day)}, {d["run_local"][11:16]}\n\n{text.strip()}'
    if block:
        add_to_journal(block, session_record(d, d["quiet"]), day)
    filed = [name for name in (inbox_note(i) for i in d["items"] if i.get("file_in_inbox")) if name]
    d["briefed"] = True
    path.write_text(json.dumps(d, indent=1, ensure_ascii=False))
    state_path = HERE / "state.json"
    state = json.loads(state_path.read_text())
    state["last_brief"] = day
    state_path.write_text(json.dumps(state, indent=1, ensure_ascii=False))
    return {"journal": str(journal.relative_to(ROOT)), "line": block, "filed": filed}


def main():
    try:
        out = publish()
    except Refused as err:
        sys.exit(f"Refused:\n{err}")
    print(f'Journal: {out["journal"]}' if out["line"] else "Second quiet run today: nothing added.")
    if out["line"]:
        print(out["line"])
    print(f'Filed in Inbox: {len(out["filed"])}')
    for name in out["filed"]:
        print(f"  {name}")
    phone.after_run()  # last step: Red lines go to the phone. Plain Python, and it cannot stop the run.


if __name__ == "__main__":
    main()
