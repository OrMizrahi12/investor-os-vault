"""Overlap lesson, step 1: how the five paper names moved together. Pulls nothing.

    .venv/bin/python -I sensors/overlap/analyze.py

Reads the concentration lesson's saved returns and writes cache/results.json.
The prices are someone else's copy of Yahoo's data, so keep the page and cache on this computer.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(__file__).resolve().parent / "cache"
SRC = ROOT / "sensors/concentration/cache"
T = ["GLW", "APH", "AVGO", "NVDA", "VZ"]
AI = T[:4]
CIK = {"GLW": "24741", "APH": "820313", "AVGO": "1441634", "NVDA": "1045810", "VZ": "732712"}
SEED, DRAWS, BLOCK = 20261103, 2000, 21


def bets(frame):
    """Three ways to ask how many unrelated stocks these five act like, at equal weights."""
    x = frame[T]
    cov = x.cov().to_numpy()
    corr = x.corr().to_numpy()
    w = np.full(5, 0.2)
    port = w @ cov @ w
    vol = np.sqrt(np.diag(cov))
    e = np.linalg.eigvalsh(corr)[::-1]
    return dict(
        same_swing=float(np.diag(cov).mean() / port),      # average stock's variance / portfolio variance
        ratio=float((w @ vol) ** 2 / port),                # diversification ratio squared
        eigen=float(e.sum() ** 2 / (e ** 2).sum()),        # eigenvalue participation
        first=float(e[0] / e.sum()),
    )


def risk_share(frame):
    cov = frame[T].cov().to_numpy()
    w = np.full(5, 0.2)
    c = w * (cov @ w)
    c = c / c.sum()
    return {t: float(v) for t, v in zip(T, c)}


def pairs(frame, names):
    c = frame[names].corr().to_numpy()
    return float(c[np.triu_indices(len(names), 1)].mean())


def compound(r, rule):
    return (1 + r).resample(rule).prod() - 1


def mat(frame):
    return [[round(float(v), 4) for v in row] for row in frame[T].corr().to_numpy()]


def residuals(frame, m):
    m = m.reindex(frame.index)
    out = pd.DataFrame(index=frame.index)
    betas = {}
    for t in T:
        b = np.cov(frame[t], m)[0, 1] / m.var()
        out[t] = frame[t] - b * m
        betas[t] = float(b)
    return out, betas


def block_ci(frame, key):
    rng = np.random.default_rng(SEED)
    n = len(frame)
    vals = []
    arr = frame[T].to_numpy()
    for _ in range(DRAWS):
        starts = rng.integers(0, n - BLOCK + 1, n // BLOCK + 1)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        vals.append(bets(pd.DataFrame(arr[idx], columns=T))[key])
    return [float(np.percentile(vals, 5)), float(np.percentile(vals, 95))]


def falls(basket, r, top=4):
    """Largest peak-to-trough falls that do not overlap, with what each stock did over the same dates."""
    level = (1 + basket).cumprod()
    level = pd.concat([pd.Series([1.0], index=[basket.index[0] - pd.Timedelta(days=1)]), level])
    used, out = [], []
    dd = level / level.cummax() - 1
    for _ in range(40):
        free = dd.copy()
        for a, b in used:
            free[a:b] = 0
        trough = free.idxmin()
        if free[trough] >= 0 or len(out) >= top:
            break
        peak = level[:trough].idxmax()
        rec = level[trough:][level[trough:] >= level[peak]]
        end = rec.index[0] if len(rec) else level.index[-1]
        used.append((peak, end))
        sub = r.loc[(r.index > peak) & (r.index <= trough)]
        out.append(dict(peak=str(peak.date()), trough=str(trough.date()), fall=float(level[trough] / level[peak] - 1),
                        names={t: float((1 + sub[t]).prod() - 1) for t in T}))
    return sorted(out, key=lambda d: d["fall"])


def main():
    all_r = pd.read_parquet(SRC / "returns.parquet")
    all_r.index = pd.to_datetime(all_r.index)
    r = all_r[T]
    m = all_r.drop(columns=T).mean(axis=1)
    basket = r[AI].mean(axis=1)
    res, _ = residuals(r, m)
    yr1, yr3 = r["2025-11-03":], r["2023-11-03":]
    monthly, quarterly = compound(r, "ME"), compound(r, "QE")
    out = dict(start=str(r.index[0].date()), end=str(r.index[-1].date()), days=len(r), others=all_r.shape[1] - 5)
    out["corr"] = dict(daily=mat(r), last3=mat(yr3), last1=mat(yr1), monthly=mat(monthly), quarterly=mat(quarterly), residual=mat(res))
    out["counts"] = dict(last1=len(yr1), last3=len(yr3), monthly=len(monthly), quarterly=len(quarterly))
    out["bets"] = {k: bets(v) for k, v in dict(daily=r, last3=yr3, last1=yr1, monthly=monthly, quarterly=quarterly, residual=res).items()}
    out["ci"] = {k: {j: block_ci(v, j) for j in ("same_swing", "ratio", "eigen")} for k, v in dict(daily=r, last1=yr1).items()}
    out["risk"] = {k: risk_share(v) for k, v in dict(daily=r, last1=yr1, monthly=monthly, residual=res).items()}
    out["beta"] = residuals(r, m)[1]
    out["beta_last1"] = residuals(yr1, m)[1]
    out["vol"] = {t: float(r[t].std() * 252 ** 0.5) for t in T}
    out["pairs"] = {k: dict(four=pairs(v, AI), vz=float(v[AI].corrwith(v["VZ"]).mean())) for k, v in dict(daily=r, last1=yr1, residual=res, monthly=monthly).items()}
    years = []
    for y, g in r.groupby(r.index.year):
        if len(g) > 200:
            years.append(dict(year=int(y), days=len(g), four=pairs(g, AI), vz=float(g[AI].corrwith(g["VZ"]).mean()),
                              glw_nvda=float(g["GLW"].corr(g["NVDA"]))))
    out["years"] = years
    out["falls"] = falls(basket, r)
    worst = basket.nsmallest(25).index
    out["worst25"] = dict(four=float(basket[worst].mean()), vz=float(r.loc[worst, "VZ"].mean()), vz_up=int((r.loc[worst, "VZ"] > 0).sum()), all4_down=int((r.loc[worst, AI] < 0).all(axis=1).sum()))
    quiet = basket[(basket <= -0.05) & (m.abs() <= 0.01)]
    out["quiet_days"] = [dict(date=str(d.date()), four=float(v), market=float(m[d]), vz=float(r.loc[d, "VZ"]), names={t: float(r.loc[d, t]) for t in AI}) for d, v in quiet.items()]
    out["quiet_by_cut"] = {}
    for cut in (0.03, 0.04, 0.05):
        q = basket[(basket <= -cut) & (m.abs() <= 0.01)]
        out["quiet_by_cut"][str(cut)] = dict(all=len(q), before_2024=int((q.index < "2024-01-01").sum()), first=str(q.index[0].date()))
    out["multiple"] = {t: float((1 + r[t]).prod()) for t in T}
    chk = pd.read_parquet(SRC / "check_returns.parquet")
    chk.index = pd.to_datetime(chk.index)
    cc = chk[[CIK[t] for t in T]].dropna()
    cc.columns = T
    a, b = r.reindex(cc.index), cc
    out["check"] = dict(last=str(cc.index[-1].date()), days=len(cc), ratio={t: float((1 + b[t]).prod() / (1 + a[t]).prod()) for t in T},
                        corr_gap=float(np.abs(a.corr().to_numpy() - b.corr().to_numpy()).max()), big_days={t: int(((a[t] - b[t]).abs() > 0.02).sum()) for t in T})
    CACHE.mkdir(exist_ok=True)
    (CACHE / "results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
