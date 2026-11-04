**Buy both, on paper: Made-up A $7,100 and Made-up B $10,000. Cash left: $82,900, or 82.9% (calc.).** A and B are made up, so this is a worked scenario and no real trade. The test for one thesis has not run. If you rule them one thesis, B shrinks to $100.

| Company | Action | Size | Share of portfolio | What set it | Lost if wrong |
|---|---|---|---|---|---|
| Made-up A | **Buy** | $7,100 | 7.1% | the 5% limit | $4,970 |
| Made-up B | **Buy** | $10,000 | 10.0% | the Middling cap | $2,000 |
| Cash after | | $82,900 | 82.9% | above normal | |

All sums are calc., from `pm.py` on your figures in `Rules/sizing.md` (approved Nov. 3, 2026) and `Portfolio/Paper portfolio.md` (as of Nov. 3, 2026). That note has $100,000 in cash and no positions. Nothing real is on file.

**Cash.** A goes first, since it has the higher score. Cash goes $100,000 to $92,900 to $82,900. All of it comes from cash above the 15% reserve ($15,000, calc.), so any grade may spend it. The floor is not touched.

**Shared exposures: 2 positions, 0 groups, 2 bets, with or without proposed groups.** No group means the test was not run, not that it passed. Neither name has a thesis text or kill lines on file, so I have no event to test and I propose no group. It matters: if you rule them one thesis, the sum is 4.97% + 2.00% = 6.97%, over the 5% limit. In that what-if, A stays at $7,100, B falls to $100 and cash is $92,800 (calc., a what-if, not my answer).

**Alerts.** None. Each position is inside the 5% limit, and cash is above its floor.

**Where I am unsure**

1. **One thesis or two.** See above. You settle it, and it moves B from $10,000 to $100.
2. **What "hit" means.** I used the table's prices, $50 and $40, which are under the buy-belows of $53.33 and $50.67. A higher price changes the answer, because the loss changes:
   - Just under, at $53.32 and $50.66: A $6,200, B $10,000, cash $83,800 (calc., what-if).
   - Exactly at the line: not under it, so no position for either, on my reading of "under" (what-if). You can correct that reading.
3. **The refresh.** `Rules/cash.md` says a hit is real only after value is refreshed from the newest 10-Q or 10-K. Made-up names have no filings, so I took your figures as given. No newer filing can apply. The only outside check is Aaa, still 6.12% for Oct. 2026 (`sensors/macro/downloads/AAA.csv`), so the 9% stays closed.
4. **The scores.** `Rules/sizing.md` gives totals of 9 and 7. The five-test splits come from `sensors/sizing/draw.py`. Only the totals affect the answer, and neither split has a 0.
5. **Few names, much cash.** Two positions is under the 5 in rule 2, and nothing here forces a third. Cash above 50% is counted from Nov. 3, 2026 in the Paper portfolio note, so the 24-month alert cannot come before Nov. 2028 (calc.).

**What I did not do.** I placed no order, and `Portfolio/` is unchanged. Made-up names go in that note only on your yes to an exact change, which I would show you first. `Rules/sizing.md` says this worked example recommends no trade, and that stands: these are buys in a scenario.

---

## Parts both share

**Thesis, and what would prove it wrong.** Recorded, by your ruling in this request. No text exists: `Companies/` has no note on either, and no kill criteria file. You rule no line is crossed. I cannot name a line or what would prove either wrong.

**Price against value.** All figures are made up, from `Rules/sizing.md` (Nov. 3, 2026). The buy-below and coverage are calc.

| | Made-up A | Made-up B |
|---|---|---|
| Base low to high | $18.00 to $60.00 | $34.00 to $42.00 |
| Base middle | $40.00 | $38.00 |
| Price (taken as today, Nov. 3, 2026) | $50.00 | $40.00 |
| Coverage, against the 75% bar | 80.0% | 95.0% |
| Buy-below | $53.33 | $50.67 |
| Strategic value | unknown | unknown |
| Trim-above | unknown | unknown |

Base high comes from `sensors/sizing/draw.py`, not the rules table. No strategic value was given, so neither has a trim-above, and I cannot say when a trim would apply. Past multiples, rival multiples and the growth the price needs: none exist for made-up names. They get no vote anyway.

**Strongest case against.** No objection is written. You ruled that both survived the skeptic, so the buy can be shown in this scenario. I cannot say why they survived. For a real company, I would stop here until the review is on file.

**What you lose if the thesis is wrong.** See each block. It is a distance, not a forecast. It leaves out tax and does not cover a market fall. If both are wrong, you lose $6,970. If both go to zero, $17,100 (`Rules/sizing.md`, calc.).

**Standing decisions and what is due.** These stand, from your rulings of Nov. 3, 2026: the 5% limit; the caps of 20%, 10% and 5%; a rise through the limit only alerts you and never forces a sale; the 15% reserve and 5% floor. Nothing on these two names is due.

**What would change this.** Your ruling that they are one thesis. A ruling that changes a gate or a score. New figures from a filing, if these were real. A different price at the hit moves gate 3 and the loss, as item 2 shows, but no grade or group.

---

**Made-up A: buy. Size: $7,100, 7.1% of the portfolio.** Made up, on paper.

Score 9, Strong, cap 20% (ruled by you). All three gates pass. The cap would allow $20,000, but 5% ÷ 70% is 7.1%, so the limit sets the size. Cash goes from $100,000 to $92,900, above normal both ways.

Value if wrong: $18.00 − $3.00 = $15.00. Loss if wrong: 70.0%. At this size: $4,970, which is 99% of the $5,000 limit (calc.). It leaves almost no room, so a small rise in its share or fall in its value can break the limit at a refresh. That would alert you and stop adds. It would not force a sale.

Unsure items: 1, 2, 3, 4.

The decision is yours.

**Made-up B: buy. Size: $10,000, 10.0% of the portfolio.** Made up, on paper.

Score 7, Middling, cap 10% (ruled by you). All three gates pass. 5% ÷ 20% is 25%, so the cap sets the size. Cash goes from $92,900 to $82,900, above normal both ways. A Middling idea may spend only cash above 15%, and there is plenty.

Value if wrong: $34.00 − $2.00 = $32.00. Loss if wrong: 20.0%. At this size: $2,000, which is 40% of the limit (calc.). It gets more dollars than A because it can lose so much less.

Unsure items: 1, 2, 3, 4.

The decision is yours.
