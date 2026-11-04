"""Read what the sensors already saved, and the Corning note through health.py. No network and no writes.

It imports the sensors' pure readers, so the page's numbers match economy.html. prices.py and macro.py
hold a fetch and a manifest writer as well: this file must never call fetch, download or update_manifest.
It does not import edgar.py or watch.py at all, because those talk to SEC.
"""

import calendar
import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SENSORS = ROOT / "sensors"
sys.path[:0] = [str(SENSORS / "macro"), str(SENSORS / "prices")]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import draw  # noqa: E402
import earnings  # noqa: E402
import health  # noqa: E402
import macro  # noqa: E402
import prices  # noqa: E402

WATCHLIST = SENSORS / "8k-watch" / "watchlist.toml"
INBOX = ROOT / "Inbox"
EDGAR_CACHE = SENSORS / "edgar" / "cache"
RADAR_RUNS = SENSORS / "radar" / "runs"
VALUATION_RUNS = SENSORS / "valuation" / "runs"
PAPER_PORTFOLIO = ROOT / "Portfolio" / "Paper portfolio.md"
POSITION_NOTES = ROOT / "Portfolio"
RESEARCH = ROOT / "Research"
JOURNAL = ROOT / "Journal"
COMPANIES = ROOT / "Companies"
CATALYSTS = ROOT / "Catalysts"
LESSONS = ROOT / "Lessons"
GUARD_LOG = ROOT / ".claude" / "guardrails" / "blocked.jsonl"
VALUATION_KEYS = ("worked_out", "run_utc", "run_file", "price", "series", "base", "coverage", "buy_below", "strategic", "trim_above", "zone", "scenarios", "no_vote", "growth_needed", "inputs", "checks", "what_if")
RADAR_KEYS = ("run_date", "run_utc", "report", "sensors", "problems", "dates", "events", "walks", "screen", "horizon_days", "leads_line")
CORNING = "GLW"
LEVELS = ("high", "medium", "low")

# What can go wrong reading a saved file. The page shows the message and keeps the other sections.
PROBLEMS = (macro.MacroError, prices.PriceError, earnings.EarningsError, OSError, ValueError, KeyError, TypeError,
            IndexError, ArithmeticError)

nice_date = draw.nice_date
nice_month = draw.nice_month


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def local_today():
    """The Journal's days are local, so ages count from the local day. All of the board's dates come through here or now_utc, so a test can move them both."""
    return dt.date.today()


# ---- Age limits. Mine, approved Nov. 4, 2026. Words only: no colour, no level and no alert, since a source's age alone is never an alert (Rules/alerts.md). ----

AGE_LIMITS = Path(__file__).resolve().parent / "age_limits.toml"
ROUTINE_LIMITS = {"Daily run": "run_daily", "Event run": "run_event", "Weekly thesis check": "run_weekly", "Monthly hunt": "run_monthly", "Quarterly refresh": "run_quarterly"}
LIMITS_UNREAD = "Its age against my limit is Unknown: dashboard/age_limits.toml could not be read. Putting that file back would fill it."


def age_limits(path=None):
    return tomllib.loads(Path(path or AGE_LIMITS).read_text())


def _as_day(then):
    if isinstance(then, dt.datetime):
        return then.date()
    return then if isinstance(then, dt.date) else dt.date.fromisoformat(str(then)[:10])


def days_old(then, today=None):
    return (( today or local_today()) - _as_day(then)).days


def _days(n):
    return f'{n} day{"" if n == 1 else "s"}'


def past_limit(kind, then, today=None, limits=None):
    """The words for a source past my limit, and an empty string for one within it. A limit that cannot be read says so. It is never taken as within it."""
    try:
        limit = (limits or age_limits())[kind]
    except (OSError, ValueError, KeyError):
        return LIMITS_UNREAD
    old = days_old(then, today)
    return f'{limit["what"]} is {_days(old)} old, past my limit of {_days(limit["days"])}.' if old > limit["days"] else ""


def against_limit(kind, then, today=None, limits=None):
    """One cell for the table of sources: within the limit, or the words past it."""
    words = past_limit(kind, then, today, limits)
    if words:
        return words
    limit = (limits or age_limits())[kind]
    return f'Within my limit of {_days(limit["days"])}, counted from {limit["counted"]}.'


def test_copy_label(mark=ROOT / "TEST_COPY.txt"):
    """The words for the banner on a made-up copy of the vault. Only dashboard/tools/busy_copy.py writes this file, and only in a copy."""
    mark = Path(mark)
    return mark.read_text().strip() if mark.exists() else None


def parse_time(text):
    return dt.datetime.fromisoformat(text)


# ---- Watchlist and prices ----

def load_watchlist(path=WATCHLIST):
    return tomllib.loads(Path(path).read_text())["company"]


def last_price(ticker, cache=prices.CACHE):
    """The newest saved close for a ticker, or None if nothing is on file. Never fetches."""
    folder = Path(cache) / ticker
    if prices.latest_good(prices.load_manifest(folder)) is None:
        return None
    rows, entry = prices.read_latest(folder, ticker)
    last = rows[-1]
    if last["date"] != entry["last"]:
        raise ValueError(f"{entry['file']} ends on {last['date']}, and its manifest says {entry['last']}.")
    return {"close": last["close"], "date": last["date"], "fetched": parse_time(entry["started_utc"]),
            "file": entry["file"], "source": entry["source"], "folder": f"sensors/prices/cache/{ticker}"}


def close_fill(ticker):
    """What would fill a missing close. The price sensor saves only one ticker today, so it says that."""
    if ticker == prices.TICKER:
        return "Running sensors/prices/prices.py by hand would fill it."
    return f"A saved close in sensors/prices/cache/{ticker}/ would fill it. sensors/prices/prices.py saves only {prices.TICKER} today, so it needs extending first."


def watchlist_rows(path=WATCHLIST, cache=prices.CACHE):
    rows = []
    for company in load_watchlist(path):
        row = {"name": company["name"], "ticker": company["ticker"], "price": None, "problem": None}
        try:
            row["price"] = last_price(company["ticker"], cache)
        except PROBLEMS as err:
            row["problem"] = str(err)
        rows.append(row)
    return rows


# ---- Inbox ----

def front_matter(text):
    """The small YAML subset watch.py writes: key: value, JSON strings and lists, and one block list."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("no front matter")
    if "---" not in lines[1:]:
        raise ValueError("front matter is not closed")
    out, current = {}, None
    for line in lines[1:lines.index("---", 1)]:
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current is None:
                raise ValueError(f"list item with no key: {line!r}")
            out[current].append(json.loads(line[4:]))
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"bad line: {line!r}")
        value = value.strip()
        if not value:
            current, out[key] = key, []
            continue
        current = None
        out[key] = json.loads(value) if value[0] in '"[' else value
    return out


def read_inbox(folder=INBOX):
    """Every 8-K note, newest filing first. A note that cannot be read is listed, not hidden."""
    notes = []
    for path in Path(folder).glob("*.md"):
        if path.name == "README.md":
            continue
        try:
            meta = front_matter(path.read_text())
            if not str(meta["form"]).startswith("8-K"):
                continue
            level = str(meta.get("attention", "")).strip().lower()
            sources = meta.get("sources") or []
            notes.append({"name": path.name, "filed": meta["filed"], "accession": meta.get("accession", ""),
                          "company": meta.get("company", ""), "ticker": meta.get("ticker", ""), "form": meta["form"],
                          "items": meta.get("items", []), "flagged": meta.get("flagged", []),
                          "attention": level if level in LEVELS else "unknown", "rated_by": meta.get("rated by", ""),
                          "reason": meta.get("reason", ""), "url": sources[0] if sources else None, "problem": None})
        except PROBLEMS as err:
            notes.append({"name": path.name, "filed": path.name[:10], "accession": "", "company": "", "ticker": "",
                          "form": "", "items": [], "flagged": [], "attention": "unknown", "rated_by": "", "reason": "",
                          "url": None, "problem": str(err)})
    return sorted(notes, key=lambda n: (n["filed"], n["accession"]), reverse=True)


# ---- Catalyst radar ----

def latest_radar(runs=RADAR_RUNS):
    """The newest saved radar run, or None if there is none. It reads the file the radar saved and asks nothing of SEC."""
    files = sorted(Path(runs).glob("*.json"), key=lambda p: p.stem)
    if not files:
        return None
    run = json.loads(files[-1].read_text())
    missing = [k for k in RADAR_KEYS if k not in run]
    if run.get("schema") != 1 or missing:
        raise ValueError(f"{files[-1].name} is not a radar run this page can read: schema {run.get('schema')}, missing {missing}.")
    return run


# ---- Alerts: what the routines wrote in the Journal ----

ROUTINES = ("Daily run", "Event run", "Weekly thesis check", "Monthly hunt", "Quarterly refresh")
_LEVEL_LINE = re.compile(r"^(?:###\s*|\*\*)(Red|Orange|Info)(?:\*\*)?\s*$")
_RULE = re.compile(r"\b([ROI]\d{1,2})\b")
_FAILED = re.compile(r"^(?:- )?(Daily run|Event run|Weekly thesis check|Monthly hunt|Quarterly refresh) FAILED at step .*$")
_RULED = re.compile(r"^- Ruled: (\d{4}-\d{2}-\d{2}) ([ROI]\d{1,2})\. (\S.*)$")


def _routine_of(heading):
    """Only a routine's own session record counts. A person's session that talks about a routine does not."""
    low = heading.lower()
    if low.startswith("## daily brief"):  # sensors/daily/publish.py heads a busy brief this way
        return "Daily run"
    return next((name for name in ROUTINES if low.startswith(f"## session: {name.lower()}")), None)


def journal_alerts(folder=JOURNAL):
    """Every Red, Orange and Info line a routine wrote, newest day first, and the last day each routine left a record.

    It reads the Journal as written and judges nothing. A failed run's own line counts as an Orange, as O16 says.
    Each line starting "- Ruled:" is kept apart in "rulings", for waiting_list. It is never an alert."""
    alerts, last_run, rulings = [], {}, []
    for path in sorted(Path(folder).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"), reverse=True):
        day = path.stem
        level, routine = None, "Daily run"  # a brief sits under the date, above its session record
        for line in path.read_text().splitlines():
            line = line.rstrip()
            if line.startswith("## "):
                routine = _routine_of(line)
                if routine:
                    last_run.setdefault(routine, day)
                level = None
                continue
            if line.startswith("- Ruled:"):
                found = _RULED.match(line)
                rulings.append({"line": line[2:], "written": day, "routine": routine, "day": found[1] if found else None,
                                "rule": found[2] if found else None, "words": found[3] if found else None})
                continue
            failed = _FAILED.match(line)
            if failed:
                alerts.append({"day": day, "level": "Orange", "rule": "O16", "routine": failed[1], "text": line.removeprefix("- ")})
                last_run.setdefault(failed[1], day)
                continue
            found = _LEVEL_LINE.match(line)
            if found:
                level = found[1]
            elif line.startswith("#"):
                level = None
            elif level and routine and line.startswith("- ") and line.strip() != "- Nothing.":
                rule = _RULE.search(re.sub(r"\]\([^)]*\)", "]", line))  # a web address is no rule ID
                alerts.append({"day": day, "level": level, "rule": rule[1] if rule else "", "routine": routine, "text": line[2:]})
    return {"alerts": alerts, "last_run": last_run, "rulings": rulings, "days_read": len(list(Path(folder).glob("[0-9]*.md")))}


def _real_day(text):
    try:
        dt.date.fromisoformat(text)
    except (TypeError, ValueError):
        return False
    return True


def alert_source(text):
    """The first https link in a line, as (label, url), or the first vault file named in backticks. None if the line names neither."""
    found = re.search(r"\[([^\]]+)\]\((https://[^)\s]+)\)", text)
    if found:
        return (found[1], found[2])
    found = re.search(r"`([^`]+\.\w+)`", text)
    return found[1] if found else None


def waiting_list(book, today):
    """Which Reds and Oranges have no Ruled: line, Reds first, then oldest first. A ruling closes one alert with its day and rule.

    What cannot be matched is listed in "problems", never dropped: a line that cannot be read, a ruling with no alert, one a routine wrote
    (routines report and never rule), one written before its alert, and an alert with no rule ID, which no ruling could ever close."""
    problems = []
    open_by_key = {}
    for alert in sorted((a for a in book["alerts"] if a["level"] != "Info"), key=lambda a: a["day"]):  # stable, so Journal order within a day
        open_by_key.setdefault((alert["day"], alert["rule"]), []).append(alert)
        if not alert["rule"]:
            problems.append(f'A {alert["level"]} of {nice_date(alert["day"])} has no rule ID, so no Ruled: line can close it.')
    closed = []
    for ruling in sorted(book.get("rulings", []), key=lambda r: r["written"]):
        where = f'Journal/{ruling["written"]}.md'
        key = (ruling["day"], ruling["rule"])
        if ruling["day"] is None or not _real_day(ruling["day"]):
            problems.append(f'{where}: this line cannot be read as "- Ruled: <day> <rule ID>. <my words>": {ruling["line"]}')
        elif ruling["routine"]:
            problems.append(f'{where}: {ruling["routine"]} wrote this, and a routine does not rule, so it closes nothing: {ruling["line"]}')
        elif ruling["written"] < ruling["day"]:
            problems.append(f'{where}: this is dated before its alert, so it closes nothing: {ruling["line"]}')
        elif not open_by_key.get(key):
            problems.append(f'{where}: this matches no alert still waiting: {ruling["line"]}')
        else:
            alert = open_by_key[key].pop(0)
            closed.append({**alert, "ruled": ruling["words"], "ruled_in": ruling["written"]})
    for (day, rule), rows in open_by_key.items():
        if rows and any((c["day"], c["rule"]) == (day, rule) for c in closed):
            problems.append(f'{len(rows)} of the alerts of {day} {rule} still wait. A ruling closes the first in Journal order, and each needs its own line.')
    rows = [{**a, "days": (today - dt.date.fromisoformat(a["day"])).days, "source": alert_source(a["text"]), "journal": f'Journal/{a["day"]}.md'}
            for waiting in open_by_key.values() for a in waiting]
    rows.sort(key=lambda a: (a["level"] != "Red", a["day"]))
    return {"rows": rows, "closed": closed, "problems": problems}


_BRIEF_HEAD = re.compile(r"^## Daily brief, ")
_QUIET_BRIEF = re.compile(r"^\*\*Daily brief, [^*]*: nothing needs me\.\*\*\s*(.*)$")
_SINCE = re.compile(r"^\*\*Since ([^*]*?):\*\*\s*(.*)$")


def last_brief(folder=JOURNAL):
    """The newest brief: its Since sentence and Info lines. publish.py puts the newest at the top of the day's file, so the first found wins.

    Only the top of a day's file or a "## Daily brief" heading counts, so a session quoting a brief cannot pass for one."""
    for path in sorted(Path(folder).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"), reverse=True):
        inside, level, brief = True, None, None
        for line in path.read_text().splitlines():
            if line.startswith("## "):
                if brief:
                    break
                inside = bool(_BRIEF_HEAD.match(line))
                continue
            if not inside:
                continue
            quiet = _QUIET_BRIEF.match(line)
            since = _SINCE.match(line)
            if quiet:
                return {"day": path.stem, "file": f"Journal/{path.name}", "quiet": True, "since": quiet[1], "info": []}
            if since:
                brief = {"day": path.stem, "file": f"Journal/{path.name}", "quiet": False, "since": f"Since {since[1]}: {since[2]}", "info": []}
            found = _LEVEL_LINE.match(line)
            if found:
                level = found[1]
            elif brief and level == "Info" and line.startswith("- ") and line.strip() != "- Nothing.":
                brief["info"].append(line[2:])
        if brief:
            return brief
    return None


def guard_events(path=GUARD_LOG):
    """What the guardrail hook stopped or undid, newest first. It only reads the hook's own record."""
    path = Path(path)
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return list(reversed(rows))


# ---- Paper portfolio ----

def _note_table(text, heading):
    """The rows of the first table under a heading in a note, as lists of cell text. Header and rule rows are left out."""
    _, found, rest = text.partition(f"\n## {heading}\n")
    if not found:
        raise ValueError(f"no section called {heading}")
    rows = []
    for line in rest.split("\n## ")[0].splitlines():
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows[2:]


def cash_level(share):
    """The levels in Rules/cash.md. Over 15% is above normal, 5% to 15% is normal, under 5% is the floor."""
    return "Above normal" if share > .15 else "Normal" if share >= .05 else "Floor"


def paper_portfolio(path=PAPER_PORTFOLIO, cache=prices.CACHE):
    """The paper note, and it refuses any other. Figures are at the last saved closes, as read_book says."""
    book = read_book(path, cache)
    if book["kind"] != "paper":
        raise ValueError(f"{Path(path).name} is not marked as paper.")
    return book


def _number(text):
    return float(str(text).replace("$", "").replace(",", ""))


def _months_between(first, last):
    """Whole months from one day to another."""
    return (last.year - first.year) * 12 + last.month - first.month - (last.day < first.day)


def read_book(path, cache=prices.CACHE, today=None):
    """One note in Portfolio/, at the last saved closes, as Rules/cash.md says: stocks at today's prices.

    A position with no saved close has no value today. Then its share, the total, the cash share and the level are all None, and no figure falls back to cost.
    A note marked neither real nor paper is refused, so the two can never mix."""
    path, today = Path(path), today or local_today()
    text = path.read_text()
    meta = front_matter(text)
    kind = meta.get("kind")
    if kind not in ("real", "paper"):
        raise ValueError("it is not marked real or paper, so it is not read")
    positions, missing, closes = [], [], []
    for row in _note_table(text, "Positions"):
        if len(row) != 5:
            raise ValueError(f"a row in its Positions table has {len(row)} columns, not the five the table heads: {row[0]}")
        ticker, shares, bought, cost, thesis = row
        try:
            price, trouble = last_price(ticker, cache), None
        except PROBLEMS as err:
            price, trouble = None, f"{type(err).__name__}: {err}"
        if price is None:
            missing.append(ticker)
        else:
            closes.append(price["date"])
        count = _number(shares)
        positions.append({"ticker": ticker, "shares": count, "bought": bought, "cost": _number(cost), "thesis": thesis, "price": price, "problem": trouble,
                          "value": count * price["close"] if price else None, "share": None})
    cash = float(meta["cash"])
    total = None if missing else cash + sum(p["value"] for p in positions)
    share = cash / total if total else None
    for p in positions:
        p["share"] = p["value"] / total if total and p["value"] is not None else None
    since = meta.get("cash above 50% since")
    months = _months_between(dt.date.fromisoformat(since), today) if since else None
    changes = [dict(zip(("date", "change", "cash", "yes"), row)) for row in (_note_table(text, "Changes") if "\n## Changes\n" in text else [])]
    return {"kind": kind, "cash": cash, "total": total, "share": share, "level": None if share is None else cash_level(share), "positions": positions, "changes": changes,
            "missing": missing, "newest_close": max(closes) if closes else None, "as_of": meta.get("as of"), "last_checked": meta["last checked"],
            "above_50_since": since, "above_50_months": months, "file": f"Portfolio/{path.name}"}


# ---- Price against value ----

def valuation_zone(mid, price, trim, bar=.75):
    """Compares unrounded figures, as the rule does."""
    under, above = mid / price >= bar, price > trim
    return "under_and_above" if under and above else "under" if under else "above" if above else "between"


def latest_valuation(runs=VALUATION_RUNS):
    """The newest saved valuation run, or None. This file is all the panel reads: no price file, no note, no sums beyond checking the file agrees with itself."""
    files = sorted(Path(runs).glob("*.json"), key=lambda p: p.stem)
    if not files:
        return None
    return _checked_valuation(files[-1])


def _checked_valuation(path):
    run = json.loads(path.read_text())
    missing = [k for k in VALUATION_KEYS if k not in run]
    if run.get("schema") != 1 or missing:
        raise ValueError(f"{path.name} is not a valuation run this page can read: schema {run.get('schema')}, missing {missing}.")
    base, price = run["base"], run["price"]["close"]
    wrong = []
    if not run["series"] or run["series"][-1] != [run["price"]["date"], price]:
        wrong.append("the price is not the last row of its series")
    if not base["low"] <= base["mid"] <= base["high"]:
        wrong.append("the base range is out of order")
    for name, stored, sum_ in (("buy-below", run["buy_below"], base["mid"] / .75), ("trim-above", run["trim_above"], base["mid"] + run["strategic"]),
                               ("coverage", run["coverage"]["mid"], base["mid"] / price)):
        if abs(stored - sum_) > 1e-6:
            wrong.append(f"{name} does not follow from the base and the price")
    if run["zone"] != valuation_zone(base["mid"], price, run["trim_above"]):
        wrong.append("the zone does not follow from the price and the two lines")
    if wrong:
        raise ValueError(f"{path.name} does not agree with itself: {'; '.join(wrong)}.")
    return run


# ---- Home: Coming up and Where things stand ----

_MONTHS = {m: i + 1 for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}
_COLUMN = re.compile(r"^(.+?) \(([A-Z][a-z]{2})[a-z]*\.? (\d{4})\)$")


def next_kill_checks(today, folder=RESEARCH):
    """For each company's newest "* kill criteria.md": the lines marked T for the next report in its Calendar of checks. Month labels are the note's own estimates."""
    newest, rows, problems = {}, [], []
    for path in sorted(Path(folder).glob("* kill criteria.md")):  # the name starts with its date, so a later file replaces an earlier one
        newest[path.stem[11:]] = path
    for path in newest.values():
        name = path.stem[11:].removesuffix(" kill criteria")
        where = f"Research/{path.name}"
        try:
            section = path.read_text().split("\n## Calendar of checks\n", 1)[1].split("\n## ", 1)[0]
            table = []
            for line in section.splitlines():
                if line.startswith("|"):
                    table.append([c.strip() for c in line.strip().strip("|").split("|")])
                elif table:
                    break
            columns = [_COLUMN.match(c) for c in table[0][1:]]
            if not all(columns):
                raise ValueError("a column does not read as a report and a month")
            for i, col in enumerate(columns):
                year, month = int(col[3]), _MONTHS[col[2]]
                if dt.date(year, month, calendar.monthrange(year, month)[1]) >= today:
                    fires = [row[0].split()[0] for row in table[2:] if row[i + 1] == "T"]
                    rows.append({"company": name, "report": col[1], "month": f"{col[2]}. {year}", "start": dt.date(year, month, 1), "lines": fires, "file": where, "written": path.stem[:10]})
                    break
            else:
                problems.append(f"{where}: the calendar has no report after {nice_date(today)}.")
        except (OSError, ValueError, IndexError, KeyError) as err:
            problems.append(f"{where}: its Calendar of checks could not be read: {err}")
    return {"rows": rows, "problems": problems}


def coming_up(run, checks, today):
    """Dates in the saved radar run's horizon and each company's next report, nearest first. A date already past today has left the list."""
    rows = []
    for c in run["dates"]["soon"] if run else []:
        start, end = dt.date.fromisoformat(c["date_start"]), dt.date.fromisoformat(c["date_end"])
        if end >= today:
            rows.append({"sort": max(start, today), "rank": 1, "when": c["date_quote"], "kind": c["date_kind"], "title": c["title"],
                         "source": c.get("source"), "file": c["file"], "written": run["run_date"]})
    for k in checks["rows"]:
        if k["lines"]:
            rows.append({"sort": max(k["start"], today), "rank": 0, "when": f'about {k["month"]}', "kind": "my estimate", "title": f'{k["company"]}: {", ".join(k["lines"])} can fire on the {k["report"]} report',
                         "source": None, "file": k["file"], "written": k["written"]})
    rows.sort(key=lambda r: (r["sort"], r["rank"]))
    return rows


def position_notes(folder=POSITION_NOTES, cache=prices.CACHE):
    """Real and paper stay apart. A note marked neither is a problem to show, and is never counted as either."""
    out = {"real": [], "paper": [], "problems": []}
    for path in sorted(Path(folder).glob("*.md")):
        if path.name == "README.md":
            continue
        try:
            book = read_book(path, cache)
            out[book["kind"]].append(book)
        except PROBLEMS as err:
            out["problems"].append(f"Portfolio/{path.name}: {err}")
    return out


def latest_valuations(runs=VALUATION_RUNS):
    """The newest saved run for each company. A run that disagrees with itself is a problem, not a row."""
    newest, problems = {}, []
    for path in sorted(Path(runs).glob("*.json"), key=lambda p: p.stem):
        try:
            run = _checked_valuation(path)
            newest[run["ticker"]] = run
        except PROBLEMS as err:
            problems.append(str(err))
    return {"rows": list(newest.values()), "problems": problems}


def where_it_stands(run, cache=prices.CACHE):
    """I9 for one company: last saved close, its date, the two lines. It compares nothing. With no close on file the close is None, never the run's price."""
    try:
        price = last_price(run["ticker"], cache)
    except PROBLEMS:
        price = None
    return {"company": run["company"], "ticker": run["ticker"], "price": price, "buy_below": run["buy_below"], "trim_above": run["trim_above"],
            "run_file": run["run_file"], "worked_out": run["worked_out"]}


def _block(read, *args):
    """A block that cannot be read shows its problem, and the rest of the screen still draws."""
    try:
        return read(*args), None
    except PROBLEMS as err:
        return None, f"{type(err).__name__}: {err}"


def home_view(today=None, journal=JOURNAL, research=RESEARCH, radar_runs=RADAR_RUNS, valuation_runs=VALUATION_RUNS, notes=POSITION_NOTES, cache=prices.CACHE):
    """Everything Home shows, from files. It judges nothing and compares no close to a line. The Journal's days are local, so today is too."""
    today = today or local_today()
    book, book_problem = _block(journal_alerts, journal)
    brief, brief_problem = _block(last_brief, journal)
    run, run_problem = _block(latest_radar, radar_runs)
    checks, checks_problem = _block(next_kill_checks, today, research)
    checks = checks or {"rows": [], "problems": []}
    books, books_problem = _block(position_notes, notes, cache)
    values, values_problem = _block(latest_valuations, valuation_runs)
    values = values or {"rows": [], "problems": []}
    sources, sources_problem = _block(source_rows, now_utc(), WATCHLIST, cache, EDGAR_CACHE, INBOX, macro.DOWNLOADS, radar_runs, valuation_runs, journal, notes)
    return {"today": today, "past": None if sources is None else past_sources(sources, today), "past_problem": sources_problem, "book": book, "book_problem": book_problem, "waiting": waiting_list(book, today) if book else None,
            "brief": brief, "brief_problem": brief_problem,
            "coming": coming_up(run, checks, today), "coming_problems": [p for p in (run_problem, checks_problem, *checks["problems"]) if p], "radar_date": run["run_date"] if run else None,
            "books": books, "books_problem": books_problem,
            "stands": [where_it_stands(r, cache) for r in values["rows"]], "stands_problems": [p for p in (values_problem, *values["problems"]) if p]}


# ---- Company page ----

_REF = re.compile(r"^\[([^\]]+)\]:\s*(\S+)\s*$", re.M)
_WIKI = re.compile(r"\[\[([^\]|]+)")
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
_FIRST_LINK = re.compile(r"\[([^\]]+)\]\((https://[^)\s]+)\)")


def _meta(text):
    """Front matter, with a blank field as "". front_matter reads a blank as the start of a list."""
    return {k: "" if v == [] else v for k, v in front_matter(text).items()}


def split_note(text):
    """A note's words: its sections in order and its link references. Front matter, %% comments %% and reference lines are not words on the page."""
    body = text.split("\n---", 1)[1].split("\n", 1)[1] if text.startswith("---") else text
    refs = dict(_REF.findall(body))
    body = _REF.sub("", re.sub(r"%%.*?%%", "", body, flags=re.S))
    pieces = re.split(r"^## ", body, flags=re.M)
    return {"top": pieces[0].strip(), "refs": refs,
            "sections": [{"title": piece.split("\n", 1)[0].strip(), "text": piece.split("\n", 1)[1].strip() if "\n" in piece else ""} for piece in pieces[1:]]}


def _section(parts, title):
    return next((s["text"] for s in parts["sections"] if s["title"] == title), None)


def company_list(folder=COMPANIES):
    """One row per note in Companies/. A note that cannot be read is a row with its problem, never left out."""
    rows = []
    for path in sorted(Path(folder).glob("*.md"), key=lambda p: p.stem.lower()):
        if path.name == "README.md":
            continue
        row = {"name": path.stem, "file": f"Companies/{path.name}", "ticker": "", "status": "", "sector": "", "base_value": "", "last_checked": "", "problem": None}
        try:
            meta = _meta(path.read_text())
            row.update(ticker=str(meta.get("ticker", "")), status=str(meta.get("status", "")), sector=str(meta.get("sector", "")),
                       base_value=str(meta.get("base value", "")), last_checked=str(meta.get("last checked", "")))
        except PROBLEMS as err:
            row["problem"] = str(err)
        rows.append(row)
    return rows


def company_slug(row):
    """What goes after ?company=. The ticker if the note has one, or the note's name."""
    return row["ticker"] or row["name"]


def find_company(wanted, rows):
    """Only a name on the list can match, so an address can never reach a file outside Companies/. A ticker wins over a name."""
    wanted = (wanted or "").strip().lower()
    if not wanted:
        return None
    return next((r for r in rows if r["ticker"].lower() == wanted), None) or next((r for r in rows if r["name"].lower() == wanted), None)


def company_run(name, ticker, runs=VALUATION_RUNS):
    """This company's newest saved run. One that disagrees with itself is a problem, and no older run stands in for it."""
    problems = []
    for path in sorted(Path(runs).glob("*.json"), key=lambda p: p.stem, reverse=True):
        try:
            raw = json.loads(path.read_text())
        except PROBLEMS as err:
            problems.append(f"{path.name} could not be read, so it may belong to this company: {err}")
            continue
        if raw.get("company") == name or (ticker and raw.get("ticker") == ticker):
            try:
                return {"run": _checked_valuation(path), "problems": problems}
            except PROBLEMS as err:
                return {"run": None, "problems": [*problems, str(err)]}
    return {"run": None, "problems": problems}


def _md_tables(text):
    """Every table in some note text, each with its headers and rows, and the words outside them. A "###" heading is not a word on the page."""
    tables, words, current = [], [], None
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if current is None:
                current = {"headers": cells, "rows": []}
                tables.append(current)
            elif not all(set(c) <= set("-: ") for c in cells):
                current["rows"].append(cells)
        else:
            current = None
            if line.strip() and not line.startswith("#"):
                words.append(line.strip())
    return tables, words


def _top_remark(text):
    """The first whole line in italics: a file's own dated remark on itself, such as "Not adopted"."""
    for line in text.splitlines():
        line = line.strip()
        if re.fullmatch(r"\*[^*].*[^*]\*", line):
            return line.strip("*")
    return ""


def research_files(name, folder=RESEARCH):
    """Every dated file in Research/ for this company, newest first."""
    rows = []
    for path in sorted(Path(folder).glob("*.md"), key=lambda p: p.name, reverse=True):
        if not (_DAY.fullmatch(path.stem[:10]) and path.stem[11:].startswith(f"{name} ")):
            continue
        text = path.read_text()
        try:
            meta = _meta(text)
        except PROBLEMS:
            meta = {}
        kind = path.stem[11 + len(name):].strip()
        rows.append({"file": f"Research/{path.name}", "kind": kind, "written": str(meta.get("written") or path.stem[:10]), "status": str(meta.get("status", "")),
                     "skeptic": str(meta.get("skeptic review", "")), "remark": _top_remark(split_note(text)["top"] + "\n" + "\n".join(s["text"] for s in split_note(text)["sections"])), "path": path})
    return rows


def company_thesis(name, research):
    """What is on file about a thesis, all of it draft. The note's own Thesis section is shown apart, word for word."""
    drafts = [r for r in research if r["kind"].startswith("thesis")]
    kills = [r for r in research if r["kind"] == "kill criteria"]
    out = {"drafts": [{k: v for k, v in r.items() if k != "path"} for r in drafts], "kill_file": None}
    if kills:  # newest first, so the first is the one that counts
        newest = kills[0]
        parts = split_note(newest["path"].read_text())
        empty = {"headers": [], "rows": []}
        claims, claim_words = _md_tables(_section(parts, "The claims") or "")
        lines, _ = _md_tables(_section(parts, "The criteria") or "")
        calendar, calendar_words = _md_tables(_section(parts, "Calendar of checks") or "")
        out.update(kill_file=newest["file"], written=newest["written"], kill_status=newest["status"], refs=parts["refs"],
                   claims=claims[0] if claims else empty, claim_words=claim_words, lines=lines[0] if lines else empty,  # later tables in that section show how a line is read, not the lines
                   calendar=calendar, calendar_words=calendar_words)
    return out


def typed_links(folder=COMPANIES):
    """Every row of every Typed links table, by the note it is written in. A row that cannot be read is listed, not dropped."""
    rows, problems = [], []
    for path in sorted(Path(folder).glob("*.md")):
        if path.name == "README.md":
            continue
        text = _section(split_note(path.read_text()), "Typed links")
        for line in (text or "").splitlines():
            if not line.startswith("| ") or line.startswith("| Link") or not line.strip("| "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if len(cells) != 7:
                problems.append(f"Companies/{path.name}: a Typed links row has {len(cells)} columns, not 7: {line[:60]}")
                continue
            rows.append(dict(zip(("link", "other", "chain", "what", "size", "evidence", "source"), cells), written_in=path.stem, plain=re.sub(r"\[\[|\]\]| \(no note\)", "", cells[1])))
    return rows, problems


def _link_key(a, b, label):
    if label == "supplies":
        return ("supplies", a, b)
    if label == "customer of":
        return ("supplies", b, a)
    return (label, *sorted((a, b)))


def company_links(name, folder=COMPANIES):
    """The company's neighbors, one row each as its own note wrote them, then any link only another note holds, labelled so."""
    rows, problems = typed_links(folder)
    own = [r for r in rows if r["written_in"] == name]
    seen = {_link_key(name, r["plain"], r["link"]) for r in own}
    only_there = [r for r in rows if r["plain"] == name and r["written_in"] != name and _link_key(r["written_in"], name, r["link"]) not in seen]
    return {"rows": own, "only_there": only_there, "problems": [p for p in problems if f"Companies/{name}.md" in p]}


def company_catalysts(name, ticker, folder=CATALYSTS):
    """Catalyst notes with this ticker, or that link this company, nearest date first and undated last. The note's own date wording is kept."""
    rows = []
    for path in sorted(Path(folder).glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text()
        try:
            meta, parts = _meta(text), split_note(text)
        except PROBLEMS as err:
            rows.append({"title": path.stem, "file": f"Catalysts/{path.name}", "why": "Could not be read", "problem": str(err), "start": "", "last_checked": "", "kind": "", "quote": "", "type": "", "window": "", "in_numbers": "", "outcome": False, "source": None})
            continue
        own = bool(ticker) and str(meta.get("ticker", "")) == ticker
        named = name in _WIKI.findall(text.split("\n---", 1)[1] if text.startswith("---") else text)
        if not (own or named):
            continue
        when, outcome = _section(parts, "When") or "", _section(parts, "Outcome") or ""
        found, quote = _FIRST_LINK.search(when), str(meta.get("date quote", ""))
        problem = None if not quote or quote in when else f"The date wording {quote!r} is no longer in the note's When section."
        rows.append({"title": path.stem, "file": f"Catalysts/{path.name}", "why": "The note's ticker" if own else "The note links this company", "problem": problem,
                     "start": str(meta.get("date start", "")), "quote": quote, "kind": str(meta.get("date kind", "")), "type": str(meta.get("catalyst type", "")), "window": str(meta.get("window", "")),
                     "in_numbers": str(meta.get("in reported numbers", "")), "outcome": bool(outcome) and not outcome.startswith("Not known"),
                     "source": (found[1], found[2]) if found else None, "last_checked": str(meta.get("radar checked") or meta.get("last checked") or "")})
    return sorted(rows, key=lambda r: (not r["start"], r["start"], r["title"]))


def company_history(name, journal=JOURNAL, lessons=LESSONS):
    """Decision files for this company, and the files that name it. A name match, not a reading. The system's view in a decision file is not read out."""
    word = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)")
    decisions, mentions = [], []
    for path in sorted((Path(journal) / "decisions").glob("*.md"), reverse=True):
        if path.name == "README.md":
            continue
        meta = _meta(path.read_text())
        if meta.get("company") == name:
            decisions.append({"date": str(meta["date"]), "stage": str(meta.get("stage", "")), "file": f"Journal/decisions/{path.name}"})
    for path in sorted(Path(journal).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"), reverse=True):
        count = sum(bool(word.search(line)) for line in path.read_text().splitlines())
        if count:
            mentions.append({"date": path.stem, "file": f"Journal/{path.name}", "lines": count})
    for path in sorted(Path(lessons).glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text()
        count = sum(bool(word.search(line)) for line in text.splitlines())
        if count:
            found = _DAY.search(text)
            mentions.append({"date": found[0] if found else None, "file": f"Lessons/{path.name}", "lines": count})
    mentions.sort(key=lambda m: m["date"] or "", reverse=True)
    return {"decisions": decisions, "mentions": mentions}


def _note_sections_left(parts):
    """Sections shown on the page in their own blocks, or that hold only the note's pointers to the rules, are not repeated."""
    return [s for s in parts["sections"] if s["title"] not in ("Thesis", "Typed links", "Financial health summary", "Rules this note depends on") and s["text"]]


def whats_missing(model):
    """What the page could not show, and what would fill it. It starts nothing."""
    note, out = model["note"], []
    if model["thesis_section"] is None:
        out.append(("A recorded thesis", "The note has no Thesis section. I record a thesis there after a draft and the skeptic's review."))
    elif model["thesis_section"].startswith("Not written"):
        out.append(("A recorded thesis", "The note's Thesis section says it is not written. I record one there after a draft and the skeptic's review."))
    if not model["thesis"]["drafts"]:
        out.append(("A thesis draft", "Not in Research/. The thesis skill writes one there, for a company that passed triage."))
    if not model["thesis"]["kill_file"]:
        out.append(("Claims and kill lines", "No kill criteria file in Research/. They come with a thesis draft."))
    if model["value"]["run"] is None:
        out.append(("Base value, strategic value, buy-below and trim-above", f'No saved run in sensors/valuation/runs/. The note says base value: {note["base_value"] or "nothing"}. A run needs its own check that the method fits this company (Rules/when-to-buy.md), then the valuation skill.'))
    if not note["ticker"]:
        out.append(("Last close", "The note gives no ticker, so no close can be saved for it."))
    elif model["close"] is None:
        out.append(("Last close", f'No saved close in sensors/prices/cache/{note["ticker"]}/. {close_fill(note["ticker"])}'))
    if note["ticker"] and model.get("periodic") is None:
        out.append(("Latest 10-Q or 10-K", f'No saved SEC filing list holds one for {note["ticker"]}. sensors/edgar/edgar.py {note["ticker"]} would fill it.'))
    if note["ticker"] != CORNING:
        out.append(("Financial health and earnings yield", "These panels read only Corning's tables so far. This note has no Financial health summary for them to read."))
    if not model["catalysts"]:
        out.append(("Catalysts", "No note in Catalysts/ has this ticker or links this company."))
    if not model["links"]["rows"] and not model["links"]["only_there"]:
        out.append(("Graph neighbors", "No Typed links row names this company."))
    if not model["filings"]:
        out.append(("8-K notes", "None in Inbox/ for this company. The 8-K watcher follows only the watchlist."))
    return out


def company_view(row, today=None, folder=COMPANIES, research=RESEARCH, runs=VALUATION_RUNS, catalysts=CATALYSTS, journal=JOURNAL, lessons=LESSONS, inbox=INBOX, cache=prices.CACHE):
    """Everything the page shows for one company except Corning's own panels. One block that cannot be read shows its problem, and the rest still draw."""
    today = today or local_today()
    name, ticker = row["name"], row["ticker"]
    parts = split_note((Path(folder) / f"{name}.md").read_text())
    found, found_problem = _block(research_files, name, research)
    thesis, thesis_problem = _block(company_thesis, name, found or [])
    value, value_problem = _block(company_run, name, ticker, runs)
    close, close_problem = _block(last_price, ticker, cache) if ticker else (None, None)
    rows, catalysts_problem = _block(company_catalysts, name, ticker, catalysts)
    links, links_problem = _block(company_links, name, folder)
    filings, filings_problem = _block(read_inbox, inbox)
    history, history_problem = _block(company_history, name, journal, lessons)
    periodic = None
    if ticker:
        periodic, _ = _block(latest_periodic, ticker)
    model = {"note": row, "today": today, "refs": parts["refs"], "thesis_section": _section(parts, "Thesis"), "other_links": _section(parts, "Typed links") or "", "left": _note_sections_left(parts),
             "section_count": len(parts["sections"]),
             "research": [{k: v for k, v in r.items() if k != "path"} for r in found or []], "thesis": thesis or {"drafts": [], "kill_file": None},
             "value": value or {"run": None, "problems": []}, "close": close, "periodic": periodic, "catalysts": rows or [], "links": links or {"rows": [], "only_there": [], "problems": []},
             "filings": [n for n in filings or [] if ticker and n["ticker"] == ticker], "history": history or {"decisions": [], "mentions": []},
             "problems": {"research": found_problem or thesis_problem, "value": value_problem, "close": close_problem, "catalysts": catalysts_problem, "links": links_problem, "filings": filings_problem, "history": history_problem}}
    model["missing"] = whats_missing(model)
    return model


# ---- Earnings yield against Aaa ----

# ---- Ideas and alerts ----

ALERT_STATES = ("Waiting", "Ruled", "No ruling asked")
HUNT_SETTINGS = SENSORS / "hunt" / "settings.toml"
REJECTION_LOG = RESEARCH / "Rejection log.md"
_TICKER = re.compile(r"\(([A-Z][A-Z.]*)\)\s*$")
_LOOK_MONTH = re.compile(r"about (?:early |mid |late )?(Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)\.? (\d{4})")
_LOOK_YEAR = re.compile(r"about (?:early |mid |late )?(\d{4})")
_MONTH_NAMES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "June": 6, "July": 7, "Aug": 8, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12}
_LONG_DAY = re.compile(r"^([A-Z][a-z]+)\.? (\d{1,2}), (\d{4})$")


def alert_rows(book, today):
    """Every line the routines wrote, each with its state. Waiting and Ruled come from waiting_list, so this screen and Home can never disagree.

    Info asks for no ruling, so it never shows as waiting. Reds first, then Oranges, then Info. Within a level, what waits comes first, oldest first, then the rest, newest first."""
    waiting = waiting_list(book, today)
    closed = list(waiting["closed"])
    rows = []
    for alert in sorted(book["alerts"], key=lambda a: a["day"]):  # the order waiting_list closes them in
        row = {**alert, "journal": f'Journal/{alert["day"]}.md', "source": alert_source(alert["text"]), "state": "No ruling asked" if alert["level"] == "Info" else "Waiting",
               "ruled": None, "ruled_in": None, "days": None}
        if alert["level"] != "Info":
            found = next((c for c in closed if (c["day"], c["rule"]) == (alert["day"], alert["rule"])), None)
            if found:
                closed.remove(found)
                row.update(state="Ruled", ruled=found["ruled"], ruled_in=found["ruled_in"])
            else:
                row["days"] = (today - dt.date.fromisoformat(alert["day"])).days
        rows.append(row)
    newest_first = sorted(rows, key=lambda r: r["day"], reverse=True)  # stable, so Journal order stays within a day
    ordered = []
    for level in ("Red", "Orange", "Info"):
        ordered += sorted((r for r in rows if r["level"] == level and r["state"] == "Waiting"), key=lambda r: r["day"])
        ordered += [r for r in newest_first if r["level"] == level and r["state"] != "Waiting"]
    return {"rows": ordered, "problems": waiting["problems"]}


def filter_alerts(rows, levels=(), rules=(), routines=(), states=(), first=None, last=None):
    """An empty filter lets everything through. Days are compared as written in the Journal."""
    return [r for r in rows if (not levels or r["level"] in levels) and (not rules or r["rule"] in rules) and (not routines or r["routine"] in routines)
            and (not states or r["state"] in states) and (first is None or r["day"] >= str(first)) and (last is None or r["day"] <= str(last))]


def look_again_month(words):
    """The month a look-again line names, as YYYY-MM, or None. It reads the words as written and judges nothing. sensors/hunt/hunt.py reads them the same way, and a test holds the two together."""
    found = _LOOK_MONTH.search(words)
    if found:
        return f"{found[2]}-{_MONTH_NAMES[found[1]]:02d}"
    year = _LOOK_YEAR.search(words)
    return f"{year[1]}-01" if year else None


def long_day(words):
    """'Nov. 3, 2026' as 2026-11-03, or None if the words cannot be read as a date."""
    found = _LONG_DAY.match(words.strip())
    try:
        return dt.date(int(found[3]), _MONTHS[found[1][:3]], int(found[2])).isoformat()
    except (TypeError, KeyError, ValueError):
        return None


def _company_cell(words):
    """'Corning (GLW)' as ('Corning', 'GLW'). With no ticker, the whole cell is the name."""
    found = _TICKER.search(words)
    return (words[:found.start()].strip(), found[1]) if found else (words.strip(), "")


def _log_row(cells):
    name, ticker = _company_cell(cells[1])
    month = look_again_month(cells[4])
    named = bool(_LOOK_MONTH.search(cells[4]))  # "about early 2027" sorts as January but names no month, so the page shows the year
    shown = "None named" if not month else f'{nice_date(month + "-01").split()[0]} {month[:4]}' if named else month[:4]
    return {"date_words": cells[0], "date": long_day(cells[0]), "company": cells[1], "name": name, "ticker": ticker, "gate": cells[2], "reason": cells[3], "look": cells[4], "month": month, "month_shown": shown}


def rejection_log(path=REJECTION_LOG):
    """Every row of the log as written, nearest month to look again first, and a row with no month last. A row that cannot be read is listed in problems, never dropped."""
    path = Path(path)
    if not path.exists():
        return None
    text = path.read_text()
    parts = split_note(text)
    tables, _ = _md_tables(parts["top"])
    rows, problems = [], []
    for table in tables:
        if [h.lower() for h in table["headers"]] != ["date", "company", "gate", "reason", "look again"]:
            problems.append(f"{path.name}: a table has headers this page cannot read: {table['headers']}")
            continue
        for cells in table["rows"]:
            if len(cells) != 5:
                problems.append(f"{path.name}: a row has {len(cells)} cells, not 5: {cells[0]} {cells[1] if len(cells) > 1 else ''}")
            else:
                rows.append(_log_row(cells))
    if not tables:
        problems.append(f"{path.name}: no table found.")
    rows.sort(key=lambda r: (r["month"] is None, r["month"] or ""))
    return {"file": f"Research/{path.name}", "written": str(_meta(text).get("written", "")), "remark": _top_remark(parts["top"]), "rows": rows, "problems": problems}


def hunt_reports(folder=RESEARCH):
    """Every report of the monthly hunt, newest first, as hunt.py writes them: the funnel, the tested companies and the proposed lines. No run leaves an empty list."""
    out = []
    for path in sorted(Path(folder).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] Monthly hunt.md"), reverse=True):
        parts = split_note(path.read_text())
        tables = {s["title"]: _md_tables(s["text"])[0] for s in parts["sections"]}
        proposed_text = _section(parts, "Proposed lines for the Rejection log") or ""
        proposed = []
        for line in proposed_text.splitlines():
            if line.startswith("|"):
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
                if len(cells) == 5 and not set(cells[0]) <= set("-: "):
                    proposed.append(_log_row(cells))
        funnel = tables.get("The funnel") or []
        tested = tables.get("The tested companies") or []
        sources = next((line for line in (_section(parts, "The tested companies") or "").splitlines() if line.startswith("Sources:")), "")
        out.append({"file": f"Research/{path.name}", "day": path.stem[:10], "funnel": funnel[0] if funnel else None, "tested": tested[0] if tested else None, "sources": sources,
                    "proposed": proposed, "remark": _top_remark(parts["top"]), "not_done": _section(parts, "Not done") or ""})
    return out


def idea_notes(folder=INBOX):
    """Every idea note the hunt wrote to Inbox/. A note that cannot be read is listed with its problem, never hidden."""
    out = []
    for path in sorted(Path(folder).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] * idea.md"), reverse=True):
        try:
            text = path.read_text()
            meta = front_matter(text)
            parts = split_note(text)
            sources = meta.get("sources") or []
            out.append({"file": f"Inbox/{path.name}", "name": str(meta["company"]), "ticker": str(meta.get("ticker", "")), "day": str(meta.get("surfaced") or path.name[:10]),
                        "why": _section(parts, "Why it surfaced") or "", "url": sources[0] if sources else None, "refs": parts["refs"], "problem": None})
        except PROBLEMS as err:
            out.append({"file": f"Inbox/{path.name}", "name": path.name, "ticker": "", "day": path.name[:10], "why": "", "url": None, "refs": {}, "problem": str(err)})
    return out


def triage_rows(folder=RESEARCH):
    """The result rows of each triage report in Research/, as written."""
    out = []
    for path in sorted(Path(folder).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] *riage.md")):
        text = path.read_text()
        tables, _ = _md_tables(_section(split_note(text), "Results") or "")
        for table in tables:
            if not {"Company", "Sorted"} <= set(table["headers"]):
                continue
            for cells in table["rows"]:
                row = dict(zip(table["headers"], cells))
                name, ticker = _company_cell(row["Company"])
                out.append({"file": f"Research/{path.name}", "day": path.stem[:10], "company": row["Company"], "name": name, "ticker": ticker, "sorted": row["Sorted"], "look": row.get("Look again", ""), "gate3": row.get("Gate 3", "")})
    return out


def watch_tickers(path=HUNT_SETTINGS):
    """The watchlist has no file of its own. The hunt skips these tickers, from its settings."""
    path = Path(path)
    return {w["ticker"]: w.get("look_again", "") for w in tomllib.loads(path.read_text()).get("watch", [])} if path.exists() else {}


def is_paper_name(name):
    return bool(re.search(r"\b(demo|paper)\b", name, re.I))


def decision_files(journal=JOURNAL):
    """Each coach file: my view and what I then decided, in my words. The system's view is a recommendation, and the board gives none, so it is never read out."""
    out = []
    for path in sorted((Path(journal) / "decisions").glob("*.md"), reverse=True):
        if path.name == "README.md":
            continue
        text = path.read_text()
        meta = _meta(text)
        parts = split_note(text)
        view_lines = [line[2:] for line in (_section(parts, "My view") or "").splitlines() if line.startswith("- ")]
        decided = [line.strip() for line in (_section(parts, "What I then decided") or "").splitlines() if line.strip() and not line.startswith(("Only my own words", "Not said yet"))]
        out.append({"file": f"Journal/decisions/{path.name}", "name": str(meta.get("company", path.stem[11:])), "ticker": str(meta.get("ticker", "")), "day": str(meta.get("date", path.stem[:10])),
                    "stage": str(meta.get("stage", "")), "view": view_lines, "decided": " ".join(decided) or None})
    return out


def skeptic_rulings(journal=JOURNAL):
    """My rulings on a skeptic's review: a line under "What we decided" that says survived or did not survive, and says it is my decision. A reading of words, not a judgment."""
    out = []
    for path in sorted(Path(journal).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md")):
        heading = ""
        for line in path.read_text().splitlines():
            if line.startswith("#"):
                heading = line.lstrip("# ").strip()
            elif heading == "What we decided" and re.search(r"\bsurvived? the skeptic", line) and "My decision" in line:
                out.append({"day": path.stem, "file": f"Journal/{path.name}", "line": line.removeprefix("- ")})
    return out


def _evidence(stage, says, words=(), source=None, day=None, refs=None):
    """`says` is the page's own words. `words` are lines copied as written from the file named in `source`."""
    return {"stage": stage, "says": says, "words": [w for w in words if w], "source": source, "day": day, "refs": refs or {}, "paper": False}


STAGES = ("lead", "map", "tested", "idea", "watchlist", "research", "thesis", "skeptic", "decision")
OFF_RAMP = "rejected"
_STAGE_ORDER = ("lead", "map", "tested", "rejected", "idea", "watchlist", "research", "thesis", "skeptic", "decision")
_ONLY_IF_NOTHING_ELSE = ("lead", "map")


def idea_pipeline(radar, log, reports, ideas, triage, watch, decisions, rulings, notes, research=RESEARCH):
    """Every company or lead at one stage, from what the files already say. It raises nothing and judges nothing.

    A company sits at its newest dated step. On the same day, the furthest step wins. A row on the screen or a note on the map counts only when nothing else is on file,
    because the screen comes back every run and the map skips no one. The rest of what is on file stays beside it as "also on file"."""
    book = {}
    by_name = {r["name"]: (r["ticker"] or r["name"]).upper() for r in notes}
    note_of = {(r["ticker"] or r["name"]).upper(): r for r in notes}

    def entry(key, name, ticker="", plain_name=True):
        """A note's name wins, then the name our own files use. SEC's name, from the screen, is the last resort."""
        item = book.setdefault(key, {"key": key, "name": name, "ticker": ticker, "evidence": [], "note": note_of.get(key), "named_by_sec": not plain_name})
        if plain_name and item["named_by_sec"]:
            item.update(name=name, ticker=ticker or item["ticker"], named_by_sec=False)
        return item

    def key_of(name, ticker):
        return ticker.upper() if ticker else by_name.get(name, name.upper())

    for row in notes:
        if row["problem"]:
            continue
        item = entry(key_of(row["name"], row["ticker"]), row["name"], row["ticker"])
        checked = row.get("last_checked") or ""
        item["evidence"].append(_evidence("map", "A note in Companies/. Status in the note:", [row["status"]], row["file"], checked if _real_day(checked) else None))

    run_day = (radar or {}).get("run_date")
    lead_rows = []
    for step in (radar or {"screen": {"steps": []}})["screen"]["steps"]:
        for hidden, leads in ((False, step["leads"]), (True, step.get("hidden_leads", []))):
            for lead in leads:
                key = by_name.get(lead.get("on_map")) or (lead.get("ticker") or lead["name"]).upper()
                item = entry(key, lead["name"], lead.get("ticker") or "", plain_name=False)
                item["evidence"].append(_evidence("lead", f'A row on the radar\'s screen, {step["earlier"]} to {step["later"]}.', (), (radar or {}).get("report"), run_day))
                lead_rows.append((key, step, lead, hidden))

    for row in log["rows"] if log else []:
        item = entry(key_of(row["name"], row["ticker"]), row["name"], row["ticker"])
        item["evidence"].append(_evidence("rejected", f'In the rejection log, {row["gate"]}.', (), log["file"], row["date"]))
    for report in reports:
        for row in report["proposed"]:
            item = entry(key_of(row["name"], row["ticker"]), row["name"], row["ticker"])
            item["evidence"].append(_evidence("tested", f'The monthly hunt tested it. A proposed line for the log, {row["gate"]}, not in the log unless I add it:', [row["reason"]], report["file"], report["day"]))
    for note in ideas:
        if note["problem"]:
            continue
        item = entry(key_of(note["name"], note["ticker"]), note["name"], note["ticker"])
        item["evidence"].append(_evidence("idea", "An idea note the hunt wrote. It cleared the screen and two quick gates, with no thesis and no skeptic's review.", note["why"].splitlines(), note["file"], note["day"], note["refs"]))
    for row in triage:
        stage = {"watchlist": "watchlist", "research": "research"}.get(row["sorted"].strip("* ").lower())
        if stage:
            item = entry(key_of(row["name"], row["ticker"]), row["name"], row["ticker"])
            item["evidence"].append(_evidence(stage, f'Sorted "{row["sorted"]}" in the triage. What Gate 3 found, then when to look again:', [row["gate3"], row["look"]], row["file"], row["day"]))
    for ticker in watch:
        if not any(e["stage"] == "watchlist" for e in book.get(ticker, {"evidence": []})["evidence"]):
            item = entry(ticker, ticker, ticker)
            item["evidence"].append(_evidence("watchlist", "Named on the hunt's watchlist in its settings. No triage row found for it.", (), "sensors/hunt/settings.toml", None))
    for path in sorted(Path(research).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] * thesis draft.md")):
        name = path.stem[11:].removesuffix(" thesis draft")
        item = entry(key_of(name, ""), name, "")
        item["evidence"].append(_evidence("thesis", "A thesis draft in Research/. A draft, not a recorded thesis.", (), f"Research/{path.name}", path.stem[:10]))
    for ruling in rulings:
        for key, item in list(book.items()):
            if re.search(rf"(?<!\w){re.escape(item['name'])}(?!\w)", ruling["line"]):
                item["evidence"].append(_evidence("skeptic", "My ruling on the skeptic's review:", [ruling["line"]], ruling["file"], ruling["day"]))
    for file in decisions:
        item = entry(key_of(file["name"], file["ticker"]), file["name"], file["ticker"])
        says = "A coach file. My view, then what I decided, in my words:" if file["decided"] else "A coach file. My view, in my words, and no decision of mine in it yet:"
        item["evidence"].append({**_evidence("decision", says, [*file["view"], file["decided"]], file["file"], file["day"]), "paper": is_paper_name(file["name"])})

    def rank(ev):
        return (ev["day"] or "", _STAGE_ORDER.index(ev["stage"]))

    stages = {stage: [] for stage in (*STAGES, OFF_RAMP)}
    for item in book.values():
        strong = [ev for ev in item["evidence"] if ev["stage"] not in _ONLY_IF_NOTHING_ELSE]
        pool = strong or [ev for ev in item["evidence"] if ev["stage"] == "map"] or item["evidence"]
        at = max(pool, key=rank)
        item["at"] = at
        item["stage"] = at["stage"]
        item["also"] = sorted((ev for ev in item["evidence"] if ev is not at), key=lambda ev: _STAGE_ORDER.index(ev["stage"]), reverse=True)
        stages[at["stage"]].append(item)
    for rows in stages.values():
        rows.sort(key=lambda item: item["name"].lower())

    for row in log["rows"] if log else []:
        row["stage"] = book[key_of(row["name"], row["ticker"])]["stage"]
    steps = []
    moved = 0
    for step in (radar or {"screen": {"steps": []}})["screen"]["steps"]:
        here = [(lead, hidden) for key, s, lead, hidden in lead_rows if s is step and book[key]["stage"] == "lead"]
        steps.append({"step": step, "leads": [lead for lead, hidden in here if not hidden], "hidden": [lead for lead, hidden in here if hidden]})
    for key, _, lead, _ in lead_rows:
        if book[key]["stage"] != "lead":
            moved += len(lead["lines"])
    rows_total = sum(len(lead["lines"]) for _, _, lead, _ in lead_rows)
    return {"stages": stages, "steps": steps, "screen_rows": rows_total, "rows_elsewhere": moved, "radar": radar}


def ideas_view(journal=JOURNAL, research=RESEARCH, inbox=INBOX, radar_runs=RADAR_RUNS, companies=COMPANIES, settings=HUNT_SETTINGS):
    """What the Ideas half of the screen reads. A file that cannot be read becomes one problem, and the other parts still show."""
    problems = []

    def part(label, fallback, read, *args):
        found, trouble = _block(read, *args)
        if trouble:
            problems.append(f"{label} could not be read: {trouble}")
            return fallback
        return found

    radar = part("The saved radar run", None, latest_radar, radar_runs)
    log = part("The rejection log", None, rejection_log, Path(research) / "Rejection log.md")
    reports = part("The hunt's reports", [], hunt_reports, research)
    ideas = part("The idea notes", [], idea_notes, inbox)
    triage = part("The triage reports", [], triage_rows, research)
    watch = part("The hunt's settings", {}, watch_tickers, settings)
    decisions = part("The coach files", [], decision_files, journal)
    rulings = part("The Journal", [], skeptic_rulings, journal)
    notes = part("Companies/", [], company_list, companies)
    pipeline = idea_pipeline(radar, log, reports, ideas, triage, watch, decisions, rulings, notes, research)
    problems += [f'{r["file"]} could not be read: {r["problem"]}' for r in notes if r["problem"]]
    problems += [f'{n["file"]} could not be read: {n["problem"]}' for n in ideas if n["problem"]]
    problems += (log or {}).get("problems", [])
    triaged = sorted({r["file"] for r in triage})
    return {**pipeline, "log": log, "reports": reports, "problems": problems, "pages": notes, "triage_files": triaged}


def yield_view(cache=prices.CACHE, downloads=macro.DOWNLOADS, edgar_cache=EDGAR_CACHE):
    """Same inputs and steps as sensors/macro/draw.py, without its writes."""
    rows, entry = prices.read_latest(Path(cache) / CORNING, CORNING)
    end = dt.date.fromisoformat(entry["last"])
    start = macro.window_start(end)
    aaa = macro.read_series("AAA", downloads, end)
    if aaa is None:
        raise ValueError("AAA.csv is not downloaded yet.")
    facts_path = sec_folder(CORNING, edgar_cache) / "facts.jsonl"
    facts = [json.loads(line) for line in facts_path.read_text().splitlines()]
    steps = earnings.steps_in_window(earnings.eps_steps(facts), start)
    ey = earnings.yield_series(rows, steps, start)
    if not ey:
        raise ValueError("No earnings yield in the window.")
    months = draw.build_months(start, end, {"AAA": aaa["rows"]}, ey)
    latest = ey[-1]
    step = next(s for s in steps if s["accession"] == latest["accession"])
    aaa_day, aaa_value = [(d, v) for d, v in aaa["rows"] if v is not None][-1]
    above, compared = draw.beat_count(months)
    last_above, since = draw.since_above(months)
    return {"months": months, "yield": latest["yield"], "close": latest["close"], "eps": latest["eps"],
            "date": latest["date"], "step": step, "aaa": aaa_value, "aaa_month": aaa_day,
            "aaa_downloaded": parse_time(aaa["downloaded_utc"]), "aaa_url": macro.page_url("AAA"),
            "above": above, "compared": compared, "last_above": last_above, "since": since,
            "fetched": parse_time(entry["started_utc"])}


# ---- Age of each source ----

def sec_folder(ticker, cache=EDGAR_CACHE):
    table = json.loads((Path(cache) / "company_tickers.json").read_text())
    for row in table.values():
        if row["ticker"] == ticker:
            return Path(cache) / f"CIK{int(row['cik_str']):010d}"
    raise ValueError(f"{ticker} is not in the saved SEC ticker list.")


def _newest_filed(path):
    return max(json.loads(line)["filed"] for line in Path(path).read_text().splitlines())


def _source(name, used_for, retrieved=None, data_label=None, data_end=None, note="", url=None, problem=None, kind=None, counted=None, no_limit=None):
    """`kind` names my limit in age_limits.toml and `counted` is the day it counts from. A source with neither says why in `no_limit`."""
    return {"name": name, "used_for": used_for, "retrieved": retrieved, "data_label": data_label,
            "data_end": data_end, "note": note, "url": url, "problem": problem, "kind": kind, "counted": counted if counted is not None else data_end, "no_limit": no_limit}


def _guarded(name, used_for, read):
    try:
        return read()
    except PROBLEMS as err:
        return _source(name, used_for, problem=f"It could not be read: {type(err).__name__}: {err}. A fresh run of its sensor, sensors/README.md, would fill it.")


def _guarded_list(name, used_for, read):
    try:
        return read()
    except PROBLEMS as err:
        return [_source(name, used_for, problem=f"It could not be read: {type(err).__name__}: {err}.")]


def _price_source(ticker, cache):
    name, used = f"Yahoo prices, {ticker}", "Last price, earnings yield"
    manifest = prices.load_manifest(Path(cache) / ticker)
    entry = prices.latest_good(manifest)
    if entry is None:
        return _source(name, used, problem=f"No price on file. {close_fill(ticker)}")
    tries = manifest["attempts"]
    note = f"Last try failed: {tries[-1]['started_utc'][:10]}." if tries[-1]["status"] != "ok" else ""
    day = dt.date.fromisoformat(entry["last"])
    return _source(name, used, parse_time(entry["started_utc"]), nice_date(day), day, note, kind="close")


def _sec_source(ticker, cache, manifest_key, jsonl, name, used, url):
    folder = sec_folder(ticker, cache)
    entry = json.loads((folder / "manifest.json").read_text())[manifest_key]
    day = dt.date.fromisoformat(_newest_filed(folder / jsonl))
    when = parse_time(entry["retrieved_utc"])
    return _source(name, used, when, f"Filed {nice_date(day)}", day, url=url or entry["url"], kind="sec_copy", counted=when.date())


def latest_periodic(ticker, cache=EDGAR_CACHE):
    """The newest 10-Q or 10-K on the saved filing list, or None. It reads the list and fetches nothing."""
    folder = sec_folder(ticker, cache)
    rows = [json.loads(line) for line in (folder / "filings.jsonl").read_text().splitlines()]
    found = [r for r in rows if r["form"] in ("10-Q", "10-K")]
    if not found:
        return None
    newest = max(found, key=lambda r: r["filed"])
    return {"form": newest["form"], "filed": newest["filed"], "url": newest["url"], "retrieved": parse_time(json.loads((folder / "manifest.json").read_text())["submissions.json"]["retrieved_utc"])}


def _periodic_source(ticker, cache):
    name, used = f"Latest 10-Q or 10-K, {ticker}", "When the value refresh is due"
    found = latest_periodic(ticker, cache)
    if found is None:
        return _source(name, used, problem=f"None on the saved filing list. sensors/edgar/edgar.py {ticker} would fill it.")
    day = dt.date.fromisoformat(found["filed"])
    return _source(name, used, found["retrieved"], f'{found["form"]}, filed {nice_date(day)}', day, url=found["url"], kind="periodic_filing")


def _oldest_note(folder, name, used, kind):
    """Every note's last checked date in a folder. The oldest is what the row shows, and a note with no such date is named."""
    days, undated = [], []
    for path in sorted(Path(folder).glob("*.md")):
        if path.name == "README.md":
            continue
        day = str(_meta(path.read_text()).get("last checked", ""))
        if _real_day(day):
            days.append(dt.date.fromisoformat(day[:10]))
        else:
            undated.append(path.stem)
    if not days:
        return _source(name, used, problem=f"No note in {Path(folder).name}/ gives a last checked date. Checking a note against a source, then writing its date, would fill it.")
    note = f"{len(days)} notes. " + (f'No last checked date: {", ".join(undated)}. Writing one in each would fill them.' if undated else "")
    newest = max(path.stat().st_mtime for path in Path(folder).glob("*.md"))
    return _source(name, used, dt.datetime.fromtimestamp(newest, dt.timezone.utc), f"Oldest last checked {nice_date(min(days))}", min(days), note=note, kind=kind)


def _research_source(folder):
    """The newest thesis or kill-line file for each company. An older one that a newer one replaced does not count."""
    name, used = "Thesis and kill-line files, oldest", "Claims, kill lines and the calendar of checks"
    newest = {}
    for path in Path(folder).glob("*.md"):
        found = re.fullmatch(r"(\d{4}-\d{2}-\d{2}) (.+?) (thesis draft|thesis note|kill criteria)", path.stem)
        if found:
            newest[found[2]] = max(newest.get(found[2], ""), found[1])
    if not newest:
        return _source(name, used, problem="None in Research/. The thesis skill writes them there, for a company that passed triage.")
    day = dt.date.fromisoformat(min(newest.values()))
    return _source(name, used, parse_time(f"{day}T00:00:00+00:00"), f"Written {nice_date(day)}", day, note=f'Newest file for each of: {", ".join(sorted(newest))}. Retrieved is the date in the file name.', kind="research_file")


def _routine_sources(journal):
    last = journal_alerts(journal)["last_run"]
    rows = []
    for routine, kind in ROUTINE_LIMITS.items():
        name, used = f"{routine}, last record", "What the routines wrote"
        if routine not in last:
            rows.append(_source(name, used, problem="No record in the Journal yet. Its first run would fill it. A run that did not happen leaves no line."))
            continue
        day = dt.date.fromisoformat(last[routine])
        rows.append(_source(name, used, parse_time(f"{day}T00:00:00+00:00"), f"Record of {nice_date(day)}", day, note="Retrieved is the Journal day.", kind=kind))
    return rows


def _portfolio_sources(folder):
    """Each note in Portfolio/, real or paper. A note that cannot be read is shown as a problem by the screens that read it."""
    rows = []
    for path in sorted(Path(folder).glob("*.md")):
        if path.name == "README.md":
            continue
        meta = front_matter(path.read_text())
        day = dt.date.fromisoformat(str(meta["last checked"]))
        label = "Paper portfolio note" if meta.get("kind") == "paper" else f"{path.stem}, Portfolio note"
        note = "Made-up money. " if meta.get("kind") == "paper" else ""
        rows.append(_source(label, "Portfolio and cash", health.file_time(path), f"Last checked {nice_date(day)}", day, note=note + "Retrieved is the note's file time, when it was last edited.", kind="portfolio_note"))
    return rows


def _inbox_source(folder):
    notes = [n for n in read_inbox(folder) if not n["problem"]]
    if not notes:
        return _source("Inbox 8-K notes", "Latest 8-Ks", problem="No notes in Inbox.")
    newest = max(n["filed"] for n in notes)
    written = max((Path(folder) / n["name"]).stat().st_mtime for n in notes)
    day = dt.date.fromisoformat(newest)
    return _source("Inbox 8-K notes", "Latest 8-Ks", dt.datetime.fromtimestamp(written, dt.timezone.utc),
                   f"Filed {nice_date(day)}", day, note="Retrieved is the newest note's file time. Editing a note moves it.",
                   no_limit="No limit: no new 8-K is not an old source. The filing list's own age speaks for that.")


def _fred_source(series_id, used, downloads, today):
    name = {"AAA": "FRED, Moody's Aaa", "DGS10": "FRED, 10-year Treasury", "CPIAUCSL": "FRED, CPI"}[series_id]
    found = macro.read_series(series_id, downloads, today)
    if found is None:
        return _source(name, used, problem=f"{series_id}.csv is not downloaded yet. Downloading it by hand, as sensors/README.md says, would fill it.", url=macro.page_url(series_id))
    day = dt.date.fromisoformat(found["last_value_date"])
    if found["frequency"] == "monthly":  # a monthly figure covers the month, so its age counts from the month's end
        label, day = nice_month(day), day.replace(day=calendar.monthrange(day.year, day.month)[1])
    else:
        label = nice_date(day)
    return _source(name, used, parse_time(found["downloaded_utc"]), label, day, url=macro.page_url(series_id),
                   note="Retrieved is the file's modified time.", kind=None if series_id == "DGS10" else "fred_monthly",
                   no_limit="No limit: this file is saved and no screen shows it." if series_id == "DGS10" else None)


def _note_source():
    day = dt.date.fromisoformat(health.read_note()["last_checked"])
    return _source("Corning note", "Financial health summary, tables behind its charts", health.file_time(health.NOTE),
                   f"Last checked {nice_date(day)}", day, note="Retrieved is the note's file time, when it was last edited.", kind="company_note")


def _tenk_source():
    newest = health.latest_10k()
    day = dt.date.fromisoformat(newest["filed"])
    return _source("Latest 10-K, saved copy", "The check on the financial health panel", health.file_time(health._cached_path(newest["url"])),
                   f"Filed {nice_date(day)}", day, note="Retrieved is the saved file's time.", url=newest["url"], kind="tenk")


def _radar_source(runs):
    name, used = "Catalyst radar, saved run", "Catalyst radar"
    run = latest_radar(runs)
    if run is None:
        return _source(name, used, problem="No radar run on file. Run the radar by hand.")
    day = dt.date.fromisoformat(run["run_date"])
    return _source(name, used, parse_time(run["run_utc"]), f"Run {nice_date(day)}", day, note="Its SEC frames were read during that run.", kind="radar_run")


def _valuation_source(runs):
    name, used = "Valuation, saved run", "Corning price against value"
    run = company_run("Corning", CORNING, runs)["run"]
    if run is None:
        return _source(name, used, problem="No valuation run on file. Run sensors/valuation/save.py by hand.")
    day = dt.date.fromisoformat(run["worked_out"])
    return _source(name, used, parse_time(run["run_utc"]), f"Worked out {nice_date(day)}", day,
                   note=f'Its price is the close of {nice_date(run["price"]["date"])}.', kind="value_run")


def source_rows(now=None, watchlist=WATCHLIST, cache=prices.CACHE, edgar_cache=EDGAR_CACHE, inbox=INBOX,
                downloads=macro.DOWNLOADS, runs=RADAR_RUNS, valuation_runs=VALUATION_RUNS, journal=JOURNAL, notes=POSITION_NOTES, companies=COMPANIES, catalysts=CATALYSTS, research=RESEARCH):
    today = (now or now_utc()).date()
    rows = []
    for company in load_watchlist(watchlist):
        ticker = company["ticker"]
        rows.append(_guarded(f"Yahoo prices, {ticker}", "Last price, earnings yield", lambda: _price_source(ticker, cache)))
        rows.append(_guarded(f"SEC filing list, {ticker}", "A newer 8-K than this list would not show",
                             lambda: _sec_source(ticker, edgar_cache, "submissions.json", "filings.jsonl",
                                                 f"SEC filing list, {ticker}", "A newer 8-K than this list would not show", None)))
        rows.append(_guarded(f"Latest 10-Q or 10-K, {ticker}", "When the value refresh is due", lambda: _periodic_source(ticker, edgar_cache)))
    rows.append(_guarded(f"SEC financial facts, {CORNING}", "EPS in the earnings yield",
                         lambda: _sec_source(CORNING, edgar_cache, "companyfacts.json", "facts.jsonl",
                                             f"SEC financial facts, {CORNING}", "EPS in the earnings yield", None)))
    rows.append(_guarded("Inbox 8-K notes", "Latest 8-Ks", lambda: _inbox_source(inbox)))
    rows.append(_guarded("Catalyst radar, saved run", "Catalyst radar", lambda: _radar_source(runs)))
    rows.append(_guarded("Valuation, saved run", "Corning price against value", lambda: _valuation_source(valuation_runs)))
    rows += _guarded_list("Portfolio notes", "Portfolio and cash", lambda: _portfolio_sources(notes))
    rows.append(_guarded("Company notes, oldest", "The Company page", lambda: _oldest_note(companies, "Company notes, oldest", "The Company page", "company_note")))
    rows.append(_guarded("Catalyst notes, oldest", "Coming up, and the Company page", lambda: _oldest_note(catalysts, "Catalyst notes, oldest", "Coming up, and the Company page", "catalyst_note")))
    rows.append(_guarded("Thesis and kill-line files, oldest", "Claims, kill lines and the calendar of checks", lambda: _research_source(research)))
    rows += _guarded_list("Routine records", "What the routines wrote", lambda: _routine_sources(journal))
    rows.append(_guarded("Corning note", "Financial health summary, tables behind its charts", lambda: _note_source()))
    rows.append(_guarded("Latest 10-K, saved copy", "The check on the financial health panel", lambda: _tenk_source()))
    for series_id, used in (("AAA", "Aaa yield"), ("DGS10", "Saved, not shown on this page"), ("CPIAUCSL", "Saved, not shown on this page")):
        rows.append(_guarded(series_id, used, lambda s=series_id, u=used: _fred_source(s, u, downloads, today)))
    return rows


def month_end(day):
    """A monthly figure counts from the end of its month."""
    day = _as_day(day)
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


DAILY_RUNS = SENSORS / "daily" / "runs"
SENSOR_FEEDS = {"8-K watcher": "Latest 8-Ks and the Inbox's 8-K notes", "Radar": "Coming up, the leads and the radar's tables"}


def run_trouble(runs=None):
    """What the Daily run's newest digest says about its own sensors, as it wrote it. It reads and compares nothing else.

    A run can die after its sensors and before its brief. Then no line reaches the Journal, so this is the only place a failure shows. None when the newest run is clean."""
    files = sorted(Path(runs or DAILY_RUNS).glob("[0-9]*.json"))
    if not files:
        return None
    digest = json.loads(files[-1].read_text())
    failed = [{"name": r["name"], "feeds": SENSOR_FEEDS.get(r["name"], "what it saves")} for r in digest.get("sensors", []) if not r.get("ok")]
    no_brief = not digest.get("briefed")
    if not failed and not no_brief:
        return None
    return {"file": f"sensors/daily/runs/{files[-1].name}", "day": digest["today"], "failed": failed, "no_brief": no_brief}


def run_trouble_or_problem(runs=None):
    try:
        return run_trouble(runs), None
    except PROBLEMS as err:
        return None, f"{type(err).__name__}: {err}"


def past_sources(rows, today=None):
    """The sources past my limits, in words. Nothing compares a close to a line here, and nothing here is an alert."""
    out = []
    for r in rows:
        if r["kind"] and not r["problem"]:
            words = past_limit(r["kind"], r["counted"], today)
            if words:
                out.append({"name": r["name"], "words": words})
    return out


def age_text(then, now):
    """Plain age. Accepts two datetimes (hours under two days) or two dates (days)."""
    if isinstance(then, dt.datetime):
        hours = (now - then).total_seconds() / 3600
        if hours < 1:
            return "under 1 hour"
        if hours < 48:
            return f"{int(hours)} hour{'s' if int(hours) != 1 else ''}"
        days = int(hours // 24)
    else:
        days = (now - then).days
        if days <= 0:
            return "today"
    return f"{days} day{'s' if days != 1 else ''}"


# ---- Journal ----

BOARD_VERSION_FILE = Path(__file__).resolve().parent / "VERSION"
_DAY_FILE = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"
_ONLY_NOTHING = re.compile(r"^\W*nothing(?: new)?\W*$", re.I)  # a session saying so, as Rules/memory.md asks. "Nothing new. No investing decision." has words of its own, and stays.
_FOR_ME = re.compile(r"^\W*for me\b", re.I)
_WE_DECIDED = re.compile(r"^\*\*We decided\b")  # the first entries, written before the three headings existed
_WRITTEN = re.compile(r"Written (\d{4}-\d{2}-\d{2})")
_SESSION_NOTE = re.compile(r"^(?:Correction|Addition|Update) to the session above\b")  # a note on the session, which By day still shows. It is no decision or open item.
_COMMENT = re.compile(r"%%.*?%%", re.S)
TOP_OF_FILE = "Top of the day's file"


def board_version(path=None):
    """What the launcher and the browser tab call this board. Unknown stays Unknown."""
    try:
        return Path(path or BOARD_VERSION_FILE).read_text().strip() or None
    except OSError:
        return None


def _session_items(text, heading):
    """The lines under one ### heading, as written. A nested line stays with the line above it. Words after --- are a note on the session, not an item."""
    items, inside = [], False
    for line in text.splitlines():
        if line.startswith("#"):
            inside = line.lstrip("# ").strip() == heading
        elif line.strip() == "---":
            inside = False
        elif inside and line.strip():
            if line.startswith((" ", "\t")) and items:
                items[-1] += "\n" + line.strip()
            else:
                items.append(line.strip().removeprefix("- ").removeprefix("* "))
    return items


def read_journal_day(path):
    """One day's file: the words above its first ## heading, and each ## block under its heading. Nothing is dropped except the file's title and the --- rules between blocks."""
    parts = split_note(Path(path).read_text())
    clean = lambda text: "\n".join(line for line in text.splitlines() if line.strip() != "---").strip()  # noqa: E731
    top = "\n".join(line for line in parts["top"].splitlines() if not line.startswith("# "))
    return {"day": Path(path).stem, "file": f"Journal/{Path(path).name}", "top": clean(top), "refs": parts["refs"],
            "sessions": [{"heading": s["title"], "text": clean(s["text"]), "raw": s["text"]} for s in parts["sections"]]}


def journal_view(journal=JOURNAL):
    """Every day, newest first, and across days every decided and every left-open line. Inside a day the newest session comes first. It reads as written and judges nothing."""
    days, problems = [], []
    for path in sorted(Path(journal).glob(_DAY_FILE), reverse=True):
        try:
            days.append(read_journal_day(path))
        except PROBLEMS as err:
            problems.append(f"{path.name} could not be read: {err}. Putting the file right would fill it.")
    decided, left_open, quiet = [], [], {"decided": 0, "left_open": 0}
    for day in days:
        where = {"day": day["day"], "file": day["file"], "refs": day["refs"]}
        for session in reversed(day["sessions"]):
            for out, heading, kind in ((decided, "What we decided", "decided"), (left_open, "What we left open", "left_open")):
                for words in _session_items(session["raw"], heading):
                    if _ONLY_NOTHING.match(words):
                        quiet[kind] += 1
                    elif not _SESSION_NOTE.match(words):
                        out.append({**where, "session": session["heading"], "text": words, "for_me": bool(_FOR_ME.match(words))})
        decided.extend({**where, "session": TOP_OF_FILE, "text": line.strip(), "for_me": False} for line in day["top"].splitlines() if _WE_DECIDED.match(line.strip()))
    return {"days": days, "decided": decided, "left_open": left_open, "quiet": quiet, "problems": problems}


def lesson_files(folder=LESSONS):
    """Every lesson, newest first: its title, its date and its words. The date is the note's own "Written" line, then its last-checked field, then the first date in it. With none it is None."""
    out, problems = [], []
    for path in sorted(Path(folder).glob("*.md")):
        if path.name == "README.md":
            continue
        try:
            text = path.read_text()
            body = text.split("\n---", 1)[1].split("\n", 1)[1] if text.startswith("---") else text
            body = _COMMENT.sub("", body)
            title = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), path.stem)
            words = "\n".join(line for line in body.splitlines() if not line.startswith("# "))
            found = _WRITTEN.search(text) or _DAY.search(str(_meta(text).get("last checked", "")) if text.startswith("---") else "") or _DAY.search(text)
            out.append({"file": f"Lessons/{path.name}", "title": title, "day": found[1] if found and found.re is _WRITTEN else found[0] if found else None,
                        "text": _REF.sub("", words).strip(), "refs": dict(_REF.findall(body))})
        except PROBLEMS as err:
            problems.append(f"{path.name} could not be read: {err}. Putting the file right would fill it.")
    out.sort(key=lambda r: (r["day"] or "", r["title"]), reverse=True)
    return {"lessons": out, "problems": problems}


def search_journal(words, journal=JOURNAL, lessons=LESSONS):
    """Plain text, any case, line by line, across the daily Journal files and Lessons. It is no pattern, so any character is safe. Journal/decisions/ is left out, because a coach file holds the system's view, and the board gives none."""
    wanted = " ".join(str(words).split()).casefold()
    rows, problems = [], []
    if not wanted:
        return {"rows": rows, "problems": problems}
    files = [(path, path.stem) for path in sorted(Path(journal).glob(_DAY_FILE), reverse=True)]
    files += [(path, None) for path in sorted(Path(lessons).glob("*.md")) if path.name != "README.md"]
    for path, day in files:
        try:
            text = _COMMENT.sub(lambda m: "\n" * m[0].count("\n"), path.read_text())  # a comment is not a word on the page, and the line numbers stay the file's
        except PROBLEMS as err:
            problems.append(f"{path.name} could not be read: {err}. Putting the file right would fill it.")
            continue
        where, refs = "", dict(_REF.findall(text))
        when = day or (_WRITTEN.search(text) or [None, None])[1]
        rule_lines = text.split("\n---", 1)[0].count("\n") + 2 if text.startswith("---") else 0  # a lesson's field block is not its words
        for number, line in enumerate(text.splitlines(), 1):
            if number <= rule_lines:
                continue
            if line.startswith(("# ", "## ")):
                where = line.lstrip("# ").strip()
            if wanted in " ".join(line.split()).casefold() and not _REF.fullmatch(line.strip()):
                rows.append({"file": f"{'Journal' if day else 'Lessons'}/{path.name}", "day": when, "line": number, "where": where, "text": line.strip().removeprefix("- ").removeprefix("* ").lstrip("# "), "refs": refs})
    return {"rows": rows, "problems": problems}
