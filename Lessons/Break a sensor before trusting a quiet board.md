---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-04"
sources: []
---

# Break a sensor before trusting a quiet board

*Written 2026-11-04.*

## What happened

Claude caught this on a labelled test copy, before any real failure. No wrong result reached the owner.

The 8-K watcher was broken in the copy, and the real `sensors/daily/collect.py` ran there. If the run then died before its brief, Home said "Nothing waiting", and no screen named the failure, although the digest in `sensors/daily/runs/` said it plainly. Once a brief existed, Home and Ideas and alerts showed the O16 line, and the Company page's Latest 8-Ks, Portfolio and cash and Journal still said nothing (calc., read from each screen, Nov. 4, 2026).

The tests had only ever tried busy days, so they never saw a screen that looks calm because a sensor stopped.

## What it taught us

A quiet board and a broken board can look the same. So break a sensor and read every screen, not only the screen meant to show it.

## What changed

- Every screen shows what the newest digest says about a failed sensor or a missing brief (`dashboard/view.py`, `dashboard/app.py`). Tests in `dashboard/test_dashboard.py`, class `AFailedSensor`.
- `dashboard/tools/broken_copy.py` runs the break again, whenever wanted.

## What it does not say

That every failure now shows. A run that never starts writes no digest, so the board says nothing until the 4-day limit on the Daily run's record passes. A sensor that exits cleanly with wrong data shows nothing at all.
