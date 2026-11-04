# An open gate from a refused input is not a lead

*Written 2026-11-04.*

## What happened

Claude caught these while testing the monthly hunt on scratch copies. All had passed or had no test at the time. No note or decision used a wrong figure, and nothing reached the real Inbox.

- **A false idea.** Archrock's free cash flow record fell, so `value.py` refused a growth of 0% above that record. Claude's script treated the refusal as "base not worked out", which leaves Gate 2 open, and an open gate lets a lead through. So Archrock reached Inbox as an idea, on a bug. Fixed, its base covers 63.1% of the price and it stops at Gate 2 (calc., [StockAnalysis, close Nov. 3, 2026, retrieved Nov. 4, 2026](https://stockanalysis.com/stocks/aroc/)). On this month's screen, that bug was the difference between one idea and none.
- **A look-again month read as a filing.** Powell's log line says "After the 10-K, about Nov. 2026 (my estimate)". The first version let it back in because the month had come, though no new 10-K exists, so it would have been retested on the same figures.
- **A span with the wrong sign.** The twelve-month sum looked for last year's span in the wrong direction, so most companies came back open. The hand sorts on 15 companies caught it at once.
- **Resetting a scratch copy by deleting.** To rerun, Claude used `rm` on run files inside the same scratch copy, several times. On Nov. 3, 2026 I had refused that and asked for a fresh copy. Nothing in the vault was deleted, but Claude repeated what I had said no to, and it says so here.

## What it taught us

An open gate means a figure could not be read. So anything that can make a gate open by accident can also write a false lead. Look at why each lead got through on its first real run, not only at how many did.

## What changed

- `sensors/hunt/gates.py` lets a falling record be the ceiling, as `Rules/when-to-buy.md` says. A test covers it.
- `sensors/hunt/hunt.py` lets a rejected company back only when a newer filing of the right form exists. A test covers it.
- `sensors/hunt/test_hunt.py` holds the 15 hand sorts as its check.
- Claude makes a fresh scratch copy for each rerun.

## What it does not say

That the gates are now right on every company. They have run on 15 hand sorts and five new ones.
