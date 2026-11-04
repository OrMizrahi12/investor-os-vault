"""Base-value method for Corning, as approved Nov. 3, 2026 and saved in Rules/when-to-buy.md. No network, and it writes nothing.
All per-share figures use 871M diluted shares (Q3 2026). Amounts are $M unless marked."""

import csv
import importlib.util
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
_spec = importlib.util.spec_from_file_location("parts_model", ROOT / "sensors/parts/model.py")
parts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parts)

PRICE = 123.20  # close of Nov. 2, 2026, the latest saved. Today's close is not in.
SHARES = 871
RATE = 0.09
AAA = 0.0612  # Moody's Aaa, Oct. 2026, FRED
MOST = 0.75  # the approved number for "most"

YEARS = list(range(2016, 2026))
NORMAL_NI = dict(zip(YEARS, [1323, 1496, 1270, 783, 133, 1519, 1097, 543, 577, 1543]))  # normal.html
NORMAL_EPS = dict(zip(YEARS, [1.16, 1.47, 1.35, 0.87, 0.05, 1.74, 1.28, 0.63, 0.66, 1.77]))
SALES = dict(zip(YEARS, [9390, 10116, 11290, 11503, 11303, 14082, 14189, 12588, 13118, 15629]))
FCF = dict(zip(YEARS, [1407, 200, 677, 53, 803, 1775, 1011, 615, 974, 1413]))
YEAR_END_CLOSE = dict(zip(YEARS, [24.27, 31.99, 30.21, 29.11, 36.00, 37.23, 31.94, 30.45, 47.52, 87.56]))

# Twelve months to Sept. 30, 2026: FY2025 + nine months of 2026 - nine months of 2025.
TTM_SALES = 15629 + 13504 - 11414
TTM_NI = 1596 + 1610 - 1056
# The three kinds of item I confirmed for normal earnings, net income effect, as (FY2025, 9M 2025, 9M 2026).
# 10-K filed Feb. 12, 2026; 10-Q filed Oct. 29, 2026; Q3 release, Oct. 27, 2026.
TTM_ITEMS = {"Foreign debt translation": (40, 50, 0), "Unrealized hedge results": (-111, -47, -41),
             "Investment, business and asset sales": (18, 7 + 4, 22 - 1 - 12)}
TTM_ADJ = {k: v[0] - v[1] + v[2] for k, v in TTM_ITEMS.items()}
TTM_NORMAL_NI = TTM_NI + sum(TTM_ADJ.values())

# Cash readings, twelve months to Sept. 30, 2026, $M, as on worth.html.
CASH_LOW, CASH_MID, CASH_HIGH = 971, 1256, 1505
OCF = 4192
LINE = 956  # filed deposits and incentives line
UPKEEP_CEILING = 965  # lowest capex in ten years, FY2024
STOCK_PAY, LEASES, RECEIVABLES = 368, 428, 165


def perpetuity(cash, g, r):
    return cash * (1 + g) / (r - g)


def worth(cash, g, r, t=0.03):
    """The worth.html formula: g for ten years, t after."""
    ten = sum(cash * (1 + g) ** i / (1 + r) ** i for i in range(1, 11))
    return ten + cash * (1 + g) ** 10 * (1 + t) / (r - t) / (1 + r) ** 10


def need(price, cash, r, t=0.03):
    """Growth for ten years that the price needs, as priced-in.html solves it."""
    lo, hi = -0.5, 1.0
    for _ in range(80):
        x = (lo + hi) / 2
        if worth(cash, x, r, t) < price:
            lo = x
        else:
            hi = x
    return lo


def cagr(a, b, n):
    return (b / a) ** (1 / n) - 1


def anchors():
    low = sum(NORMAL_NI.values()) / 10 / SHARES
    mid = NORMAL_NI[2025] / SHARES
    high = TTM_NORMAL_NI / SHARES
    margin = sum(NORMAL_NI.values()) / sum(SALES.values())
    owner = OCF - LINE - UPKEEP_CEILING - STOCK_PAY - LEASES - RECEIVABLES
    return dict(low=low, mid=mid, high=high, margin=margin, margin_eps=margin * TTM_SALES / SHARES,
                owner=owner, owner_eps=owner / SHARES)


def growth():
    return dict(fcf=cagr(FCF[2016], FCF[2025], 9), ni=cagr(NORMAL_NI[2016], NORMAL_NI[2025], 9),
                sales=cagr(SALES[2016], SALES[2025], 9), fcf_sh=cagr(1.23, 1.62, 9))


def past_tags():
    tags = {y: YEAR_END_CLOSE[y] / NORMAL_EPS[y] for y in YEARS}
    vals = sorted(tags.values())
    return dict(tags=tags, low=vals[0], median=statistics.median(vals), high=vals[-1])


def methods(r=RATE):
    a, g, t = anchors(), growth(), past_tags()
    pp = parts.build()["cases"]
    return [
        dict(key="earn", name="Normal earnings, no growth", low=a["low"] / r, mid=a["mid"] / r, high=a["high"] / r, w=.40),
        dict(key="cash", name="Cash sum, record growth", low=perpetuity(CASH_LOW / SHARES, 0, r),
             mid=perpetuity(CASH_MID / SHARES, g["ni"], r), high=perpetuity(CASH_HIGH / SHARES, .03, r), w=.40),
        dict(key="bond", name="Normal earnings at the Aaa yield", low=a["low"] / AAA, mid=a["mid"] / AAA, high=a["high"] / AAA, w=.20),
        dict(key="past", name="Own past tag on normal earnings", low=t["low"] * a["low"], mid=t["median"] * a["mid"],
             high=t["median"] * a["high"], w=0),
        dict(key="parts", name="Parts at rival multiples", low=pp[0]["eq"] / SHARES, mid=pp[1]["eq"] / SHARES, high=pp[2]["eq"] / SHARES, w=0),
    ]


def combine(ms, weights=None):
    wt = weights or {m["key"]: m["w"] for m in ms}
    tot = sum(wt.values())
    return {k: sum(m[k] * wt.get(m["key"], 0) for m in ms) / tot for k in ("low", "mid", "high")}


def buy_below(base_mid, most=MOST):
    return base_mid / most


def closes():
    with open(ROOT / "sensors/prices/cache/GLW/2026-11-02.csv") as f:
        return [(r["date"], float(r["close"])) for r in csv.DictReader(f)]


def days_under(level):
    rows = closes()
    hits = [d for d, c in rows if c < level]
    since = [r for r in rows if r[0] >= "2016-01-01"]
    return dict(all=len(hits), of=len(rows), last=hits[-1] if hits else None, since16=sum(c < level for _, c in since), of16=len(since))


if __name__ == "__main__":
    a, g = anchors(), growth()
    print(a), print(g), print(past_tags()), print("TTM", TTM_NI, TTM_ADJ, TTM_NORMAL_NI)
    ms = methods()
    for m in ms:
        print(m["name"], round(m["low"], 2), round(m["mid"], 2), round(m["high"], 2), m["w"])
    b = combine(ms)
    print("BASE", b, "coverage", {k: v / PRICE for k, v in b.items()})
    print("MoS", (b["mid"] - PRICE) / b["mid"], "fall to base", 1 - b["mid"] / PRICE)
    for most in (.51, .60, 2 / 3, .75, .9, 1.0):
        bb = buy_below(b["mid"], most)
        print(f"most {most:.2f} buy {bb:.2f} low cov {b['low'] / bb:.2f} high cov {b['high'] / bb:.2f} need9 from1.73 {need(bb, CASH_HIGH / SHARES, .09):.3f} from1.44 {need(bb, CASH_MID / SHARES, .09):.3f} P/E on 1.77 {bb / a['mid']:.1f}", days_under(bb))
    for r in (.08, .09, .10, .11):
        c = combine(methods(r))
        print("rate", r, {k: round(v, 1) for k, v in c.items()}, "buy", round(buy_below(c["mid"]), 1))
    ms9 = methods()
    for label, w in [("earn only", dict(earn=1)), ("earn+cash", dict(earn=1, cash=1)), ("proposed", None), ("add past 10", dict(earn=.35, cash=.35, bond=.2, past=.1)),
                     ("add past+parts 10", dict(earn=.3, cash=.3, bond=.2, past=.1, parts=.1)), ("equal all 5", dict(earn=1, cash=1, bond=1, past=1, parts=1))]:
        c = combine(ms9, w)
        print(label, {k: round(v, 1) for k, v in c.items()}, "buy", round(buy_below(c["mid"]), 1), 'cov', round(c['mid'] / PRICE, 3))
    for p in (25, 50, 75, 100, 123.2):
        print("price", p, "need from 1.73 at 9%", round(need(p, CASH_HIGH / SHARES, .09), 3))
