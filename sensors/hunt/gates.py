"""Gate 1 and Gate 2 of the hunt triage, from one company's saved SEC facts. No network, no price of its own, no view.

The gates are the ones in Research/2026-11-03 Triage.md, which the owner accepted on Nov. 3, 2026.
Gate 2's base is the shortcut there: reported net income for normal earnings, one cash reading. It is a proposal.
A figure that cannot be read leaves its test open. It never counts as a pass or a fail.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/valuation/scripts"))
import value  # noqa: E402

NI = ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"]
REV = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet"]
OCF = ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]
CAPEX = ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets", "PaymentsToAcquireOilAndGasPropertyAndEquipment"]
OPINC = ["OperatingIncomeLoss"]
INT = ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt"]
DEBT_TOTAL = ["DebtLongtermAndShorttermCombinedAmount", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations", "DebtInstrumentCarryingAmount"]
DEBT_PARTS = ["LongTermDebtNoncurrent", "LongTermDebtCurrent", "ShortTermBorrowings", "CommercialPaper", "ConvertibleNotesPayable", "ConvertibleDebt", "ConvertibleLongTermNotesPayable", "ConvertibleNotesPayableCurrent", "ConvertibleDebtNoncurrent", "ConvertibleDebtCurrent", "SeniorNotes"]
SHARES = ["WeightedAverageNumberOfDilutedSharesOutstanding"]
CL = ["ContractWithCustomerLiability"]
CL_PARTS = ["ContractWithCustomerLiabilityCurrent", "ContractWithCustomerLiabilityNoncurrent"]


def days(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


class Facts:
    def __init__(self, data):
        self.gaap = data.get("facts", {}).get("us-gaap", {})

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def rows(self, tag, unit=None):
        units = self.gaap.get(tag, {}).get("units", {})
        return units.get(unit) if unit else (units.get("USD") or units.get("shares") or [])

    def annual(self, tags, pick="first"):
        """Period end to value, from 10-K forms and a full year. The newest filing wins, so a restated figure replaces the old one."""
        out = {}
        for tag in tags:
            best = {}
            for r in self.rows(tag):
                if "start" in r and r.get("form", "").startswith(("10-K", "20-F", "40-F")) and 340 < days(r["start"], r["end"]) < 380:
                    if r["end"] not in best or r["filed"] > best[r["end"]]["filed"]:
                        best[r["end"]] = r
            for end, r in best.items():
                if end not in out or (pick == "max" and r["val"] > out[end]):
                    out[end] = r["val"]
        return dict(sorted(out.items()))

    def after_year(self, tags, year_end):
        """The newest year-to-date span after a year end, and the same span a year earlier, from 10-Q forms."""
        for tag in tags:
            rows = [r for r in self.rows(tag) if "start" in r and r.get("form", "").startswith("10-Q")]
            now = [r for r in rows if year_end is None or (0 < days(year_end, r["start"]) < 15)]
            if not now:
                continue
            newest = max(r["end"] for r in now)  # the newest end, and the longest span to it: the year to date
            cur = max((r for r in now if r["end"] == newest), key=lambda r: (days(r["start"], r["end"]), r["filed"]))
            prior = [r for r in rows if abs(days(r["end"], cur["end"]) - 365) < 12 and abs(days(r["start"], cur["start"]) - 365) < 12]
            return cur, (max(prior, key=lambda r: r["filed"]) if prior else None)
        return None, None

    def twelve_months(self, tags):
        """Last year + this year to date - last year to date. Returns value, a description, and the end date. None if it cannot be built."""
        ann = self.annual(tags)
        if not ann:
            return None, "no full year on file", None
        end = list(ann)[-1]
        cur, prior = self.after_year(tags, end)
        if cur is None or cur["end"] <= end:
            return ann[end], f"year to {end}", end
        if prior is None:
            return None, f"no same span a year before {cur['end']}", None
        return ann[end] + cur["val"] - prior["val"], f"twelve months to {cur['end']}", cur["end"]

    def balance(self, tags, near=None):
        for tag in tags:
            rows = [r for r in self.rows(tag) if "start" not in r and r.get("form", "").startswith(("10-K", "10-Q"))]
            if rows:
                r = max(rows, key=lambda x: (x["end"], x["filed"]))
                if near is None or abs(days(r["end"], near)) < 120:
                    return r["val"], r["end"]
        return None, None

    def balance_at(self, tags, day, slack=25):
        for tag in tags:
            rows = [r for r in self.rows(tag) if "start" not in r and abs(days(r["end"], day)) <= slack]
            if rows:
                return max(rows, key=lambda x: (x["filed"]))["val"]
        return None

    def newest_end(self):
        ends = [r["end"] for tag in OCF + NI for r in self.rows(tag) if r.get("form", "").startswith(("10-K", "10-Q"))]
        return max(ends) if ends else None

    def latest_year_revenue(self):
        rev = self.annual(REV, pick="max")
        return (list(rev)[-1], rev[list(rev)[-1]]) if rev else (None, None)


def m(v):
    return f"{'-' if v < 0 else ''}${abs(v) / 1e6:,.1f}M"


def gate1(f):
    """Every test: name, state (pass, fail, open), and what it read. The sort: any fail is a fail, else any open is open."""
    tests = []
    ni = f.annual(NI)
    years = list(ni.items())[-10:]
    wins, losses = sum(v > 0 for _, v in years), sum(v <= 0 for _, v in years)
    if not years:
        tests.append(("Profit years", "open", "No full year on file."))
    elif len(years) == 10:
        tests.append(("Profit years", "pass" if wins >= 8 else "fail", f"Profit in {wins} of 10 years, FY ending {years[0][0][:4]} to {years[-1][0][:4]}."))
    elif losses > 2:
        tests.append(("Profit years", "fail", f"Losses in {losses} of the {len(years)} years on file, so 8 of 10 can no longer be reached."))
    else:
        tests.append(("Profit years", "open", f"Only {len(years)} years on file, {losses} with a loss."))

    ocf, ocf_span, _ = f.twelve_months(OCF)
    capex, _, _ = f.twelve_months(CAPEX)
    if ocf is None and not f.annual(OCF):  # a new filer: only the year to date
        cur, _ = f.after_year(OCF, None)
        cap, _ = f.after_year(CAPEX, None)
        if cur and cap and cur["end"] == cap["end"]:
            fcf = cur["val"] - cap["val"]
            tests.append(("Free cash flow", "fail" if fcf <= 0 else "open", f"{m(fcf)} from {cur['start']} to {cur['end']}, under a year."))
        else:
            tests.append(("Free cash flow", "open", "Not readable."))
    elif ocf is None or capex is None:
        tests.append(("Free cash flow", "open", f"Not readable: {ocf_span}."))
    else:
        fcf = ocf - capex
        tests.append(("Free cash flow", "pass" if fcf > 0 else "fail", f"{m(fcf)}, {ocf_span}: {m(ocf)} of operating cash less {m(capex)} of capex."))

    near = f.newest_end()
    debt, on = f.balance(DEBT_TOTAL, near)
    if debt is None:
        parts = [f.balance([t], near) for t in DEBT_PARTS]
        have = [p for p in parts if p[0] is not None]
        if have:
            debt, on = sum(p[0] for p in have), max(p[1] for p in have)
    if debt is None:
        tests.append(("Debt", "open", "No debt line on file for the newest period. That does not mean no debt."))
    elif ocf is None or ocf <= 0:
        tests.append(("Debt", "open" if debt else "pass", f"Debt {m(debt)} at {on}, with no positive operating cash to compare."))
    else:
        tests.append(("Debt", "pass" if debt <= 4 * ocf else "fail", f"Debt {m(debt)} at {on} is {debt / ocf:.1f}× twelve-month operating cash, against a bar of 4×."))

    op, it = f.annual(OPINC), f.annual(INT)
    both = [(op[k], it[k]) for k in op if k in it and it[k] > 0][-10:]
    if len(both) < 3:
        tests.append(("Interest cover", "open", f"Operating profit and interest both on file for only {len(both)} years."))
    else:
        cover = sum(a for a, _ in both) / sum(b for _, b in both)
        tests.append(("Interest cover", "pass" if cover >= 3 else "fail", f"Operating profit {cover:.1f}× interest over {len(both)} years, against a bar of 3×."))

    rev = list(f.annual(REV, pick="max").items())[-10:]
    if len(rev) < 2:
        tests.append(("Sales", "open", "Fewer than two years of sales on file."))
    else:
        tests.append(("Sales", "pass" if rev[-1][1] > rev[0][1] else "fail", f"{m(rev[0][1])} in FY ending {rev[0][0][:4]} to {m(rev[-1][1])} in FY ending {rev[-1][0][:4]}."))

    states = {t[1] for t in tests}
    return {"state": "fail" if "fail" in states else "open" if "open" in states else "pass", "tests": [dict(name=a, state=b, read=c) for a, b, c in tests]}


def base(f, aaa, aaa_src, sec_url, retrieved, peak_flag=3.0):
    """The Gate 2 shortcut, summed by the valuation skill's value.py. Returns None and a reason if an input is missing."""
    ni = f.annual(NI)
    if not ni:
        return None, "No full year of net income on file."
    years = list(ni.items())
    last_end, last = years[-1]
    avg = sum(v for _, v in years[-10:]) / len(years[-10:])
    ttm, ttm_span, _ = f.twelve_months(NI)
    ocf, _, ocf_end = f.twelve_months(OCF)
    capex, _, _ = f.twelve_months(CAPEX)
    if ttm is None or ocf is None or capex is None:
        return None, "Twelve-month earnings or cash could not be read."
    rows = [r for r in f.rows(SHARES[0]) if "start" in r and r.get("form", "").startswith(("10-K", "10-Q"))]
    if not rows:
        return None, "No diluted share count on file."
    newest = max(r["end"] for r in rows)
    shares = min((r for r in rows if r["end"] == newest), key=lambda r: (days(r["start"], r["end"]), r["filed"]))["val"]
    if ocf_end is None:
        return None, "No end date for the twelve months."
    start = (dt.date.fromisoformat(ocf_end) - dt.timedelta(days=365)).isoformat()
    now, then = f.balance_at(CL, ocf_end), f.balance_at(CL, start)
    if now is None or then is None:
        pn = [f.balance_at([t], ocf_end) for t in CL_PARTS]
        pt = [f.balance_at([t], start) for t in CL_PARTS]
        if pn[0] is not None and pt[0] is not None:
            now, then = sum(x or 0 for x in pn), sum(x or 0 for x in pt)
    rise = (now - then) if now is not None and then is not None else 0
    cl_read = f"contract liabilities {m(then)} to {m(now)}" if now is not None and then is not None else "no contract liabilities on file for both dates, so none taken out"
    fcf = ocf - capex
    cash = fcf - rise
    # Growth: the record of free cash flow per share, never above 3%.
    of, cf = f.annual(OCF), f.annual(CAPEX)
    both = [k for k in of if k in cf][-10:]
    rec = 0.0
    if len(both) >= 2 and of[both[0]] - cf[both[0]] > 0 and of[both[-1]] - cf[both[-1]] > 0:
        rec = ((of[both[-1]] - cf[both[-1]]) / (of[both[0]] - cf[both[0]])) ** (1 / (len(both) - 1)) - 1
    # A falling record is the ceiling too, Rules/when-to-buy.md: growth at no more than the company's own record.
    g = min(value.GROWTH_CAP, rec)
    g_low = min(0.0, g)
    src = f"[SEC company facts, retrieved {retrieved}]({sec_url})"
    node = lambda v, what="": {"v": v, "src": f"{what} {src}".strip(), "status": "unconfirmed"}
    d = {"inputs": {
        "shares_diluted_m": node(shares / 1e6), "aaa": {"v": aaa, "src": aaa_src}, "record_growth": node(rec),
        "earnings_m": {"low": node(avg / 1e6), "mid": node(last / 1e6), "high": node(ttm / 1e6)},
        "cash_m": {k: node(cash / 1e6) for k in ("low", "mid", "high")},
        "growth": {"low": {"v": g_low, "src": "no growth, or the record if it fell, base.html and Rules/when-to-buy.md, Nov. 3, 2026"}, "mid": {"v": g, "src": "the record, capped, Rules/when-to-buy.md, Nov. 3, 2026"}, "high": {"v": g, "src": "the record, capped, Rules/when-to-buy.md, Nov. 3, 2026"}},
    }}
    inp = value.Inputs()
    b = value.base(d, inp)
    if b is None or inp.problems:
        return None, "; ".join(inp.problems)
    combined = b["combined"]
    earlier = [v for _, v in years[:-1]]
    peak = last / max(earlier) if earlier and max(earlier) > 0 and last > 0 else None
    return {"low": combined["low"], "mid": combined["mid"], "high": combined["high"], "buy_below": combined["mid"] / value.COVER_BAR,
            "reads": {"earnings_low": avg, "earnings_mid": last, "earnings_high": ttm, "earnings_span": ttm_span, "fcf": fcf, "rise": rise, "cash": cash, "cl": cl_read,
                      "shares": shares, "shares_end": newest, "growth": g, "record": rec, "year": last_end},
            "peak": peak, "peak_flag": bool(peak and peak >= peak_flag)}, None
