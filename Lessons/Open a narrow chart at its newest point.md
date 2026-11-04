---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Open a narrow chart at its newest point

*Written 2026-11-03.*

## What happened

Claude caught this while checking `cash-reserve.html`, before showing it. In a narrow window, the time charts scrolled sideways and opened on their left end. The newest years and the end labels were out of sight. The pattern came from `sizing.html`'s styles. No number was wrong, and no decision used it.

## What it taught us

"No sideways page scroll" is not enough. A chart that scrolls inside its own box can still hide the point the reader came for. Look at what shows first.

## What changed

The three time charts on `cash-reserve.html` now open at their newest month. No rule changed. Other pages with time charts were not checked.
