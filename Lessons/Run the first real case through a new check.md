# Run the first real case through a new check

*Written 2026-11-03.*

## What happened

Claude caught the first two, in dry runs of the quarterly refresh on scratch copies. All tests passed each time. No note or decision used a wrong figure.

- **A sum refused.** `quarterly.py` wanted a read's number inside one quote, unless the checklist marked it as a sum. Claude had not marked `sales_fy`, which adds three lines with no printed total. The first run stopped with its failure line and left the number empty, as the prompt asks. That cost a second run, $3.97 at list price.
- **Nine false notices.** The second run listed amended filings from 1998 to 2014 as method triggers, because the script counted every amendment on the filing list. The same code would have repeated a 10-K notice on every run until the next 10-Q.
- **A delete I refused.** To rerun, Claude tried to empty `sensors/reviews/runs/` inside the scratch copy. I said no. Claude made a fresh copy instead, and nothing was deleted from the vault or that copy.

## What it taught us

A check is tested on made-up rows until it meets the real filing and the real filing list. Run the real case before calling it done. For a rerun, make a new copy and leave the old one.

## What changed

A list of quotes now counts as a sum in `sensors/reviews/quarterly.py`. An amendment counts only if it came after the 10-Q before this one, and a notice is told once. `sensors/reviews/test_reviews.py` covers both. No Claude run has used the second fix. No rule changed.
