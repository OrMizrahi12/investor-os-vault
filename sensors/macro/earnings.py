"""Earnings yield from the caches: trailing-12-month diluted EPS from SEC, divided by Yahoo's close. No network."""

import datetime as dt


class EarningsError(Exception):
    pass


def _days(row):
    return (dt.date.fromisoformat(row["end"]) - dt.date.fromisoformat(row["start"])).days


def _year_earlier(text):
    day = dt.date.fromisoformat(text)
    return day.replace(year=day.year - 1).isoformat()


def eps_steps(facts):
    """One step per 10-K or 10-Q, using what that filing and the 10-K before it reported.

    Picks periods by their dates, never SEC's fy field. 10-Qs give year-to-date figures, so
    trailing EPS = last full year + this year to date - last year to date.
    """
    rows = [r for r in facts if r["taxonomy"] == "us-gaap" and r["concept"] == "EarningsPerShareDiluted"
            and r["unit"] == "USD/shares" and r["form"] in ("10-K", "10-Q") and r["start"]]
    filings = {}
    for r in rows:
        filings.setdefault(r["accession"], []).append(r)
    ordered = sorted(filings.values(), key=lambda g: (g[0]["filed"], g[0]["accession"]))
    annual = []  # 10-K full-year figures, as filed
    steps = []
    for group in ordered:
        end = max(r["end"] for r in group)
        current = [r for r in group if r["end"] == end]
        longest = max(current, key=_days)
        if len({r["value"] for r in current if r["start"] == longest["start"]}) > 1:
            raise EarningsError(f"{longest['accession']} has two values for one period.")
        step = {"filed": longest["filed"], "form": longest["form"], "accession": longest["accession"],
                "url": longest["filing_url"], "period_end": end}
        if longest["form"] == "10-K":
            if not 350 <= _days(longest) <= 380:
                raise EarningsError(f"{longest['accession']}: no full-year EPS for {end}.")
            step.update(eps=longest["value"], full_year=longest["value"], ytd=None, ytd_prior=None, full_year_filing=None)
            annual.append({"end": end, "value": longest["value"], "filed": longest["filed"],
                           "accession": longest["accession"], "url": longest["filing_url"]})
            steps.append(step)
            continue
        if not 80 <= _days(longest) <= 290:
            raise EarningsError(f"{longest['accession']}: no year-to-date EPS for {end}.")
        prior = [r for r in group if r["end"] == _year_earlier(end) and r["start"] == _year_earlier(longest["start"])]
        year_end = (dt.date.fromisoformat(longest["start"]) - dt.timedelta(days=1)).isoformat()
        full_year = next((a for a in reversed(annual) if a["end"] == year_end), None)
        if not prior or not full_year:
            step.update(eps=None)  # fine before the window. The caller stops if the window needs it.
            steps.append(step)
            continue
        step.update(eps=round(full_year["value"] + longest["value"] - prior[0]["value"], 4), full_year=full_year["value"],
                    ytd=longest["value"], ytd_prior=prior[0]["value"], full_year_filing=full_year)
        steps.append(step)
    return steps


def steps_in_window(steps, start):
    """The last step known when the window opens, and every step after. Stops if one cannot be computed."""
    text = start.isoformat()
    before = [s for s in steps if s["filed"] <= text]
    if not before:
        raise EarningsError(f"No EPS filing on or before {text}.")
    chosen = [before[-1]] + [s for s in steps if s["filed"] > text]
    bad = [s["accession"] for s in chosen if s["eps"] is None]
    if bad:
        raise EarningsError(f"Trailing EPS cannot be computed for {bad}.")
    return chosen


def yield_series(prices, steps, start):
    """Each trading day's close against the EPS on file that day, not what was reported later."""
    out = []
    index = 0
    for p in prices:
        if p["date"] < start.isoformat():
            continue
        if p["stock_splits"]:
            raise EarningsError(f"A split on {p['date']} would make EPS and the close disagree.")
        while index + 1 < len(steps) and steps[index + 1]["filed"] <= p["date"]:
            index += 1
        step = steps[index]
        if step["filed"] > p["date"]:
            continue
        out.append({"date": p["date"], "close": p["close"], "eps": step["eps"],
                    "yield": step["eps"] / p["close"] * 100, "accession": step["accession"]})
    return out


def cpi_yearly_change(rows):
    """Percent change from the same month a year earlier. A missing month stays a gap."""
    values = dict(rows)
    out = []
    for day, value in rows:
        earlier = values.get(day.replace(year=day.year - 1))
        out.append((day, None if value is None or earlier is None else (value / earlier - 1) * 100))
    return out
