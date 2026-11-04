---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Hold a reason to the method it defends

*Written 2026-11-03.*

## What happened

Claude caught two things while building `base.html`, before handover. The first draft said the 75% bar "needs no more growth than the record", and compared it with sales growth of 5.8%. The same page says sales growth does not count, because sales are not what owners receive. Against the other rates the claim holds only from $1.73, not from $1.44 (calc.). Also, the price chart's axis stopped at $140 and cut off the 2026 peak of $255.69 (calc.). The first screenshot showed it. No decision used either.

## What it taught us

[[Check the comparison words too]] tests whether a comparison is true. A true comparison can still break the page's own rule. Check each reason against the method it is arguing for. Set a chart's axis from the data, not from the value you expect.

## What changed

The reason on `base.html` now gives each rate and says which one it relies on. The axis is set from the data, and `sensors/base/test_base.py` tests the peak and the comparisons. No rule changed.
