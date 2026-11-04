---
ticker: GLW
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Check the comparison words too

*Written 2026-11-03.*

## What happened

Claude caught this while building `parts.html`, before showing it. A caption said Optical's range of $31.3B "is more than" all the other parts together, $32.2B. Both figures came from the script and were right. The word "more" was wrong. A chart label was also clipped, and the first screenshot showed it. No decision used either.

## What it taught us

[[Compute the numbers in the words]] and [[Check counts and ranges in the words too]] check the figures. "More than", "below" and "highest" are claims as well, and a computed number can sit inside a false one. Test the comparison, not only the digits.

## What changed

The caption is fixed. `sensors/parts/test_parts.py` now tests that comparison. No rule changed.
