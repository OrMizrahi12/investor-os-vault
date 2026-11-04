---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/files/divisions/corpfin/cffilingreview.htm"
---

# Read a sensor's code before saying what it skips

*Written 2026-11-03.*

## What happened

Claude caught this after I had approved the alert map. The proposal said no sensor lists SEC letters, and recommended adding UPLOAD to the radar's list. I approved that. `collect_filing_events` in `sensors/radar/radar.py` has no form filter, so every filing after the baseline is already an event. The radar's settings list only which forms name a catalyst, and Claude read that as the list of forms it sees. The radar's own first run showed no letter only because none fell inside its window.

Claude also dated those two letter alerts by the date on the letter. SEC releases letters no earlier than 20 business days after a review ends ([SEC filing review page, undated, retrieved Nov. 3, 2026](https://www.sec.gov/files/divisions/corpfin/cffilingreview.htm)), so neither could have reached us on that date.

## What it taught us

Before saying a sensor misses something, read the code that decides what it keeps. A settings list may do a different job from what its name suggests. And a filing's date is not always the day it became public.

## What changed

`Rules/alerts.md` and `alerts.html` now say the sensors surface 12 of the 27 Oranges, not 10, and that a letter explains a change and cannot warn of one. The total stays 27. No radar setting changed. Part of the Journal's earlier entry today gives the old figure, and the new entry corrects it.
