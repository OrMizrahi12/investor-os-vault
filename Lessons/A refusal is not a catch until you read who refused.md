# A refusal is not a catch until you read who refused

*Written 2026-11-04.*

## What happened

Claude caught these, reading the raw results of the guardrail attempts before reporting them.

- **Three false passes.** In three attempts (H3, H5, H6) the file stayed unchanged, but no guardrail had seen the call. Claude's Edit tool refused my badly formed requests first: a replacement identical to the original, a string found 11 times, and a settings edit that failed the settings check.
- **One false failure.** A should-work command (S5) failed because it wrote outside the working folder, for a reason unrelated to the guardrails.
- **A proxy that was wrong.** The panel first counted any Journal session naming a routine as a run of it, so "the monthly hunt and the event run", a person's build session, showed as an event run on Nov. 4. Viewing the panel on real data caught it.
- **My first test design was refused,** by the auto mode safety check, because it switched permission prompts off. The safer design, one allow rule per attempt, also sits closer to how a routine runs.

No note or decision used a wrong result.

## What it taught us

"File unchanged" does not say what stopped the change. A test of a guard must name who refused, and a refusal for another reason counts as a broken test. This is [[Test a guard through a whole run]] again, from the other side: there the guard stopped too much, and here the test credited it with too much.

## What changed

`sensors/guardrails/attempts.py` names who refused and sets a refusal for want of an allow rule apart. `sensors/guardrails/test_guardrails.py` fails if a saved row was not refused by a guardrail. The four attempts were rerun and the page says so. `dashboard/data.py` counts only a routine's own session record. No rule changed.
