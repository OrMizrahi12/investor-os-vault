"""Daily run, part 1: run the sensors as plain scripts and work out what is new since the last brief.

Run from the project root, with no arguments:
    .venv/bin/python sensors/daily/collect.py

It runs the 8-K watcher and the radar, one at a time, and writes a digest to
sensors/daily/runs/YYYY-MM-DD-NN.json. Each item carries a first-pass level from the map in Rules/alerts.md.
A first pass is what a form or item number says before anyone opens the filing. It sends nothing and recommends nothing.

It never runs the price sensor and never asks Yahoo: my decision of Nov. 3, 2026 is by hand (Rules/alerts.md, decision 7).
It reads the saved closes, and only to see whether a line was crossed. A close saved by hand is checked on the next run,
with every day since the last one it saw, so a crossing between saves shows up late, not never.

Sensors remember what they reported, so a digest not yet briefed is carried into the next one.
publish.py marks a digest as briefed. Nothing is lost if a run dies between the two.
"""

import datetime as dt
import html
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "sensors" / "alerts"))
sys.path.insert(0, str(ROOT / "sensors" / "edgar"))
sys.path.insert(0, str(ROOT / "sensors" / "prices"))
import alertmap  # noqa: E402
import edgar  # noqa: E402
import prices  # noqa: E402

RUNS = HERE / "runs"
STATE = HERE / "state.json"
SEEN = ROOT / "sensors" / "8k-watch" / "seen.json"
RADAR_RUNS = ROOT / "sensors" / "radar" / "runs"
VALUATION_RUNS = ROOT / "sensors" / "valuation" / "runs"
PORTFOLIO = ROOT / "Portfolio"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
SENSORS = [("8-K watcher", ["sensors/8k-watch/watch.py"]),
           ("Radar", ["sensors/radar/radar.py"])]
EIGHT_K = {"8-K", "8-K/A"}
INSIDER = {"3", "4", "5", "144", "3/A", "4/A", "5/A", "144/A"}
ORDER = {"Red": 0, "Orange": 1, "Info": 2}
NOT_READ = "News, calls and customers' releases are not read by this run."


def nice(day):
    d = dt.date.fromisoformat(day[:10])
    month = {5: "May", 6: "June", 7: "July", 9: "Sept."}.get(d.month, d.strftime("%b") + ".")
    return f"{month} {d.day}, {d.year}"


def newest(folder):
    files = sorted(Path(folder).glob("*.json"))
    return json.loads(files[-1].read_text()) if files else None


def eight_k_level(items):
    """The worst first pass among the items. Red first, as in R3. An item off the map stays Orange until read."""
    items = list(items or [])
    if not items:
        return "Orange", "8-K first pass", "The items could not be read."
    worst, why = "Info", []
    for item in items:
        level, note = alertmap.ITEMS.get(item, ("Orange", "Not on the map, so Orange until read."))
        if item == "1.02" and "1.01" not in items:
            level, note = "Red", "1.02 with no 1.01."
        why.append(f"{item}: {note}")
        if ORDER[level] < ORDER[worst]:
            worst = level
    if worst == "Red":
        rule = "R3"
    elif "3.02" in items:
        rule = "O3"
    elif "5.02" in items:
        rule = "O11"
    else:
        rule = "8-K first pass"
    return worst, rule, " ".join(why)


def form_level(form, summary=""):
    """Level, rule and whether a person or a session must read it, for anything that is not an 8-K."""
    if form in {"10-K/A", "10-Q/A", "NT 10-K", "NT 10-Q"}:
        return "Orange", "O9", True
    if form in {"10-Q", "10-K"}:
        return "Info", "I3", False
    if form == "UPLOAD":
        return "Orange", "O10", True
    if "13D" in form:
        return "Orange", "O12", True
    if form == "424B5":
        return "Orange", "O3", True
    if form in INSIDER and "code P" in summary:
        return "Orange", "O12", False
    return "Info", "I5", False


def filing_items(events, seen_before, seen_after):
    """One item per new filing. The insider forms roll into one line, as I4 says."""
    out, insiders = [], []
    filings = {e["id"]: e for e in events if e["kind"] == "filing"}
    for accession in sorted(set(seen_after) - set(seen_before)):
        entry = seen_after[accession]
        filings.setdefault(accession, {"id": accession, "kind": "filing", "ticker": entry.get("ticker", ""), "company": entry.get("company", ""),
                                       "form": entry.get("form", "8-K"), "filed": entry.get("filed", ""), "url": entry.get("url", ""),
                                       "summary": entry.get("reason", "")})
    for accession, e in sorted(filings.items(), key=lambda kv: (kv[1]["filed"], kv[0])):
        form = e["form"]
        if form in EIGHT_K:
            entry = seen_after.get(accession, {})
            level, rule, why = eight_k_level(entry.get("items"))
            only_routine = set(entry.get("items") or ["x"]) <= {"5.03", "5.07", "9.01"}
            out.append({"id": accession, "level": level, "rule": rule, "form": form, "filed": e["filed"], "url": e["url"],
                        "ticker": e["ticker"], "company": e["company"], "items": entry.get("items"), "first_pass": why,
                        "summary": e.get("summary", ""), "excerpts": entry.get("excerpts", {}), "needs_reading": not only_routine,
                        "inbox_note": entry.get("note")})
        elif form in INSIDER and "code P" not in e.get("summary", ""):
            insiders.append(e)
        else:
            level, rule, read = form_level(form, e.get("summary", ""))
            out.append({"id": accession, "level": level, "rule": rule, "form": form, "filed": e["filed"], "url": e["url"], "ticker": e["ticker"],
                        "company": e["company"], "summary": e.get("summary", ""), "needs_reading": read, "file_in_inbox": True})
    if insiders:
        sales = sum("code S" in e.get("summary", "") for e in insiders)
        last = max(e["filed"] for e in insiders)
        out.append({"id": f"insider-{last}", "level": "Info", "rule": "I4", "form": "3/4/144", "filed": last, "url": insiders[-1]["url"],
                    "ticker": insiders[0]["ticker"], "company": insiders[0]["company"], "count": len(insiders), "sales": sales,
                    "summary": f"{len(insiders)} insider forms, {sales} with a sale.", "lines": [f'{e["form"]}, filed {e["filed"]}: {e.get("summary", "")} {e["url"]}' for e in insiders],
                    "needs_reading": False, "file_in_inbox": True, "roll_up": True})
    return out


def lead_item(events, report):
    leads = [e for e in events if e["kind"] == "screen"]
    if not leads:
        return []
    return [{"id": f"leads-{len(leads)}", "level": "Info", "rule": "I7", "form": "Screen", "filed": "", "url": report, "count": len(leads),
             "summary": f"{len(leads)} new screen leads. A lead is never a pick.", "needs_reading": False}]


def date_snapshot(radar_run):
    snap = {}
    if not radar_run:
        return snap
    for bucket in ("soon", "passed", "wide"):
        for c in radar_run["dates"].get(bucket, []):
            snap[c["title"]] = {"bucket": bucket, "start": c.get("date_start"), "end": c.get("date_end"), "quote": c.get("date_quote"), "kind": c.get("date_kind"),
                                "days": c.get("days_to_start"), "file": c.get("file"), "url": (c.get("source") or {}).get("url")}
    return snap


def date_items(old, new, run_day):
    """Only what changed: O13 for a stated date that passes or moves, I6 at the 90-day horizon and again at 7 days."""
    out = []
    for title, c in sorted(new.items()):
        was = old.get(title)
        where = c.get("url") or c.get("file")
        base = {"form": "Catalyst date", "filed": run_day, "url": where, "needs_reading": False, "file": c.get("file")}
        if c["bucket"] == "passed" and (not was or was["bucket"] != "passed"):
            stated = c.get("kind") == "stated"
            out.append(dict(base, id=f"date-passed:{title}", level="Orange" if stated else "Info", rule="O13" if stated else "I6",
                            summary=f'{title}: "{c["quote"]}" passed with no Outcome written.'))
        elif was and (was.get("start"), was.get("end")) != (c.get("start"), c.get("end")) and c.get("kind") == "stated":
            out.append(dict(base, id=f"date-moved:{title}", level="Orange", rule="O13",
                            summary=f'{title}: the stated date moved from "{was.get("quote")}" to "{c["quote"]}".'))
        elif c["bucket"] == "soon" and (not was or was["bucket"] != "soon"):
            out.append(dict(base, id=f"date-soon:{title}", level="Info", rule="I6", summary=f'{title}: "{c["quote"]}" is now inside 90 days.'))
        elif c["bucket"] == "soon" and c.get("days") is not None and 0 <= c["days"] <= 7 and (not was or (was.get("days") or 99) > 7):
            out.append(dict(base, id=f"date-7:{title}", level="Info", rule="I6", summary=f'{title}: "{c["quote"]}" is inside 7 days.'))
    return out


def price_items(rows, through, old_lines, lines, held, source):
    """A line crossed, once per crossing. No change and no percent, so a price move alone can never appear."""
    out = []
    earlier = [r for r in rows if r["date"] <= through]
    new = [r for r in rows if r["date"] > through]
    previous = earlier[-1]["close"] if earlier else None
    for r in new:
        close = r["close"]
        if previous is not None and previous >= lines["buy_below"] > close:
            out.append({"id": f'O4:{r["date"]}', "level": "Orange", "rule": "O4", "form": "Close", "filed": r["date"], "url": source["url"], "needs_reading": False, "token": "buy-below",
                        "summary": f'The close of {nice(r["date"])}, ${close:.2f}, is under the buy-below, ${lines["buy_below"]:.2f}.'})
        if held and previous is not None and previous <= lines["trim_above"] < close:
            out.append({"id": f'O5:{r["date"]}', "level": "Orange", "rule": "O5", "form": "Close", "filed": r["date"], "url": source["url"], "needs_reading": False, "token": "trim-above",
                        "summary": f'The close of {nice(r["date"])}, ${close:.2f}, is above the trim-above, ${lines["trim_above"]:.2f}.'})
        previous = close
    if old_lines and rows and old_lines != lines:
        last = rows[-1]["close"]
        for key, name in (("buy_below", "buy-below"), ("trim_above", "trim-above")):
            if (old_lines[key] > last) != (lines[key] > last):
                out.append({"id": f'O6:{key}:{lines["run_file"]}', "level": "Orange", "rule": "O6", "form": "Refresh", "filed": rows[-1]["date"], "url": lines["run_file"], "needs_reading": False, "token": name,
                            "summary": f'A refresh moved the {name} from ${old_lines[key]:.2f} to ${lines[key]:.2f}, across the last close, ${last:.2f}.'})
    return out


def real_holdings(folder):
    """Portfolio/ holds no real positions unless a note other than the README and the paper lesson appears."""
    return any(p.name not in {"README.md", "Paper portfolio.md"} for p in Path(folder).glob("*.md"))


def plain_text(body):
    """A filing as wrapped lines. A release can be one huge line, too long for Read, so this is what a session reads."""
    text = body.decode("utf-8", "replace")
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?i)</(p|div|tr|table|h\d)>|<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</t[dh]>", " | ", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).replace("\xa0", " ")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", re.sub(r"(\s*\|\s*)+", " | ", line)).strip(" |")
        if line:
            lines += textwrap.wrap(line, 180) or [line]
    return "\n".join(lines) + "\n"


def save_documents(items, client=None):
    """Save what a session must read, through the EDGAR client. A failure is noted, and the item stays at its first pass."""
    if not any(i["needs_reading"] and i["form"] not in {"Close"} and str(i["url"]).startswith("http") for i in items):
        return
    settings = edgar.load_settings()
    client = client or edgar.SecClient(settings["user_agent"], settings["rate"])
    for item in items:
        if not item["needs_reading"] or not str(item["url"]).startswith("http"):
            continue
        item["documents"] = []
        try:
            match = re.search(r"/data/(\d+)/(\d{18})/", item["url"])
            cik, plain = int(match.group(1)), match.group(2)
            cache = edgar.Cache(edgar.CACHE / f"CIK{cik:010d}", lambda: client, edgar.MAX_AGE_HOURS)
            base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{plain}/"
            listing = json.loads(client.get(base + "index.json"))
            names = [f["name"] for f in listing["directory"]["item"] if re.search(r"\.(htm|html|txt|pdf)$", f["name"], re.I)]
            wanted = [Path(item["url"]).name] + [n for n in names if re.search(r"ex-?_?99", n, re.I)]
            for name in dict.fromkeys(wanted):
                saved = f'documents/{item["id"]}-{name}'
                text_path = cache.folder / (saved + ".txt")
                if name.lower().endswith(".pdf"):  # no reader here for a PDF's text, and Read opens the file itself
                    cache.fetch(saved, base + name)
                    item["documents"].append(str((cache.folder / saved).relative_to(ROOT)))
                    continue
                text_path.write_text(plain_text(cache.fetch(saved, base + name)))
                item["documents"].append(str(text_path.relative_to(ROOT)))
        except Exception as err:  # the run must still produce its brief
            item["document_problem"] = f"{type(err).__name__}: {err}"[:200]


def run_sensors():
    results = []
    for name, args in SENSORS:
        done = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=560)
        results.append({"name": name, "ok": done.returncode == 0, "out": (done.stdout + done.stderr)[-800:]})
    return results


def overdue_results(seen, readings_text, today, alerted):
    """O16: a results 8-K three trading days old with no reading on file. Weekdays only, so a holiday can make it a day late."""
    out = []
    for accession, entry in seen.items():
        if "2.02" not in (entry.get("items") or []) or accession in readings_text or accession in alerted:
            continue
        day, left = dt.date.fromisoformat(entry["filed"]), 3
        while left:
            day += dt.timedelta(days=1)
            left -= day.weekday() < 5
        if today > day:
            out.append({"id": f"O16:{accession}", "level": "Orange", "rule": "O16", "form": "Silence", "filed": entry["filed"], "url": entry["url"], "needs_reading": False,
                        "summary": f'Results 8-K filed {nice(entry["filed"])} has no reading on file, three trading days on.', "token": accession})
    return out


def collect(now=None, sensors=run_sensors, documents=save_documents):
    now = now or dt.datetime.now().astimezone()
    today = now.date()
    RUNS.mkdir(exist_ok=True)
    seen_before = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    radar_before = newest(RADAR_RUNS)
    if STATE.exists():
        state = json.loads(STATE.read_text())
    else:  # the first run starts from the last radar run and the last saved close, so history is not news
        rows, _ = prices.read_latest()
        state = {"last_brief": None, "closes_through": rows[-1]["date"], "dates": date_snapshot(radar_before),
                 "problems": (radar_before or {}).get("problems", []), "lines": None, "o16": []}
    results = sensors()
    seen_after = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    radar = newest(RADAR_RUNS)
    fresh_radar = bool(radar) and radar != radar_before
    events = radar["events"] if fresh_radar else []
    report = radar["report"] if radar else ""
    val = newest(VALUATION_RUNS)
    lines = {"buy_below": val["buy_below"], "trim_above": val["trim_above"], "run_file": val["run_file"]}
    rows, entry = prices.read_latest()
    source = {"url": YAHOO, "label": f'Yahoo through yfinance, fetched {nice(entry["started_utc"])}'}

    items = []
    for r in results:
        if not r["ok"]:
            items.append({"id": f'O16:{r["name"]}:{today}', "level": "Orange", "rule": "O16", "form": "Sensor", "filed": today.isoformat(), "url": "sensors/daily/runs/", "needs_reading": False,
                          "summary": f'{r["name"]} failed: {r["out"].strip()[-300:]}', "token": r["name"]})
    for problem in (radar["problems"] if fresh_radar else []):
        if problem not in state.get("problems", []):
            items.append({"id": f"O16:problem:{problem[:40]}", "level": "Orange", "rule": "O16", "form": "Sensor", "filed": today.isoformat(), "url": report, "needs_reading": False, "summary": f"Radar problem: {problem}", "token": "Radar problem"})
    items += filing_items(events, seen_before, seen_after)
    items += lead_item(events, report)
    if fresh_radar:
        items += date_items(state.get("dates", {}), date_snapshot(radar), today.isoformat())
    items += price_items(rows, state["closes_through"], state.get("lines"), lines, real_holdings(PORTFOLIO), source)
    readings = (ROOT / "sensors" / "8k-watch" / "readings.toml").read_text()
    overdue = overdue_results(seen_after, readings, today, set(state.get("o16", [])))
    items += overdue

    carried = []
    for path in sorted(RUNS.glob("*.json")):
        old = json.loads(path.read_text())
        if not old.get("briefed"):
            carried += [dict(i, carried_from=old["stem"]) for i in old["items"]]
            old.update(briefed=True, superseded=True)
            path.write_text(json.dumps(old, indent=1, ensure_ascii=False))
    known = {i["id"] for i in items}
    items += [i for i in carried if i["id"] not in known]
    documents(items)
    items.sort(key=lambda i: (ORDER[i["level"]], i["filed"], i["id"]))

    seq = len(list(RUNS.glob(f"{today}-*.json"))) + 1
    stem = f"{today}-{seq:02d}"
    list_saved = next((s for s in (radar or {}).get("sensors", []) if s["name"].startswith("SEC filing list")), None)
    digest = {"stem": stem, "run_local": now.isoformat(timespec="minutes"), "today": today.isoformat(), "since": state.get("last_brief"), "since_text": f'the brief of {nice(state["last_brief"])}' if state.get("last_brief") else "the last radar run", "closes_through_before": state["closes_through"],
              "quiet": not items, "briefed": False, "sensors": results, "items": items, "brief_path": f"sensors/daily/runs/{stem}.brief.md",
              "kill_criteria": "Research/2026-11-03 Corning kill criteria.md", "company_note": "Companies/Corning.md",
              "stands": {"close": rows[-1]["close"], "date": rows[-1]["date"], "buy_below": lines["buy_below"], "trim_above": lines["trim_above"], "source_label": source["label"], "source_url": source["url"], "lines_file": lines["run_file"], "held": real_holdings(PORTFOLIO)},
              "sec_list": {"url": (list_saved or {}).get("url"), "fetched": (list_saved or {}).get("saved")}, "radar_report": report, "not_read": NOT_READ}
    (RUNS / f"{stem}.json").write_text(json.dumps(digest, indent=1, ensure_ascii=False))
    state.update(closes_through=rows[-1]["date"], lines=lines, o16=sorted(set(state.get("o16", [])) | {i["token"] for i in overdue}))
    if fresh_radar:
        state.update(dates=date_snapshot(radar), problems=radar["problems"])
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False))
    return digest


def main():
    digest = collect()
    print(f'Digest: sensors/daily/runs/{digest["stem"]}.json')
    print("QUIET" if digest["quiet"] else f'NOT QUIET: {len(digest["items"])} items')
    for r in digest["sensors"]:
        print(f'{r["name"]}: {"ok" if r["ok"] else "FAILED"}')


if __name__ == "__main__":
    main()
