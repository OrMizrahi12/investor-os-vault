---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://huggingface.co/datasets/defeatbeta/yahoo-finance-data"
  - "https://huggingface.co/datasets/finsaber-team/FINSABER-V2-Data"
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Compare a data copy to a second copy

*Written 2026-11-03.*

## What happened

Claude caught these while building `concentration.html`, before showing it. No decision used them.

The free [price copy, updated Nov. 3, 2026](https://huggingface.co/datasets/defeatbeta/yahoo-finance-data), matched our Corning file, so it looked sound. Comparing every stock with a [second copy, updated May 21, 2026](https://huggingface.co/datasets/finsaber-team/FINSABER-V2-Data), showed more:

- The BNY ticker carried a different fund's prices before Dec. 1, 2025, a rise of 993% in one day (calc.).
- Monster's prices flipped between about $47 and $95 on several days in 2026.
- Some dividends were adjusted for later splits and some were not. That overstated returns for stocks such as Lam Research.
- A SEC ID match returned a preferred share for old DuPont.

Claude also made its own mistakes. The first run took 2020's high instead of the worst fall, so the "crash" landed in December. The check marked every name as vanished because of a stray date. A `.capitalize()` call lowercased the source links, which only the screenshot showed. The results looked wrong or the page showed it, and all three were fixed.

## What it taught us

One stock matching does not clear a whole file. Compare every series with a second source and read the outliers, and look for one-day jumps before using a price file.

## What changed

`sensors/concentration/prepare.py` repairs or drops these series and logs them. Its asserts stop on a one-day rise over 100%. The page lists the repairs and the stocks that still differ. No rule changed.
