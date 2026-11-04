---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://fred.stlouisfed.org/legal/"
  - "https://fred.stlouisfed.org/series/AAA"
  - "https://github.com/ranaroussi/yfinance"
  - "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. %%

# Check a source's terms before its sensor

*Written 2026-11-03.*

## What happened

The plan was to script FRED's CSV downloads and cache them, treating Yahoo as the only source with limits. Claude read the terms before any FRED data was fetched. Without written consent, they bar storing or caching FRED content and limit scripts and bots. They allow downloading a copy for personal use ([FRED terms, undated, retrieved Nov. 2, 2026][t]). Moody's also owns the Aaa series and bars redistribution ([FRED AAA page, updated Nov. 2, 2026][a]).

Claude read these through a tool that shows short quotes, so the end of the scripts clause was not read in full.

Then Claude repeated the mistake with Yahoo. It ran `sensors/prices/prices.py` on Nov. 2, 2026 after reading only the yfinance README, and listed Yahoo's own terms as an open item. When I asked, it read them. They bar collecting data "using any automated means" "for any purpose without our express, prior permission" ([Yahoo Terms of Service, updated Nov. 1, 2026][y]). The earlier script test for `sensors.html` falls under the same clause. "Personal use" is not an exception to it.

## What it taught us

"Free" and "no key" do not mean a script may collect the data or keep it. Read the terms first, and do not assume the public source has the looser ones.

## What changed

`sensors/macro/` makes no FRED requests. I download the files by hand and it reads them. `sensors/README.md` says so. It also records my decision of Nov. 3, 2026 to keep `sensors/prices/` once a day despite Yahoo's terms. No rule changed. A sensor's first run comes after reading the source's own terms, not a library's summary of them.

[t]: https://fred.stlouisfed.org/legal/
[a]: https://fred.stlouisfed.org/series/AAA
[y]: https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html
