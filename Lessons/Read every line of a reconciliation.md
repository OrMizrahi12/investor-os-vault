---
ticker: GLW
status: no buy
sector: Information Technology
base value: "$14.06 to $30.03, middle $21.73, buy below $28.97 (calc., Nov. 3, 2026)"
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Read every line of a reconciliation

*Written 2026-11-03.*

## What happened

Claude caught this while testing the `valuation` skill: one test run flagged it, and the main session checked it against the release. [[Corning]]'s twelve-month normal earnings of $2,029M take out investment, business and asset sale results at −1 and −12 for nine months of 2026. The same table also has a "Loss on investments" line of +$22M ([Q3 release, Oct. 27, 2026][r]). `normal.html` counts that kind of line. With it the twelve months are $2,051M, or $2.35 a share, and the base high is $30.03, not $29.83 (all calc.). The low, middle, 18% coverage, $28.97 buy-below and $36.06 trim-above do not change. No buy or trim decision used the high. It also sits in `sensors/base/test_base.py`, which pinned the same sum, so the test could not catch it.

## What it taught us

A kind of item can sit on a line that shows up in one period and not in another. List the lines used for each period, and do not pin a sum in a test from the same reading that made it.

## What changed

I approved the fix on Nov. 3, 2026. `sensors/base/model.py` and the two test files now carry $2,051M, `base.html` and `strategic.html` are redrawn, and [[Corning]] shows $14.06 to $30.03 and $2.35. The `valuation` skill's `references/base.md` says to read every line for every period, and its Corning inputs are updated. Journal entries and `valuation-test.html`'s test answers keep the old figure as dated records. No rule changed.

[r]: https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm
