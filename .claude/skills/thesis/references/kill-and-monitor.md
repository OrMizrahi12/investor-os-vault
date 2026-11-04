# Kill criteria and the monitoring plan

## What makes a line

A kill line says: this number or event, past this threshold, by this date, makes us look again at this claim.

| Part | Test |
|---|---|
| Claim | One claim, by its C number. |
| Measure | Defined so two people read the same figure: which line, which filing, how it is summed. |
| Threshold | A number, or a yes-or-no event with a named speaker and a dated source. "Weakens" or "disappoints" is not a threshold. |
| Date | The quarter it is tested, or the first and last quarters it runs. Add the likely report date, labeled `my estimate` unless a source gives it. |
| Today | The reading now, sourced or calc., and whether it is crossed. |
| Set by | `owner, <date>`, or `proposed, for you to set`. |

**Owner-set lines come first, copied exactly.** Do not reword, widen or tighten them. If you think one is flawed, say so under "What I cut", and leave it standing.

**Crossing opens a review, never a sale.** Say so in the section's first lines. Tell the owner in the same session, read the source itself, and say if the claim holds and why. The owner decides. If a holding exists and the thesis breaks, `Rules/when-to-trim.md` covers it.

## Before you offer a line, try to break it

- **Can it fire at all?** A line that waits for someone to speak can stay silent forever. Add a stop date, so that silence counts.
- **Does it fire on the record?** Where the vault holds past figures, count how often the line would have fired and what followed. Say so, even if it is awkward. A line that fires every year says nothing, and one that never could is decoration.
- **Is the threshold today's figure?** Then say it sits on the line until the test date.
- **Does it test the claim?** Say what a pass does **not** prove. Usually a pass is not proof.
- **Which way does it run?** A line that proves our doubt wrong is not a kill line. It goes under question 6 as such.
- **Is it really a price?** No line is a price, under `Rules/monitoring.md`.

A claim with no line is allowed, and it goes under "What I cut" with the reason. A gap on paper is better than a fake measure.

## Table for the note

| Line | Claim | Measure | Threshold | Test date | Today | Status | Set by | Source |

After the table, for each line only what the table cannot hold: what a pass does not prove, and the back-test.

## The monitoring plan

Say honestly what will and will not catch each line. Read the sensor's code or README, not its name. Do not run a sensor to find out.

| Line | Where it shows | How often | Next read | What catches it | Who reads the number |

What the vault's sensors do, as of Nov. 3, 2026. Check that it still holds:

- `sensors/8k-watch/watch.py`: 8-K filings, on the company's watchlist. It says a filing arrived, and copies only first paragraphs.
- `sensors/radar/radar.py`: filings and catalyst dates. It lists filings and names notes. It reads no table.
- `sensors/prices/`: never for a kill line. No line is a price.
- **No sensor reads a threshold, and none runs by itself.** Calls are not filings, so a line resting on a call rests on a person. Say so for each line it applies to.

A company not on the watchlist has no sensor coverage. Say that, and let the owner decide. Do not add it.

Add a calendar: date, kind of date (stated, scheduled, target, forecast, `my estimate`), what to read, and which lines it tests. Then list what the owner must decide: schedules, watchlist changes and set lines. Set up nothing yourself.
