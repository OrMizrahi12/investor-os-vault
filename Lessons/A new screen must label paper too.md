---
last checked: "2026-11-04"
sources: []
---

# A new screen must label paper too

*Written 2026-11-04.*

## What happened

Claude caught this in a screenshot, before you saw it. No wrong result reached you.

The Journal's Decisions table showed the Demo portfolio's coach file, "Buy what passes" and "At most $30,000", with nothing to say it was paper (`Journal/decisions/2026-11-03 Demo portfolio.md`, Nov. 3, 2026). The rule "Real and paper never mix" is in `dashboard/PLAN.md`, and each new screen has to keep it by hand. The figure test and the word test both passed, because neither looks for that label. The same screenshot showed a count of 110 blocks on a page with 111.

## What it taught us

A passing test only speaks to what it checks. Read a new screen as the owner would, and go through the plan's rules one by one, not only the ones a test holds.

## What changed

- Decisions marks a demo or paper file "Paper, made-up money" (`dashboard/view.py`), and `JournalScreen` in `dashboard/test_dashboard.py` holds it for both real files. The name check moved to one place, `data.is_paper_name`, which Ideas and alerts also uses.
- By day counts the top block too (`dashboard/screens/journal.py`).
