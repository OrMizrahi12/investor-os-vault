# Base value: the inputs

The base is what the business has already proven. Everything below is from the approved method (`Rules/when-to-buy.md`, worked on `base.html`).

## Inputs

| Input | How | Corning, Nov. 3, 2026 |
|---|---|---|
| Diluted shares | Today's, latest filing | 871M |
| Normal earnings, low | Ten-year average of normal net income, in dollars, over today's shares. Not the average of past EPS | $1,028M, so $1.18, not the note's $1.10 |
| Normal earnings, middle | Last audited year | $1,543M, FY2025 |
| Normal earnings, high | Last twelve months: FY + this year to date − last year to date, adjusted the same way | $2,051M |
| Cash | Free cash flow over the last twelve months, customer deposits out. Three readings when the filing does not split the line | $971M, $1,256M, $1,505M |
| Cash growth | Low 0%. Middle the record of normal net income. High the best record. Both capped at 3% | 0%, 1.72%, 3% |
| Aaa | Moody's Aaa, latest month, from the owner's FRED download | 6.12%, Oct. 2026 |

Sums, in `scripts/value.py`: earnings ÷ shares ÷ 9%; cash ÷ shares × (1 + g) ÷ (9% − g); earnings ÷ shares ÷ Aaa. Votes 40, 40, 20 at each of low, middle and high.

## Normal earnings

Normal earnings start from reported net income and take out items the owner has confirmed, listed in the note's "Normal earnings" section and `normal.html`. For Corning: foreign debt translation, unrealized hedge results, and investment, business and asset sales. The owner confirms each kind of item, company by company. For a new company, mark your adjustments `unconfirmed` and show reported beside them.

**Read every line of the reconciliation, for every period you add.** A kind of item can sit on a line that shows up in one period and not another. Corning's "investment, business and asset sales" is three lines in the release: investments, sale of business, sale of assets. List the lines you used for each period, so a missing one shows. Do the same when finding one quarter's normal earnings for a what-if.

## Traps from Lessons

- **EDGAR's `fy` is the filing year.** Pick a period by its dates. Tags change and old numbers get restated. See `Lessons/EDGAR fy is the filing year.md`.
- **A split can sit between two filings.** Twelve-month EPS adds pieces that may count shares differently. Use dollars of net income over today's diluted shares, and tie EPS to it. See `Lessons/A split can sit between two filings.md`.
- **Take out both sides of a deposit.** Show readings until a filing separates the line. See `Lessons/Take out both sides of a deposit.md`.
- **One good period says little.** Show the ten-year figure beside the latest. The middle being the best of ten years is worth saying.

## No vote, always shown

- **Past multiples:** the lowest and median year-end tags on normal earnings. Low uses the lowest tag on low earnings. Middle and high use the median.
- **Rival multiples:** the sum of the parts, per diluted share.
- **Growth the price needs:** ten years of growth, then 3%, at 9%, from the cash readings. Needs a price.

If one cannot be sourced, say "unknown". Do not drop the row. None of them changes the base.

## New company: the fit check

The rule says a new company needs its own check that the method fits. The owner approved these questions on Nov. 3, 2026. Report each, then say what it means. The owner decides whether the method fits.

1. **Ten years of record?** If it is shorter, the low is not a ten-year average.
2. **Is the ten-year record the same business?** A large purchase, spin-off or restructuring means the average describes a different company, and twelve-month figures may hold part of a deal and all of its debt.
3. **Was the growth earned or bought?** Add up what deals cost against free cash flow over the ten years. If deals took much of it, the record is not the growth the cash could fund, the cash sum treats money spent on deals as the owner's, and the 3% may need more deals. Say what the organic record is, or that it is unknown.
4. **Are recent margins normal?** Compare the last twelve months with the ten-year figure. The method takes a peak as proven in the high and the cash row.
5. **Are earnings and free cash flow meaningful?** Banks, insurers and REITs do not fit this cash sum. Repeated losses make normal earnings hard to define.
6. **Are normal earnings confirmed by the owner?** If not, everything built on them is a proposal.
7. **Do customer deposits or prepayments sit in cash?** Can they be taken out from what is filed? Corning's three cash readings came from its deposits line. A company with no such line has no rule for three readings, so that is the owner's decision. Show what each reading gives.
8. **Do debt or dilution matter beyond what the votes see?** The votes are per share and do not take off debt. Say if debt changed a lot in the twelve months.
9. **Are there scenarios?** Strategic value needs catalyst notes on this company. If there are none, it is not worked out.
10. **Is there a dated price?** Only Corning has a saved close.

A poor fit is a finding to report. Do not change the method, and do not recommend a buy.
