"""Corning's price tags from saved data: P/E, EV/EBIT, free cash flow yield. No network.

Reads the EDGAR, prices and macro caches. Stops if a number is missing.
Two bases, kept apart:
  known: what was on file that day, as first filed. Same rule as the earnings yield in economy.html.
  year: that fiscal year's full results, from the latest 10-K reporting them. Ties to Companies/Corning.md.
"""

import csv
import datetime as dt
import importlib.util
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GLW = ROOT / "sensors/edgar/cache/CIK0000024741/facts.jsonl"
APH = ROOT / "sensors/edgar/cache/CIK0000820313/facts.jsonl"
PRICES = ROOT / "sensors/prices/cache/GLW/2026-11-02.csv"
FRED = ROOT / "sensors/macro/downloads"
FIRST_YEAR, LAST_YEAR = 2016, 2025

# Tags changed over the years, so each measure tries them in order.
OCF = ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]
CAPEX = ["PaymentsForCapitalImprovements", "PaymentsToAcquireProductiveAssets", "PaymentsForProceedsFromProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"]
EBIT = ["OperatingIncomeLoss"]
EPS = ["EarningsPerShareDiluted"]
CASH = ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]


class Stop(Exception):
    pass


def load_facts(path):
    with open(path) as handle:
        rows = [json.loads(line) for line in handle]
    return [r for r in rows if r["form"] in ("10-K", "10-Q")]


def days(r):
    return (dt.date.fromisoformat(r["end"]) - dt.date.fromisoformat(r["start"])).days


def flow(group, tags, start, end):
    """A flow for an exact period from one filing. Tries each tag in order."""
    for tag in tags:
        hits = {r["value"] for r in group if r["concept"] == tag and r["start"] == start and r["end"] == end}
        if len(hits) > 1:
            raise Stop(f"{tag} has two values for {start} to {end}.")
        if hits:
            return hits.pop()
    return None


def balance(group, tags, end):
    for tag in tags:
        hits = {r["value"] for r in group if r["concept"] == tag and r["start"] is None and r["end"] == end}
        if hits:
            return hits.pop()
    return None


def filings(rows):
    out = {}
    for r in rows:
        out.setdefault(r["accession"], []).append(r)
    return sorted(out.values(), key=lambda g: (g[0]["filed"], g[0]["accession"]))


def filing_end(group):
    """The period a 10-K or 10-Q reports, from its income statement rows, not its cover."""
    ends = [r["end"] for r in group if r["concept"] == "EarningsPerShareDiluted" and r["start"]]
    if not ends:
        raise Stop(f"{group[0]['accession']} has no diluted EPS.")
    return max(ends)


def cover(group):
    hits = [r for r in group if r["concept"] == "EntityCommonStockSharesOutstanding"]
    if not hits:
        raise Stop(f"{group[0]['accession']} has no cover share count.")
    newest = max(hits, key=lambda r: r["end"])
    return newest["value"], newest["end"]


def trailing(step, annuals, tags):
    """Last full year + this year to date - last year to date. A 10-K is just its full year."""
    group, end = step["group"], step["end"]
    year = int(end[:4])
    if end.endswith("12-31"):
        value = flow(group, tags, f"{year}-01-01", end)
        if value is None:
            raise Stop(f"{tags[0]} missing for {end}.")
        return value
    prior_end = f"{year - 1}-12-31"
    full = flow(annuals[prior_end], tags, f"{year - 1}-01-01", prior_end)
    ytd = flow(group, tags, f"{year}-01-01", end)
    ytd_prior = flow(group, tags, f"{year - 1}-01-01", end.replace(str(year), str(year - 1), 1))
    if None in (full, ytd, ytd_prior):
        raise Stop(f"{tags[0]}: cannot build twelve months to {end} ({full}, {ytd}, {ytd_prior}).")
    return full + ytd - ytd_prior


def prepare(rows):
    annuals, steps = {}, []
    for group in filings(rows):
        if not any(r["concept"] == "EarningsPerShareDiluted" and r["start"] for r in group):
            continue
        end = filing_end(group)
        step = {"group": group, "end": end, "filed": group[0]["filed"], "form": group[0]["form"],
                "accession": group[0]["accession"], "url": group[0]["filing_url"]}
        if group[0]["form"] == "10-K":
            annuals.setdefault(end, group)  # first filed
        steps.append(step)
    return annuals, steps


def closes():
    with open(PRICES) as handle:
        rows = list(csv.DictReader(handle))
    if any(float(r["stock_splits"]) for r in rows if r["date"] >= f"{FIRST_YEAR - 1}"):
        raise Stop("A split would make EPS and the close disagree.")
    return [(r["date"], float(r["close"])) for r in rows]


def close_on_or_before(prices, day):
    hit = [p for p in prices if p[0] <= day]
    if not hit:
        raise Stop(f"No close on or before {day}.")
    return hit[-1]


def read_fred(name):
    with open(FRED / f"{name}.csv") as handle:
        return [(r["observation_date"], float(r[name])) for r in csv.DictReader(handle) if r[name] not in ("", ".")]


def tag(price, shares, debt, preferred, nci, cash, eps, ebit, ocf, capex):
    cap = price * shares
    ev = cap + debt + preferred + nci - cash
    fcf = ocf - capex
    return {"price": price, "shares": shares, "cap": cap, "debt": debt, "preferred": preferred, "nci": nci, "cash": cash,
            "ev": ev, "eps": eps, "ebit": ebit, "ocf": ocf, "capex": capex, "fcf": fcf,
            "pe": price / eps if eps > 0 else None, "ey": eps / price * 100,
            "ev_ebit": ev / ebit if ebit > 0 else None, "fcfy": fcf / cap * 100}


def point(price_row, step, annuals):
    group, end = step["group"], step["end"]
    shares, shares_date = cover(group)
    debt_now = balance(group, ["DebtCurrent"], end)
    debt_long = balance(group, ["LongTermDebtAndCapitalLeaseObligations"], end)
    cash = balance(group, CASH, end)
    nci = balance(group, ["MinorityInterest"], end)
    if None in (debt_now, debt_long, cash, nci):
        raise Stop(f"Balance sheet gap at {end}: {debt_now}, {debt_long}, {cash}, {nci}.")
    preferred = balance(group, ["PreferredStockValue"], end) or 0
    out = tag(price_row[1], shares, debt_now + debt_long, preferred, nci, cash,
              trailing(step, annuals, EPS), trailing(step, annuals, EBIT), trailing(step, annuals, OCF), trailing(step, annuals, CAPEX))
    out.update(date=price_row[0], period_end=end, shares_date=shares_date, filed=step["filed"], form=step["form"],
               accession=step["accession"], url=step["url"])
    return out


def latest_annual(rows, tags, year):
    """The latest 10-K reporting a full fiscal year, as Companies/Corning.md's tables do."""
    start, end = f"{year}-01-01", f"{year}-12-31"
    for tag_name in tags:
        hits = [r for r in rows if r["concept"] == tag_name and r["form"] == "10-K" and r["start"] == start and r["end"] == end]
        if hits:
            return max(hits, key=lambda r: r["filed"])["value"]
    raise Stop(f"{tags[0]} missing for FY{year}.")


def year_basis(rows, annuals, prices, year):
    day = close_on_or_before(prices, f"{year}-12-31")
    group = annuals[f"{year}-12-31"]
    end = f"{year}-12-31"
    shares, shares_date = cover(group)
    debt = (balance(group, ["DebtCurrent"], end) or 0) + balance(group, ["LongTermDebtAndCapitalLeaseObligations"], end)
    out = tag(day[1], shares, debt, balance(group, ["PreferredStockValue"], end) or 0, balance(group, ["MinorityInterest"], end),
              balance(group, CASH, end), latest_annual(rows, EPS, year), latest_annual(rows, EBIT, year),
              latest_annual(rows, OCF, year), latest_annual(rows, CAPEX, year))
    out.update(date=day[0], period_end=end, shares_date=shares_date, filed=group[0]["filed"], url=group[0]["filing_url"])
    return out


def summary(values):
    kept = [v for v in values if v is not None]
    return {"mean": statistics.mean(kept), "median": statistics.median(kept), "n": len(kept), "low": min(kept), "high": max(kept)}


def build():
    rows = load_facts(GLW)
    annuals, steps = prepare(rows)
    prices = closes()
    aaa, dgs = read_fred("AAA"), read_fred("DGS10")
    known, year = [], []
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        day = close_on_or_before(prices, f"{y}-12-31")
        step = [s for s in steps if s["filed"] <= day[0]][-1]
        p = point(day, step, annuals)
        p["aaa"] = dict(aaa)[f"{y}-12-01"]
        p["aaa_date"] = f"{y}-12-01"
        p["dgs_date"], p["dgs"] = next((d, v) for d, v in reversed(dgs) if d <= day[0])
        known.append(p)
        year.append(year_basis(rows, annuals, prices, y))
    last = prices[-1]
    today = point(last, steps[-1], annuals)
    today["aaa_date"], today["aaa"] = aaa[-1]
    today["dgs_date"], today["dgs"] = dgs[-1]
    stats = {k: summary([p[k] for p in known]) for k in ("pe", "ey", "ev_ebit", "fcfy", "aaa", "dgs")}
    stats_year = {k: summary([p[k] for p in year]) for k in ("pe", "ey", "ev_ebit", "fcfy")}
    return {"known": known, "year": year, "today": today, "stats": stats, "stats_year": stats_year}


def amphenol(price):
    """Amphenol on our rules, from its saved SEC facts. The price is the outside page's.

    It split 2-for-1 on Sept. 2, 2026. The Q3 10-Q restates its year-to-date EPS, but FY2025 EPS
    in the 10-K does not change, so adding them straight mixes old and new shares. EPS here is
    net income over the 10-Q's own diluted share count, and the old-share sum is tested against it.
    """
    rows = load_facts(APH)
    annuals, steps = prepare(rows)
    step = steps[-1]
    group, end = step["group"], step["end"]
    shares, shares_date = cover(group)
    debt = balance(group, ["LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities"], end)
    cash = balance(group, ["CashCashEquivalentsAndShortTermInvestments"], end)
    nci = balance(group, ["MinorityInterest"], end) or 0
    ocf_tags = ["NetCashProvidedByUsedInOperatingActivitiesContinuingOperations", "NetCashProvidedByUsedInOperatingActivities"]
    capex_tags = ["PaymentsToAcquirePropertyPlantAndEquipment"]
    net = trailing(step, annuals, ["NetIncomeLoss"])
    year = int(end[:4])
    start = f"{year}-01-01"
    diluted = max(r["value"] for r in group if r["concept"] == "WeightedAverageNumberOfDilutedSharesOutstanding" and r["start"] == start and r["end"] == end)
    full = flow(annuals[f"{year - 1}-12-31"], EPS, f"{year - 1}-01-01", f"{year - 1}-12-31")
    ytd = flow(group, EPS, start, end)
    prior = flow(group, EPS, f"{year - 1}-01-01", end.replace(str(year), str(year - 1), 1))
    eps = full / 2 + ytd - prior  # FY2025's $3.34 on new shares
    if abs(eps - net / diluted) > 0.02:
        raise Stop(f"Amphenol EPS {eps} does not tie to net income over diluted shares {net / diluted}.")
    out = tag(price, shares, debt, 0, nci, cash, eps, trailing(step, annuals, EBIT),
              trailing(step, annuals, ocf_tags), trailing(step, annuals, capex_tags))
    out.update(period_end=end, shares_date=shares_date, filed=step["filed"], url=step["url"], net=net, diluted=diluted,
               straight_sum=full + ytd - prior)
    return out


def earnings_module():
    spec = importlib.util.spec_from_file_location("earnings", ROOT / "sensors/macro/earnings.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
