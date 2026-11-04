"""Event run, the plain-script parts. No advice. The prompt is in Playbooks/Event run.md.

Run from the project root:
    .venv/bin/python sensors/hunt/events.py start      look for new Item 1.01 or 1.02 8-Ks in the graph, walk to theses and paper holdings
    .venv/bin/python sensors/hunt/events.py finish     check the run's readings.json, add the alerts to the end of today's Journal
    .venv/bin/python sensors/hunt/events.py start --replay ACCESSION[,ACCESSION]    treat past filings as new. Only on a scratch copy.

It makes one SEC request per company, then one per new filing. It never asks Yahoo and never changes a note.
A level is set by what the filing says and rests on a quote the script finds in the filing. How near the link is sets no level.
"""
import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE), str(ROOT / "sensors/radar"), str(ROOT / "sensors/edgar"), str(ROOT / "sensors/prices"), str(ROOT / "sensors/daily"), str(ROOT / "sensors/phone")]
import edgar  # noqa: E402
import phone  # noqa: E402
import radar  # noqa: E402
from collect import plain_text  # noqa: E402
from hunt import is_us, nice, squeeze  # noqa: E402
from publish import ADVICE  # noqa: E402

RUNS = HERE / "runs"
STATE = HERE / "events-state.json"
JOURNAL = ROOT / "Journal"
ITEMS = {"1.01", "1.02"}  # Owner's ruling, Nov. 4, 2026: 1.02 too, because a customer ending a deal is K2. Not 7.01 or 8.01.
ORDER = {"Red": 0, "Orange": 1, "Info": 2}
ALLOWED = {"Red": {"R1", "R2", "R3", "R4"}, "Orange": {"O2", "O14", "O15"}, "Info": {"I2", "I8"}}
FIRST_PASS = ("Orange", "8-K first pass")


def first_pass(items):
    """Rules/alerts.md: 1.02 with no 1.01 is presumed Red (R3), and only the owner can drop it. Everything else here is Orange until read."""
    return ("Red", "R3") if "1.02" in items and "1.01" not in items else FIRST_PASS
PRICE = re.compile(r"\b(share price|stock price|price target|closing price)\b", re.I)


class Refused(Exception):
    pass


def settings():
    return tomllib.loads((HERE / "settings.toml").read_text())["events"]


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"baseline": None, "seen": [], "alerts": []}


def paper_tickers(path):
    """Positions from the paper portfolio's table. Empty is a fine answer. A broken note stops the run."""
    text = Path(path).read_text()
    sect = re.search(r"^## Positions\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not sect:
        raise Refused(f"{path} has no Positions section.")
    rows = [r for r in sect.group(1).splitlines() if r.startswith("|")][2:]
    return [r.strip("|").split("|")[0].strip() for r in rows if r.strip("| ")]


def note_by_ticker(folder):
    out = {}
    for name in radar.note_names(folder):
        meta = radar.front_fields(radar.split_note((Path(folder) / f"{name}.md").read_text())[0])
        tick = meta.get("ticker", "").strip()
        if tick:
            out[tick.upper()] = name
    return out


def has_kill_lines(path):
    return path.exists() and bool(re.search(r"^\| \*\*K\d+\*\* \|", path.read_text(), re.M))


def find_targets(root=ROOT, cfg=None):
    """Companies with a thesis (owner's ruling, Nov. 4, 2026: only notes with kill lines count) or a paper holding."""
    cfg = cfg or settings()
    out, problems = {}, []
    for c in tomllib.loads((root / cfg["theses"]).read_text())["company"]:
        if has_kill_lines(root / c["kill"]):
            out[c["name"]] = {"name": c["name"], "why": ["thesis, " + c["thesis_status"]], "note": c["note"], "thesis": c["thesis"], "kill": c["kill"]}
    names = note_by_ticker(root / "Companies")
    for tick in paper_tickers(root / cfg["portfolio"]):
        name = names.get(tick.upper())
        if not name:
            problems.append(f"{tick} is held on paper but has no note in Companies/, so nothing can walk to it.")
            continue
        out.setdefault(name, {"name": name, "why": [], "note": f"Companies/{name}.md", "thesis": None, "kill": None})["why"].append("held on paper")
    return out, problems


def reach(links, filer, targets):
    """Each target the walk reaches from the filer, with every path. Filer itself is left out: the daily run reads a watched company's own 8-Ks."""
    rows = radar.walk(links, filer)
    found = {}
    for row in rows:
        if row["node"] in targets and row["node"] != filer:
            found.setdefault(row["node"], []).append(row)
    out = []
    for name, rows_ in found.items():
        step = min(r["step"] for r in rows_)
        paths = []
        for r in rows_:
            if r["step"] == 1:
                paths.append({"step": 1, "text": radar.relation(r), "chain": r["chain"], "what": r["what"], "evidence": r["evidence"], "weak": r["weak"], "source": r["source"]})
            else:
                first = next((x for x in rows if x["step"] == 1 and x["node"] == r["via"] and x["chain"] == r["chain"]), None)
                paths.append({"step": 2, "text": f'{radar.relation(first) if first else filer + " to " + r["via"]}; then {radar.relation(r)}', "chain": r["chain"], "what": r["what"],
                              "evidence": r["evidence"], "weak": r["weak"] or bool(first and first["weak"]), "source": r["source"]})
        out.append({"target": name, "step": step, "paths": paths})
    return sorted(out, key=lambda x: x["target"])


def filers(paths, client):
    """Graph companies SEC can answer for: US filers, and the rest named and left out."""
    table = radar.ticker_table(paths)
    by_cik = radar.map_nodes(paths, table)
    links, problems = radar.read_links(paths.companies)
    graph = {x for link in links for x in (link["a"], link["b"])}
    found, left = {}, []
    for cik, name in sorted(by_cik.items(), key=lambda kv: kv[1]):
        if name not in graph:
            continue
        sub = json.loads(client.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
        us, where = is_us(sub)
        if us:
            found[name] = {"cik": cik, "sub": sub}
        else:
            left.append(f"{name} ({where or 'state blank, no 10-K or 10-Q'})")
    left += [f"{n} (no SEC filer found)" for n in sorted(graph) if n not in by_cik.values()]
    return found, left, links, problems


def new_items(name, info, seen, baseline, replay):
    r = info["sub"]["filings"]["recent"]
    out = []
    for form, day, items, acc, doc in zip(r["form"], r["filingDate"], r["items"], r["accessionNumber"], r["primaryDocument"]):
        if replay:
            if acc not in replay:
                continue
        elif not form.startswith("8-K") or not ITEMS & set((items or "").split(",")) or acc in seen or day < baseline:
            continue
        out.append({"company": name, "cik": info["cik"], "form": form, "filed": day, "items": items.split(","), "accession": acc,
                    "url": f'https://www.sec.gov/Archives/edgar/data/{info["cik"]}/{acc.replace("-", "")}/{doc}'})
    return out


def quiet_line(today, count, note=""):
    return f"Event run, {nice(today)}: {count} graph companies checked, no new Item 1.01 or 1.02 8-K.{note}"


def append_journal(today, text):
    path = JOURNAL / f"{today}.md"
    old = path.read_text() if path.exists() else f"# {today}\n"
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(old.rstrip("\n") + "\n\n" + text.strip() + "\n")
    temp.replace(path)


def journal_hits(event, folder=JOURNAL):
    """Journal files that already name this filing, so a run need not read the whole Journal."""
    needles = (event["accession"], event["accession"].replace("-", ""))
    return [p.name for p in sorted(Path(folder).glob("*.md")) if any(n in p.read_text() for n in needles)]


def start(today=None, replay=None, client=None):
    today = today or dt.date.today().isoformat()
    s = state()
    paths = radar.Paths()
    if client is None:
        sec = edgar.load_settings()
        client = edgar.SecClient(sec["user_agent"], sec["rate"])
    targets, problems = find_targets()
    found, left, links, link_problems = filers(paths, client)
    problems += link_problems
    first_run = not s["baseline"] and not replay
    if first_run:
        s["baseline"] = today
    events = []
    for name, info in found.items():
        events += new_items(name, info, set(s["seen"]), s["baseline"] or today, set(replay or []))
    if replay and not events:
        raise Refused("None of those accessions is on the filing lists.")
    s["last_run"] = today
    if not events:
        STATE.write_text(json.dumps(s, indent=1) + "\n")
        note = " First run: only filings from today on count." if first_run else ""
        note += "".join(f" Problem: {p}" for p in problems)
        append_journal(today, quiet_line(today, len(found), note))
        print("QUIET: " + quiet_line(today, len(found), note))
        return None
    run = RUNS / f"events-{today}"
    (run / "docs").mkdir(parents=True, exist_ok=True)
    for e in events:
        e["reached"] = reach(links, e["company"], targets)
        e["own_daily"] = e["company"] in targets
        e["doc"] = str((run / "docs" / f'{e["accession"]}.txt').relative_to(ROOT))
        (ROOT / e["doc"]).write_text(plain_text(client.get(e["url"])))
        e["first_pass"], e["first_rule"] = first_pass(e["items"])
        e["journal_hits"] = journal_hits(e)
        e["other_items"] = [i for i in e["items"] if i not in ITEMS]
    STATE.write_text(json.dumps(s, indent=1) + "\n")
    rows = sum(len(e["reached"]) for e in events)
    order = {"today": today, "replay": bool(replay), "events": sorted(events, key=lambda e: (e["filed"], e["company"])), "targets": targets, "graph_filers": sorted(found), "left_out": left,
             "problems": problems, "already_alerted": s["alerts"][-30:], "readings": str((run / "readings.json").relative_to(ROOT))}
    (run / "order.json").write_text(json.dumps(order, indent=1) + "\n")
    print(f'OPEN: {(run / "order.json").relative_to(ROOT)}')
    print(f"{len(events)} new filing(s), {rows} reading(s) to give.")
    return run


def open_run():
    runs = sorted((p for p in RUNS.glob("events-*") if (p / "order.json").exists() and not (p / "closed.json").exists()), reverse=True)
    if not runs:
        raise Refused("No open run. Run start first.")
    return runs[0]


def check(order, readings):
    problems = []
    wanted = {(e["accession"], r["target"]) for e in order["events"] for r in e["reached"]}
    got = {(x.get("accession"), x.get("target")) for x in readings}
    problems += [f"No reading for {a} and {t}." for a, t in sorted(wanted - got)]
    problems += [f"{a} and {t} is not a pair the walk reached." for a, t in sorted(got - wanted, key=str)]
    docs = {e["accession"]: e["doc"] for e in order["events"]}
    known = set(docs)
    firsts = {e["accession"]: first_pass(e["items"]) for e in order["events"]}
    targets = order.get("targets", {})
    for x in readings:
        tag = f'{x.get("accession")}, {x.get("target")}'
        level, rule = x.get("level"), x.get("rule")
        says = x.get("says", "") or ""
        hit = ADVICE.search(says)
        if hit:
            problems.append(f'{tag}: reads as advice ("{hit.group(0)}"): {says[:80]}')
        if PRICE.search(says):
            problems.append(f"{tag}: names a price: {says[:80]}")
        if x.get("same_event_as") and x["same_event_as"] not in known:
            problems.append(f"{tag}: same_event_as names a filing not in this run.")
        first = firsts.get(x.get("accession"), FIRST_PASS)
        if x.get("read") is False:
            if (level, rule) != first:
                problems.append(f'{tag}: a filing not read keeps its first pass: level "{first[0]}", rule "{first[1]}".')
            continue
        if first[0] == "Red" and level != "Red":
            problems.append(f"{tag}: item 1.02 with no 1.01 stays Red under R3. Only the owner can drop it. Say what ended in \"says\".")
            continue
        if rule == "R3" and first[0] != "Red":
            problems.append(f"{tag}: R3 is only for item 1.02 with no 1.01.")
            continue
        if level not in ALLOWED or rule not in ALLOWED[level]:
            problems.append(f'{tag}: level {level} with rule {rule}. Allowed: ' + "; ".join(f"{k} {sorted(v)}" for k, v in ALLOWED.items()))
            continue
        quote = squeeze(x.get("quote", "") or "")
        if len(quote) < 40:
            problems.append(f"{tag}: quote the filing, at least 40 characters, word for word.")
        elif x.get("accession") in docs and quote not in squeeze((ROOT / docs[x["accession"]]).read_text()):
            problems.append(f"{tag}: the quote is not in {docs[x['accession']]}. Copy it word for word.")
        if not says.strip():
            problems.append(f"{tag}: say what the filing means for the claim in one sentence.")
        if rule == "R1" and not re.search(r"\bK\d\b", says):
            problems.append(f"{tag}: an R1 names its kill line.")
        numbered = targets.get(x.get("target"), {"kill": True}).get("kill")  # a paper holding may have no numbered claims
        if rule in ("R2", "O2") and numbered and not re.search(r"\bC\d\b", says):
            problems.append(f"{tag}: {rule} names its claim, C1 to C8.")
        if rule == "R2" and "appears broken" not in says:
            problems.append(f'{tag}: an R2 says "appears broken". The owner rules.')
    return problems


def grouped(order, readings):
    """One event, one alert. Filings tied by same_event_as make one group per target, at the group's highest level."""
    events = {e["accession"]: e for e in order["events"]}
    groups = {}
    for x in readings:
        key = (x.get("same_event_as") or x["accession"], x["target"])
        groups.setdefault(key, []).append(x)
    # a filing others point at joins its own group by the key above
    out = []
    for (_, target), rows in groups.items():
        rows.sort(key=lambda r: ORDER[r["level"]])
        top = rows[0]
        parts = []
        for r in rows:
            e = events[r["accession"]]
            path = next(p for g in e["reached"] if g["target"] == target for p in g["paths"])
            if r.get("read") is False:
                parts.append(f'{e["company"]} filed it, not read ([{e["form"]}, filed {nice(e["filed"])}]({e["url"]}), {e["accession"]})')
            else:
                parts.append(f'{e["company"]}: "{squeeze(r["quote"])}" ([{e["form"]}, filed {nice(e["filed"])}]({e["url"]}), {e["accession"]}; link: {path["text"]}, {path["evidence"]})')
        out.append({"level": top["level"], "rule": top["rule"], "target": target, "says": top.get("says", "not read"), "parts": parts, "filers": [events[r["accession"]]["company"] for r in rows]})
    return sorted(out, key=lambda a: ORDER[a["level"]])


def alert_line(a):
    return f'- **{a["target"]}, {a["rule"]}.** {a["says"]} ' + " ".join(a["parts"])


def render(order, alerts):
    events = order["events"]
    no_reach = [e for e in events if not e["reached"]]
    out = [f'# Event run, {nice(order["today"])}', "", "*Item 1.01 and 1.02 8-Ks in our graph, walked to the companies with a thesis or a paper holding. Facts only. Recommends nothing. A link does not mean the event reaches that company.*", ""]
    if order["replay"]:
        out += ["**A replay of past filings on today's graph, thesis and kill lines. Written with hindsight. Nothing was held.**", ""]
    for level in ("Red", "Orange", "Info"):
        lines = [alert_line(a) for a in alerts if a["level"] == level]
        out += [f"## {level}", ""] + (lines or ["- Nothing."]) + [""]
    if no_reach:
        out += ["## Reached nobody", ""] + [f'- {e["company"]}, [{e["form"]}, filed {nice(e["filed"])}]({e["url"]}), {e["accession"]}.' for e in no_reach] + [""]
    out += ["## Who was checked", "", "Graph companies read: " + ", ".join(order["graph_filers"]) + ".", "", "Left out: " + ", ".join(order["left_out"]) + ".", "",
            "Targets: " + ", ".join(f'{t["name"]} ({"; ".join(t["why"])})' for t in order["targets"].values()) + ".", ""]
    out += [f"- Problem: {p}" for p in order["problems"]]
    return "\n".join(out) + "\n"


def finish():
    run = open_run()
    order = json.loads((run / "order.json").read_text())
    path = run / "readings.json"
    readings = json.loads(path.read_text()) if path.exists() else []
    problems = check(order, readings)
    if problems:
        print("REFUSED. Fix these in readings.json and run finish again:")
        for p in problems:
            print("  " + p)
        return 1
    alerts = grouped(order, readings)
    (run / "report.md").write_text(render(order, alerts))
    today = order["today"]
    red, orange, info = ([a for a in alerts if a["level"] == x] for x in ("Red", "Orange", "Info"))
    body = ""
    if red:
        body += "\n**Red**\n\n" + "\n".join(alert_line(a) for a in red) + "\n"
    if orange:
        body += "\n**Orange**\n\n" + "\n".join(alert_line(a) for a in orange) + "\n"
    if not body:
        body = "\nNo Orange and no Red.\n"
    left = "\n".join(f"- {p}" for p in order["problems"]) or "- Nothing."
    append_journal(today, f"## Session: event run\n\n### What we did\n\n- Read {len(order['events'])} new Item 1.01 or 1.02 8-K(s) and walked the graph: {len(red)} Red, {len(orange)} Orange, {len(info)} Info (calc.). Every reading is in `{(run / 'report.md').relative_to(ROOT)}`.\n{body}\n### What we decided\n\n- Nothing. The run recommends nothing and made no investing decision.\n\n### What we left open\n\n{left}\n")
    s = state()
    s["seen"] += [e["accession"] for e in order["events"]]
    s["alerts"] += [alert_line(a)[:300] for a in red + orange]
    STATE.write_text(json.dumps(s, indent=1) + "\n")
    (run / "closed.json").write_text(json.dumps({"closed": today}) + "\n")
    print(f"Done. Journal/{today}.md: {len(red)} Red, {len(orange)} Orange, {len(info)} Info.")
    return 0


def main():
    args = sys.argv[1:]
    try:
        if args[:1] == ["start"]:
            replay = args[2].split(",") if len(args) == 3 and args[1] == "--replay" else None
            if len(args) != 1 and not replay:
                print(__doc__)
                return 2
            start(replay=replay)
            phone.after_run()  # a quiet day still retries a Red that could not be sent earlier
            return 0
        if args == ["finish"]:
            code = finish()
            if code == 0:
                phone.after_run()  # last step: Red lines go to the phone. Plain Python, and it cannot stop the run.
            return code
        print(__doc__)
        return 2
    except (Refused, edgar.EdgarError) as err:
        print("STOPPED: " + str(err))
        return 1


if __name__ == "__main__":
    sys.exit(main())
