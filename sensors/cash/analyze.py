"""Cash lesson, step 2: work out every figure the page uses. No network.

    .venv/bin/python -I sensors/cash/analyze.py

Reads cache/monthly.csv and annual.csv. Writes cache/results.json. History, not a forecast.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
START, END = "2006-10", "2026-10"
BANDS = [("Low", 0, 20, 5), ("Middle", 20, 30, 15), ("High", 30, 999, 25)]
FIXED = [0, 5, 10, 15, 20, 25, 30, 50]


def load():
    m = pd.read_csv(CACHE / "monthly.csv")
    m.index = pd.PeriodIndex.from_fields(year=m.year, month=m.month, freq="M")
    d = m.loc["1928-01":].copy()
    d["bg"] = 1 + d.bill_pct / 100 * d.index.days_in_month / 365  # roll the bill at that month's average rate
    d["bill"] = d.bg.shift(1).fillna(1).cumprod()
    return m, d, pd.read_csv(CACHE / "annual.csv").set_index("year")


def period(s, e, d):
    x = d.loc[s:e]
    years = (len(x) - 1) / 12
    sp, bill, cpi = (x[c].iloc[-1] / x[c].iloc[0] for c in ("tr", "bill", "cpi"))
    real_bill = x.bill / x.cpi
    dd = x.tr / x.tr.cummax() - 1
    rd = real_bill / real_bill.cummax() - 1
    return {"start": s, "end": e, "years": years, "sp": sp, "bill": bill, "cpi": cpi,
            "sp_cagr": sp ** (1 / years) - 1, "bill_cagr": bill ** (1 / years) - 1, "cpi_cagr": cpi ** (1 / years) - 1,
            "sp_real_cagr": (sp / cpi) ** (1 / years) - 1, "bill_real_cagr": (bill / cpi) ** (1 / years) - 1,
            "sp_worst": dd.min(), "sp_worst_month": str(dd.idxmin()), "bill_real_worst": rd.min(), "bill_real_worst_month": str(rd.idxmin())}


def underwater(x):
    """Longest run of months below an earlier high, and the months from that high to getting back."""
    best = run = 0
    peak = x.iloc[0]
    for v in x:
        if v >= peak:
            peak, run = v, 0
        else:
            run += 1
            best = max(best, run)
    return best


def waits(x, cape_all=None):
    rows = []
    for n in (1, 2, 3, 5, 10):
        sp = (x.tr.shift(-12 * n) / x.tr).dropna()
        bill = (x.bill.shift(-12 * n) / x.bill).dropna()
        rows.append({"years": n, "starts": len(sp), "bills_won": int((bill > sp).sum()), "share": float((bill > sp).mean()),
                     "sp_median": float(sp.median()), "bill_median": float(bill.median()), "sp_worst": float(sp.min()),
                     "cost_median": float((sp - bill).median() * 100000)})
    return rows


def by_band(d):
    out = []
    for n in (1, 5, 10):
        gap = (d.tr.shift(-12 * n) / d.tr) ** (1 / n) - (d.bill.shift(-12 * n) / d.bill) ** (1 / n)
        gap = gap.dropna()
        cape = d.cape.reindex(gap.index)
        for name, lo, hi, _ in BANDS:
            k = gap[(cape >= lo) & (cape < hi)]
            eps = []
            months = list(k.index)
            for t in months:
                if eps and (t - eps[-1][1]).n == 1:
                    eps[-1][1] = t
                else:
                    eps.append([t, t])
            out.append({"years": n, "band": name, "starts": len(k), "bills_won": int((k < 0).sum()), "share": float((k < 0).mean()),
                        "gap_median": float(k.median()), "runs": len(eps),
                        "runs_list": [f"{a}..{b}" for a, b in eps] if len(eps) < 12 else None})
    return out


def line(cape):
    for _, lo, hi, pct in BANDS:
        if lo <= cape < hi:
            return pct / 100
    raise ValueError(cape)


def mix(s, e, d, rule):
    """Reset once a year to the reserve the rule gives, on last month's gauge. A sum: it sells to move, and my rules would not."""
    x = d.loc[s:e]
    tr, bg, cape = x.tr.values, x.bg.values, x.cape.values
    r = rule(cape[0])
    stock, cash = 1 - r, r
    peak = 1.0
    worst = 0.0
    for i in range(1, len(x)):
        stock *= tr[i] / tr[i - 1]
        cash *= bg[i - 1]
        v = stock + cash
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
        if i % 12 == 0:
            r = rule(cape[i - 1])
            stock, cash = v * (1 - r), v * r
    return {"end": (stock + cash) * 100000, "worst": worst, "cagr": (stock + cash) ** (12 / (len(x) - 1)) - 1}


def main():
    m, d, a = load()
    w = d.loc[START:END]
    c = m.cape.dropna()
    res = {"window": period(START, END, d), "since_2000": period("2000-01", END, d), "decade_2000": period("2000-01", "2009-12", d),
           "from_low": period("2009-03", END, d)}
    res["underwater_months"] = underwater(w.tr)
    res["waits"] = waits(w)
    res["waits_long"] = waits(d)
    res["by_band"] = by_band(d)
    res["series"] = [{"t": str(t), "sp": v.tr / w.tr.iloc[0] * 100000, "bill": v.bill / w.bill.iloc[0] * 100000, "cpi": v.cpi / w.cpi.iloc[0] * 100000,
                      "rate": v.bill_pct} for t, v in w.iterrows()]
    gauge = m.loc["2000-01":END]
    res["gauge"] = [{"t": str(t), "cape": v.cape} for t, v in gauge.iterrows()]
    res["today"] = {"cape": float(c.iloc[-1]), "month": str(c.index[-1]), "rank_all": float((c < c.iloc[-1]).mean()),
                    "rank_window": float((w.cape < c.iloc[-1]).mean()), "median_all": float(c.median()), "first": str(c.index[0]),
                    "median_window": float(w.cape.median()), "min_window": float(w.cape.min()), "min_month": str(w.cape.idxmin()),
                    "max_window": float(w.cape.max()), "max_month": str(w.cape.idxmax()),
                    "last_below_20": str(c[c < 20].index[-1]), "last_below_30": str(c[c < 30].index[-1]), "last_below_25": str(c[c < 25].index[-1])}
    res["years"] = []
    for y in (2000, 2008, 2020, 2022):
        q = m.loc[str(y)]
        jan = f"{y}-01"
        end = pd.Period(jan) + 60
        last = min(end, pd.Period(END))
        n = (last - pd.Period(jan)).n / 12
        res["years"].append({"year": y, "jan": float(q.cape.iloc[0]), "high": float(q.cape.max()), "high_m": str(q.cape.idxmax()),
                             "low": float(q.cape.min()), "low_m": str(q.cape.idxmin()), "next_years": n, "next_end": str(last),
                             "next_sp": float(d.tr[last] / d.tr[jan] - 1), "next_bill": float(d.bill[last] / d.bill[jan] - 1)})
    res["band_time"] = {}
    for label, x in (("window", w), ("since_2000", d.loc["2000-01":END]), ("since_1928", d.loc["1928-01":END]), ("since_1881", m.loc["1881-01":END])):
        res["band_time"][label] = {"months": int(x.cape.notna().sum()),
                                   **{n: float(((x.cape >= lo) & (x.cape < hi)).sum() / x.cape.notna().sum()) for n, lo, hi, _ in BANDS}}
    res["low_2000_2003"] = {"cape": float(m.loc["2000-01":"2003-12"].cape.min()), "month": str(m.loc["2000-01":"2003-12"].cape.idxmin())}
    res["mixes"] = {}
    for label, s in (("window", START), ("since_2000", "2000-01")):
        res["mixes"][label] = {"fixed": {str(p): mix(s, END, d, lambda _c, r=p / 100: r) for p in FIXED}, "band": mix(s, END, d, line)}
    # second copy: Shiller and Treasury against Damodaran
    x = d.loc["2006-12":"2025-12"]
    y = a.loc[2007:2025]
    res["check"] = {"shiller_sp": float(x.tr.iloc[-1] / x.tr.iloc[0]), "damodaran_sp": float((1 + y.sp500_tr).prod()),
                    "treasury_bill": float(x.bill.iloc[-1] / x.bill.iloc[0]), "damodaran_bill": float((1 + y.tbill).prod()),
                    "worst_year": max(((yr, abs(d.tr[f"{yr}-12"] / d.tr[f"{yr-1}-12"] - 1 - a.sp500_tr[yr])) for yr in range(2007, 2026)), key=lambda t: t[1])[0],
                    "worst_year_gap": max(abs(d.tr[f"{yr}-12"] / d.tr[f"{yr-1}-12"] - 1 - a.sp500_tr[yr]) for yr in range(2007, 2026))}
    (CACHE / "results.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main()
    for k, v in r.items():
        if k in ("series", "gauge"):
            continue
        print(k, json.dumps(v, default=str)[:1500])
