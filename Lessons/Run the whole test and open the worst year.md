---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://www.sec.gov/Archives/edgar/data/24741/000156276221000023/glw-20201231x10k.htm"
  - "https://www.sec.gov/Archives/edgar/data/24741/000143774923003123/glw20221231_10k.htm"
---

# Run the whole test and open the worst year

*Written 2026-11-03.*

## What happened

Claude caught this while drawing `balance.html`. The strength tests in [[Corning]] were incomplete in three ways. They left out the skill's after-tax coverage rows, one of which passes at 4.7x against 4.3x (calc.). They showed one "Fail" for the enterprising test, which has one part that passes and one that fails. And the poorest-year figure of 3.3x (calc., [10-K, filed Feb. 13, 2023][k22]) includes a one-off $498M gain ([10-K, filed Feb. 12, 2021][k20]). Without the gain it was 1.5x (calc.). No overall conclusion changes, and no decision used these rows.

## What it taught us

A script's optional inputs are still part of the test, so read the reference table and not only the output. Show each part of a test on its own. Before quoting a worst year, open that year and see what is in it.

## What changed

[[Corning]]'s test table and notes are corrected. No rule changed. This adds to [[Test coverage on the record, not only trailing]].

[k22]: https://www.sec.gov/Archives/edgar/data/24741/000143774923003123/glw20221231_10k.htm
[k20]: https://www.sec.gov/Archives/edgar/data/24741/000156276221000023/glw-20201231x10k.htm
