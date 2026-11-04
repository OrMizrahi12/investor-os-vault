---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/files/company_tickers.json"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Read a sensor's output, not only its tests

*Written 2026-11-03.*

## What happened

Claude caught these while building the catalyst radar, before handing it over. All tests passed each time. No company or decision used the wrong labels.

- **A link beside a fact was not its source.** The radar showed the first link in a note's When section as the source of the date. For [[$20 billion run rate by end of 2026]], that put a calendar site beside a Corning target. The link supports only the projected results date.
- **Wrong tickers.** A company can have several tickers on [SEC's ticker list, retrieved Nov. 2, 2026 or earlier](https://www.sec.gov/files/company_tickers.json), and the lookup kept the last one. 12 companies in the screen got the wrong one, such as `ORCL-PD` for Oracle. Claude saw it in a screenshot of the panel.
- **Thin Form 4 lines.** Director grants read "1 derivative rows, not counted here", which told the reader nothing.

## What it taught us

A test proves what you thought to check. Read a sample of the real output as its reader would, and ask whether each label says what it seems to.

## What changed

The column is now called "First link in When, which may not source this date". `sensors/radar/radar.py` keeps a company's first listed ticker, which is the order seen on the list, not a rule SEC states. It names each derivative row. `sensors/radar/test_radar.py` tests the ticker on the real list and the derivative wording. The first run's report and saved output were regenerated, and the 12 tickers corrected in place. No rule changed.
