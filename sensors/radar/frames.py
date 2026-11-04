"""The market-wide screen: SEC's free XBRL frames, one balance per company per calendar quarter.

Every request goes through the EDGAR sensor's client, which declares us, spaces the requests below SEC's limit
of 10 per second, honours Retry-After, and stops on a 403. Frames are cached, so a second run the same day sends nothing.

A row here is a lead to read, never a pick. A frame cannot tell a new order from an acquisition, a reclassification,
a season or a unit error. It holds no ticker, no form and no filing date.
"""

import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "edgar"))
import edgar  # noqa: E402

CACHE = HERE / "cache" / "frames"
RECENT_HOURS, OLD_HOURS = 24, 24 * 7  # the two newest quarters are still filling up. Older frames rarely change.


def latest_ended_quarter(today):
    """The newest calendar quarter that has ended by today, as (year, quarter)."""
    quarter = (today.month - 1) // 3
    return (today.year, quarter) if quarter else (today.year - 1, 4)


def quarters_back(year, quarter, count):
    """Newest first."""
    out = []
    for _ in range(count):
        out.append((year, quarter))
        year, quarter = (year, quarter - 1) if quarter > 1 else (year - 1, 4)
    return out


def frame_name(year, quarter):
    return f"CY{year}Q{quarter}I"  # I: a balance at a point in time


def frame_url(tag, name):
    return f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{name}.json"


def filing_index_url(cik, accession):
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}-index.html"


class Fetcher:
    """Reads a frame from the cache or SEC, and refuses to pass the run's request cap."""

    def __init__(self, cache, client_factory, cap):
        self.cache, self.client_factory, self.cap = cache, client_factory, cap
        self.missing = []

    def __call__(self, tag, name, recent):
        client = self.client_factory()
        if len(client.sent) >= self.cap:
            raise edgar.EdgarError(f"Stopped at the cap of {self.cap} SEC requests for this run.")
        self.cache.max_age = dt.timedelta(hours=RECENT_HOURS if recent else OLD_HOURS)
        try:
            return json.loads(self.cache.fetch(f"{tag}-{name}.json", frame_url(tag, name)))
        except edgar.EdgarError as err:
            if getattr(err.__cause__, "code", None) == 404:  # SEC has no frame until someone files one
                self.missing.append(f"{tag} {name}")
                return None
            raise


CURRENT, NONCURRENT = "ContractWithCustomerLiabilityCurrent", "ContractWithCustomerLiabilityNoncurrent"
TOTAL_NOT_UP = "Current plus noncurrent total did not grow"
UP_A_YEAR_AGO = "Same step also up by the limit a year earlier"


def by_company(frame):
    rows = {}
    for row in (frame or {}).get("data", []):
        if row["cik"] in rows:
            raise edgar.EdgarError(f"Frame {frame.get('tag')} {frame.get('ccp')} has two rows for CIK {row['cik']}.")
        rows[row["cik"]] = row
    return rows


def is_unit_slip(earlier, later):
    """A later balance about 1,000 or 1,000,000 times the earlier one is more likely a scaling slip than a business."""
    ratio = later / earlier
    return any(0.8 * size <= ratio <= 1.2 * size for size in (1_000, 1_000_000))


def rounded_differently(earlier, later):
    """One figure is to the nearest $100M and the other is not, so they may come from different parts of a filing."""
    return (earlier % 100_000_000 == 0) != (later % 100_000_000 == 0)


def step_rise(a, b, limits):
    """The rise from a to b in percent (calc.), or None if the two are not one quarter apart or a is not positive."""
    days = (dt.date.fromisoformat(b["end"]) - dt.date.fromisoformat(a["end"])).days
    if not limits["min_days_between"] <= days <= limits["max_days_between"] or a["val"] <= 0:
        return None
    return (b["val"] - a["val"]) / a["val"] * 100


def compare(tag, label, frames, limits):
    """Rows for one tag and one step. frames: the earlier, later, and same two a year before, each (name, frame)."""
    (name_a, frame_a), (name_b, frame_b), year_a, year_b = frames
    earlier, later = by_company(frame_a), by_company(frame_b)
    before, after = by_company(year_a[1]), by_company(year_b[1])
    rows, counts = [], {"both": 0, "apart": 0, "not_positive": 0}
    for cik, b in later.items():
        a = earlier.get(cik)
        if a is None:
            continue
        counts["both"] += 1
        if a["val"] <= 0:
            counts["not_positive"] += 1
            continue
        pct = step_rise(a, b, limits)
        if pct is None:
            counts["apart"] += 1
            continue
        rise = b["val"] - a["val"]
        if pct < limits["min_rise_pct"] or rise < limits["min_rise_usd"] or b["val"] < limits["min_later_usd"]:
            continue
        year_pct = step_rise(before[cik], after[cik], limits) if cik in before and cik in after else None
        rows.append({
            "cik": cik, "name": b["entityName"], "tag": tag, "label": label,
            "frame_earlier": name_a, "frame_later": name_b,
            "end_earlier": a["end"], "end_later": b["end"], "earlier": a["val"], "later": b["val"],
            "rise_usd": rise, "rise_pct": round(pct, 1),
            "year_ago_pct": None if year_pct is None else round(year_pct, 1),
            "accession_earlier": a["accn"], "accession_later": b["accn"],
            "filing_earlier": filing_index_url(cik, a["accn"]), "filing_later": filing_index_url(cik, b["accn"]),
            "frame_url_earlier": frame_url(tag, name_a), "frame_url_later": frame_url(tag, name_b),
            "unit_slip": is_unit_slip(a["val"], b["val"]),
            "rounded_differently": rounded_differently(a["val"], b["val"]),
        })
    return rows, counts


def not_new_growth(lead, totals, min_rise_pct):
    """Why a lead may not be new growth, or None. The radar hides these unless the company is on our map.

    totals: the four frames of (current earlier, current later, noncurrent earlier, noncurrent later), each by company.
    A rise a year earlier suggests a season but does not prove one, so the saved run keeps the row.
    """
    tags = {line["tag"] for line in lead["lines"]}
    cik = lead["cik"]
    if tags <= {CURRENT, NONCURRENT} and all(cik in frame for frame in totals):
        a, b, c, d = (frame[cik]["val"] for frame in totals)
        if b + d <= a + c:
            return TOTAL_NOT_UP
    if all(line["year_ago_pct"] is not None and line["year_ago_pct"] >= min_rise_pct for line in lead["lines"]):
        return UP_A_YEAR_AGO
    return None


def group_leads(rows):
    """One lead per company, largest rise first. Each company keeps a line per tag."""
    leads = {}
    for row in rows:
        lead = leads.setdefault(row["cik"], {"cik": row["cik"], "name": row["name"], "lines": []})
        lead["lines"].append(row)
    out = list(leads.values())
    for lead in out:
        lead["lines"].sort(key=lambda r: -r["rise_pct"])
    return sorted(out, key=lambda lead: (-lead["lines"][0]["rise_pct"], lead["cik"]))


def screen(settings, today, client_factory, cache_folder=CACHE):
    """Read the frames and compare the last two steps. The newest step is still filling up while companies file."""
    limits, tags = settings, settings["tag"]
    cache = edgar.Cache(cache_folder, client_factory, RECENT_HOURS)
    fetch = Fetcher(cache, client_factory, settings["max_requests_per_run"])
    quarters = quarters_back(*latest_ended_quarter(today), settings["quarters_back"])
    names = [frame_name(*q) for q in quarters]
    frames, filers = {}, {}
    for item in tags:
        for i, name in enumerate(names):
            frames[(item["tag"], name)] = fetch(item["tag"], name, recent=i < 2)
        filers[item["tag"]] = {n: len((frames[(item["tag"], n)] or {}).get("data", [])) for n in names}
    steps = []
    for later_at in (0, 1):
        later_name, earlier_name = names[later_at], names[later_at + 1]
        year_after, year_before = names[later_at + 4], names[later_at + 5]
        rows, tally = [], {}
        for item in tags:
            pair = [(earlier_name, frames[(item["tag"], earlier_name)]), (later_name, frames[(item["tag"], later_name)]),
                    (year_before, frames[(item["tag"], year_before)]), (year_after, frames[(item["tag"], year_after)])]
            found, counts = compare(item["tag"], item["label"], pair, limits)
            rows += found
            tally[item["tag"]] = dict(counts, filers_earlier=filers[item["tag"]][earlier_name], filers_later=filers[item["tag"]][later_name], rows=len(found))
        ranked = group_leads([r for r in rows if not r["unit_slip"]])
        totals = [by_company(frames.get((tag, name))) for tag in (CURRENT, NONCURRENT) for name in (earlier_name, later_name)]
        for lead in ranked:
            lead["not_new_growth"] = not_new_growth(lead, totals, limits["min_rise_pct"])
        steps.append({"earlier": earlier_name, "later": later_name, "tally": tally,
                      "leads": ranked, "unit_check": group_leads([r for r in rows if r["unit_slip"]]),
                      "year_ago_step": f"{year_before} to {year_after}"})
    return {"steps": steps, "missing_frames": fetch.missing}
