---
ticker:
status: researching
sector:
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

# Test a guard through a whole run

*Written 2026-11-03.*

## What happened

I built the coach's guard and told the owner that all 45 test calls gave the expected result. In its first live run, on Corning, the coach changed its stage line and then every tool was blocked, including the edit to save its log. My test had checked each call alone, so it never saw that one allowed call shuts the gate on the next. When I added a test of a whole run, it found a second fault before the coach hit it: with only the view in the file, the coach had nothing to attach new sections to. The owner's view was never at risk. It was written first and did not change.

I made two more mistakes in the same work. I told the owner the coach "needs a restart", though the Journal of Nov. 3 already says the same claim about the skeptic was overtaken: the agent was available by the next message. And the coach's log said its run was "blind" to the owner's view, when it had read the owner's words. What is true is that its inputs match a file dated before the view.

## What it taught us

This is [[Check which tools a subagent really has]] again. A guard's tests must play the job from start to finish, in order, not only ask what each call does alone. A new agent may load by the next message, so try it again before calling for a restart. Say what was checked, not a word that claims more.

## What changed

`.claude/hooks/coach-guard.py` no longer gates Edit, and allows a pure addition after the view. `sensors/coach/test_guard.py` plays a whole run. `.claude/agents/coach.md` closes the stage last and no longer says "blind". `Journal/decisions/2026-11-03 Corning.md` has a correction. No rule changed.
