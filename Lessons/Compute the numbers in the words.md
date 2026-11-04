---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Compute the numbers in the words

*Written 2026-11-03.*

## What happened

Claude caught this while building `worth.html`. The charts computed their numbers, but Claude typed the worked example in the words by hand from a rough sum. Four were wrong: $25.08 for $24.14, $14.90 for $14.87, $53.21 for $53.12 and $22.48 for $22.44 (calc.). A separate script run before the page was opened showed the gaps. All were lessons in arithmetic, and no decision used them.

## What it taught us

A page's charts can be right while its sentences are wrong. Check every number in the words with a script that shares no code with the page.

## What changed

The four numbers on `worth.html` are fixed before handover. No rule changed.
