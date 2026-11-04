# Inputs to pm.py

One JSON file: `label`, `as_of`, `portfolio`, `companies`, and `groups`. A value you cannot source stays out of the file, or `null`. The script then says unknown.

## portfolio

- `{"file": "Portfolio/Paper portfolio.md"}` reads cash and shares from the note. A position there with no matching company stops the run, because a whole-portfolio answer must cover every position.
- `{"source": "...", "cash": N, "positions": {"TICKER": dollars}}` is a made-up scenario. It is labeled made up on every run. It never goes in `Portfolio/`.

## companies

| Field | Values | Where it comes from |
|---|---|---|
| `name`, `ticker` | | The company note |
| `run` | path | Newest `sensors/valuation/runs/*.json`. Fills price, its date, base and strategic, so nothing is re-typed |
| `price`, `price_date`, `base`, `strategic` | numbers, or leave out | Only if no run exists and you have a dated source. Without a run, normally leave them out |
| `downside_if_wrong` | dollars a share, or leave out | Downside scenarios that still bite if the thesis is wrong, at full amount. `0` needs a source. Corning's `0` is `Rules/sizing.md`'s worked example |
| `thesis` | `none`, `draft`, `recorded` | The Thesis section of the company note. `recorded` only if the owner recorded it |
| `thesis_state` | `intact`, `broken`, or leave out | `broken` only on the owner's ruling. `intact` only with a recorded thesis, after you read new results against it |
| `skeptic` | `survived`, `did_not_survive`, `not_run` | The owner's ruling in the Journal |
| `kill_line_crossed` | `true`, `false`, or leave out | The kill criteria note, read against the newest numbers. Leave out if no lines exist |
| `scores` | five tests, each 0, 1 or 2 | `Rules/sizing.md`. Price enters none of them. Link the evidence in your answer |
| `scores_status` | `ruled`, `claude_reading` | `ruled` only if the owner ruled on them |
| `rose_through_trim` | `true`, `false`, or leave out | Did a rise take the price through the trim-above? Needs a dated entry and a past price. Leave out if you cannot show it |

## groups

`{"name", "status": "proposed" or "ruled", "event", "members": [tickers], "evidence"}`. `ruled` only on the owner's ruling. Proposed groups count in the limit and in the bet count, labeled, and the script also gives the count on rulings only.

## The order the script applies

Not held:
1. Thesis ruled broken: no position.
2. All three gates pass, no kill line crossed, and size, limits and cash leave room: **buy**.
3. Otherwise: **no position**.

Held:
1. Thesis ruled broken: **sell**, the whole position, because the rule reassesses all of it.
2. Above the trim-above and under the buy-below at once: **hold**, and ask.
3. Recorded and intact thesis, a rise through the trim-above: **trim**.
4. Gates pass, thesis intact, no kill line crossed, and room remains: **add**.
5. Otherwise: **hold**.

Size is the smaller of the grade's cap and 5% ÷ loss rounded up to 10 points, rounded down to 0.1% of the portfolio. A shared limit may cut it. Then the cash: above 15% for any grade, down to 5% for Strong only, never the floor. Several hits go highest score first, then highest coverage.

## What the owner has ruled

- "Did not survive the skeptic" does not mean broken, so a held position stays a hold on that alone (Journal, Nov. 3, 2026).
- Made-up A and B are separate theses, so they share no limit. `ruled_separate` in their input file records this (Journal, Nov. 3, 2026).

## Readings the rules leave open

The script takes one reading of each. All are Claude's, for the owner to correct. The script names them under "Unsure" when they bite, so keep them in the answer.

| Open point | Reading taken | Why |
|---|---|---|
| Trim amount | Sell back to the most the cap and limit allow today, ignoring the gates, which fail above the buy-below anyway. If no such amount, unset | Item 1 of `recommendations` asks for a size. The rules give none |
| Sale on a broken thesis | The whole position | "Reassess the whole position" is not "sell". The owner's ruling opens it |
| Held with no recorded thesis | Hold | Override 7 allows a sale only by `when-to-trim` or a broken thesis |
| Group room | (5% − others' loss) ÷ this position's unrounded loss | The group sum uses the unrounded loss |
| Cash-limited size | Rounded down to 0.1% | The rule rounds size that way |
| Proposed groups | Count in the limit, labeled | Stricter until the owner rules |
| Price exactly at the buy-below | Not under it | The rule says under |
| Value if wrong below zero | Loss capped at 100% | Long only: a position cannot lose more than it cost |
| A name in two groups | Joins them in the bet count, with each group's own limit | The rule asks only for positions and groups |
| Grade's cap while gated | The script shows the grade's cap on a held position, and alerts over it | `sizing`'s worked table shows 0% while gated, for an unheld idea |
| The 24-month cash alert | Counted from the date in the Portfolio note | The script cannot see history |
