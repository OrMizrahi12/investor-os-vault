---
ticker: APH
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/Archives/edgar/data/820313/000110465926120646/aph-20260930x10q.htm"
  - "https://stockanalysis.com/stocks/aph/statistics/"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# A split can sit between two filings

*Written 2026-11-03.*

## What happened

Claude caught this while building `multiples.html`. The first run gave [[Amphenol]] trailing EPS of $3.97 and a P/E of 20.7x (calc.). An outside page showed 35.78x ([StockAnalysis, read Nov. 3, 2026](https://stockanalysis.com/stocks/aph/statistics/)). The 10-Q for Sept. 30, 2026 restates nine-month 2025 EPS from $2.41 to $1.21 after a two-for-one split ([10-Q, filed Oct. 30, 2026](https://www.sec.gov/Archives/edgar/data/820313/000110465926120646/aph-20260930x10q.htm)). FY2025 EPS of $3.34 comes from an earlier 10-K and stays on the old shares, so the sum mixed the two. Halved, it gives $2.30 and 35.8x (calc.). No wrong number reached a page or a decision.

## What it taught us

Trailing EPS adds pieces from two filings, and they may count shares differently. Tie EPS to net income over diluted shares, and read a large gap with an outside figure rather than picking one.

## What changed

`sensors/multiples/multiples.py` halves the old figure and stops if the result does not tie to net income over diluted shares. `sensors/multiples/test_multiples.py` tests this. The fact is in [[Amphenol]]. `sensors/macro/earnings.py` was not changed: it reads Corning only, and no split fell in its window. It would hit the same problem if Corning split.
