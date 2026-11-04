---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company it affects. %%

# Check every filing that carries a line

*Written 2026-11-03.*

## What happened

Claude caught this while writing the K5 catalyst note, after telling me the opposite. The monitoring plan said the 8-K watcher misses K5, deposit-out cash, because the watcher follows only 8-Ks and K5 reads from a 10-Q. But the results release is an exhibit to an 8-K, and it carries the cash flow statement with the deposits line ([Q3 release, Oct. 27, 2026](https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm)). So the watcher does catch the filing that holds it. Claude had this release open while writing the plan. No decision used the wrong reading, and I set the lines before the fix.

## What it taught us

Before saying a sensor misses a number, list every filing that carries the number, not just the one you read it from.

## What changed

`monitor.html` and [[2026-11-03 Corning kill criteria]] now show the watcher catching K5, with the 10-Q as the check. The Journal entry that said "K5 gets only a listed 10-Q" stays as written, and a later entry corrects it. No rule changed.
