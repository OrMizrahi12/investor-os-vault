## Position sizing

**Status: approved by me, Nov. 3, 2026: the whole method, including the gates, the five tests, how the loss is worked out, the 5% limit, the caps, that a rise through the limit only alerts me, and the test for one thesis.** Changing the method needs my approval. The worked example is paper and recommends no trade. Page: `sizing.html`.

**The method: the thesis sets how big I want to go, the loss sets how big I can afford to go, and the smaller one wins.**

Size = the smaller of the grade's cap and 5% ÷ loss if wrong, rounded down to 0.1% of the portfolio.

Size only what has already cleared `when-to-buy`. This method never makes a buy case.

### Step 1: three gates

Any "no" means no position, and the size is $0.

1. A thesis is recorded in the company note.
2. I have ruled that it survived the skeptic's review.
3. The price is under the buy-below, so base value covers at least 75% of it.

### Step 2: grade the thesis

Score each test 0, 1 or 2 from the company note, and link the evidence. Claude proposes and I rule. **The price enters no test.**

| Test | Where in the note | 2 | 1 | 0 |
|---|---|---|---|---|
| **Mechanism** | Thesis, Latest results, Cash flow | Filings show every step, down to owner cash | Filings show the cause, but one step rests on a target | Filings do not show the cause |
| **Record** | Ten-year history, Normal earnings, Cash flow | Normal earnings and deposit-out cash both grew over ten years | One of them grew | Neither grew |
| **Customers** | What customers say | Three independent public sources, each on a different customer, confirm the claim the thesis rests on | The sources exist but leave that claim open | Fewer than three |
| **Kill lines** | Thesis, kill criteria | Every claim has a line with a threshold and a date, a filing can settle it, and none is crossed | Lines exist, but a claim has none or a line rests on someone's word | No lines, or one is crossed |
| **Unknowns** | Thesis, "we simply do not know" | No fact that would settle the case is missing | One is missing, and it would not change the decision | A fact that would change the decision is missing |

| Score | Grade | Cap | Why this cap |
|---|---|---|---|
| 8 to 10 | Strong | 20% | One position in 5, the bottom of rule 2 |
| 5 to 7 | Middling | 10% | One position in 10 |
| 3 to 4, or 5 and up with any 0 | Thin | 5% | One position in 20, the top of rule 2 |
| 0 to 2 | None | 0% | No position |

A grade changes only on a dated event, never on a price move. The caps are limits, not targets.

### Step 3: estimate the loss if wrong

- **Value if wrong = base low, less any downside scenario that still bites if the thesis is wrong.** Take such a downside at its full amount, not times its chance. Leave out every upside scenario and all strategic value.
- **Loss if wrong = (price − value if wrong) ÷ price.** Round up to the next 10 points before sizing, so the size comes straight off the grid.
- **Dollars lost = position × the unrounded loss.**
- It is a distance, not a forecast. It leaves out tax, and it does not cover a market fall. Past and rival multiples are shown beside it and get no vote.

### The hard limit

**If the thesis is wrong, no position may lose more than 5% of the portfolio.**

- It counts the whole position, including any add.
- **Positions that rest on one thesis share one limit, because they fail together.** Add position × unrounded loss across them. The sum may not pass 5%.
- **The test for one thesis.** For each position, name the single event that would most surely break its thesis. If that event would also cross a kill line or break a load-bearing claim in another position's note, those positions rest on one thesis for that event. A position can sit in more than one such group, and each group has its own limit.
- **Count the whole position.** No discount for the share of sales that is exposed.
- **Same direction only.** An event that helps one and hurts the other does not join them. A market fall does not join them either, since this limit does not cover one.
- **Claude proposes the groups, with the event and its evidence, and I rule.** A group changes only on a dated event, never on a price move. Prices moving together can raise the question. They cannot answer it.
- **Each refresh shows names against bets:** the number of positions and the number of groups. It is a display. Rule 2 still counts positions.
- At a buy, it is absolute: no buy over the limit, whatever the grade.
- After a buy, check it at each refresh on today's price, base value and portfolio. If it breaks, tell me and add nothing more. **It never forces a sale.** Selling stays with `when-to-trim` and a broken thesis (override 7).

**Why 5%: it is a judgment, not a measured result.** A 5% loss takes a 5.3% gain to repair (calc.: 1 ÷ 0.95 − 1). At a 100% loss the limit gives 5%, or one position in 20, so it fits inside rule 2. Ten positions all failing at the limit would still lose 50% (calc.), so this protects against a single failure, not against every position failing together.

### The cash

Pay only as `Rules/cash.md` allows (rule 4). What is not bought stays cash.

### The arithmetic, on a $100,000 paper portfolio

Corning's figures are from `sensors/valuation/runs/2026-11-03-01.md` (calc., Nov. 3, 2026), with the price the close of Nov. 2, 2026 ([Yahoo through yfinance, fetched Nov. 2, 2026](https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d)). **Both other ideas and all their numbers are made up.** All sums are calc.

| | Corning | Made-up A | Made-up B |
|---|---|---|---|
| Price | $123.20 | $50.00 | $40.00 |
| Base low / middle | $14.06 / $21.73 | $18.00 / $40.00 | $34.00 / $38.00 |
| Coverage, against the 75% bar | 17.6% | 80.0% | 95.0% |
| Downside that stays if wrong | none | $3.00 | $2.00 |
| Value if wrong | $14.06 | $15.00 | $32.00 |
| Loss if wrong | 88.6% | 70.0% | 20.0% |
| Gates | fail all three | pass | pass |
| Score and grade | 3, Thin, gated out | 9, Strong | 7, Middling |
| Grade's cap | 0% while gated | 20% | 10% |
| 5% ÷ loss | not reached | 5% ÷ 70% = 7.1% | 5% ÷ 20% = 25% |
| Size | **$0** | **$7,100** | **$10,000** |
| Lost if wrong | $0 | $4,970 | $2,000 |
| What set the size | the gates | the limit | the cap |

**Cash: $100,000 − $7,100 − $10,000 = $82,900.** If both positions are wrong, the loss is $6,970. If both go to zero, it is $17,100.

**Corning's score, Claude's reading for me to correct:**

- Mechanism 0: my ruling says the engine is not shown (Journal, Nov. 3, 2026).
- Record 1: normalized EPS rose from $1.16 to $1.77 from FY2016 to FY2025, and free cash flow stayed flat at $1,407M to $1,413M (calc., `normal.html` and `priced-in.html`, Nov. 3, 2026).
- Customers 1: seven public voices, and none gives a fiber price or says how firm the deals are ([[Corning]], gathered Nov. 3, 2026).
- Kill lines 1: nine lines, none crossed, but claims C6 and C8 have no line (`Research/2026-11-03 Corning kill criteria.md`, Nov. 3, 2026).
- Unknowns 0: how firm the deals are and what price they carry are not in the vault (`Research/2026-11-03 Corning thesis note.md`, Nov. 3, 2026).

**What the lesson shows:** the middling idea gets more dollars than the strong one, because it can lose so much less. The grid gives Corning $0 because of the gates, not because of the loss. With the gates ignored, the Thin cap would allow $5,000 and lose $4,429 (calc.). That is a sum, not a size.

### What I decided, Nov. 3, 2026

1. The limit is 5%. For comparison, at 3%, A gets $4,200 and cash is $85,800. At 8%, A gets $11,400 and cash is $78,600 (calc.). B stays at $10,000 in both.
2. The caps are 20%, 10% and 5%.
3. A rise through the limit only alerts me. So if A doubled to $100, a fall to its $15 value if wrong would lose $12,070, or 11.3% of a $107,100 portfolio (calc.). Below its trim-above, no sale is allowed.
4. Rule 4's reserve figure, open on this list at first, was set the same day: `Rules/cash.md`.
5. Positions share a limit by the test for one thesis, counted whole. Page: `overlap.html`.

**What changed:** one line in `CLAUDE.md`. `rules.md` and `my-rules.md` stay as they are. This method fills in items 1 and 4 of `recommendations`. Corning's scores stay Claude's reading: they change nothing while the gates fail.
