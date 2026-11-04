---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

%% status: researching, no buy, candidate or owned. Ticker, sector and status are those of the company involved. If there is none, leave ticker and sector blank. %%

# Check which tools a subagent really has

*Written 2026-11-03.*

## What happened

I built the skeptic's guard to allow only `jq` and one web search in Bash, because its list of tools named Grep and Glob for reading the vault. Those two tools do not exist in this setup. So the first review, on Nov. 3, 2026, could not list a folder. It read 7 of 29 Lessons and 7 of 39 Catalyst notes, and it said so. My guard tests passed, because they tested only what the guard blocks and allows, not whether the agent could do its job. The researcher's guard already allowed `grep` and `ls`, and I did not ask why.

## What it taught us

A tool named in an agent's file may not exist. Before tightening a guard, check what the agent has left to do the job with. Then look at what a real run says it could not do.

## What changed

`.claude/hooks/skeptic-guard.py` now allows `grep` and `ls` inside this vault, and `.claude/agents/skeptic.md` no longer names the two tools. `skeptic.html` labels the Nov. 3 review as partial. No rule changed.
