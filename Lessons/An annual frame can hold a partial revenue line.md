---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

# An annual frame can hold a partial revenue line

*Written 2026-11-03.*

## What happened

Claude caught this during the hunt, before any gate ran. [SEC's CY2025 frames, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/frames/us-gaap/Revenues/USD/CY2025.json), gave Comfort Systems revenue of $1,831M. Its own [company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001035983.json), give $9,102M for FY2025. A first reading of the ranking would have put it near the top on a wrong ratio.

## What it taught us

A market-wide frame is good for ranking, not for a figure. A too-small revenue only pushes a company up, so check the top of the ranking against company facts before using it.

## What changed

`sensors/demo/check.py` does that check, and `sensors/README.md` says to run it. The top ten were checked. The result is in `Research/2026-11-03 Hunt triage.md`.
