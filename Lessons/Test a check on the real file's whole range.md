---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://fred.stlouisfed.org/series/CPIAUCSL"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Test a check on the real file's whole range

*Written 2026-11-03.*

## What happened

Claude caught this before running the script on the real files. To catch a CPI file downloaded in percent-change units, `macro.py` refused any value below 100. The real file starts at 21.480 in Jan. 1947 ([FRED CPIAUCSL, downloaded Nov. 3, 2026](https://fred.stlouisfed.org/series/CPIAUCSL)), so the check would have rejected a good file. The tests passed because Claude's made-up files started in 2010. No wrong number reached a page.

## What it taught us

Made-up files prove what you assumed about the data. They do not prove the assumption.

## What changed

The floor in `sensors/macro/macro.py` is now 15, which still catches percent-change units in modern values. `sensors/macro/test_macro.py` has a test with CPI starting in 1947. No rule changed.
