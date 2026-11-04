---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Count the book after the actions

*Written 2026-11-03.*

## What happened

Two mistakes while building the `portfolio-manager` skill. A test run caught the first, and I caught the second reading the results. No decision used either.

- `pm.py` counted positions, bets and group sums before the buys in the same run. On made-up A and B it said "0 positions, 0 bets" beside two buys, and a group that had just cut B to $100 read "Held 0.0%: inside the limit". The sizes were right. The lines around them were not.
- My first word checks failed the run without the skill on things it had done, such as "buy $7,100" written in a table. That made the skill look better than it was: 4 of 9 on the made-up ideas, which became 9 of 10 once fair.

## What it taught us

A line that describes the book must say which book: before the actions or after. A check that compares two answers must be read against the loser's answer too.

## What changed

`.claude/skills/portfolio-manager/scripts/pm.py` now counts after the actions and says so, with a check in `test_pm.py`. `evals/grade.py` was loosened, and `portfolio.html` says so.
