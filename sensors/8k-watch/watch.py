"""8-K watch: find new 8-Ks for each company on the watchlist and write one Inbox note per filing.

Run from the project root:
    uv run python sensors/8k-watch/watch.py            ask SEC for the latest filing list
    uv run python sensors/8k-watch/watch.py --cached   use the EDGAR sensor's cache if under 24 hours old

Filing lists and documents come through sensors/edgar/edgar.py. Each 8-K is read, because
EDGAR's index can leave out items (Lessons/Read 8-K items in the filing.md).

"New" means not in seen.json. A note you delete or move is not written again.
A note you edited is never overwritten.
"""

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "edgar"))
import edgar  # noqa: E402

WATCHLIST = HERE / "watchlist.toml"
READINGS = HERE / "readings.toml"
SEEN = HERE / "seen.json"
INBOX = ROOT / "Inbox"
FORMS = {"8-K", "8-K/A"}
LEVELS = ("high", "medium", "low")

# Titles from SEC's Form 8-K: https://www.sec.gov/files/form8-k.pdf (undated, retrieved Nov. 2, 2026).
ITEM_NAMES = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "1.04": "Mine Safety – Reporting of Shutdowns and Patterns of Violations",
    "1.05": "Material Cybersecurity Incidents",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant",
    "2.04": "Triggering Events That Accelerate or Increase a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard; Transfer of Listing",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year",
    "5.04": "Temporary Suspension of Trading Under Registrant's Employee Benefit Plans",
    "5.05": "Amendments to the Registrant's Code of Ethics, or Waiver of a Provision of the Code of Ethics",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "5.08": "Shareholder Director Nominations",
    "6.01": "ABS Informational and Computational Material",
    "6.02": "Change of Servicer or Trustee",
    "6.03": "Change in Credit Enhancement or Other External Support",
    "6.04": "Failure to Make a Required Distribution",
    "6.05": "Securities Act Updating Disclosure",
    "6.06": "Static Pool",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}

# The first-pass rating, before anyone opens the filing. A separate question from the flags:
# a flag is the owner's list, and this also catches bad news that list leaves out, such as 4.02.
HIGH_ITEMS = {"1.01", "1.02", "1.03", "2.01", "2.04", "2.06", "3.01", "3.02", "3.03", "4.01", "4.02", "5.01", "5.02"}
MEDIUM_ITEMS = {"1.05", "2.02", "2.03", "2.05", "7.01", "8.01"}


class WatchError(Exception):
    """Something the owner should see. The script stops instead of writing a doubtful note."""


def item_name(number):
    return ITEM_NAMES.get(number, "not in Form 8-K's item list")


def _lines(document):
    """Filing HTML to one line per block. Raw line breaks inside a block do not count."""
    text = document.decode("utf-8", "replace") if isinstance(document, bytes) else document
    text = re.sub(r"(?is)<ix:header.*?</ix:header>|<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?i)</(p|div|tr|table|li|h[1-6])>|<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</t[dh]>", " ", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = re.sub(r"[‎‏﻿]", "", text).replace("\xa0", " ")
    return [line for line in (re.sub(r"\s+", " ", raw).strip() for raw in text.split("\n")) if line]


# A heading starts its block. "Item 7.01 of this report" also can, so those words rule it out.
_HEADING = re.compile(r"(?i)^item\s*(\d\.\d\d)(?!\d)[.:\s\u2013\u2014-]*(.*)$")
_CROSS_REFERENCE = re.compile(r"(?i)^(of|in|above|below|and|or|hereof|is)\b")
_BOILERPLATE = re.compile(r"(?i)^(in accordance with general instruction|the information (furnished|in this|contained)|\(d\)\s*exhibit)")


def read_items(document):
    """Return ({item: first real paragraph}, in filing order) from the filing's own headings."""
    items, current = {}, None
    for line in _lines(document):
        match = _HEADING.match(line)
        if match and not _CROSS_REFERENCE.match(match.group(2)):
            current = match.group(1)
            items.setdefault(current, "")
        elif re.match(r"(?i)^signatures?\b", line):
            current = None
        elif current and not items[current] and not _BOILERPLATE.match(line) and len(line) > 40:
            items[current] = line
    return items


def split_index_items(text):
    return [i.strip() for i in (text or "").split(",") if i.strip()]


def combine_items(index_items, filing_items):
    """Union of the two, sorted. Trust neither alone: either may lack an item the other has."""
    return sorted(set(index_items) | set(filing_items))


def rule_rating(items):
    high = [i for i in items if i in HIGH_ITEMS]
    medium = [i for i in items if i in MEDIUM_ITEMS]
    if not items:
        return "medium", "Rule only, not read yet: no items could be found, so open it."
    if high:
        return "high", f"Rule only, not read yet: Item {high[0]} ({item_name(high[0])})."
    if medium:
        return "medium", f"Rule only, not read yet: Item {medium[0]} ({item_name(medium[0])})."
    return "low", f"Rule only, not read yet: only routine items ({', '.join(items)})."


def load_watchlist(path=WATCHLIST):
    try:
        data = tomllib.loads(Path(path).read_text())
        flags, companies = data["flag_items"], data["company"]
        for company in companies:
            dt.date.fromisoformat(company["since"])
            if not company["name"] or not company["ticker"]:
                raise KeyError("name or ticker")
    except (OSError, KeyError, ValueError, TypeError, tomllib.TOMLDecodeError) as e:
        raise WatchError(f"Cannot read {path}: {e!r}. Each [[company]] needs name, ticker and since.") from e
    unknown = [i for i in flags if i not in ITEM_NAMES]
    if unknown:
        raise WatchError(f"{path}: flag_items has items Form 8-K does not list: {unknown}")
    return flags, companies


def load_readings(path=READINGS):
    if not Path(path).exists():
        return {}
    try:
        rows = tomllib.loads(Path(path).read_text()).get("reading", [])
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise WatchError(f"Cannot read {path}: {e!r}") from e
    readings = {}
    for row in rows:
        missing = [k for k in ("accession", "attention", "reason", "read") if not row.get(k)]
        if missing or row["attention"] not in LEVELS:
            raise WatchError(f"{path}: bad reading {row.get('accession')}: missing {missing} or attention not in {LEVELS}")
        if row["accession"] in readings:
            raise WatchError(f"{path}: two readings for {row['accession']}")
        readings[row["accession"]] = row
    return readings


def load_seen(path=SEEN):
    return json.loads(Path(path).read_text()) if Path(path).exists() else {}


def save_seen(seen, path=SEEN):
    edgar._write_atomic(Path(path), json.dumps(seen, indent=1, sort_keys=True).encode())


def rating(entry, readings):
    """The reading if someone opened the filing, else the rule. Always says which."""
    reading = readings.get(entry["accession"])
    if reading:
        return {"attention": reading["attention"], "reason": reading["reason"], "rated_by": "reading", "reading": reading}
    attention, reason = rule_rating(entry["items"])
    return {"attention": attention, "reason": reason, "rated_by": "rule", "reading": None}


def nice_date(iso):
    day = dt.date.fromisoformat(iso)
    month = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."][day.month - 1]
    return f"{month} {day.day}, {day.year}"


def index_url(entry):
    plain = entry["accession"].replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{entry['cik']}/{plain}/{entry['accession']}-index.html"


def note_name(entry):
    form = re.sub(r"[^A-Za-z0-9-]", "-", entry["form"])
    return f"{entry['filed']} {entry['ticker']} {form} {entry['accession']}.md"


def _fm(value):
    return json.dumps(value, ensure_ascii=False)  # JSON strings and lists are valid YAML


def render_note(entry, flags, readings, company_note=True):
    rated = rating(entry, readings)
    flagged = [i for i in entry["items"] if i in flags]
    label = f"{entry['form']}, filed {nice_date(entry['filed'])}"
    reading = rated["reading"]
    sources = [entry["url"], index_url(entry)]
    if reading and reading.get("source_url"):
        sources.append(reading["source_url"])
    out = ["---", f"ticker: {entry['ticker']}", f"company: {_fm(entry['company'])}", f"form: {entry['form']}",
           f'filed: "{entry["filed"]}"', f"accession: {entry['accession']}", f"items: {_fm(entry['items'])}",
           f"flagged: {_fm(flagged)}", f"attention: {rated['attention']}", f"rated by: {rated['rated_by']}",
           f"reason: {_fm(rated['reason'])}", "sources:"]
    out += [f"  - {_fm(s)}" for s in sources] + ["---", ""]
    out += [f"# {entry['company']} {entry['form']}, filed {nice_date(entry['filed'])}", ""]
    who = f"[[{entry['company']}]]" if company_note else entry["company"]
    out += [f"*Written by `sensors/8k-watch/watch.py`. Company: {who}. Source: [{label}][k]; [filing index, {nice_date(entry['filed'])}][i].*", ""]
    how = (f"Read {nice_date(reading['read'])}; Claude's judgment, for me to confirm." if reading
           else "Rated from the item numbers only. Nobody has opened this filing yet.")
    out += [f"**Attention: {rated['attention']}.** {rated['reason']} {how}", ""]
    if reading and reading.get("source_url"):
        out += [f"Reason also rests on: [{reading.get('source_label', 'exhibit')}][x].", ""]
    out += ["## Items", "", "| Item | Name | Flagged |", "|---|---|---|"]
    out += [f"| {i} | {item_name(i)} | {'yes' if i in flags else 'no'} |" for i in entry["items"]]
    out += ["", f"Flagged: {', '.join(flagged) if flagged else 'none'}.", ""]
    # Item 9.01 is only an exhibit list, so it has nothing to quote.
    excerpts = [(i, entry["excerpts"].get(i)) for i in entry["items"] if i != "9.01" and entry["excerpts"].get(i)]
    if excerpts:
        out += ["## What the filing says", "", "The first paragraph under each item, copied from the filing.", ""]
        for number, text in excerpts:
            short = text if len(text) <= 400 else text[:400].rsplit(" ", 1)[0] + " ..."
            out += [f"**Item {number}:** {short}", ""]
    out += ["## Index check", ""]
    if not entry["items_filing"]:
        out += [f"**No item headings could be read in the filing.** Items above come from EDGAR's index only: {', '.join(entry['items_index']) or 'none'}. Open the filing.", ""]
    else:
        only_filing = [i for i in entry["items_filing"] if i not in entry["items_index"]]
        only_index = [i for i in entry["items_index"] if i not in entry["items_filing"]]
        if only_filing:
            out += [f"EDGAR's index leaves out {', '.join(only_filing)}, which the filing lists."]
        if only_index:
            out += [f"EDGAR's index lists {', '.join(only_index)}, but no such heading was found in the filing."]
        if not only_filing and not only_index:
            out += ["EDGAR's index and the filing list the same items."]
        out += [""]
    out += [f"[k]: {entry['url']}", f"[i]: {index_url(entry)}"]
    if reading and reading.get("source_url"):
        out += [f"[x]: {reading['source_url']}"]
    return "\n".join(out) + "\n"


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def write_new(company, filings, fetch, seen, flags, readings, inbox, seen_path, today):
    """Write a note for each new 8-K, oldest first. Saved after each one, so a stop loses nothing."""
    written = []
    new = [f for f in filings if f["form"] in FORMS and company["since"] <= f["filed"] <= today and f["accession"] not in seen]
    for filing in sorted(new, key=lambda f: (f["filed"], f["accession"])):
        if not filing["url"]:
            raise WatchError(f"{filing['accession']} has no document on EDGAR's list.")
        filing_items = read_items(fetch(filing))
        index_items = split_index_items(filing["items"])
        entry = {
            "accession": filing["accession"], "cik": company["cik"], "ticker": company["ticker"],
            "company": company["name"], "form": filing["form"], "filed": filing["filed"],
            "report_date": filing["report_date"], "url": filing["url"], "items_index": index_items,
            "items_filing": sorted(filing_items), "items": combine_items(index_items, filing_items),
            "excerpts": filing_items,
        }
        name = note_name(entry)
        text = render_note(entry, flags, readings, company_note=(inbox.parent / "Companies" / f"{company['name']}.md").exists())
        edgar._write_atomic(inbox / name, text.encode())
        entry.update(note=name, note_sha=_sha(text))
        seen[entry["accession"]] = entry
        save_seen(seen, seen_path)
        written.append(entry)
    return written


def sync_readings(seen, flags, readings, inbox, seen_path):
    """Bring notes up to date with readings added later. Leaves deleted and hand-edited notes alone."""
    updated, skipped = [], []
    for entry in seen.values():
        path = inbox / entry["note"]
        if not path.exists():
            continue
        current = path.read_text()
        fresh = render_note(entry, flags, readings, company_note=(inbox.parent / "Companies" / f"{entry['company']}.md").exists())
        if fresh == current:
            continue
        if _sha(current) != entry["note_sha"]:
            skipped.append(entry["note"])
            continue
        edgar._write_atomic(path, fresh.encode())
        entry["note_sha"] = _sha(fresh)
        updated.append(entry["note"])
    if updated:
        save_seen(seen, seen_path)
    return updated, skipped


def _sec_fetcher(cik, folder):
    """Reuses the EDGAR sensor's limiter, User-Agent and cache. Named by accession: old names repeat."""
    settings = edgar.load_settings()
    client = edgar.SecClient(settings["user_agent"], settings["rate"])
    (Path(folder) / "documents").mkdir(parents=True, exist_ok=True)
    cache = edgar.Cache(folder, lambda: client, edgar.MAX_AGE_HOURS)

    def fetch(filing):
        document = Path(filing["primary_document"]).name
        return cache.fetch(f"documents/{filing['accession']}-{document}", filing["url"])
    return fetch, client


def run(cached=False):
    flags, companies = load_watchlist()
    readings = load_readings()
    seen = load_seen()
    today = dt.date.today().isoformat()
    INBOX.mkdir(exist_ok=True)
    for company in companies:
        folder = edgar.pull(company["ticker"], refresh=not cached)
        company = dict(company, cik=int(folder.name.removeprefix("CIK")))
        filings = [json.loads(line) for line in (folder / "filings.jsonl").read_text().splitlines()]
        fetch, client = _sec_fetcher(company["cik"], folder)
        written = write_new(company, filings, fetch, seen, flags, readings, INBOX, SEEN, today)
        print(f"{company['name']}: {len(written)} new 8-K notes since {company['since']}. "
              f"Document requests to SEC: {len(client.sent)}. Busiest second: {client.busiest_second()}.")
        for entry in written:
            rated = rating(entry, readings)
            print(f"  {entry['filed']} {','.join(entry['items']):<16} {rated['attention']:<7} {rated['reason']}")
    updated, skipped = sync_readings(seen, flags, readings, INBOX, SEEN)
    if updated:
        print(f"Updated {len(updated)} notes from readings.toml.")
    for name in skipped:
        print(f"Left alone, because it was edited by hand: Inbox/{name}")


def main():
    parser = argparse.ArgumentParser(description="Write one Inbox note for each new 8-K on the watchlist.")
    parser.add_argument("--cached", action="store_true", help="use the EDGAR sensor's cached list if under 24 hours old")
    args = parser.parse_args()
    try:
        run(args.cached)
    except (WatchError, edgar.EdgarError) as e:
        sys.exit(f"Stopped: {e}")


if __name__ == "__main__":
    main()
