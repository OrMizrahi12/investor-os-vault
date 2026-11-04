---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-02"
sources:
  - "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
  - "https://www.sec.gov/Archives/edgar/data/24741/000002474117000011/q4201610k.htm"
  - "https://www.sec.gov/Archives/edgar/data/24741/000002474118000010/glw-20171231x10k.htm"
---

# EDGAR fy is the filing year

*Written 2026-11-02.*

## What happened

Claude caught these while building the EDGAR sensor, before the chart was drawn. No wrong number reached a page.

In [SEC company facts, retrieved Nov. 2, 2026][f], [[Corning]]'s FY2016 revenue row carries `fy: 2018`, because `fy` describes the filing that reported it. Revenue also sits under two tags, `SalesRevenueGoodsNet` then `Revenues`. And one period can hold two values: FY2016 operating cash flow is $2,521M in the [10-K, filed Feb. 6, 2017][a] and $2,537M in the [10-K, filed Feb. 15, 2018][b].

## What it taught us

Pick a period by its start and end dates, never by `fy`. Expect tags to change over time and old numbers to be restated.

## What changed

`sensors/edgar/draw.py` picks years by date, joins the revenue tags, stops if a year is missing, and lists any restated number on `edgar.html`. No rule changed.

[f]: https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json
[a]: https://www.sec.gov/Archives/edgar/data/24741/000002474117000011/q4201610k.htm
[b]: https://www.sec.gov/Archives/edgar/data/24741/000002474118000010/glw-20171231x10k.htm
