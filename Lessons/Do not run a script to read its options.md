---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Do not run a script to read its options

*Written 2026-11-03.*

## What happened

Claude caught this right after doing it. While finishing `multiples.html`, Claude ran `sensors/graph/draw.py --help`, which had no part in the task. The script ignores that flag and rebuilt `graph.html`. The Journal of the same day already records this exact slip, and it was not read as a rule. The file is 76,199 bytes, as before, and the typed links were not edited, but no copy was kept to compare byte for byte. No research depends on the rebuild.

## What it taught us

A correction written only in the Journal does not stop a repeat. Our draw scripts take no flags and write when run, so read the file instead of running it, and run only what the task needs.

## What changed

Added a warning line to the graph section of `sensors/README.md`. The script itself is unchanged, for me to decide whether it should refuse unknown flags.
