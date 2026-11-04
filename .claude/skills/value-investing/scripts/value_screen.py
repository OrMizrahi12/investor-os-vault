#!/usr/bin/env python3
"""Apply the classic quantitative value-investing tests, with the 2003
recalibration, to one or more companies.

Standard library only. Input is JSON (one company object, or a list of them).
See ../assets/company_input_template.json for every supported field; all fields
except "name" and "price" are optional, and each test reports "insufficient data"
instead of guessing when its inputs are missing.

Usage:
  python3 value_screen.py company.json                 # markdown report
  python3 value_screen.py companies.json --format json # machine-readable
  python3 value_screen.py holdings.json --aa-yield 0.052   # list input adds the portfolio test
  python3 value_screen.py company.json --cpi-multiplier 8.0 --aaa-yield 0.055

Money amounts must all be in the same currency and unit (e.g. dollars, or
millions of dollars); per-share fields must be per share. Rates are decimals
(0.055 = 5.5%).
"""

import argparse
import json
import math
import sys

# The classic size floors are in 1971-72 dollars. Multiply by a CPI ratio to
# translate. CPI-U 1971 avg = 40.5; mid-2020s ~ 315-325, i.e. ~7.8-8.0x.
DEFAULT_CPI_MULTIPLIER = 7.9

# The coverage table: minimum coverage of total fixed charges.
# (7-year average, poorest year) before taxes, and after taxes.
COVERAGE_MINIMUMS = {
    "utility": {"pretax": (4.0, 3.0), "aftertax": (2.65, 2.10)},
    "railroad": {"pretax": (5.0, 4.0), "aftertax": (3.20, 2.65)},
    "industrial": {"pretax": (7.0, 5.0), "aftertax": (4.30, 3.20)},
    "retail": {"pretax": (5.0, 4.0), "aftertax": (3.20, 2.65)},
}
# Classic alternative for high-rate eras: pretax earnings as % of debt principal
# (7-year average); poorest year about two-thirds of this.
EARNINGS_TO_DEBT_MINIMUMS = {"industrial": 0.33, "utility": 0.20, "railroad": 0.25, "retail": 0.25}
# The 2003 recalibration's size floor is in 2003 dollars: CPI-U 2003 avg = 184.0 vs 1971 avg = 40.5.
CPI_1971, CPI_2003 = 40.5, 184.0


# ---------------------------------------------------------------- helpers

def num(d, key):
    v = d.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def series(d, key):
    """Return a chronologically sorted list of (period, value) from a dict or list."""
    raw = d.get(key)
    if not raw:
        return []
    if isinstance(raw, dict):
        items = []
        for k, v in raw.items():
            if v is None:
                continue
            items.append((str(k), float(v)))
        items.sort(key=lambda kv: kv[0])
        return items
    if isinstance(raw, list):
        return [(str(i), float(v)) for i, v in enumerate(raw) if v is not None]
    return []


def values(d, key):
    return [v for _, v in series(d, key)]


def avg(xs):
    return sum(xs) / len(xs) if xs else None


def fmt(x, pct=False, digits=2):
    if x is None:
        return "n/a"
    if pct:
        return f"{x * 100:.{digits}f}%"
    if abs(x) >= 1e6:
        return f"{x:,.0f}"
    return f"{x:,.{digits}f}"


def result(name, passed, detail, source, missing=None):
    if missing:
        return {"test": name, "status": "insufficient data", "detail": f"needs: {', '.join(missing)}", "source": source}
    return {"test": name, "status": "PASS" if passed else "FAIL", "detail": detail, "source": source}


def info(name, detail, source):
    return {"test": name, "status": "INFO", "detail": detail, "source": source}


# ------------------------------------------------------- derived quantities

def derived(c):
    out = {}
    price = num(c, "price")
    shares = num(c, "shares_outstanding")
    dil = num(c, "diluted_shares") or shares
    out["price"] = price
    out["shares"] = shares
    out["diluted_shares"] = dil

    eps = values(c, "eps_history")
    out["eps"] = eps
    out["eps_ttm"] = num(c, "eps_ttm") if num(c, "eps_ttm") is not None else (eps[-1] if eps else None)
    out["eps_avg3"] = avg(eps[-3:]) if len(eps) >= 3 else None
    out["eps_avg7"] = avg(eps[-7:]) if len(eps) >= 7 else None
    out["eps_avg5"] = avg(eps[-5:]) if len(eps) >= 5 else None
    # "Current (normal)" earnings for the 8.5 + 2g formula: the current
    # year's earning power without special items. Use a supplied eps_normal,
    # else the 3-year average as a smoothed proxy.
    out["eps_normal"] = num(c, "eps_normal") or out["eps_avg3"] or out["eps_ttm"]

    ca = num(c, "current_assets")
    cl = num(c, "current_liabilities")
    tl = num(c, "total_liabilities")
    pref = num(c, "preferred_stock") or 0.0
    ltd = num(c, "long_term_debt")
    eq = num(c, "shareholders_equity")
    intang = num(c, "intangibles") or 0.0
    out.update(ca=ca, cl=cl, tl=tl, pref=pref, ltd=ltd, equity=eq, intangibles=intang)

    out["working_capital"] = ca - cl if ca is not None and cl is not None else None
    out["current_ratio"] = ca / cl if ca is not None and cl not in (None, 0) else None
    # "Net current assets" for bargain issues: current assets minus ALL
    # liabilities and preferred stock (the "net-net").
    out["ncav"] = ca - tl - pref if ca is not None and tl is not None else None
    out["ncav_ps"] = out["ncav"] / shares if out["ncav"] is not None and shares else None
    # Book value per share on basic shares, as reported (defensive criterion 7);
    # tangible book per diluted share, the conservative asset-backing figure.
    out["book_ps"] = (eq - pref) / shares if eq is not None and shares else None
    out["tangible_book"] = (eq - pref - intang) if eq is not None else None
    out["tbv_ps"] = out["tangible_book"] / dil if out["tangible_book"] is not None and dil else None
    out["market_cap"] = price * shares if price is not None and shares else None

    # Warrants/options: add their market value to the common's market price.
    wmv = num(c, "warrants_market_value") or 0.0
    out["warrant_adjusted_price"] = (price + wmv / shares) if price is not None and shares and wmv else price
    return out


def dividend_years(c):
    """Years of uninterrupted dividends: the reported figure, else the run of
    paying years at the end of the supplied history. Returns (years, note)."""
    yrs = num(c, "years_of_uninterrupted_dividends")
    if yrs is not None:
        return yrs, f"{int(yrs)} years reported"
    divs = values(c, "dividends_per_share_history")
    if not divs:
        return None, None
    run = 0
    for v in reversed(divs):
        if v > 0:
            run += 1
        else:
            break
    return run, f"{run} consecutive paying years in supplied history ({len(divs)} years supplied)"


def growth_window(eps):
    """Defensive criterion 5 compares the latest 3-yr average EPS with the 3-yr
    average ten years earlier (1958-60 vs 1968-70), which needs 13 years.
    With 10-12 years, fall back to the first three years supplied: a shorter,
    stricter span. Returns (start_avg, end_avg, label) or None."""
    if len(eps) >= 13:
        return avg(eps[-13:-10]), avg(eps[-3:]), "3-yr averages ten years apart"
    if len(eps) >= 10:
        span = len(eps) - 3
        return avg(eps[:3]), avg(eps[-3:]), f"3-yr averages only {span} years apart (stricter than the classic 10; supply 13 years for the exact test)"
    return None


# --------------------------------------------------------------- the tests

def defensive_tests(c, d, cpi):
    """The seven statistical requirements for the defensive investor."""
    t = []
    ctype = (c.get("type") or "industrial").lower()
    src = "Classic: defensive criteria"

    # 1. Adequate size
    sales = num(c, "revenue")
    assets = num(c, "total_assets")
    if ctype == "utility":
        floor = 50e6 * cpi
        if assets is None:
            t.append(result("1. Adequate size", None, "", src, ["total_assets"]))
        else:
            t.append(result("1. Adequate size", assets >= floor,
                            f"total assets {fmt(assets)} vs floor {fmt(floor)} ($50M in 1971 dollars x CPI {cpi})", src))
    else:
        floor = 100e6 * cpi
        if sales is None:
            t.append(result("1. Adequate size", None, "", src, ["revenue"]))
        else:
            t.append(result("1. Adequate size", sales >= floor,
                            f"annual sales {fmt(sales)} vs floor {fmt(floor)} ($100M in 1971 dollars x CPI {cpi}); amounts must be in units, not millions", src))

    # 2. Strong financial condition
    if ctype == "utility":
        if d["ltd"] is None or d["equity"] is None:
            t.append(result("2. Strong financial condition", None, "", src, ["long_term_debt", "shareholders_equity"]))
        else:
            ok = d["ltd"] <= 2 * (d["equity"] - d["pref"])
            tot = d["ltd"] + (num(c, "short_term_debt") or 0)
            alt = "passes" if tot <= 2 * d["equity"] else "fails"
            t.append(result("2. Strong financial condition", ok,
                            f"long-term debt {fmt(d['ltd'])} vs 2x common equity at book {fmt(2 * (d['equity'] - d['pref']))}; "
                            f"broader reading (total debt {fmt(tot)} vs 2x equity incl. preferred {fmt(2 * d['equity'])}) {alt}. "
                            "'Stock equity' is ambiguous in the classic rule; report both when close", src))
    elif ctype in ("financial", "bank", "insurance"):
        t.append(info("2. Strong financial condition",
                      "current-ratio tests do not apply to financial companies; judge capital adequacy separately (the classic rules treat financials apart)", src))
    else:
        miss = [k for k, v in (("current_assets", d["ca"]), ("current_liabilities", d["cl"]), ("long_term_debt", d["ltd"])) if v is None]
        if miss:
            t.append(result("2. Strong financial condition", None, "", src, miss))
        else:
            ok = d["current_ratio"] >= 2.0 and d["ltd"] <= d["working_capital"]
            t.append(result("2. Strong financial condition", ok,
                            f"current ratio {fmt(d['current_ratio'])} (need >= 2.0); long-term debt {fmt(d['ltd'])} vs net current assets {fmt(d['working_capital'])} (debt must not exceed it)", src))

    # 3. Earnings stability: positive earnings in each of the past 10 years
    eps = d["eps"]
    if len(eps) < 10:
        t.append(result("3. Earnings stability (10 yrs, no deficit)", None, "", src, [f"10 years of eps_history (have {len(eps)})"]))
    else:
        last10 = eps[-10:]
        t.append(result("3. Earnings stability (10 yrs, no deficit)", all(e > 0 for e in last10),
                        f"deficit years in last 10: {sum(1 for e in last10 if e <= 0)}", src))

    # 4. Dividend record: uninterrupted for at least 20 years
    yrs, note = dividend_years(c)
    if yrs is None:
        t.append(result("4. Dividend record (20 yrs uninterrupted)", None, "", src, ["years_of_uninterrupted_dividends or dividends_per_share_history"]))
    else:
        t.append(result("4. Dividend record (20 yrs uninterrupted)", yrs >= 20, note, src))

    # 5. Earnings growth: +1/3 over 10 years, 3-year averages at both ends
    gw = growth_window(eps)
    if gw is None:
        t.append(result("5. Earnings growth (>= +33% over 10 yrs, 3-yr avgs)", None, "", src, ["10-13 years of eps_history"]))
    else:
        start, end, label = gw
        if start <= 0:
            t.append(result("5. Earnings growth (>= +33% over 10 yrs, 3-yr avgs)", False,
                            f"starting 3-yr average {fmt(start)} not positive", src))
        else:
            g = end / start - 1
            t.append(result("5. Earnings growth (>= +33% over 10 yrs, 3-yr avgs)", g >= 1 / 3,
                            f"3-yr avg EPS {fmt(start)} -> {fmt(end)} = {fmt(g, pct=True)}; {label}", src))

    # 6. Moderate P/E: price <= 15x average EPS of past 3 years
    pe3 = None
    if d["price"] is None or not d["eps_avg3"]:
        t.append(result("6. Moderate P/E (<= 15x 3-yr avg EPS)", None, "", src, ["price", "3 years of eps_history"]))
    elif d["eps_avg3"] <= 0:
        t.append(result("6. Moderate P/E (<= 15x 3-yr avg EPS)", False, "3-yr average EPS not positive", src))
    else:
        pe3 = d["price"] / d["eps_avg3"]
        t.append(result("6. Moderate P/E (<= 15x 3-yr avg EPS)", pe3 <= 15,
                        f"P/E on 3-yr avg {fmt(pe3)}", src))

    # 7. Moderate price-to-assets: P/B <= 1.5, or P/E x P/B <= 22.5
    if d["price"] is None or not d["book_ps"]:
        t.append(result("7. Price-to-assets (P/B <= 1.5 or P/E x P/B <= 22.5)", None, "", src, ["price", "shareholders_equity", "shares_outstanding"]))
    else:
        pb = d["price"] / d["book_ps"] if d["book_ps"] > 0 else float("inf")
        prod = pe3 * pb if pe3 is not None else None
        ok = pb <= 1.5 or (prod is not None and prod <= 22.5)
        detail = f"P/B {fmt(pb)}; P/E x P/B {fmt(prod)}"
        if d["tbv_ps"]:
            ptb = d["price"] / d["tbv_ps"] if d["tbv_ps"] > 0 else float("inf")
            ok_t = ptb <= 1.5 or (pe3 is not None and pe3 * ptb <= 22.5)
            detail += f"; on tangible book: P/TB {fmt(ptb)}, P/E x P/TB {fmt(pe3 * ptb if pe3 is not None else None)}"
            if ok and not ok_t:
                detail += " — passes on total book only (intangibles carry it): flag this"
        t.append(result("7. Price-to-assets (P/B <= 1.5 or P/E x P/B <= 22.5)", ok, detail, src))
    return t


def modern_2003_checks(c, d, cpi):
    """The early-2003 recalibration of the seven criteria."""
    t = []
    src = "Modern update (2003)"
    floor = 2e9 * cpi * CPI_1971 / CPI_2003
    if d["market_cap"] is None:
        t.append(result("Size: market value >= $2B in 2003 dollars", None, "", src, ["price", "shares_outstanding"]))
    else:
        t.append(result("Size: market value >= $2B in 2003 dollars", d["market_cap"] >= floor,
                        f"market value {fmt(d['market_cap'])} vs {fmt(floor)} today (CPI-translated); own smaller companies through a small-cap fund", src))
    gw = growth_window(d["eps"])
    if gw and gw[0] > 0:
        g = gw[1] / gw[0] - 1
        t.append(result("Growth: >= +50% over 10 yrs on 3-yr averages (the classic +33% is under 3% a year)", g >= 0.5,
                        f"{fmt(g, pct=True)}; +100% (about 7% a year) is the stricter version: {'met' if g >= 1 else 'not met'}; {gw[2]}", src))
    else:
        t.append(result("Growth: >= +50% over 10 yrs on 3-yr averages", None, "", src, ["10 years of eps_history with a positive start"]))
    inst = num(c, "institutional_ownership")
    if inst is None:
        t.append(result("Not 'overowned' (institutional ownership <= 60%)", None, "", src, ["institutional_ownership"]))
    else:
        t.append(result("Not 'overowned' (institutional ownership <= 60%)", inst <= 0.60,
                        f"{fmt(inst, pct=True)}; institutions tend to sell together", src))
    t.append(info("P/E basis", "P/E above is price / trailing 3-yr average EPS computed by hand. Never substitute a forward P/E: "
                  "Dreman found most consensus forecasts miss by 15% or more", src))
    t.append(info("Homework before buying", "read 5 years of annual and quarterly reports and the latest proxy; "
                  "an investor unwilling to do this should own an index fund instead", src))
    return t


def general_rules_tests(c, d, cpi):
    """The classic general rules for the defensive investor's common stocks (looser)."""
    t = []
    src = "Classic: defensive stock rules"
    src_mod = "Modern update (2003)"
    # "Large": $50M of assets or of sales in 1972 terms, CPI-scaled like the
    # seven-criteria size floor. Modern update: market value >= $10B in 2003 dollars.
    sales, assets = num(c, "revenue"), num(c, "total_assets")
    floor = 50e6 * cpi
    if sales is None and assets is None:
        t.append(result("Large: assets or sales >= $50M in 1972 dollars", None, "", src, ["total_assets or revenue"]))
    else:
        ok = (assets is not None and assets >= floor) or (sales is not None and sales >= floor)
        t.append(result("Large: assets or sales >= $50M in 1972 dollars", ok,
                        f"total assets {fmt(assets)}; sales {fmt(sales)}; floor {fmt(floor)} ($50M x CPI {cpi}); "
                        "either one suffices; apply with common sense, not rigidly", src))
    mfloor = 10e9 * cpi * CPI_1971 / CPI_2003
    if d["market_cap"] is None:
        t.append(result("Large (2003 recalibration): market value >= $10B in 2003 dollars", None, "", src_mod, ["price", "shares_outstanding"]))
    else:
        t.append(result("Large (2003 recalibration): market value >= $10B in 2003 dollars", d["market_cap"] >= mfloor,
                        f"market value {fmt(d['market_cap'])} vs {fmt(mfloor)} today (CPI-translated); "
                        "separate from the $2B floor used with the seven criteria", src_mod))
    # "Prominent": first quarter or first third of its industry by size.
    rank, peers = num(c, "industry_size_rank"), num(c, "industry_peer_count")
    if rank and peers:
        third, quarter = rank <= peers / 3, rank <= peers / 4
        t.append(result("Prominent: in the first third (or quarter) of its industry by size", third,
                        f"rank {rank:g} of {peers:g} by size; first quarter {'yes' if quarter else 'no'}; "
                        "check the peer group is the right one", src))
    else:
        t.append(info("Prominent: in the first third (or quarter) of its industry by size",
                      "needs judgment: supply industry_size_rank (1 = largest) and industry_peer_count to test it", src))
    # Dividend continuity: about 20 years (classic), at least 10 (modern minimum).
    yrs, note = dividend_years(c)
    if yrs is None:
        t.append(result("Long continuous dividend record (about 20 years)", None, "", src,
                        ["years_of_uninterrupted_dividends or dividends_per_share_history"]))
        t.append(result("Dividend continuity, modern minimum (>= 10 years)", None, "", src_mod,
                        ["years_of_uninterrupted_dividends or dividends_per_share_history"]))
    else:
        t.append(result("Long continuous dividend record (about 20 years)", yrs >= 20, note, src))
        t.append(result("Dividend continuity, modern minimum (>= 10 years)", yrs >= 10,
                        f"{note}; 20 years is not overly restrictive today", src_mod))
    if d["price"] is not None and d["eps_avg7"] and d["eps_ttm"]:
        ok = d["price"] <= 25 * d["eps_avg7"] and d["price"] <= 20 * d["eps_ttm"]
        t.append(result("Price <= 25x 7-yr avg EPS and <= 20x TTM EPS", ok,
                        f"P/E7 {fmt(d['price'] / d['eps_avg7'])}; P/E TTM {fmt(d['price'] / d['eps_ttm'])}", src))
    else:
        t.append(result("Price <= 25x 7-yr avg EPS and <= 20x TTM EPS", None, "", src, ["7 years of eps_history", "price"]))
    ctype = (c.get("type") or "industrial").lower()
    if d["equity"] is not None:
        debt = (num(c, "long_term_debt") or 0) + (num(c, "short_term_debt") or 0)
        cap = d["equity"] + debt
        share = (d["equity"] - d["pref"]) / cap if cap else None
        need = 0.30 if ctype in ("utility", "railroad") else 0.50
        t.append(result(f"Conservatively financed (common equity >= {int(need * 100)}% of capitalization incl. bank debt)",
                        share is not None and share >= need, f"common equity share {fmt(share, pct=True)}", src))
    return t


def enterprising_tests(c, d):
    """The Stock Guide screen for the enterprising investor (looser standards)."""
    t = []
    src = "Classic: enterprising screen"
    ctype = (c.get("type") or "industrial").lower()
    pe_ttm = d["price"] / d["eps_ttm"] if d["price"] is not None and d["eps_ttm"] and d["eps_ttm"] > 0 else None
    t.append(info("Starting filter: low multiplier (the classic screen used P/E <= 9 when AA bonds yielded ~7.5%)",
                  f"P/E on latest 12 months {fmt(pe_ttm)}; relate the cut-off to current high-grade bond yields", src))
    if ctype in ("industrial", "retail"):
        miss = [k for k, v in (("current_assets", d["ca"]), ("current_liabilities", d["cl"]), ("long_term_debt", d["ltd"])) if v is None]
        if miss:
            t.append(result("1. Financial condition (CA >= 1.5x CL; debt <= 110% of net current assets)", None, "", src, miss))
        else:
            ok = d["current_ratio"] >= 1.5 and d["working_capital"] > 0 and d["ltd"] <= 1.10 * d["working_capital"]
            t.append(result("1. Financial condition (CA >= 1.5x CL; debt <= 110% of net current assets)", ok,
                            f"current ratio {fmt(d['current_ratio'])}; debt / NCA {fmt(d['ltd'] / d['working_capital'] if d['working_capital'] else None)}", src))
    else:
        t.append(info("1. Financial condition", "the enterprising financial-condition test is stated for industrials", src))
    eps = d["eps"]
    if len(eps) >= 5:
        t.append(result("2. Earnings stability (no deficit in last 5 yrs)", all(e > 0 for e in eps[-5:]),
                        f"last 5 EPS {[round(e, 2) for e in eps[-5:]]}", src))
    else:
        t.append(result("2. Earnings stability (no deficit in last 5 yrs)", None, "", src, ["5 years of eps_history"]))
    divs = values(c, "dividends_per_share_history")
    cur_div = num(c, "dividend_per_share_current")
    if cur_div is None and divs:
        cur_div = divs[-1]
    if cur_div is None:
        t.append(result("3. Dividend record (some current dividend)", None, "", src, ["dividend_per_share_current"]))
    else:
        t.append(result("3. Dividend record (some current dividend)", cur_div > 0, f"current dividend {fmt(cur_div)}", src))
    if len(eps) >= 6:
        t.append(result("4. Earnings growth (last year > 5 years earlier)", eps[-1] > eps[-6],
                        f"EPS {fmt(eps[-6])} -> {fmt(eps[-1])}", src))
    else:
        t.append(result("4. Earnings growth (last year > 5 years earlier)", None, "", src, ["6 years of eps_history"]))
    if d["price"] is not None and d["tbv_ps"]:
        r = d["price"] / d["tbv_ps"] if d["tbv_ps"] > 0 else float("inf")
        t.append(result("5. Price < 120% of net tangible assets", r < 1.2, f"price / tangible book {fmt(r)}", src))
    else:
        t.append(result("5. Price < 120% of net tangible assets", None, "", src, ["shareholders_equity", "intangibles", "shares"]))
    return t


def valuation(c, d, aaa):
    rows = []
    price = d["price"]
    # Net current asset value (bargain issues)
    if d["ncav_ps"] is not None and price:
        if d["ncav_ps"] <= 0:
            rows.append(info("Net current asset value per share (net-net)",
                             f"{fmt(d['ncav_ps'])}: liabilities exceed current assets, so this is not a net-net candidate",
                             "Classic: net current assets"))
        else:
            rows.append(result("Net-net: price below net current asset value",
                               price < d["ncav_ps"],
                               f"NCAV/share {fmt(d['ncav_ps'])}; price/NCAV {fmt(price / d['ncav_ps'])}; "
                               f"the classic practice bought at <= 2/3 of NCAV (<= {fmt(d['ncav_ps'] * 2 / 3)}). "
                               "Buy only as a diversified group (a couple dozen at least), dropping names with losses in the last 12 months if enough remain",
                               "Classic; modern update"))
    # Defensive price ceiling (derived from defensive criterion 7)
    if d["eps_avg3"] and d["book_ps"] and d["eps_avg3"] > 0 and d["book_ps"] > 0:
        gn = math.sqrt(22.5 * d["eps_avg3"] * d["book_ps"])
        rows.append(info("Defensive price ceiling sqrt(22.5 x EPS(3-yr avg) x BVPS)",
                         f"{fmt(gn)} vs price {fmt(price)} ({fmt(price / gn - 1, pct=True)} vs ceiling). "
                         "This is the highest price meeting the defensive P/E x P/B <= 22.5 test, not an estimate of value", "Classic: defensive criteria"))
    # Growth formula, shown across earnings definitions as a range
    g = num(c, "expected_growth_rate")
    bases = [("latest year", d["eps_ttm"]), ("3-yr avg", d["eps_avg3"]), ("7-yr avg", d["eps_avg7"])]
    if num(c, "eps_normal"):
        bases.insert(0, ("supplied normal", num(c, "eps_normal")))
    bases = [(k, e) for k, e in bases if e and e > 0]
    if g is not None and bases and price:
        gp = g * 100
        vals = [(k, e * (8.5 + 2 * gp)) for k, e in bases]
        warn = " WARNING: growth above ~8% a year cannot be capitalized reliably." if gp > 8 else ""
        rows.append(info("Growth-formula value E x (8.5 + 2g)",
                         f"g {gp:.1f}%: " + "; ".join(f"{k} {fmt(v)}" for k, v in vals) +
                         f" vs price {fmt(price)}.{warn} Present as a range; the 7-yr figure is the conservative end. "
                         "the formula approximates elaborate methods, not 'true value'", "Classic: security analysis"))
    if price and bases:
        rows.append(info("Growth rate implied by price (P/E - 8.5)/2",
                         "; ".join(f"on {k} EPS: P/E {fmt(price / e)} -> {(price / e - 8.5) / 2:.1f}% a year" for k, e in bases)
                         + " for 7-10 years", "Classic: security analysis"))
    # Margin of safety: earnings yield vs high-grade bond yield
    bond = num(c, "aa_bond_yield") or aaa
    if bond and price:
        parts = []
        for k, e in (("3-yr avg", d["eps_avg3"]), ("7-yr avg earning power", d["eps_avg7"])):
            if e:
                ey = e / price
                parts.append(f"{k}: earnings yield {fmt(ey, pct=True)}, spread {fmt(ey - bond, pct=True)}, 10-yr excess ~{fmt((ey - bond) * 10, pct=True)} of price")
        if parts:
            rows.append(info("Earnings yield vs high-grade bond yield",
                             f"bond {fmt(bond, pct=True)}. " + "; ".join(parts) +
                             ". The classic case was 9% vs 4% = ~50% of price; 'no margin' when the spread is ~0", "Classic: margin of safety"))
    # Near-tangible-book screen
    if d["tbv_ps"] and price and d["tbv_ps"] > 0:
        r = price / d["tbv_ps"]
        rows.append(info("Price / tangible book",
                         f"{fmt(r)} (defensive buyers seeking asset backing pay no more than ~1.33x; enterprising screen < 1.2x)", "Classic: asset backing"))
    if d["warrant_adjusted_price"] and price and d["warrant_adjusted_price"] != price:
        rows.append(info("Warrant/option-adjusted price",
                         f"{fmt(d['warrant_adjusted_price'])} per share after adding outstanding warrants' market value; use it in P/E", "Classic: warrants"))
    return rows


def senior_security_tests(c, d):
    """Coverage-table tests, the earnings/debt alternative, and the modern debt check."""
    rows = []
    ctype = (c.get("type") or "industrial").lower()
    mins = COVERAGE_MINIMUMS.get(ctype)
    avg_pre = num(c, "pretax_earnings_before_fixed_charges_avg7")
    poor_pre = num(c, "pretax_earnings_before_fixed_charges_poorest")
    fixed = num(c, "fixed_charges")
    fixed_avg = num(c, "fixed_charges_avg7") or fixed
    fixed_poor = num(c, "fixed_charges_poorest_year") or fixed
    prefdiv = num(c, "preferred_dividends") or 0.0
    if mins and fixed:
        if avg_pre is not None:
            cov = avg_pre / fixed_avg
            basis = "7-yr avg fixed charges" if num(c, "fixed_charges_avg7") else "current fixed charges (supply fixed_charges_avg7 for the exact test)"
            rows.append(result(f"Bond coverage, 7-yr avg pretax (>= {mins['pretax'][0]}x for {ctype})",
                               cov >= mins["pretax"][0], f"{fmt(cov)}x on {basis}", "Classic: coverage table"))
            if prefdiv:
                pc = avg_pre / (fixed_avg + 2 * prefdiv)
                rows.append(result(f"Preferred coverage, 7-yr avg: pretax / (fixed charges + 2x preferred dividends) >= {mins['pretax'][0]}x",
                                   pc >= mins["pretax"][0], f"{fmt(pc)}x", "Classic: coverage table"))
        if poor_pre is not None:
            cov = poor_pre / fixed_poor
            rows.append(result(f"Bond coverage, poorest year pretax (>= {mins['pretax'][1]}x)",
                               cov >= mins["pretax"][1], f"{fmt(cov)}x (either the average or the poorest-year test suffices)", "Classic: coverage table"))
            if prefdiv:
                pc = poor_pre / (fixed_poor + 2 * prefdiv)
                rows.append(result(f"Preferred coverage, poorest year (>= {mins['pretax'][1]}x)",
                                   pc >= mins["pretax"][1], f"{fmt(pc)}x", "Classic: coverage table"))
        avg_after = num(c, "aftertax_earnings_before_fixed_charges_avg7")
        poor_after = num(c, "aftertax_earnings_before_fixed_charges_poorest")
        if avg_after is not None:
            cov = avg_after / fixed_avg
            rows.append(result(f"Bond coverage, 7-yr avg after taxes (>= {mins['aftertax'][0]}x)",
                               cov >= mins["aftertax"][0], f"{fmt(cov)}x (use pretax tests when the company pays little tax)", "Classic: coverage table"))
        if poor_after is not None:
            cov = poor_after / fixed_poor
            rows.append(result(f"Bond coverage, poorest year after taxes (>= {mins['aftertax'][1]}x)",
                               cov >= mins["aftertax"][1], f"{fmt(cov)}x", "Classic: coverage table"))
    elif mins:
        rows.append(result("Bond coverage (coverage table)", None, "", "Classic: coverage table", ["fixed_charges", "pretax_earnings_before_fixed_charges_avg7"]))
    debt = (num(c, "long_term_debt") or 0) + (num(c, "short_term_debt") or 0)
    if avg_pre is not None and debt and ctype in EARNINGS_TO_DEBT_MINIMUMS:
        need = EARNINGS_TO_DEBT_MINIMUMS[ctype]
        r = avg_pre / debt
        note = "; retail threshold is an extrapolation; the classic rules give none" if ctype == "retail" else ""
        rows.append(result(f"High-rate-era alternative: pretax earnings >= {int(need * 100)}% of debt principal",
                           r >= need, f"{fmt(r, pct=True)} (poorest year needs ~2/3 of this{note})", "Classic: security analysis"))
    if d["market_cap"] and debt:
        rows.append(info("Stock/equity ratio (market value of common / total debt + preferred)",
                         f"{fmt(d['market_cap'] / (debt + d['pref']))}x — a rough cushion measure that embeds the market's view", "Classic: security analysis"))
    if d["equity"] is not None:
        cap = d["equity"] + debt
        ltd_pref = (num(c, "long_term_debt") or 0) + d["pref"]
        if cap:
            r = ltd_pref / cap
            rows.append(result("Long-term debt incl. preferred < 50% of total capital", r < 0.5, f"{fmt(r, pct=True)}", "Modern update"))
    return rows


def quality_checks(c, d):
    rows = []
    src = "Modern update"
    ocf = values(c, "operating_cash_flow_history")
    fcf_fin = values(c, "financing_cash_flow_history")
    if ocf and fcf_fin and len(ocf) >= 3 and len(fcf_fin) >= 3:
        neg_ops = sum(1 for v in ocf[-5:] if v < 0)
        pos_fin = sum(1 for v in fcf_fin[-5:] if v > 0)
        flag = neg_ops >= 3 and pos_fin >= 3
        rows.append(result("Not an 'OPM addict' (operating cash flow not chronically negative while financing inflows fund it)",
                           not flag, f"negative operating CF years {neg_ops}/5; positive financing CF years {pos_fin}/5", src))
    oe = num(c, "owner_earnings")
    if oe is None:
        ni, da, capex = num(c, "net_income"), num(c, "depreciation_amortization"), num(c, "maintenance_capex")
        if None not in (ni, da, capex):
            # Start from GAAP net income so "nonrecurring" charges stay deducted.
            oe = ni + da - capex - (num(c, "stock_option_cost") or 0) - (num(c, "pension_income") or 0)
    if oe is not None:
        rows.append(info("Owner earnings (net income + D&A - maintenance capex - option cost - pension income)",
                         f"{fmt(oe)}; per share {fmt(oe / d['diluted_shares']) if d['diluted_shares'] else 'n/a'}", src))
        ic = num(c, "invested_capital")
        if ic:
            roic = oe / ic
            rows.append(result("ROIC = owner earnings / invested capital >= 10% (6-7% tempting with a moat or temporary cloud)",
                               roic >= 0.10, fmt(roic, pct=True), "Davis"))
    oeh = values(c, "owner_earnings_history")
    if len(oeh) >= 5 and oeh[0] > 0 and oeh[-1] > 0:
        cagr = (oeh[-1] / oeh[0]) ** (1 / (len(oeh) - 1)) - 1
        rows.append(result("Owner earnings growing >= 6-7% a year (ideally over 10 years)", cagr >= 0.06,
                           f"{fmt(cagr, pct=True)} a year over {len(oeh) - 1} years; use per-share figures", "Modern update"))
    granted = num(c, "options_granted")
    if granted is not None and d["shares"]:
        r = granted / d["shares"]
        rows.append(result("Option grants <= ~3% of shares (per plan or per year)", r <= 0.03,
                           f"new grants = {fmt(r, pct=True)} of shares outstanding; vote against plans above this, "
                           "and against plans not tied to beating peers over 5+ years", "Modern update; Davis"))
    opts = num(c, "options_outstanding")
    if opts and d["shares"]:
        r = opts / d["shares"]
        rows.append(result("Option overhang <= 5% of shares outstanding", r <= 0.05,
                           f"options outstanding = {fmt(r, pct=True)} of shares: a dilution figure, separate from the ~3% grant test; "
                           "value per share on the fully diluted count", "Skill extension"))
    acq = num(c, "acquisitions_per_year")
    if acq is not None:
        rows.append(result("Not a serial acquirer (<= 2-3 acquisitions a year)", acq <= 3, f"{acq:g} a year", "Modern update"))
    nr = num(c, "years_with_nonrecurring_charges_last5")
    if nr is not None:
        rows.append(result("'Nonrecurring' charges not recurring (<= 1 of last 5 years)", nr <= 1, f"{nr:g} of 5 years", "Classic; modern update"))
    pen, ni = num(c, "pension_income"), num(c, "net_income")
    if pen and ni and ni > 0:
        r = pen / ni
        rows.append(result("Pension income <= 5% of net income", r <= 0.05,
                           f"{fmt(r, pct=True)} of net income; strip it from owner earnings", "Modern update"))
    pr = num(c, "pension_return_assumption")
    if pr is not None:
        rows.append(info("Assumed return on pension assets",
                         f"{fmt(pr, pct=True)}: the 2003 recalibration called anything above 6.5% implausible; judge against today's "
                         "high-grade yields plus a modest equity premium, and flag a rising assumption", "Modern update"))
    taxes = num(c, "years_paying_little_or_no_tax_while_profitable")
    if taxes is not None:
        rows.append(result("Pays taxes consistent with reported profits", taxes < 3,
                           f"{taxes:g} profitable years with little or no tax (Penn Central warning)", "Classic: Penn Central case"))
    return rows


PAYOUT_NORMAL = 0.65         # "about two-thirds" of earnings
RETAINED_RETURN_BAR = 0.10   # yardstick for a "satisfactory" return on retained EPS


def payout_info(c, d):
    divs = values(c, "dividends_per_share_history")
    eps = d["eps"]
    rows = []
    src = "Classic: dividend policy"
    name = "Dividend policy: payout ~2/3, or retained earnings shown to raise EPS"
    p = None
    if divs and eps and len(divs) >= 3 and len(eps) >= 3:
        p = avg(divs[-5:]) / avg(eps[-5:]) if avg(eps[-5:]) else None
        rows.append(info("Payout ratio (5-yr avg dividends / 5-yr avg EPS)",
                         f"{fmt(p, pct=True)} (the classic 'standard' policy paid ~2/3 of average earnings; see management-and-dividends.md)", src))
    if p is None:
        rows.append(result(name, None, "", src, ["3+ years of eps_history and dividends_per_share_history with positive average EPS"]))
        return rows
    if p >= PAYOUT_NORMAL:
        rows.append(result(name, True, f"payout {fmt(p, pct=True)} meets the ~2/3 normal payout (>= {fmt(PAYOUT_NORMAL, pct=True, digits=0)})", src))
        return rows
    # Low payout: compare the EPS gain with the EPS retained over the same years.
    e_map, d_map = dict(series(c, "eps_history")), dict(series(c, "dividends_per_share_history"))
    years = sorted(k for k in e_map if k in d_map)[-11:]
    if len(years) < 6:
        rows.append(result(name, None, "", src,
                           [f"6-11 matching years of eps_history and dividends_per_share_history to test retained earnings (have {len(years)})"]))
        return rows
    gain = e_map[years[-1]] - e_map[years[0]]
    retained = sum(e_map[y] - d_map[y] for y in years[:-1])  # earnings kept in years 0..n-1 feed EPS by year n
    span = f"{years[0]}-{years[-1]}" + ("" if len(years) == 11 else f" ({len(years) - 1} years; 10 is the full test)")
    if retained <= 0:
        rows.append(result(name, False, f"payout {fmt(p, pct=True)} below ~2/3 and no EPS retained over {span}", src))
        return rows
    r = gain / retained
    ok = r >= RETAINED_RETURN_BAR
    detail = (f"payout {fmt(p, pct=True)} is low, so the company must show retained earnings paid off: EPS {fmt(e_map[years[0]])} -> "
              f"{fmt(e_map[years[-1]])} (gain {fmt(gain)}) on cumulative retained EPS {fmt(retained)} over {span} = "
              f"{fmt(r, pct=True)} return on retained earnings vs a {fmt(RETAINED_RETURN_BAR, pct=True, digits=0)} yardstick "
              "(the yardstick is a skill extension; single-year endpoints are noisy, so check with normalized EPS)")
    if not ok:
        detail += ("; low payout without a satisfactory return on retained earnings: shareholders may inquire. "
                   "If dividends are low because finances are weak, the weak finances are the issue")
    rows.append(result(name, ok, detail, src))
    return rows


# --------------------------------------------------------------- reporting

def analyze(c, cpi, aaa_default):
    d = derived(c)
    aaa = num(c, "aaa_bond_yield") or aaa_default
    sections = {
        "Defensive investor: seven criteria": defensive_tests(c, d, cpi),
        "Defensive investor: 2003 recalibration": modern_2003_checks(c, d, cpi),
        "Defensive investor: general stock rules": general_rules_tests(c, d, cpi),
        "Enterprising investor: screen": enterprising_tests(c, d),
        "Valuation and margin of safety": valuation(c, d, aaa),
        "Senior-security and balance-sheet safety": senior_security_tests(c, d),
        "Quality and accounting checks": quality_checks(c, d) + payout_info(c, d),
    }
    passed = sum(1 for r in sections["Defensive investor: seven criteria"] if r["status"] == "PASS")
    known = sum(1 for r in sections["Defensive investor: seven criteria"] if r["status"] in ("PASS", "FAIL"))
    ent_p = sum(1 for r in sections["Enterprising investor: screen"] if r["status"] == "PASS")
    ent_k = sum(1 for r in sections["Enterprising investor: screen"] if r["status"] in ("PASS", "FAIL"))
    pe3 = d["price"] / d["eps_avg3"] if d["price"] and d["eps_avg3"] and d["eps_avg3"] > 0 else None
    return {
        "name": c.get("name", "?"),
        "ticker": c.get("ticker"),
        "as_of": c.get("as_of"),
        "summary": {
            "defensive_passed": f"{passed} passed of {known} evaluated (7 criteria)",
            "enterprising_passed": f"{ent_p} passed of {ent_k} evaluated (5 criteria)",
        },
        "_portfolio": {"price": d["price"], "eps_avg3": d["eps_avg3"], "pe3": pe3,
                       "position_value": num(c, "position_value"), "bond_yield": num(c, "aa_bond_yield") or aaa},
        "derived": {k: d[k] for k in ("eps_ttm", "eps_avg3", "eps_avg7", "book_ps", "tbv_ps",
                                       "ncav_ps", "current_ratio", "working_capital", "market_cap")},
        "sections": sections,
    }


def to_markdown(r):
    lines = [f"## {r['name']}" + (f" ({r['ticker']})" if r.get("ticker") else "") + (f" — data as of {r['as_of']}" if r.get("as_of") else "")]
    s = r["summary"]
    lines.append(f"- Defensive: {s['defensive_passed']}  |  Enterprising: {s['enterprising_passed']}")
    dd = r["derived"]
    lines.append("- Derived: " + "; ".join(f"{k} {fmt(v)}" for k, v in dd.items()))
    for title, rows in r["sections"].items():
        if not rows:
            continue
        lines.append(f"\n### {title}")
        lines.append("| Test | Result | Detail | Basis |")
        lines.append("|---|---|---|---|")
        for row in rows:
            detail = (row.get("detail") or "").replace("|", "/")
            lines.append(f"| {row['test']} | {row['status']} | {detail} | {row['source']} |")
    lines.append("\n_Mechanical tests only. Verify inputs against filings, adjust earnings for special items, and apply judgment before concluding._")
    return "\n".join(lines)


def portfolio_summary(reports, bond_yield):
    """Classic rule: the portfolio's overall earnings/price ratio should be at least the
    current high-grade (AA) bond yield."""
    rows = [r["_portfolio"] for r in reports]
    use = [x for x in rows if x["price"] and x["eps_avg3"]]
    if not use:
        return {"status": "insufficient data", "detail": "need price and 3 years of eps_history for at least one holding"}
    weights = [x["position_value"] for x in use]
    if all(w for w in weights):
        basis = "position values supplied"
    else:
        weights = [1.0] * len(use)
        basis = "equal weights (no position_value fields)"
    total = sum(weights)
    ey = sum(w * x["eps_avg3"] / x["price"] for w, x in zip(weights, use)) / total
    by = bond_yield or next((x["bond_yield"] for x in use if x["bond_yield"]), None)
    out = {"holdings_used": len(use), "weighting": basis, "earnings_yield": ey,
           "pe_equivalent": 1 / ey if ey > 0 else None, "bond_yield": by}
    if by:
        out["status"] = "PASS" if ey >= by else "FAIL"
        out["detail"] = (f"portfolio earnings yield on 3-yr avg EPS {fmt(ey, pct=True)} (P/E {fmt(out['pe_equivalent'])}) "
                         f"vs high-grade bond yield {fmt(by, pct=True)}; max portfolio P/E {fmt(1 / by)}")
    else:
        out["status"] = "insufficient data"
        out["detail"] = f"portfolio earnings yield {fmt(ey, pct=True)}; supply --aa-yield to compare with high-grade bonds"
    if len(use) < 10:
        out["detail"] += f". Only {len(use)} holdings: the defensive range is 10-30"
    return out


def portfolio_markdown(p):
    return ("\n\n## Portfolio test (classic rule)\n"
            f"- Overall earnings/price ratio >= high-grade bond yield: **{p['status']}**. {p['detail']}"
            + (f" (weighting: {p['weighting']})" if p.get("weighting") else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="JSON file with one company object or a list of them ('-' for stdin)")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown")
    ap.add_argument("--cpi-multiplier", type=float, default=DEFAULT_CPI_MULTIPLIER,
                    help="ratio of current CPI to 1971 CPI for the classic size floors (default %(default)s)")
    ap.add_argument("--aaa-yield", type=float, default=None,
                    help="current high-grade (AAA) corporate bond yield as a decimal, used when a company lacks aaa_bond_yield")
    ap.add_argument("--aa-yield", type=float, default=None,
                    help="high-grade (AA) bond yield for the portfolio earnings-yield test (defaults to the AAA yield)")
    a = ap.parse_args(argv)
    raw = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    data = json.loads(raw)
    companies = data if isinstance(data, list) else [data]
    reports = [analyze(c, a.cpi_multiplier, a.aaa_yield) for c in companies]
    port = portfolio_summary(reports, a.aa_yield or a.aaa_yield) if isinstance(data, list) else None
    for r in reports:
        r.pop("_portfolio", None)
    if a.format == "json":
        out = {"companies": reports, "portfolio": port} if port else reports[0]
        print(json.dumps(out, indent=2, default=str))
    else:
        print("\n\n".join(to_markdown(r) for r in reports) + (portfolio_markdown(port) if port else ""))


if __name__ == "__main__":
    main()
