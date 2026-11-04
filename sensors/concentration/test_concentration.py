"""Checks results.json and concentration.html without using simulate.py or draw.py for its sums. No network.

    .venv/bin/python -I sensors/concentration/test_concentration.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "cache/results.json").read_text())
returns = pd.read_parquet(HERE / "cache/returns.parquet")
uni = pd.read_csv(HERE / "cache/universe.csv", keep_default_na=False)
html = (HERE.parent.parent / "concentration.html")
fails = []


def check(name, got, want, tol):
    ok = abs(got - want) <= tol
    print(("ok  " if ok else "FAIL"), name, round(got, 4), "vs", round(want, 4))
    if not ok:
        fails.append(name)


# The set: at least 100 named companies, one row each, with a whole history.
assert returns.shape[1] == len(uni) >= 100 and uni.symbol.is_unique and uni.cik.is_unique and returns.notna().all().all()
assert returns.index[0] == "2016-11-04" and returns.index[-1] == "2026-11-02"

# Single stocks, one at a time, with plain Python.
mults = {c: float(np.prod(1 + returns[c].to_numpy())) for c in returns}
vals = sorted(mults.values())
check("median stock multiple", R["stocks"]["median_mult"], float(pd.Series(vals).median()), 1e-9)
check("stocks that lost money", R["stocks"]["lost_money"], sum(v < 1 for v in vals), 0)
check("stocks that lost half", R["stocks"]["lost_half"], sum(v < 0.5 for v in vals), 0)

# All-stock basket, yearly reset, by hand: each block runs from one Nov. 3 to the next.
value, dates = 1.0, pd.to_datetime(returns.index)
edges = [0] + [int(dates.searchsorted(pd.Timestamp(f"{y}-11-04"))) for y in range(2017, 2027)] + [len(dates)]
for lo, hi in zip(edges, edges[1:]):
    if hi > lo:
        value *= (1 + returns.iloc[lo:hi]).prod().mean()
check("basket multiple", R["all"]["mult"], value, 1e-6)

# Fresh draws with another seed and a plain loop, daily-reset rule: the textbook sum should match.
rng = np.random.default_rng(7)
arr = returns.to_numpy()
for k in (5, 10, 20):
    vols = []
    for _ in range(4000):
        pick = rng.choice(arr.shape[1], k, replace=False)
        vols.append(arr[:, pick].mean(axis=1).var(ddof=1) * 252 * 1e4)
    want = R["formula"]["avg_var"] / k + (1 - 1 / k) * R["formula"]["avg_cov"]
    check(f"textbook sum, {k} stocks (variance)", float(np.mean(vols)), want, want * 0.01)

# Fresh draws, yearly reset, plain loop over years.
cuts = [dates.searchsorted(pd.Timestamp(f"{y}-11-04")) for y in range(2017, 2027)]
blocks = np.split(arr, [c for c in cuts if c < len(arr)])
for k in (1, 5, 10, 20, 30):
    n = 3000 if k > 1 else arr.shape[1]
    vols, cagrs = [], []
    for i in range(n):
        pick = rng.choice(arr.shape[1], k, replace=False) if k > 1 else [i]
        level, path = 1.0, []
        for block in blocks:
            g = np.cumprod(1 + block[:, pick], axis=0).mean(axis=1)
            path.extend(level * g)
            level = path[-1]
        path = np.array([1.0] + path)
        vols.append(np.std(path[1:] / path[:-1] - 1, ddof=1) * np.sqrt(252) * 100)
        cagrs.append((path[-1] ** (365.25 / (dates[-1] - pd.Timestamp("2016-11-03")).days) - 1) * 100)
    s = R["sizes"][str(k)]
    check(f"{k}: median swing", float(np.median(vols)), s["vol"]["p50"], 0.2)
    check(f"{k}: low result", float(np.percentile(cagrs, 5)), s["cagr"]["p5"], 0.6)
    check(f"{k}: high result", float(np.percentile(cagrs, 95)), s["cagr"]["p95"], 0.8)

# Cross-check one stock against our own Corning file, whose adjusted close comes from a separate fetch.
glw_file = HERE.parent / "prices/cache/GLW/2026-11-02.csv"
g = pd.read_csv(glw_file).set_index("date").adj_close
check("Corning total return vs saved file", mults["GLW"], g["2026-10-30" if "2026-11-02" not in g.index else "2026-11-02"] / g["2016-11-03"], 0.02)

# Every tagged number in the page's words matches results.json.
if html.exists():
    page = html.read_text()
    spans = re.findall(r'<b data-k="([^"]+)"(?: data-x="([^"]+)")?>([^<]+)</b>', page)
    assert len(spans) > 30
    print("page values tagged", len(spans))
    for key, scale, shown in spans:
        node = R
        for part in key.split("."):
            node = node[part]
        got = abs(float(node)) * float(scale or 1)
        digits = float(re.sub(r"[^0-9.]", "", shown))
        places = len(shown.split(".")[1].rstrip("%×x")) if "." in shown else 0
        tol = 50 if scale else 0.5 * 10 ** -places + 1e-9
        if abs(digits - got) > tol:
            fails.append(key)
            print("FAIL page", key, shown, node)
    # Worked numbers in the words, recomputed here.
    med = {k: R["sizes"][str(k)]["vol"]["p50"] for k in (1, 5, 10, 15, 20, 25, 30)}
    room = med[1] - R["all"]["vol"]
    for k in (5, 10, 20, 30):
        want = f"{(med[1] - med[k]) / room * 100:.0f}%"
        if f'data-w="gone{k}">{want}<' not in page:
            fails.append(f"share gone at {k}")
            print("FAIL words", k, want)
    assert (med[10] - med[15]) / 5 > 0.1 > (med[15] - med[20]) / 5, "the 15-stock sentence"
    worst = abs(R["stocks"]["min_mult"] - 1)
    if f"{worst * 100:.0f}%" not in page:
        fails.append("worst stock")
    for name in ("Yahoo", "not advice", "no stock here is a pick"):
        assert name.lower() in page.lower(), name

print("FAILS:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
