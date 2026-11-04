---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Count from the links, not from a phrase

*Written 2026-11-03.*

## What happened

Claude made three count errors on `overlap.html`. No decision used them.

- The table said 38 of 39 catalyst notes link Corning. The search matched the words "A catalyst for [[Corning]]", and one note words it differently. The true count is every note. The page went to the owner with this wrong, and a check written later caught it.
- The table said carrier fiber was shared by 3 of 5, while its own row and the map showed four. Claude caught this before showing the page.
- A cell said all 38 graph links were built around Corning. Nine do not touch it. Claude caught this before showing the page.

## What it taught us

Count the thing itself, such as the link, not a sentence that usually comes with it. A summary column must be checked against its row.

## What changed

`overlap.html` now says 40 of 40, and `sensors/overlap/test_overlap.py` counts the links in `Catalysts/` directly. No rule changed.
