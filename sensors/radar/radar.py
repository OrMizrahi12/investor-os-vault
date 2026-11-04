"""Catalyst radar: read what the sensors saved, check catalyst dates, walk the graph for new events, screen SEC frames.

Run from the project root:
    .venv/bin/python sensors/radar/radar.py
    .venv/bin/python sensors/radar/radar.py --no-screen    skip SEC frames

It writes:
    sensors/radar/runs/YYYY-MM-DD-NN.json    the saved output. The dashboard reads this and nothing else from here.
    Research/YYYY-MM-DD Catalyst radar.md    the dated report
    Catalysts/*.md                           "radar checked" and the "Radar" section, and nothing else
    sensors/radar/state.json                 what has been reported, written last so a crash reports it again

It never asks Yahoo for a price. It reads the saved close, and computes no change from it.
SEC requests go through the EDGAR sensor's client. It gives no buy or trim view: a name match, a date and a lead are
things to read, not conclusions. It does not use base value.
"""

import argparse
import datetime as dt
import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE.parent / "edgar"), str(HERE.parent / "prices"), str(HERE)]
import edgar  # noqa: E402
import frames  # noqa: E402
import prices  # noqa: E402

SCHEMA = 1
NO_VIEW = "This radar does not set price against base value, so it gives no buy or trim view."
LEADS_LINE = "These are leads to read, never picks. A rise here can be a deal, a deposit, an acquisition, a reclassification, a season or a data slip."
STRONG = {"Stated", "Read together"}
KINDS = {"stated", "target", "forecast", "projection", "my estimate", "calc."}
KIND_WORDS = {"stated": "a date stated in a source", "target": "a target", "forecast": "a forecast", "projection": "a projected date",
              "my estimate": "my estimate", "calc.": "my arithmetic (calc.)"}
# From SEC's Form 4 general instructions.
FORM4_CODES = {"P": "open-market purchase", "S": "open-market or private sale", "A": "grant or award", "M": "option or derivative exercise",
               "F": "shares withheld for tax or exercise price", "G": "gift", "C": "conversion", "D": "sale back to the company",
               "J": "other", "V": "voluntary early report", "X": "in-the-money exercise", "W": "will or inheritance"}
INSIDER_FORMS = {"4", "4/A"}
EIGHT_K = {"8-K", "8-K/A"}
RUN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}$")


class RadarError(Exception):
    """Something the owner should see."""


class Paths:
    def __init__(self, root=ROOT, edgar_cache=None, prices_cache=None, here=None):
        root, here = Path(root), Path(here or (Path(root) / "sensors" / "radar"))
        self.root, self.here = root, here
        self.catalysts, self.companies = root / "Catalysts", root / "Companies"
        self.inbox, self.research = root / "Inbox", root / "Research"
        self.settings = HERE / "settings.toml"
        self.watchlist = root / "sensors" / "8k-watch" / "watchlist.toml"
        self.seen = root / "sensors" / "8k-watch" / "seen.json"
        self.edgar_cache = Path(edgar_cache or root / "sensors" / "edgar" / "cache")
        self.prices_cache = Path(prices_cache or root / "sensors" / "prices" / "cache")
        self.runs, self.state = here / "runs", here / "state.json"
        self.frames_cache = here / "cache" / "frames"


def nice_date(day):
    day = dt.date.fromisoformat(day) if isinstance(day, str) else day
    month = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."][day.month - 1]
    return f"{month} {day.day}, {day.year}"


def money(value):
    if abs(value) >= 1e9:
        return f"${value / 1e9:,.1f}B"
    return f"${value / 1e6:,.0f}M"


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


# ---- Notes ----

def split_note(text):
    """(front matter lines, the rest). A note with no front matter is an error, not a guess."""
    lines = text.split("\n")
    if lines[0].strip() != "---" or "---" not in lines[1:]:
        raise RadarError("no front matter")
    end = lines.index("---", 1)
    return lines[1:end], "\n".join(lines[end + 1:])


def front_fields(lines):
    out = {}
    for line in lines:
        if line.startswith((" ", "-")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) > 1:
            value = json.loads(value)
        out[key.strip()] = value
    return out


def section(body, name):
    match = re.search(rf"^## {re.escape(name)}[^\n]*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return match.group(1).strip() if match else None


def first_link(text):
    match = re.search(r"\[([^\]]+)\]\((https://[^)\s]+)\)", text or "")
    return {"label": match.group(1), "url": match.group(2)} if match else None


def note_names(folder):
    return sorted(p.stem for p in Path(folder).glob("*.md") if p.name != "README.md")


def read_catalyst(path, companies):
    item = {"title": path.stem, "file": f"Catalysts/{path.name}", "ticker": "", "window": "", "date_start": None, "date_end": None,
            "date_quote": None, "date_kind": None, "source": None, "outcome_written": False, "companies": [], "problem": None}
    try:
        lines, body = split_note(path.read_text())
    except (OSError, UnicodeDecodeError, RadarError) as err:
        item["problem"] = f"Could not read the note: {err}"
        return item
    meta = front_fields(lines)
    item.update(ticker=meta.get("ticker", ""), window=meta.get("window", ""))
    when = section(body, "When") or ""
    item["source"] = first_link(when)
    outcome = section(body, "Outcome") or ""
    item["outcome_written"] = bool(outcome) and not outcome.startswith("Not known")
    item["companies"] = sorted(set(re.findall(r"\[\[([^\]|]+)", body)) & set(companies))
    start, end, quote, kind = (meta.get(k, "") for k in ("date start", "date end", "date quote", "date kind"))
    if not (start or end or quote or kind):
        return item
    try:
        first = dt.date.fromisoformat(start)
        last = dt.date.fromisoformat(end) if end else first
    except ValueError:
        item["problem"] = f"Date fields are not dates: start {start!r}, end {end!r}."
        return item
    if last < first:
        item["problem"] = f"Date end {end} is before date start {start}."
    elif not quote or quote not in when:
        item["problem"] = f"Date quote {quote!r} is no longer in the When section, so the date fields may be out of step with the note."
    elif kind not in KINDS:
        item["problem"] = f"Date kind {kind!r} is not one of {sorted(KINDS)}."
    else:
        item.update(date_start=first.isoformat(), date_end=last.isoformat(), date_quote=quote, date_kind=kind)
    return item


def read_catalysts(paths):
    companies = note_names(paths.companies)
    return [read_catalyst(paths.catalysts / f"{n}.md", companies) for n in note_names(paths.catalysts)]


def place_dates(catalysts, today, horizon_days, wide_days):
    """Sort each catalyst into a bucket. Nothing here depends on a price."""
    horizon = today + dt.timedelta(days=horizon_days)
    for c in catalysts:
        if c["problem"]:
            c.update(bucket="problem", days_to_start=None, days_to_end=None)
            continue
        if not c["date_start"]:
            c.update(bucket="no date", days_to_start=None, days_to_end=None)
            continue
        first, last = dt.date.fromisoformat(c["date_start"]), dt.date.fromisoformat(c["date_end"])
        c["days_to_start"], c["days_to_end"] = (first - today).days, (last - today).days
        span = (last - first).days
        if last < today:
            c["bucket"] = "done" if c["outcome_written"] else "passed"
        elif last <= horizon or (span <= wide_days and first <= horizon):
            c["bucket"] = "soon"
        elif first <= horizon:
            c["bucket"] = "wide"
        else:
            c["bucket"] = "later"
    return catalysts


def date_text(c):
    if c["date_start"] == c["date_end"]:
        return nice_date(c["date_start"])
    return f'{nice_date(c["date_start"])} to {nice_date(c["date_end"])}'


def date_line(c, run_day):
    bucket = c["bucket"]
    if bucket == "problem":
        return f'**Date problem:** {c["problem"]}'
    if bucket == "no date":
        return "No date in the fields above, so the radar counts nothing here."
    what = f'"{c["date_quote"]}" in When, read as {date_text(c)}, {KIND_WORDS[c["date_kind"]]}'
    label = {"soon": "Due or opening soon", "wide": "Wide window, now open or near", "later": "Next date", "passed": "Date passed, Outcome not written",
             "done": "Date passed, Outcome written"}[bucket]
    when = f' {c["days_to_end"]} days to its end (calc., from {nice_date(run_day)}).' if c["days_to_end"] >= 0 else f' {-c["days_to_end"]} days past its end (calc., from {nice_date(run_day)}).'
    return f"**{label}:** {what}.{when}"


# ---- Typed links ----

def read_links(folder):
    """Every link in the Typed links tables, once. A row that cannot be read is listed, not dropped."""
    links, problems = {}, []
    for name in note_names(folder):
        body = (Path(folder) / f"{name}.md").read_text()
        table = section(body, "Typed links")
        if table is None:
            problems.append(f"{name}: no Typed links section")
            continue
        for line in table.splitlines():
            if not line.startswith("| ") or line.startswith("| Link") or not line.strip("| "):
                continue
            parts = [x.strip() for x in line.strip().strip("|").split(" | ")]
            if len(parts) != 7:
                problems.append(f"{name}: a row has {len(parts)} columns")
                continue
            label, other, chain, what, size, evidence, source = parts
            other = re.sub(r"\[\[|\]\]| \(no note\)", "", other)
            if label == "supplies":
                key = ("supplies", name, other)
            elif label == "customer of":
                key = ("supplies", other, name)
            elif label in ("competes with", "partners with"):
                key = (label, *sorted([name, other]))
            else:
                problems.append(f"{name}: unknown link type {label!r}")
                continue
            links.setdefault(key, {"kind": key[0], "a": key[1], "b": key[2], "chain": chain, "what": what, "size": size,
                                   "evidence": evidence, "weak": evidence not in STRONG, "source": source})
    return list(links.values()), problems


def walk(links, start):
    """Two steps out. Step 1 is any link touching the company. Step 2 stays on the chain that led there."""
    rows, near = [], set()
    for link in links:
        if start in (link["a"], link["b"]):
            node = link["b"] if link["a"] == start else link["a"]
            near.add(node)
            rows.append(dict(link, step=1, node=node, via=start))
    second = []
    for row in rows:
        for link in links:
            if row["node"] not in (link["a"], link["b"]) or start in (link["a"], link["b"]) or link["chain"] != row["chain"]:
                continue
            node = link["b"] if link["a"] == row["node"] else link["a"]
            if node not in near and not any(s["node"] == node and s["via"] == row["node"] and s["chain"] == link["chain"] for s in second):
                second.append(dict(link, step=2, node=node, via=row["node"]))
    return rows + second


def relation(row):
    verb = {"supplies": "supplies", "competes with": "competes with", "partners with": "partners with"}[row["kind"]]
    return f'{row["a"]} {verb} {row["b"]}'


# ---- Form 4 ----

def read_form4(body):
    """Who filed and what they did, from the form's own XML. Value is shares times price (calc.)."""
    root = ET.fromstring(body)
    owner = root.findtext("reportingOwner/reportingOwnerId/rptOwnerName", "").strip()
    title = root.findtext("reportingOwner/reportingOwnerRelationship/officerTitle", "").strip()
    if not title and root.findtext("reportingOwner/reportingOwnerRelationship/isDirector", "").strip() in ("1", "true"):
        title = "Director"
    moves = []
    for row in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        shares = row.findtext("transactionAmounts/transactionShares/value")
        price = row.findtext("transactionAmounts/transactionPricePerShare/value")
        moves.append({"code": row.findtext("transactionCoding/transactionCode", "").strip(),
                      "date": row.findtext("transactionDate/value", "").strip()[:10],
                      "shares": float(shares) if shares else 0.0, "price": float(price) if price else None})
    derivatives = [{"code": row.findtext("transactionCoding/transactionCode", "").strip(),
                    "security": row.findtext("securityTitle/value", "").strip(),
                    "shares": float(row.findtext("transactionAmounts/transactionShares/value") or 0)}
                   for row in root.findall("derivativeTable/derivativeTransaction")]
    relation = root.find("reportingOwner/reportingOwnerRelationship")
    roles = {tag for tag in ("isDirector", "isOfficer", "isTenPercentOwner", "isOther") if relation is not None and relation.findtext(tag, "").strip() in ("1", "true")}
    return {"owner": owner, "title": title, "roles": roles, "moves": moves, "derivatives": derivatives,
            "plan_box": root.findtext("aff10b5One", "").strip() in ("1", "true")}


def is_director_grant(form):
    """Only a director, and every row a code A grant. An officer's award, or any trade on the form, stays an event."""
    rows = form["moves"] + form["derivatives"]
    return form["roles"] == {"isDirector"} and not form["title"].replace("Director", "") and bool(rows) and all(r["code"] == "A" for r in rows)


def form4_summary(form):
    who = form["owner"] + (f' ({form["title"]})' if form["title"] else "")
    parts = []
    for code in sorted({m["code"] for m in form["moves"]}):
        rows = [m for m in form["moves"] if m["code"] == code]
        shares = sum(m["shares"] for m in rows)
        priced = [m for m in rows if m["price"]]
        worth = sum(m["shares"] * m["price"] for m in priced)
        text = f'code {code}, {FORM4_CODES.get(code, "see the form")}, {shares:,.0f} shares'
        if worth:
            text += f", about ${worth:,.0f} (calc.)"
        parts.append(text)
    for row in form["derivatives"]:
        parts.append(f'{row["security"] or "derivative"}, code {row["code"]}, {FORM4_CODES.get(row["code"], "see the form")}, {row["shares"]:,.0f} units, no value counted')
    plan = " Plan box ticked on the form." if form["plan_box"] else ""
    return f'{who}: {"; ".join(parts) or "no transaction rows"}.{plan}'


class Filings:
    """Reads a company's saved Form 4s, and saves one the sensor does not hold yet, through the EDGAR client."""

    def __init__(self, folder, client_factory):
        (Path(folder) / "documents" / "insider").mkdir(parents=True, exist_ok=True)
        self.cache = edgar.Cache(folder, client_factory, 24 * 365 * 100)  # a filed form does not change
        self.folder = Path(folder)

    def form4(self, filing, cik):
        name = Path(filing["primary_document"]).name  # the listed path is SEC's styled copy, and the plain XML sits one level up
        url = edgar.filing_url(cik, filing["accession"], name)
        form = re.sub(r"[^A-Za-z0-9]", "", filing["form"])
        return read_form4(self.cache.fetch(f'documents/insider/{filing["accession"]}-{form}-{name}', url))


# ---- What the sensors saved ----

def read_inbox(folder):
    """Inbox notes by accession. Only what the sensor wrote about attention and reason."""
    notes = {}
    for path in Path(folder).glob("*.md"):
        if path.name == "README.md":
            continue
        try:
            meta = front_fields(split_note(path.read_text())[0])
        except (OSError, UnicodeDecodeError, RadarError):
            continue
        if meta.get("accession") and meta.get("form", "8-K").strip('"').startswith("8-K"):  # other forms carry no rating here
            notes[meta["accession"]] = {"attention": meta.get("attention", ""), "rated_by": meta.get("rated by", ""),
                                        "reason": meta.get("reason", ""), "note": path.name}
    return notes


def ticker_table(paths):
    return json.loads((paths.edgar_cache / "company_tickers.json").read_text())


def main_tickers(table):
    """CIK to its first ticker. SEC lists a company's main share first, then preferred shares and warrants."""
    out = {}
    for row in table.values():
        out.setdefault(int(row["cik_str"]), row["ticker"])
    return out


def company_folder(paths, ticker, table):
    for row in table.values():
        if row["ticker"].upper() == ticker.upper():
            return paths.edgar_cache / f'CIK{int(row["cik_str"]):010d}', int(row["cik_str"])
    raise RadarError(f"{ticker} is not in the saved SEC ticker list.")


NAME_SUFFIX = r"(?:,?\s+(?:inc|incorporated|corp|corporation|co|company|plc|ltd|limited|n\.?v\.?|s\.?a\.?|se))?\.?(?:\s*/[a-z]+/?)?$"


def map_nodes(paths, table):
    """CIK to company note, using only the note's own ticker, or an exact SEC company name when it has none.

    A name alone is not enough: "Apple Hospitality REIT" is not Apple.
    """
    by_ticker = {row["ticker"].upper(): int(row["cik_str"]) for row in table.values()}
    out = {}
    for name in note_names(paths.companies):
        lines, _ = split_note((paths.companies / f"{name}.md").read_text())
        ticker = front_fields(lines).get("ticker", "").strip()
        if ticker and ticker.upper() in by_ticker:
            out[by_ticker[ticker.upper()]] = name
            continue
        pattern = re.compile(re.escape(name.lower()) + NAME_SUFFIX)
        hits = {int(row["cik_str"]) for row in table.values() if pattern.match(row["title"].lower())}
        if len(hits) == 1:
            out[hits.pop()] = name
    return out


def names_in(text, nodes, skip=()):
    return sorted(n for n in nodes if n not in skip and re.search(rf"(?<![\w&]){re.escape(n)}(?![\w&])", text))


def collect_filing_events(paths, companies, state, today, lookback, table, inbox, seen_8k, nodes, client_factory):
    """New means on the saved filing list, inside the baseline, and not reported before."""
    events, sensors, problems = [], [], []
    known = state.setdefault("companies", {})
    reported = set(state.setdefault("reported", []))
    for company in companies:
        ticker, name = company["ticker"], company["name"]
        try:
            folder, cik = company_folder(paths, ticker, table)
            filings = [json.loads(line) for line in (folder / "filings.jsonl").read_text().splitlines()]
            manifest = json.loads((folder / "manifest.json").read_text())
        except (OSError, ValueError, KeyError, RadarError) as err:
            problems.append(f"{ticker}: the saved filing list could not be read: {err}")
            continue
        baseline = known.setdefault(ticker, {"baseline": (today - dt.timedelta(days=lookback)).isoformat()})["baseline"]
        sensors.append({"name": f"SEC filing list, {ticker}", "saved": manifest["submissions.json"]["retrieved_utc"],
                        "data": f'Newest filing {filings[0]["form"]}, filed {nice_date(filings[0]["filed"])}', "url": manifest["submissions.json"]["url"]})
        forms = Filings(folder, client_factory)
        for f in sorted(filings, key=lambda x: (x["filed"], x["accession"])):
            if not baseline <= f["filed"] <= today.isoformat() or f["accession"] in reported:
                continue
            event = {"id": f["accession"], "kind": "filing", "ticker": ticker, "company": name, "form": f["form"], "filed": f["filed"],
                     "url": f["url"], "label": f'{f["form"]}, filed {nice_date(f["filed"])}', "summary": "", "text": "",
                     "attention": None, "rated_by": None}
            if f["form"] in EIGHT_K:
                note = inbox.get(f["accession"])
                entry = seen_8k.get(f["accession"], {})
                if note:
                    event.update(summary=note["reason"], attention=note["attention"], rated_by=note["rated_by"])
                else:
                    event["summary"] = "No Inbox note. Run 8-K watch, or the note was moved."
                event["text"] = " ".join([event["summary"], *entry.get("excerpts", {}).values()])
            elif f["form"] in INSIDER_FORMS:
                try:
                    form4 = forms.form4(f, cik)
                    event["summary"] = form4_summary(form4)
                    event["director_grant"] = is_director_grant(form4)
                except (edgar.EdgarError, ET.ParseError, OSError, ValueError) as err:
                    event["summary"] = f"Could not read the form: {err}"
                    problems.append(f'{f["accession"]}: {err}')
            else:
                event["summary"] = f'{f["description"] or f["form"]}. On the filing list. The radar does not read its text.'
            events.append(event)
    return events, sensors, problems


def inbox_sensor(inbox, paths):
    if not inbox:
        return {"name": "Inbox 8-K notes", "saved": None, "data": "No notes", "url": None}
    newest = max(p.stat().st_mtime for p in paths.inbox.glob("*.md") if p.name != "README.md")
    filed = max(n["note"][:10] for n in inbox.values())
    return {"name": "Inbox 8-K notes", "saved": dt.datetime.fromtimestamp(newest, dt.timezone.utc).isoformat(timespec="seconds"),
            "data": f"{len(inbox)} notes, newest filed {nice_date(filed)}", "url": None}


def price_sensors(paths, companies):
    """The saved close and its date. Nothing is compared, so nothing here can become an event."""
    out = []
    for company in companies:
        folder = paths.prices_cache / company["ticker"]
        try:
            rows, entry = prices.read_latest(folder, company["ticker"])
            out.append({"name": f'Yahoo prices, {company["ticker"]}', "saved": entry["started_utc"],
                        "data": f'Close ${rows[-1]["close"]:.2f} on {nice_date(rows[-1]["date"])}', "url": None})
        except (prices.PriceError, OSError, ValueError, KeyError) as err:
            out.append({"name": f'Yahoo prices, {company["ticker"]}', "saved": None, "data": f"Unknown: {err}", "url": None})
    return out


# ---- Events to catalysts ----

def bearing(event, catalysts, form_map, nodes, hub):
    """Which catalysts to read this event against, and why. A name match, not a reading."""
    found = {}
    for title in form_map.get(event["form"], []):
        found.setdefault(title, f'{event["form"]} is listed for this catalyst in the radar settings')
    for name in event.get("named", []):
        for c in catalysts:
            if name in c["companies"]:
                found.setdefault(c["title"], f"names {name}")
    if event["company"] != hub:
        for c in catalysts:
            if event["company"] in c["companies"]:
                found.setdefault(c["title"], f'about {event["company"]}')
    titles = {c["title"] for c in catalysts}
    return [{"title": t, "why": found[t]} for t in sorted(found) if t in titles]


def hub_of(catalysts):
    counts = {}
    for c in catalysts:
        for name in c["companies"]:
            counts[name] = counts.get(name, 0) + 1
    return max(counts, key=counts.get) if counts else None


def note_with_radar(text, c, run_day, report_stem, new_lines):
    """The note with today's radar fields. Only "radar checked" and the Radar section change. Old event lines stay."""
    lines = text.split("\n")
    end = lines.index("---", 1)
    head = [line for line in lines[1:end] if not line.startswith("radar checked:")]
    at = next((i for i, line in enumerate(head) if line.startswith("last checked:")), len(head) - 1)
    head.insert(at + 1, f'radar checked: "{run_day}"')
    body = "\n".join(lines[end + 1:])
    old = section(body, "Radar")
    kept = re.findall(r"^- .*$", old or "", re.M)
    event_lines = kept + [line for line in new_lines if line not in kept]
    block = ["## Radar", "%% Written by sensors/radar/radar.py, which replaces this section each run. Write your reading under Outcome. %%", "",
             f"*Last run {nice_date(run_day)}. Report: [[{report_stem}]].*", "", date_line(c, run_day), ""]
    if event_lines:
        block += ["Events to read against this catalyst. A name match, not a reading:", "", *event_lines, ""]
    new = "\n".join(block) + "\n"
    if old is not None:
        body = re.sub(r"^## Radar[^\n]*\n.*?(?=^## |\Z)", lambda _: new, body, count=1, flags=re.S | re.M)
    elif "## Rules this note depends on" in body:
        body = body.replace("## Rules this note depends on", new + "## Rules this note depends on", 1)
    else:
        body = body.rstrip("\n") + "\n\n" + new
    return "\n".join(["---", *head, "---"]) + "\n" + body


def update_notes(paths, catalysts, events, run_day, report_stem):
    changed = 0
    for c in catalysts:
        if c["bucket"] == "problem" and c["problem"].startswith("Could not read"):
            continue
        new_lines = [f'- [{e["label"]}]({e["url"]}), {e["ticker"] or e["company"]}: {why}. Seen {nice_date(run_day)}.'
                     for e in events for b in e["catalysts"] if b["title"] == c["title"] for why in [b["why"]]]
        path = paths.catalysts / f'{c["title"]}.md'
        text = path.read_text()
        fresh = note_with_radar(text, c, run_day, report_stem, new_lines)
        if fresh != text:
            edgar._write_atomic(path, fresh.encode())
            changed += 1
    return changed


# ---- Report ----

def lead_flags(line, lead=None):
    flags = [lead["not_new_growth"]] if lead and lead.get("not_new_growth") else []
    if line.get("unit_slip"):
        flags.append("later is about 1,000 or 1,000,000 times earlier, check the units")
    if line.get("rounded_differently"):
        flags.append("figures rounded differently")
    if line["accession_earlier"] == line["accession_later"]:
        flags.append("both from one filing")
    return "; ".join(flags)


def lead_rows(leads, limit, retrieved):
    rows = ["| Company | Ticker | Map | Measure | Earlier | Later | Change (calc.) | Same step a year earlier (calc.) | Flags | Sources |", "|---|---|---|---|---|---|---|---|---|---|"]
    shown = 0
    for lead in leads:
        for line in lead["lines"]:
            if shown >= limit:
                return rows
            shown += 1
            year = "not on file" if line["year_ago_pct"] is None else f'{line["year_ago_pct"]:+,.1f}%'
            rows.append(f'| {cell(lead["name"])} | {cell(lead.get("ticker") or "none")} | {cell(lead.get("on_map") or "")} | {cell(line["label"])} | '
                        f'{money(line["earlier"])} at {nice_date(line["end_earlier"])} | {money(line["later"])} at {nice_date(line["end_later"])} | '
                        f'+{line["rise_pct"]:,.1f}%, +{money(line["rise_usd"])} | {year} | {cell(lead_flags(line, lead))} | '
                        f'[filing with the later balance, {nice_date(line["end_later"])}]({line["filing_later"]}); '
                        f'[frame {line["frame_later"]}, retrieved {nice_date(retrieved)}]({line["frame_url_later"]}); '
                        f'[frame {line["frame_earlier"]}, retrieved {nice_date(retrieved)}]({line["frame_url_earlier"]}) |')
    return rows


def hidden_lines(run):
    """A line saying what this run hid, so nothing goes missing without a count."""
    hidden = run.get("hidden")
    if not hidden or not (hidden["grant_count"] or hidden["lead_count"] or hidden["step2_count"]):
        return []
    return [f'Hidden from these counts: {hidden["grant_count"]} director stock grants, {hidden["lead_count"]} screen leads that may not be new growth, '
            f'{hidden["step2_count"]} second-step links from walks started only by a screen lead. All are in the saved output, under `hidden`, `hidden_leads` and `hidden_step2`.', ""]


def render_report(run, limit):
    day = run["run_date"]
    d = run["dates"]
    screen = run["screen"]
    out = ["---", "company:", "ticker:", "track: catalyst radar", f"written: {day}", "base value: not used here", "---", "",
           f"# Catalyst radar, {nice_date(day)}", "",
           f'*Written by `sensors/radar/radar.py`. Saved output: `{run["run_file"]}`. Waiting for me to read. Not merged into company notes.*', "",
           f'**{len(d["soon"])} catalyst dates due or opening within {run["horizon_days"]} days, {len(d["passed"])} passed with no Outcome written, {len(run["events"])} new events, '
           f'{screen.get("lead_count", 0)} screen leads.** {NO_VIEW} {LEADS_LINE}', ""]
    out += hidden_lines(run)
    out += ["## What the sensors have saved", "", "| Sensor | Saved | Newest inside |", "|---|---|---|"]
    for s in run["sensors"]:
        saved = nice_date(s["saved"][:10]) if s["saved"] else "Unknown"
        out.append(f'| {cell(s["name"])} | {saved} | {cell(s["data"])} |')
    out += ["", "A saved close is shown for its date. The radar computes no change from it, and a price is never an event here.", ""]
    if run["problems"]:
        out += ["## Problems", ""] + [f"- {cell(p)}" for p in run["problems"]] + [""]

    def date_table(rows):
        table = ["| Catalyst | Date, as read | Note's words | Kind | Days to its start (calc.) | Days to its end (calc.) | Source in When |", "|---|---|---|---|---|---|---|"]
        for c in rows:
            source = f'[{c["source"]["label"]}]({c["source"]["url"]})' if c["source"] else "No link in the When section"
            table.append(f'| [[{c["title"]}]] | {date_text(c)} | "{cell(c["date_quote"])}" | {KIND_WORDS[c["date_kind"]]} | {c["days_to_start"]} | {c["days_to_end"]} | {source} |')
        return table + [""]

    out += [f'## Dates due or opening within {run["horizon_days"]} days', "", "Future dates are targets or forecasts, not results.", ""]
    out += date_table(d["soon"]) if d["soon"] else ["None.", ""]
    out += ["## Dates passed, Outcome not written", ""]
    out += date_table(d["passed"]) if d["passed"] else ["None.", ""]
    out += ["## Wide windows, open or near", "", "These ranges are long, so they say little about timing.", ""]
    out += date_table(d["wide"]) if d["wide"] else ["None.", ""]
    out += [f'Also: {d["later_count"]} with dates further out, {d["no_date_count"]} with no date given.', ""]

    out += ["## New events", ""]
    if run["events"]:
        out += ["| Filed | Company | Source | What the sensor saved | Named in it | Read against |", "|---|---|---|---|---|---|"]
        for e in run["events"]:
            bears = "; ".join(f'[[{b["title"]}]] ({cell(b["why"])})' for b in e["catalysts"]) or "None singled out"
            link = f'[{e["label"]}]({e["url"]})' if e["url"] else e["label"]
            out.append(f'| {nice_date(e["filed"])} | {cell(e["company"])} | {link} | {cell(e["summary"])} | {cell(", ".join(e["named"])) or "None"} | {bears} |')
        out.append("")
    else:
        out += ["None since the last run.", ""]

    out += ["## Graph walk", ""]
    if run["walks"]:
        out += ["From the Typed links tables in `Companies/`, two steps out, or one step when only a screen lead started the walk. Step 2 stays on the chain that led there. A weak link is Conditional, Reported or My reading. A step means a link exists, not that the event reaches that company.", ""]
        for start, w in run["walks"].items():
            rows = w["rows"]
            out += [f'### {start}', "", f'Started by {w["events"]} new events. {w["step1"]} links at step 1, {w["step2"]} at step 2{hidden_step2(w)}, {w["weak"]} weak. Named in the events: {", ".join(w["named"]) or "none"}. Chains: {", ".join(w["chains"]) or "none"}.', ""]
            if rows:
                out += ["| Step | Reaches | Link | Chain | Size | Evidence | Source |", "|---|---|---|---|---|---|---|"]
                out += [f'| {r["step"]} | {cell(r["node"])} | {cell(relation(r))} | {cell(r["chain"])} | {cell(r["size"])} | {cell(r["evidence"])} | {r["source"]} |' for r in rows]
                out.append("")
    else:
        out += ["Nothing to walk.", ""]

    out += ["## Market screen: SEC XBRL frames", "", LEADS_LINE, ""]
    if screen["status"] != "ok":
        out += [f'**The screen did not finish: {cell(screen["status"])}** The rest of this report stands.', ""]
    else:
        retrieved = screen["retrieved"]
        rules = screen["rules"]
        out += [f'A company is listed if a balance rose at least {rules["min_rise_pct"]}% and {money(rules["min_rise_usd"])} in one quarter, to at least {money(rules["min_later_usd"])}, on the same tag, with the two balances {rules["min_days_between"]} to {rules["max_days_between"]} days apart. Dollars only, US GAAP only. Those limits are Claude\'s first choices, in `sensors/radar/settings.toml`.', "",
                f'What a frame cannot do: it shows one number per company per quarter, last filed. It holds no filing date, so the date beside each figure is the balance date. An earlier figure may have been restated in a later filing. Companies that disclose these only in a 10-K, or only in text, do not appear. Requests to SEC this run: {screen["requests"]}, busiest second {screen["busiest_second"]}, against SEC\'s limit of 10.', ""]
        for step in screen["steps"]:
            state = (f'Still filling: {step["filers_later"]} of about {step["filers_earlier"]} filer rows so far.' if step["filling"]
                     else f'{step["filers_later"]} filer rows against {step["filers_earlier"]}.')
            hid = f' {len(step["hidden_leads"])} more hidden.' if step.get("hidden_leads") else ""
            out += [f'### {step["earlier"]} to {step["later"]}', "", f'{len(step["leads"])} companies.{hid} {state} Same step a year earlier means {step["year_ago_step"]}.', ""]
            out += lead_rows(step["leads"], limit, retrieved) + [""]
            lines = sum(len(lead["lines"]) for lead in step["leads"])
            if lines > limit:
                out += [f'Showing {limit} of {lines} rows, largest percent first. The rest are in the saved output.', ""]
            if step["unit_check"]:
                out += ["Left out of the ranking, because the units look wrong:", ""] + lead_rows(step["unit_check"], limit, retrieved) + [""]
    out += ["## Reading", "", "Not read yet. Everything above is script output. Whoever reads the filings writes here what they found, with sources and dates.", ""]
    out += ["## Rules this report depends on", "", "- [[facts]]: every fact here needs a source and a date.", "- [[when-to-buy]]: strategic value never counts toward covering the price.", "- [[monitoring]]: check the news against the thesis. No alert for a price move alone.", ""]
    return "\n".join(out)


# ---- The run ----

def hidden_step2(walk_row):
    count = len(walk_row.get("hidden_step2", []))
    return f", {count} more hidden" if count else ""


def run_names(paths, day):
    """(run file stem, report stem). A second run the same day gets its own files, so a reading is never overwritten."""
    taken = {p.stem for p in paths.runs.glob(f"{day}-*.json")} if paths.runs.exists() else set()
    seq = 1
    while f"{day}-{seq:02d}" in taken or (paths.research / f'{report_stem(day, seq)}.md').exists():
        seq += 1
    return f"{day}-{seq:02d}", report_stem(day, seq)


def report_stem(day, seq):
    return f"{day} Catalyst radar" + (f" {seq}" if seq > 1 else "")


def run_screen(settings, paths, today, client_factory, clients, nodes_by_cik, table, state, use_screen):
    if not use_screen:
        return {"status": "skipped by --no-screen", "steps": [], "lead_count": 0}
    rules = {k: v for k, v in settings.items() if k != "tag"}
    tickers = main_tickers(table)
    try:
        found = frames.screen(settings, today, client_factory, paths.frames_cache)
    except edgar.EdgarError as err:
        return {"status": str(err), "steps": [], "lead_count": 0}
    reported = set(state.setdefault("reported", []))
    count = 0
    for step in found["steps"]:
        step["filers_earlier"] = sum(t["filers_earlier"] for t in step["tally"].values())
        step["filers_later"] = sum(t["filers_later"] for t in step["tally"].values())
        step["filling"] = step["filers_later"] < 0.9 * step["filers_earlier"]
        for lead in step["leads"] + step["unit_check"]:
            lead["ticker"] = tickers.get(lead["cik"])
            lead["on_map"] = nodes_by_cik.get(lead["cik"])
            lead["id"] = f'screen:{step["later"]}:{lead["cik"]}'
            lead["new"] = lead["id"] not in reported
        # A lead that may not be new growth is hidden, unless the company is on our map.
        step["hidden_leads"] = [lead for lead in step["leads"] if lead["not_new_growth"] and not lead["on_map"]]
        step["leads"] = [lead for lead in step["leads"] if not lead["not_new_growth"] or lead["on_map"]]
        count += len(step["leads"])
    client = clients[0] if clients else None
    return {"status": "ok", "steps": found["steps"], "missing_frames": found["missing_frames"], "lead_count": count,
            "retrieved": today.isoformat(), "rules": rules, "requests": len(client.sent) if client else 0,
            "busiest_second": client.busiest_second() if client else 0}


def screen_events(screen):
    """A lead on our map counts as an event, so it gets walked. Other leads stay on the list."""
    out = []
    for step in screen["steps"]:
        for lead in step["leads"]:
            if lead["on_map"] and lead["new"]:
                line = lead["lines"][0]
                out.append({"id": lead["id"], "kind": "screen", "ticker": lead["ticker"], "company": lead["on_map"], "form": "Screen",
                            "filed": line["end_later"], "url": line["filing_later"], "label": f'filing with the balance at {nice_date(line["end_later"])}',
                            "summary": f'Screen lead, {step["earlier"]} to {step["later"]}: {line["label"]} {money(line["earlier"])} to {money(line["later"])}, +{line["rise_pct"]:,.1f}% (calc.).',
                            "text": "", "attention": None, "rated_by": None})
    return out


def run(paths=None, use_screen=True, now=None, client_factory=None):
    paths = paths or Paths()
    now = now or edgar.now_utc()
    today = now.date()
    day = today.isoformat()
    try:
        settings = tomllib.loads(paths.settings.read_text())
        companies = tomllib.loads(paths.watchlist.read_text())["company"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as err:
        raise RadarError(f"Cannot read the settings or watchlist: {err}") from err
    clients = []

    def factory():
        if not clients:
            if client_factory:
                clients.append(client_factory())
            else:
                sec = edgar.load_settings()
                clients.append(edgar.SecClient(sec["user_agent"], sec["rate"]))
        return clients[0]

    state = json.loads(paths.state.read_text()) if paths.state.exists() else {}
    catalysts = place_dates(read_catalysts(paths), today, settings["dates"]["horizon_days"], settings["dates"]["wide_window_days"])
    links, link_problems = read_links(paths.companies)
    nodes = sorted({x for link in links for x in (link["a"], link["b"])} | set(note_names(paths.companies)))
    table = ticker_table(paths)
    by_cik = map_nodes(paths, table)
    inbox = read_inbox(paths.inbox)
    seen_8k = json.loads(paths.seen.read_text()) if paths.seen.exists() else {}
    hub = hub_of(catalysts)

    events, sensors, problems = collect_filing_events(paths, companies, state, today, settings["dates"]["first_run_lookback_days"],
                                                      table, inbox, seen_8k, nodes, factory)
    sensors += [inbox_sensor(inbox, paths)] + price_sensors(paths, companies)
    problems += link_problems + [f'{c["title"]}: {c["problem"]}' for c in catalysts if c["problem"]]
    screen = run_screen(settings["screen"], paths, today, factory, clients, by_cik, table, state, use_screen)
    if screen["status"] == "ok":
        sensors.append({"name": "SEC XBRL frames", "saved": now.isoformat(timespec="seconds"),
                        "data": ", ".join(f'{s["later"]}: {s["filers_later"]} filer rows' for s in screen["steps"]), "url": None})
    else:
        problems.append(f'Screen: {screen["status"]}')
    events += screen_events(screen)
    grants = [e for e in events if e.get("director_grant")]
    events = [e for e in events if not e.get("director_grant")]
    for event in grants:
        event.update(named=[], catalysts=[])
    for event in events:
        event["named"] = names_in(event["text"], nodes, skip=(event["company"],))
        event["catalysts"] = bearing(event, catalysts, settings.get("form_catalysts", {}), nodes, hub)
    walks = {}
    for start in sorted({e["company"] for e in events}):
        started = [e for e in events if e["company"] == start]
        rows = walk(links, start)
        hidden = []
        if all(e["kind"] == "screen" for e in started):  # an unread lead is not yet known to mean anything, so one step only
            hidden = [r for r in rows if r["step"] == 2]
            rows = [r for r in rows if r["step"] == 1]
        walks[start] = {"rows": rows, "hidden_step2": hidden, "events": len(started), "step1": sum(r["step"] == 1 for r in rows), "step2": sum(r["step"] == 2 for r in rows),
                        "weak": sum(r["weak"] for r in rows), "chains": sorted({r["chain"] for r in rows}),
                        "named": sorted({n for e in started for n in e["named"]})}
    run_stem, stem = run_names(paths, day)
    pick = lambda b: sorted((c for c in catalysts if c["bucket"] == b), key=lambda c: (c["date_end"] or "", c["title"]))  # noqa: E731
    output = {"schema": SCHEMA, "run_date": day, "run_utc": now.isoformat(timespec="seconds"), "run_file": f"sensors/radar/runs/{run_stem}.json",
              "report": f"Research/{stem}.md", "first_run": not state.get("last_run"), "horizon_days": settings["dates"]["horizon_days"],
              "no_view": NO_VIEW, "leads_line": LEADS_LINE, "sensors": sensors, "problems": problems,
              "dates": {"soon": pick("soon"), "passed": pick("passed"), "wide": pick("wide"), "later_count": len(pick("later")),
                        "no_date_count": len(pick("no date")), "problem_count": len(pick("problem")), "total": len(catalysts)},
              "events": events, "walks": walks, "screen": screen,
              "hidden": {"grants": grants, "grant_count": len(grants), "lead_count": sum(len(s["hidden_leads"]) for s in screen["steps"]),
                         "step2_count": sum(len(w["hidden_step2"]) for w in walks.values())}}
    paths.research.mkdir(exist_ok=True)
    paths.runs.mkdir(parents=True, exist_ok=True)
    report = render_report(output, settings["screen"]["shown_in_report"])
    changed = update_notes(paths, catalysts, events, day, stem)
    edgar._write_atomic(paths.research / f"{stem}.md", report.encode())
    edgar._write_atomic(paths.runs / f"{run_stem}.json", json.dumps(output, indent=1, ensure_ascii=False).encode())
    ids = set(state.get("reported", [])) | {e["id"] for e in events + grants}
    ids |= {lead["id"] for step in screen["steps"] for lead in step["leads"] + step["hidden_leads"]}
    state.update(reported=sorted(ids), last_run=output["run_utc"])
    edgar._write_atomic(paths.state, json.dumps(state, indent=1).encode())
    return output, changed


def main():
    parser = argparse.ArgumentParser(description="Check saved sensor data and catalyst dates, walk the graph, and screen SEC frames.")
    parser.add_argument("--no-screen", action="store_true", help="skip the SEC frames screen")
    args = parser.parse_args()
    try:
        out, changed = run(use_screen=not args.no_screen)
    except RadarError as err:
        sys.exit(f"Stopped: {err}")
    d, s = out["dates"], out["screen"]
    print(f'Report: {out["report"]}\nSaved output: {out["run_file"]}\nCatalyst notes changed: {changed} of {d["total"]}.')
    print(f'Dates: {len(d["soon"])} due soon, {len(d["passed"])} passed with no Outcome, {len(d["wide"])} wide, {d["later_count"]} later, {d["no_date_count"]} no date, {d["problem_count"]} with a problem.')
    print(f'New events: {len(out["events"])}. Walks: {", ".join(out["walks"]) or "none"}.')
    print(f'Hidden: {out["hidden"]["grant_count"]} director stock grants, {out["hidden"]["lead_count"]} leads, {out["hidden"]["step2_count"]} second-step links.')
    print(f'Screen: {s["status"]}, {s.get("lead_count", 0)} leads. Requests to SEC: {s.get("requests", 0)}. Busiest second: {s.get("busiest_second", 0)}.')
    for problem in out["problems"]:
        print("Problem:", problem)


if __name__ == "__main__":
    main()
