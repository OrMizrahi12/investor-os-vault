"""Check coach.html, the decision file and the agent by working the figures out again.

    .venv/bin/python -I sensors/coach/test_coach.py

Shares no code with draw.py or pm.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "coach.html").read_text()
log = (ROOT / "Journal/decisions/2026-11-03 Corning.md").read_text()
agent = (ROOT / ".claude/agents/coach.md").read_text()
run = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
assets = ROOT / ".claude/skills/portfolio-manager/assets/corning-2026-11-03.json"
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


WORDS = "The price is far above what the business is worth on our numbers, so I would wait for the buy-below."
check("the owner's words are in the log, as said", f"**One main reason:** {WORDS}" in log)
check("and on the page", WORDS in page)
check("the view comes before the system's view", log.index("## My view") < log.index("## The system's view") < log.index("## Where we differ"))
check("only the owner's words under the decision", 'Nov. 3, 2026, in answer to the one question: "Yes, I would still want no position."' in log)
check("the rule routes through the coach", "goes through the `coach` first" in (ROOT / "Rules/recommendations.md").read_text())
check("the skill stops without a view", "stage: view written" in (ROOT / ".claude/skills/portfolio-manager/SKILL.md").read_text())
check("the log has every section", all(s in log for s in ("## The one question", "## What this log does not say", "## Correction")))

price = 123.20
mid = run["base"]["middle"] if "middle" in run["base"] else run["base"]["mid"]
check("coverage 17.6% is middle over price", f"{mid / price * 100:.1f}" == "17.6" and "17.6%" in page)
check("buy-below is middle over 0.75", f"{mid / 0.75:.2f}" == "28.97" and "$28.97" in page)
check("base range", all(f"${run['base'][k]:.2f}" in page for k in ("low", "high")))
check("price and source", "$123.20" in page and "close of Nov. 2, 2026" in page)

counts = [sum(1 for s in re.split(r"(?m)^## Session", (ROOT / f"Journal/{d}.md").read_text()) if "Corning decision" in s) for d in ("2026-11-02", "2026-11-03")]
check(f"103 sessions name the decision ({counts})", sum(counts) >= 103 and "103 sessions" in page)
for quote in ("We decided not to buy", "not a view that Corning is a bad business or too expensive", "We build the valuation method"):
    check("Nov. 2 words: " + quote, quote.lower() in (ROOT / "Journal/2026-11-02.md").read_text().lower().replace("[[corning]]", "corning"))
j3 = (ROOT / "Journal/2026-11-03.md").read_text()
check("the panel's words", "Coverage is under 75% and no thesis is written" in j3 and "Coverage is under 75% and no thesis is written" in page)

check("the agent asks first", "Do not call a tool until this stage is done" in agent)
check("the agent has no web and no agent tools", re.search(r"^tools: Read, Write, Edit, Bash, Skill$", agent, re.M) is not None)
check("the agent closes the stage last", "last, once they are saved" in agent)
check("the agent does not say blind", "run blind" not in agent.replace("do not call the run blind", ""))
for word in ("you should buy", "you should sell", "overpriced."):
    check(f"no advice words: {word}", word not in page.lower())
check("the page ends on whose choice it is", "The decision is yours." in page)
paper = (ROOT / "Portfolio/Paper portfolio.md").read_text()
check("the paper portfolio holds no position", "No positions. Cash $100,000" in paper)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
