---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/Archives/edgar/data/24741/000002474126000124/glw-20251231.htm"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Name each column when reading a table

*Written 2026-11-03.*

## What happened

Claude caught this while building the financial health panel on the dashboard. The quarters table in [[Corning]] has two columns named "Core", one for net income and one for EPS. Claude's reader kept the second, so core net income read $0.91 for Q3 2026, not $795M. The tie to the filings showed all 8 quarters as differences before the page was opened. The note was right. No wrong number reached a page.

## What it taught us

A reader that goes by column name can lose a column without an error. Tying each number to its source catches that, and a chart alone might not have.

## What changed

`dashboard/health.py` keeps the first of two columns with one name, and its comment says why. The check runs each time the page loads, and `dashboard/test_dashboard.py` fails on any difference but the known one. No rule changed.
