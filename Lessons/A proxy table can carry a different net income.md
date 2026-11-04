---
ticker: PWR
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://data.sec.gov/api/xbrl/companyfacts/CIK0001050915.json"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# A proxy table can carry a different net income

*Written 2026-11-03.*

## What happened

Claude caught this before any value run or page used the figure. Pulling Quanta's record, Claude's script took the latest-filed value for each year's `NetIncomeLoss`. For FY2021 to FY2025 that was the proxy statement's, which is $1,041.9M for FY2025 ([SEC company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001050915.json)). The 10-K gives $1,028.4M attributable to common stock ([10-K, filed Feb. 19, 2026](https://www.sec.gov/Archives/edgar/data/1050915/000105091526000006/pwr-20251231.htm)). The proxy's figure matches `ProfitLoss`, which includes noncontrolling interests. The gap was seen only because the five values changed form from 10-K to DEF 14A in the list.

## What it taught us

Latest-filed is not best-filed. Under one tag, take annual figures from 10-Ks only, and read the form column.

## What changed

Quanta's inputs use the 10-K figures, and FY2025 was checked in print. No script in the vault changed, since the slip was in a throwaway script. No rule changed.
