"""Concentration lesson, step 2: draw random portfolios from cache/returns.parquet and save results.json.

    .venv/bin/python -I sensors/concentration/simulate.py

No network. Fixed seed, so a rerun gives the same numbers. Lesson only: no stock here is a pick.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent / "cache"
SEED = 20261103
DRAWS = 10_000
GRID = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100]
MAIN = [1, 5, 10, 20, 30]
Q = [5, 25, 50, 75, 95]


def year_starts(dates):
    """Index of the first day of each holding year, counted from the start date."""
    first = pd.Timestamp(dates[0])
    idx = pd.to_datetime(dates)
    starts, year = [0], 1
    while True:
        when = idx.searchsorted(first.replace(year=first.year + year))
        if when >= len(idx):
            return starts
        starts.append(int(when))
        year += 1


def paths(ret, members, starts):
    """Value of each portfolio each day, equal weight, back to equal at each start in `starts`. Rows are portfolios.
    A missing return means the company is gone: it earns nothing to the next start, then the rest share it."""
    t = ret.shape[0]
    out = np.empty((members.shape[0], t))
    level = np.ones(members.shape[0])
    for a, b in zip(starts, starts[1:] + [t]):
        block = ret[a:b][:, members]  # days, portfolios, holdings
        alive = ~np.isnan(block[0])
        growth = np.cumprod(1 + np.nan_to_num(block), axis=0)
        kept = alive.sum(axis=1)
        share = np.where(kept > 0, 1 / np.maximum(kept, 1), 0)[:, None]
        value = (growth * alive * share).sum(axis=2)
        value = np.where(kept > 0, value, 1)
        out[:, a:b] = (level * value).T
        level = out[:, b - 1]
    return out


def stats(value, years, peak=None):
    start = np.ones((value.shape[0], 1))
    daily = np.diff(np.hstack([start, value]), axis=1) / np.hstack([start, value[:, :-1]])
    high = np.maximum.accumulate(np.hstack([start, value]), axis=1)[:, 1:]
    result = {
        "vol": daily.std(axis=1, ddof=1) * np.sqrt(252) * 100,
        "cagr": (value[:, -1] ** (1 / years) - 1) * 100,
        "mult": value[:, -1],
        "dd": (value / high - 1).min(axis=1) * 100,
    }
    return result


def draw(rng, size, count, pool):
    if size == 1 and len(pool) <= count:
        return pool[:, None]
    return np.stack([rng.choice(pool, size, replace=False) for _ in range(count)])


def run(ret, members, starts, years, marks=None, chunk=1000):
    keys = None
    gathered = {}
    for i in range(0, len(members), chunk):
        v = paths(ret, members[i : i + chunk], starts)
        s = stats(v, years)
        for name, (a, b) in (marks or {}).items():
            s[name] = (v[:, b] / (v[:, a] if a >= 0 else 1) - 1) * 100
        for k, x in s.items():
            gathered.setdefault(k, []).append(x)
    return {k: np.concatenate(x) for k, x in gathered.items()}


def summary(s, basket=None):
    out = {}
    for k, x in s.items():
        out[k] = {f"p{q}": float(np.percentile(x, q)) for q in Q} | {"min": float(x.min()), "max": float(x.max()), "mean": float(x.mean())}
    out["lost_money"] = float((s["mult"] < 1).mean() * 100)
    out["lost_half"] = float((s["mult"] < 0.5).mean() * 100)
    if basket is not None:
        out["beat_basket"] = float((s["mult"] > basket).mean() * 100)
    return out


def main():
    rng = np.random.default_rng(SEED)
    frame = pd.read_parquet(CACHE / "returns.parquet")
    uni = pd.read_csv(CACHE / "universe.csv", keep_default_na=False).set_index("symbol").loc[frame.columns]
    r = frame.values
    dates = list(frame.index)
    n = r.shape[1]
    t0 = pd.Timestamp("2016-11-03")
    years = (pd.Timestamp(dates[-1]) - t0).days / 365.25
    starts = year_starts(dates)
    allp = np.arange(n)

    every = run(r, allp[None, :], starts, years)
    level = paths(r, allp[None, :], starts)[0]
    day = pd.to_datetime(dates)

    def crash(a, b):
        """The worst peak-to-trough fall of the all-stock basket inside these dates."""
        mask = np.where((day >= a) & (day <= b))[0]
        path = level[mask]
        low = int((path / np.maximum.accumulate(path) - 1).argmin())
        top = int(path[: low + 1].argmax())
        return int(mask[top]), int(mask[low])

    c20, c22 = crash("2020-01-01", "2020-12-31"), crash("2022-01-01", "2022-12-31")
    marks = {"crash20": c20, "bear22": c22}
    basket_mult = float(every["mult"][0])
    results = {"sizes": {}, "n_stocks": n, "draws": DRAWS, "seed": SEED, "years": years, "days": len(dates), "rebalances": len(starts)}
    for size in GRID:
        m = draw(rng, size, DRAWS, allp)
        s = run(r, m, starts, years, marks)
        one = summary(s, basket_mult)
        one["portfolios"] = len(m)
        one["sd_cagr"] = float(s["cagr"].std())
        results["sizes"][str(size)] = one
        print(size, round(one["vol"]["p50"], 2), [round(one["cagr"][f"p{q}"], 1) for q in (5, 50, 95)], flush=True)
    full = run(r, allp[None, :], starts, years, marks)
    results["all"] = {k: float(v[0]) for k, v in full.items()}
    results["crash20_dates"] = [dates[c20[0]], dates[c20[1]]]
    results["bear22_dates"] = [dates[c22[0]], dates[c22[1]]]

    # Same result from the textbook sum: swing squared = average swing squared / n + (1 - 1/n) x average shared part.
    cov = np.cov(r, rowvar=False, ddof=1) * 252 * 1e4
    avg_var = float(np.trace(cov) / n)
    avg_cov = float((cov.sum() - np.trace(cov)) / (n * (n - 1)))
    corr = np.corrcoef(r, rowvar=False)
    results["formula"] = {"avg_var": avg_var, "avg_cov": avg_cov, "avg_corr": float(corr[np.triu_indices(n, 1)].mean()), "floor": float(np.sqrt(avg_cov))}

    def corr_between(a, b):
        c = np.corrcoef(r[a : b + 1], rowvar=False)
        return float(c[np.triu_indices(n, 1)].mean())

    results["corr_crash20"] = corr_between(*c20)
    calm = np.ones(len(r), bool)
    calm[c20[0] : c20[1] + 1] = False
    results["corr_outside_crash20"] = float(np.corrcoef(r[calm], rowvar=False)[np.triu_indices(n, 1)].mean())

    # Single stocks, each held the whole time.
    each = np.prod(1 + r, axis=0)
    gain = np.sort(each - 1)[::-1]
    top = max(1, round(n * 0.1))
    winners = set(np.argsort(each)[::-1][:top].tolist())
    results["stocks"] = {
        "median_mult": float(np.median(each)), "mean_mult": float(each.mean()), "min_mult": float(each.min()), "max_mult": float(each.max()),
        "lost_money": int((each < 1).sum()), "lost_half": int((each < 0.5).sum()), "beat_basket": int((each > basket_mult).sum()),
        "top_count": top, "top_share_of_gain": float(gain[:top].sum() / gain.sum() * 100), "top_cutoff_mult": float(np.sort(each)[::-1][top - 1]),
    }
    results["hold_a_winner"] = {}
    win = np.array(sorted(winners))
    for size in MAIN:
        m = draw(rng, size, DRAWS, allp)
        results["hold_a_winner"][str(size)] = float(np.isin(m, win).any(axis=1).mean() * 100)

    # Spreading inside one sector.
    results["sector"] = {}
    position = pd.Series(range(n), index=frame.columns)
    for name, group in uni.groupby("sector"):
        pool = position[group.index].values
        if len(pool) < 20:
            continue
        s = run(r, draw(rng, 10, 5000, pool), starts, years, marks)
        results["sector"][name] = {"count": len(pool), "10": summary(s, basket_mult)}

    # How much the holding rule matters.
    results["other_rules"] = {}
    for size in MAIN:
        m = draw(rng, size, DRAWS, allp)
        hold = run(r, m, [0], years)
        results["other_rules"].setdefault("never", {})[str(size)] = summary(hold, basket_mult)
        rows = {"vol": [], "cagr": []}
        for i in range(0, len(m), 500):
            d = r[:, m[i : i + 500]].mean(axis=2).T
            rows["vol"].append(d.std(axis=1, ddof=1) * np.sqrt(252) * 100)
            rows["cagr"].append((np.prod(1 + d, axis=1) ** (1 / years) - 1) * 100)
        results["other_rules"].setdefault("daily", {})[str(size)] = {k: {f"p{q}": float(np.percentile(np.concatenate(v), q)) for q in Q} for k, v in rows.items()}

    # Survivorship check on the second copy, through Dec. 31, 2025.
    chk = pd.read_parquet(CACHE / "check_returns.parquet")
    chk = chk[chk.notna().mean(axis=1) > 0.5]  # a stray date holding only a few names is not a trading day
    cik_alive = set(uni.cik.astype(str))
    c = chk.values
    in_set = np.array([col in cik_alive for col in chk.columns])
    cyears = (pd.Timestamp(chk.index[-1]) - t0).days / 365.25
    cstarts = year_starts(list(chk.index))
    gone = np.isnan(c[-1])
    results["check"] = {"names_all": int(c.shape[1]), "names_set": int(in_set.sum()), "names_gone_early": int(gone.sum()), "end": chk.index[-1], "sizes": {}}
    for size in MAIN:
        row = {}
        for label, pool in (("kept", np.where(in_set)[0]), ("all", np.arange(c.shape[1]))):
            row[label] = summary(run(c, draw(rng, size, 5000, pool), cstarts, cyears))
        results["check"]["sizes"][str(size)] = row

    (CACHE / "results.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
