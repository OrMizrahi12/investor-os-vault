---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources:
  - "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
  - "https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm"
---

# Test coverage on the record, not only trailing

*Written 2026-11-03.*

## What happened

I asked if [[Corning]]'s balance sheet was strong. Claude answered "yes, on debt and liquidity", citing trailing interest coverage of about 8 times. The number was right, but it came from a strong recent year. Over 2019 to 2025 coverage averaged 5.7x and was 3.3x in 2020 (calc., [SEC company facts, retrieved Nov. 2, 2026][f]). Claude had not looked at those years, and only checked when I asked it to rerun with the `value-investing` skill.

## What it taught us

One good period says little about how safe the debt is. Look at the average and the worst year, not only the latest. Check whether a relevant skill exists before answering.

## What changed

[[Corning]]'s Balance sheet section now gives the seven-year tests and changes its summary line. No rule changed.

[f]: https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json
