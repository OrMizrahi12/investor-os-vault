---
ticker: GLW
status: no buy
sector: Information Technology
last checked: "2026-11-03"
sources:
  - "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Round the sum, not the rounded parts

*Written 2026-11-03.*

## What happened

Claude caught this while building the dashboard's price against value panel. The valuation skill said [[Corning]]'s trim-above on the base high is $44.35. The sum is $30.0258 + $14.3298 = $44.3557, so $44.36 (calc., `sensors/strategic/model.py`, Nov. 3, 2026). `strategic.html` already showed $44.36. The Journal entry of the same day also says $44.35. No decision rested on the cent.

## What it taught us

A figure typed into words can differ from the page it cites by a cent. Take it from the script's output, as [[Compute the numbers in the words]] says.

## What changed

Fixed `.claude/skills/valuation/SKILL.md` and `references/strategic.md`. The Journal entry stays as written, and the entry for the panel session notes this. No rule changed.
