# Strategic value: the scenarios

Strategic value is what may come later. It adds to the trim-above and never counts toward coverage. Method from `Rules/when-to-trim.md`, worked on `strategic.html`.

## The sum

For each scenario: new profit × the base's votes, brought back at 9%, less the capital to build it, per diluted share. Multiply by its chance. Add them up. Downsides count too.

- **The multiple** is the base's votes on a dollar of new profit: 40% ÷ 9%, 40% the cash sum at the middle growth rate, 20% ÷ Aaa. The script works it out: 13.30 for Corning.
- **Brought back:** ÷ 1.09 to the power of the years away.
- **Capital:** sales × segment assets per dollar of twelve-month sales, plus any named liability, brought back over half the years. Charge it all, even if customers fund part, because deposits get repaid.
- **Margin:** the segment's newest-quarter net margin. It is before corporate costs, so it may flatter. Say so.
- **Downside:** a margin cut on the sales the other scenarios add, weighted by their chances. So raising a chance also deepens the downside: strategic value does not rise by the full amount. Use the script for any what-if. Do not add it up by hand.

## Choosing scenarios

Every catalyst note on the company is placed once: in a scenario, or out, with a reason. A scenario needs a dated source, a size tied to a filed number, dollars not yet reported, a date to check and a way to be wrong. Corning's placing of all 38 notes is `MAP` in `sensors/strategic/model.py`.

Out, as on Corning:
- Already in the numbers.
- Turns on the price, such as a buyback or share sale.
- Cannot be sized. Say so, do not guess.
- No event has happened.
- A cost, already charged as capital.

## Chances

A chance is judgment, and the vault holds no base rate. So:

- Corning's six chances are the owner's, approved Nov. 3, 2026.
- For a new company, or a new scenario, a chance you offer is `proposed`, with reasons for and against, until the owner approves it.
- **A chance changes only on a dated event, never on a price move.** Name the event and its source. The owner decides.
- Chances fall as a ladder rises. A higher step cannot beat the one under it. If a what-if breaks that, say so.

## Double-count checks

Run each one and report any that fails.

1. **Same dollars?** Deals, plants and targets sit on one ladder from the newest run rate to the top target. Its steps must add to the gap and no more. Plants and interim targets add nothing of their own.
2. **Already reported?** Each step starts above the newest quarter × 4.
3. **In the base's earnings?** Every step starts above the base's highest earnings.
4. **In the base's growth?** The base's cash growth must not reach the scenario's dollars.
5. **Deposits?** None counts as value.
6. **Shares?** Warrants and share programs are not double counted. Say what is outside the diluted count.
7. **The price?** No scenario reads the price. Do not subtract what the price "already pays for", because that makes value depend on the price.
8. **Capital twice?** Do not charge a capex plan on top of the capital in the scenarios.

## Known gap

Profit between the last audited year and the newest quarter is in neither the base's middle nor a scenario, so the trim-above leans low until the next 10-K lifts the middle. Corning: base high gives $44.36 on the same scenarios (calc., `strategic.html`, Nov. 3, 2026). The owner chose the middle on Nov. 3, 2026. Say the gap exists, and do not use the high without being asked.

## Assumptions are labeled

Size assumptions with no source, such as Corning's $2 billion for "multibillion", six years, 75% new and 5% display, are named as assumptions every time. Targets are targets. Every scenario is a forecast, not a result.
