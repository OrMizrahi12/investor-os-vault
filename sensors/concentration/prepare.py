"""Concentration lesson, step 1: turn downloaded files into a clean table of daily total returns.

    .venv/bin/python -I sensors/concentration/prepare.py <folder with price files> <wiki file> <folder with check files>

Makes no network requests. It writes cache/returns.parquet, cache/universe.csv, cache/check_returns.parquet,
and cache/prepare_log.json. See sensors/README.md for why the data is a copy of Yahoo and not a yfinance pull.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
START, END = "2016-11-03", "2026-11-02"
DROP = {
    "CTA-PB": "only a preferred share is left under this company's SEC ID, not the common stock",
    "MNST": "prices flip between about $47 and $95 on several days in Jul.-Aug. 2026",
}
STITCH = {"BNY": ("BK", "2025-12-01")}  # the bank's ticker changed; the BNY history before that date is a different fund.


def read_list(path):
    tbl = Path(path).read_text().split("==S&P 500 Component Stocks==")[1].split("|}")[0]
    rows = []
    for raw in tbl.split("|-")[1:]:
        cells = [c.strip() for c in raw.strip().lstrip("|").split("||")]
        if len(cells) < 7:
            continue
        ticker = re.search(r"\{\{\s*\w*Symbol\|([^}|]+)", cells[0], re.I) or re.search(r"\|([A-Z.\-]+)", cells[0])
        link = re.search(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", cells[1])
        ciks = re.findall(r"\b(\d{7,10})\b", cells[-1])
        rows.append(dict(ticker=ticker.group(1).strip(), name=link.group(1) if link else cells[1], sector=cells[3].strip(), cik=int(ciks[-1])))
    return pd.DataFrame(rows)


def map_universe(listed, raw):
    catalog = pd.DataFrame(json.load(open(raw / "company_tickers.json")).values())
    prices = pd.read_parquet(raw / "stock_prices.parquet", columns=["symbol", "report_date"])
    span = prices.groupby("symbol").report_date.agg(["min", "max"])
    full = lambda s: s in span.index and span.loc[s, "min"] <= START and span.loc[s, "max"] >= END
    by_cik = catalog.groupby("cik_str").ticker.apply(list).to_dict()
    mapped = []
    for _, r in listed.iterrows():
        whole = [t for t in by_cik.get(r.cik, []) if full(t)]
        dashed = r.ticker.replace(".", "-")
        if r.ticker in whole or dashed in whole:
            mapped.append(r.ticker if r.ticker in whole else dashed)
        elif whole:
            mapped.append(whole[0])
        else:  # a new holding company gets a new SEC ID; the ticker match was read by eye against the name.
            mapped.append(next((t for t in (r.ticker, dashed) if full(t)), None))
    out = listed.assign(symbol=mapped)
    return out


def load_close(path, symbols):
    px = pd.read_parquet(path, columns=["symbol", "report_date", "close"], filters=[("symbol", "in", symbols), ("report_date", ">=", "2016-10-01")])
    px["close"] = px.close.astype(float)
    return px.pivot(index="report_date", columns="symbol", values="close").sort_index()


def fix_dividends(close, raw, symbols):
    """Some dividends in the copy are split-adjusted and some are not. For a stock with a split of 1.5x or more,
    pick whichever reading of each earlier dividend has a yield nearest the yield after the split."""
    div = pd.read_parquet(raw / "stock_dividend_events.parquet", filters=[("symbol", "in", symbols), ("report_date", ">=", "2016-10-01")])
    div["amount"] = div.amount.astype(float)
    splits = pd.read_parquet(raw / "stock_split_events.parquet", filters=[("symbol", "in", symbols), ("report_date", ">=", "2016-10-01")])
    a, b = zip(*(s.split(":") for s in splits.split_factor))
    splits["factor"] = np.array(a, float) / np.array(b, float)
    changed = 0
    for sym, s in splits[(splits.factor >= 1.5) | (splits.factor <= 1 / 1.5)].groupby("symbol"):
        rows = div[div.symbol == sym].sort_values("report_date")
        if rows.empty:
            continue
        prior = close[sym].ffill().reindex(rows.report_date).values
        last = s.report_date.max()
        after = rows.report_date.values >= last
        yields = rows.amount.values / prior
        anchor = np.nanmedian(yields[after]) if after.any() else np.nanmedian(yields)
        for i, day in zip(rows.index, rows.report_date):
            later = s[s.report_date > day].factor.prod()
            if later == 1 or not anchor > 0:
                continue
            as_is, split_down = div.loc[i, "amount"], div.loc[i, "amount"] / later
            base = close[sym].ffill().get(day, np.nan)
            if abs(np.log(split_down / base / anchor)) < abs(np.log(as_is / base / anchor)):
                div.loc[i, "amount"] = split_down
                changed += 1
    return div, changed


def main():
    raw, wiki, check = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    listed = read_list(wiki)
    uni = map_universe(listed, raw)
    count_rows = len(uni)
    no_history = uni[uni.symbol.isna()].drop_duplicates("cik")
    dropped = uni[uni.symbol.isin(DROP)]
    use = uni[uni.symbol.notna() & ~uni.symbol.isin(DROP)].drop_duplicates("cik").copy()
    symbols = sorted(set(use.symbol) | {src for src, _ in STITCH.values()})
    close = load_close(raw / "stock_prices.parquet", symbols)
    for new, (old, when) in STITCH.items():
        close.loc[close.index < when, new] = close.loc[close.index < when, old]
    div, changed = fix_dividends(close, raw, symbols)
    for new, (old, when) in STITCH.items():
        div = div[~((div.symbol == new) & (div.report_date < when))]
        div.loc[(div.symbol == old) & (div.report_date < when), "symbol"] = new
    close = close[list(use.symbol)]
    paid = div.groupby(["report_date", "symbol"]).amount.sum().unstack().reindex(index=close.index, columns=close.columns).fillna(0.0)
    held = close.ffill()
    returns = ((held + paid) / held.shift(1) - 1).loc[START:].iloc[1:]
    assert returns.notna().all().all() and returns.index[-1] == END
    assert (returns < 1.0).all().all(), "a one-day rise over 100% means a stitching fault"
    returns.to_parquet(CACHE / "returns.parquet")
    use[["ticker", "symbol", "name", "sector", "cik"]].sort_values("name", key=lambda s: s.str.lower()).to_csv(CACHE / "universe.csv", index=False)

    # Check data: another public copy that keeps vanished companies, through Dec. 31, 2025.
    frames = [pd.read_parquet(check / f"p{y}.parquet", columns=["date", "symbol", "adjusted_close"]) for y in range(2016, 2026)]
    alt = pd.concat(frames)
    alt["date"] = alt.date.astype(str).str[:10]
    alt = alt.pivot_table(index="date", columns="symbol", values="adjusted_close", aggfunc="last").sort_index().loc[START:]
    keep, kinds, faults = {}, {}, 0
    for _, r in uni.drop_duplicates("cik").iterrows():
        names = [c for c in (r.symbol, r.ticker, r.ticker.replace(".", "-")) if isinstance(c, str) and c in alt]
        whole = [c for c in names if pd.notna(alt[c].iloc[0]) and pd.notna(alt[c].get("2025-12-31"))]
        col = (whole or [c for c in names if pd.notna(alt[c].iloc[0])] or [None])[0]
        if col is None:
            continue
        ret = alt[col].dropna().pct_change().dropna()
        bad = ret[(ret > 1) | (ret < -0.8)]  # a reused ticker or a broken adjustment; treat the name as sold the day before
        if len(bad):
            faults += 1
            ret = ret.loc[: bad.index[0]].iloc[:-1]
        keep[r.cik] = ret
        kinds[r.cik] = r.symbol in set(use.symbol)
    check_returns = pd.DataFrame(keep).reindex(alt.index[1:])
    check_returns.columns = [str(c) for c in check_returns.columns]
    check_returns.to_parquet(CACHE / "check_returns.parquet")
    both = check_returns[[str(c) for c, k in kinds.items() if k]]
    mine = (1 + returns.loc[:"2025-12-31"]).prod()
    cik_to_symbol = dict(zip(use.cik.astype(str), use.symbol))
    theirs = (1 + both).prod()
    ratio = pd.Series({cik_to_symbol[c]: mine[cik_to_symbol[c]] / theirs[c] for c in both.columns if c in cik_to_symbol})
    log = {
        "rows_in_list": count_rows,
        "companies_in_list": int(uni.drop_duplicates("cik").shape[0]),
        "companies_used": len(use),
        "companies_no_full_history": no_history[["ticker", "name"]].values.tolist(),
        "companies_dropped_for_faults": [[r.ticker, r["name"], DROP[r.symbol]] for _, r in dropped.iterrows()],
        "dividends_resplit": changed,
        "days": len(returns),
        "first_close": START,
        "last_close": END,
        "check_companies_alive": int(sum(kinds.values())),
        "check_companies_vanished_or_short": int(len(kinds) - sum(kinds.values())),
        "check_series_cut_for_faults": faults,
        "check_ratio_quantiles": ratio.quantile([0.05, 0.5, 0.95]).round(4).to_dict(),
        "check_within_5pct": int(((ratio - 1).abs() <= 0.05).sum()),
        "check_compared": int(len(ratio)),
        "check_off_by_more": ratio[(ratio - 1).abs() > 0.05].round(3).sort_values().to_dict(),
    }
    (CACHE / "prepare_log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps({k: v for k, v in log.items() if k != "companies_no_full_history"}, indent=1))


main()
