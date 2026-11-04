---
ticker: GLW
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Count a history before describing it

*Written 2026-11-03.*

## What happened

Claude caught this while building `strategic.html`, before showing it. The first draft said the proposed trim-above of $36.06 would have said "consider trimming" for "most of a decade". The script's own count, printed at the first build, was 974 of 2,724 days since Jan. 2016, or 36% (calc., [Yahoo through yfinance, fetched Nov. 2, 2026](https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d)). The sentence had been written before the count. The true point is narrower: every close since May 29, 2024 has been above it. No decision used the draft.

## What it taught us

[[Check counts and ranges in the words too]] says to print each count. Write the sentence after the count, not before, and put a test on any word like "most".

## What changed

The sentence on `strategic.html` is fixed, and `sensors/strategic/test_strategic.py` tests the count and "over two years". No rule changed.
