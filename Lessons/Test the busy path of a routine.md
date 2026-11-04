# Test the busy path of a routine

*Written 2026-11-03.*

## What happened

Claude caught this. The daily run passed on a copy with real sensors, but that day was quiet, so Claude read no filing. A replay of real past filings then failed at the step that matters most. Corning's Q3 release is saved as one huge line, too long for the Read tool, and the run has no Grep. So the run could not read the results. It kept the 8-K at Orange and said "not read", which was the right behavior, but the kill lines went unread.

## What changed

- `sensors/daily/collect.py` saves each document as wrapped plain text, and a test covers it.
- A second replay read the release and the SEC letter.
- `publish.py` now prints the quiet line, because the first test showed the run could not quote it.

## What it does not say

That the run reads every filing well. It was tried on one release and one letter, and not in Desktop.
