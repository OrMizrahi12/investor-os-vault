---
company:
ticker:
track: triage
written: 2026-11-03
---

# Hunt triage, Nov. 3, 2026

*Waiting for me to read. Not merged into company notes. Leads, never picks. A lesson on paper, not advice. Picture: `demo.html`. Log: [[Rejection log]]. Earlier triage and the gates: `Research/2026-11-03 Triage.md`.*

**5 went in, 5 were rejected, 0 went on the watchlist and 0 went to research (calc.).** Four fell at Gate 1 and Powell fell at Gate 2. So no thesis and no skeptic's review ran, because nothing reached them. No buy recommendation comes from this.

## How the five were chosen

The pick rule I set on Nov. 3, 2026: the largest rise on one line ÷ the latest full year's revenue, from SEC data, with no price used. Skip our map, the rejection log, the watchlist and unit-slip rows. Take the top five, and count any lead with no revenue figure. Lens: my request for US candidates.

| Step | Count (calc.) | Who |
|---|---|---|
| Leads on the [radar's run of Nov. 3, 2026](../sensors/radar/runs/2026-11-03-03.json), after what the radar hides | 117 rows, on two quarter steps | 29 and 88. A further 31 were hidden as possibly not new growth |
| Skipped rows: our map | 5 | Amazon, NVIDIA, Corning, T1 Energy, Microsoft |
| Skipped rows: rejection log | 11 | Oracle, Sandisk, Huntington Ingalls, SpaceX, Quanta, Lockheed Martin, Dell, GE Vernova, some twice |
| Skipped rows: watchlist | 1 | Micron |
| Unit-slip row | counted apart from the 117 | ePlus |
| Companies ranked | 96 | |
| No revenue figure | 3 | Cerebras, Goldman Sachs, Goldman Sachs Real Estate Finance Trust |
| Skipped as not US, in the top seven | 2 | IREN (Australia), AbCellera (British Columbia) |

**Claude's choices, for me to correct:** "US" means incorporated in the US, as on [SEC's filing lists, retrieved Nov. 3, 2026](https://data.sec.gov/submissions/CIK0001878848.json). Revenue was ranked from [SEC's CY2025 annual frames, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/frames/us-gaap/Revenues/USD/CY2025.json), taking the largest figure across three tags.

**A flaw found and handled:** a frame can hold a partial line. It gave Comfort Systems $1,831M against $9,102M in its own [company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001035983.json). A too-small figure only pushes a company up the ranking, so I checked the top ten against company facts. Comfort Systems then falls to about 0.10 (calc., $885.8M ÷ $9,101.6M), out of range. IREN's latest year is FY2026, $707.0M, which leaves it at 6.2 (calc.), still skipped as not US.

## Results

| Rank | Company | Rise ÷ revenue (calc.) | Lead | Gate 1 | Gate 2 | Gate 3 | Sorted | Look again |
|---|---|---|---|---|---|---|---|---|
| 1 | Axe Compute (AGPU) | 478.6 | Contract liabilities $0.8M to $60.8M, June 30, 2026, against revenue of $0.1M | **Fail.** Losses in all 8 years SEC has in FY2018 to FY2025, so 8 profitable years of 10 can no longer be reached. FY2025 lost $233.1M | Not run | Not run | Reject | After the 10-K, about Mar. 2027 (my estimate) |
| 2 | Backblaze (BLZE) | 2.19 | Remaining performance obligations $76.5M to $396.0M, against revenue of $145.8M | **Fail.** Losses in all 6 years on file, FY2020 to FY2025, so 8 of 10 can no longer be reached | Not run | Not run | Reject | After the 10-K, about Mar. 2027 (my estimate) |
| 3 | Kodiak Gas Services (KGS) | 0.77 | Remaining performance obligations $1,632.9M to $2,643.2M, against revenue of $1,308.1M | **Fail.** Debt $2,725.3M is 5.7× twelve-month operating cash of $478.9M, over the bar of 4×. On FY2025's $599.7M it is still 4.5×. Only five years on file, all profitable. Twelve-month free cash flow $5.0M | Not run | Not run | Reject | After the 10-K, about Feb. 2027 (my estimate) |
| 4 | Kopin (KOPN) | 0.71 | Remaining performance obligations $12.2M to $40.3M, against revenue of $39.3M | **Fail.** Profit in 1 of 10 years, FY2016 to FY2025 | Not run | Not run | Reject | After the 10-K, about Apr. 2027 (my estimate) |
| 5 | Powell Industries (POWL) | 0.54 | Remaining performance obligations $1.8B to $2.4B, against revenue of $1,104.3M | **Pass.** Profit in 8 of 10 years, no borrowings, twelve-month free cash flow $244.0M | **Fail.** Base middle $52.55 against $163.34, 32.2%. Even the high covers only 33.5%. Buy-below $70.06 | Not run | Reject | After the 10-K, about Nov. 2026 (my estimate) |

**Sources.** All sums calc. Powell's gate figures and the deposits line are below.

- Axe Compute: [SEC company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001446159.json); [10-K, filed Mar. 31, 2026](https://www.sec.gov/Archives/edgar/data/1446159/000117184326002094/poai20251231_10k.htm); [10-Q, filed Aug. 14, 2026](https://www.sec.gov/Archives/edgar/data/1446159/000117184326005556/agpu20260630_10q.htm).
- Backblaze: [SEC company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001462056.json); [10-K, filed Mar. 10, 2026](https://www.sec.gov/Archives/edgar/data/1462056/000162828026016395/blze-20251231.htm).
- Kodiak: [10-Q, filed Aug. 7, 2026](https://www.sec.gov/Archives/edgar/data/1767042/000176704226000055/kgs-20260630.htm); [SEC company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001767042.json). Operating cash: $599.74M + $170.65M − $291.50M. Capex: $315.47M + $318.58M − $160.17M.
- Kopin: [SEC company facts, retrieved Nov. 3, 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0000771266.json); [10-K, filed Apr. 13, 2026](https://www.sec.gov/Archives/edgar/data/771266/000149315226016338/form10-k.htm).
- Leads: the [radar's run of Nov. 3, 2026](../sensors/radar/runs/2026-11-03-03.json).

## Powell: the one that reached Gate 2

| | Figure | Source and date |
|---|---|---|
| Base value, low to high | $18.31 to $54.68 | calc., `value.py`, `sensors/demo/powell-2026-11-03.json`, a proposal on reported earnings |
| Base value, middle | $52.55 | calc., a proposal |
| Price | $163.34 | [StockAnalysis, close, 4:00 PM EST, Nov. 3, 2026](https://stockanalysis.com/stocks/powl/) |
| Coverage | 32.2%, range 11.2% to 33.5% | calc. |
| Buy-below | $70.06 | calc., $52.55 ÷ 0.75 |
| Strategic value, trim-above | not worked out | no catalyst notes. This does not mean zero |
| Past and rival multiples, no vote | unknown | not worked out at triage |
| Growth the price needs, no vote | 22.9% a year for ten years, then 3%, at 9% | calc. |

**Inputs.** Diluted shares 36.604M, after a three-for-one split on Apr. 2, 2026 ([10-Q, filed Aug. 4, 2026](https://www.sec.gov/Archives/edgar/data/80420/000008042026000107/powl-20260630.htm)). Reported earnings stand in for normal: $42.49M ten-year average, $180.75M in FY2025 ([10-K, filed Nov. 19, 2025](https://www.sec.gov/Archives/edgar/data/80420/000008042025000152/powl-20250930.htm)) and $190.86M over twelve months (calc., $180.75M + $139.44M − $129.33M). Cash $77.1M (calc.): free cash flow $243.96M less a rise in contract liabilities from $299.5M to $466.36M. Growth 0%, 3%, 3%, capped. Aaa 6.12% ([FRED AAA, Oct. 2026, downloaded Nov. 3, 2026](https://fred.stlouisfed.org/series/AAA)).

**The result does not depend on the deposits reading.** What-if, which the method bars: with deposits left in, the middle is $83.85 and coverage 51.3%, range 23.6% to 52.6% (calc.). Still under 75%.

**What the Gate 1 pass hides.** The two loss years were FY2017 and FY2018, so it clears the bar of 8 exactly. FY2025's $180.75M is the best of the ten years, 4.3× the average (calc.), so the middle already takes a high year as proven. Interest: SEC's facts give interest expense only to FY2021, at most $0.23M a year, and the 10-Q reports interest income, net, of $13.5M for nine months. Coverage in the years after was not read in print, and with no borrowings it would not change the result.

## What this does not say

- That a rejected stock will fall or should be sold. [[Paper portfolio]] holds none of them.
- That a Gate 1 fail means the business will fail. It means the record does not show the answer today.
- That the screen is empty. Only 5 of the 96 ranked companies were tested.

## What the two rules together found

My question for this pick rule was whether large companies were why leads fail Gate 2. **On this batch, ranking by size moved the failure up a gate.** Small companies led the ranking, and three of the five fell on years of losses. The one company with a clean enough record, Powell, still fell at Gate 2. Fifteen leads have now been triaged (calc., 9 + 1 + 5), and none reached research.

## Not done

- Normal earnings not worked out, so Powell's base is a proposal.
- The fit check did not run in full on any of the five.
- Ten-year figures come from SEC's XBRL facts, not read in print. I read Powell's and Kodiak's 10-Qs in print only for the lines cited.
- Why each lead rose was not read, except where a line above says so.
- One free page gave the one quote. The four Gate 1 fails needed no price, so none was taken.
- Look-again dates are my estimates, from last year's filing dates.
- None of the five has a note in `Companies/`, and none was created.
