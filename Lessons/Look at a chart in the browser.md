---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Look at a chart in the browser

*Written 2026-11-03.*

## What happened

Claude caught this before handing over `dashboard/`. The yield chart drew nothing. All the Python tests passed and the network check was clean. A column named `Moody's Aaa` has an apostrophe, and the chart library in the browser reads it as an unclosed quote. The only sign was an error in the browser's console. The screenshot showed the gap. No wrong number reached a page.

## What it taught us

A test that runs the page in Python does not prove the browser drew it. Open the page and look.

## What changed

The chart's columns in `dashboard/view.py` have plain names. `dashboard/test_dashboard.py` fails on any chart column name that is not plain letters. No rule changed.
