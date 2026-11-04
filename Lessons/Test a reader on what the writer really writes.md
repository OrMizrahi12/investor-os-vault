# Test a reader on what the writer really writes

*Written 2026-11-04.*

## What happened

Claude caught this while building Home. `sensors/daily/publish.py` puts a busy brief under the heading `## Daily brief, <date>, <time>`. `journal_alerts` in `dashboard/data.py` treated that heading as not a routine's, and dropped every line under it. So a real brief with a Red gave 0 alerts. The dashboard's Alerts panel would have shown none, and Home would have said "Nothing waiting" over a live Red. The phone reads the brief its own way, so a Red would still have gone out.

The panel's test passed because its made-up brief left out that heading. No real alert was lost: no busy brief has been written yet, and the real Journal still reads 0 lines with the fix in.

A second slip, the same kind of trust in a number: Home first measured as fitting while Streamlit's top bar covered its headline and two block headings. Only the screenshot showed it.

## What changed

- `journal_alerts` reads the `## Daily brief` heading as the daily run's.
- `dashboard/test_dashboard.py` now writes its brief through the real `publish.add_to_journal`, so the test fails if the two ever part.
- `dashboard/tools/measure_home.py` fails on anything the bar covers, and on a cut figure. A viewed screenshot stays part of the check.

## What it does not say

That the other routines' forms are safe for good. The event run's and the weekly check's forms are tested on text copied from their code and prompt, not written by them. None has written a real alert yet.
