# List a method's inputs before saying every number

*Written 2026-11-04.*

## What happened

Claude caught this when I asked which numbers the quarterly run must re-verify. The checklist from Nov. 3, 2026 was presented as "every number", but it left out the six filed figures behind the growth ceiling, free cash flow per share in FY2016 and FY2025. The dry run's 50 of 50 did not cover them. No figure was wrong: the check now gives 3.1074%, the same as the approved input ([10-K, filed Feb. 12, 2019](https://www.sec.gov/Archives/edgar/data/24741/000002474119000016/glw-20181231x10k.htm); [10-K, filed Feb. 12, 2026](https://www.sec.gov/Archives/edgar/data/24741/000002474126000124/glw-20251231.htm); calc.).

## What it taught us

"Every" is a claim. Walk the inputs file line by line and map each input to a check, or name it as unchecked.

## What changed

`sensors/reviews/checklist-GLW.toml` has a `record` part and `sensors/reviews/quarterly.py` checks it. A test ties it to the approved input. No Claude run has used it, and no rule changed.
