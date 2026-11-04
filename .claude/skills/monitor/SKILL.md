---
name: monitor
description: The monitoring package - the five routines' playbooks and the alert map. Use whenever the owner asks what the routines do or when they run, what is waiting in the alerts, how an item should be levelled, whether a filing or fact is Red, Orange or Info, how to run a routine by hand, what happens at each level, whether the prompts in Desktop still match the playbooks, or why a guardrail stopped a run, even if the word monitor is not used. It reports conditions with a source and date. It never recommends, never trades and changes no rule, map or portfolio file.
---

# Monitor

The routines watch. The map levels what they see. The owner decides. Conclusion first, plain words, short sentences.

This skill is an index. It keeps no second copy, because two copies drift.

| What | The only copy |
|---|---|
| The alert map, the levels, what the owner does at each | `Rules/alerts.md` |
| The map as data, for the page and its test | `sensors/alerts/alertmap.py` |
| What to do while monitoring | `Rules/monitoring.md` |
| Each routine's steps | its playbook, below |
| What a routine may touch, and each guardrail's test | `guardrails.html` |

## The routines

| Routine | Desktop task | When | Playbook | Page |
|---|---|---|---|---|
| Daily run | `daily-test` | Daily | `Playbooks/Daily run.md` | `daily.html` |
| Event run | `event-run` | Weekdays at 8:30 | `Playbooks/Event run.md` | `hunt-events.html` |
| Monthly hunt | `monthly-hunt` | The 15th | `Playbooks/Monthly hunt.md` | `hunt-events.html` |
| Weekly thesis check | `weekly-thesis-check` | Its playbook says | `Playbooks/Weekly thesis check.md` | `reviews.html` |
| Quarterly refresh | `quarterly-refresh` | `30 10 * 2,4,5,7,8,10,11 2,5` | `Playbooks/Quarterly refresh.md` | `reviews.html` |

Each playbook's first lines say whether it is live. Read them. Do not take "live" from this table.

## Limits

- **State a condition, its rule ID, its source and its date. Give no recommendation** (`Rules/recommendations.md`). If the owner wants to act, the coach goes first.
- **No alert sells anything.** A Red opens a review. With no holding, a Red only reopens the draft.
- **A price move alone is never an alert**, and neither is a source's age (`Rules/monitoring.md`).
- **Claude says "appears broken". The owner rules.** Only the owner drops a presumed Red.
- **The routine prompts say "use no skill".** So this skill is for a session with the owner. A routine follows its own prompt.
- A possible inside tip stays out of every level and every file. Tell the owner to ask a lawyer.

## What to do

**"What is waiting?"** Read the Journal's newest files for `### Red`, `**Red**`, `### Orange`, `**Orange**` and any `FAILED` line. Or point to the Alerts panel on the dashboard (`dashboard/run.sh`). Say the level, rule, source and date of each. Say if the routines have not run: nothing notices a run that did not happen (O16).

**"What level is this?"** Read the map in `Rules/alerts.md`. For a company, read its note, thesis and kill lines first, as `Rules/memory.md` says. Read the filing, not its item number. Reading can lower or raise a first pass, except that R3 stays Red until the owner rules. Give the level and the rule ID, and say who has to do what next, from the map's table.

**"What does this routine do?"** Read its playbook and answer from that.

**"Do the routines still match?"** Run:

    python3 .claude/skills/monitor/scripts/check.py

It compares each playbook's prompt with the Desktop task's copy, and the map's IDs in `Rules/alerts.md` with `sensors/alerts/alertmap.py`. It changes nothing. If a prompt differs, tell the owner which. A task's prompt lives in Desktop, and the guardrails wall it off from Claude, so the owner pastes it.

**"A guardrail stopped something."** Read `.claude/guardrails/blocked.jsonl`, or the panel. It gives the rule, the tool and the target. W1 to W5 are the walls, T1 to T5 the broker and trade checks. A row that says "after-check" means a walled file changed and was put back, with the changed copy in `.claude/guardrails/quarantine/`. Do not try another way. Tell the owner what stopped and why.

**Changing the map, a rule, the method or the portfolio.** Claude cannot, in any session. On the owner's yes, write the new text to a file outside the walls, and give the owner this line to type:

    ! python3 .claude/hooks/owner-apply.py <new text> <walled file>

Changing the method or the map still needs the owner's approval first.
