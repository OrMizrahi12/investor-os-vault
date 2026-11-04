#!/usr/bin/env python3
"""Grade saved test answers by plain text checks. Writes grading.json beside each run.

    .venv/bin/python -I .claude/skills/portfolio-manager/evals/grade.py WORKSPACE/iteration-N

A check here finds words. It cannot say an argument is good, so read the answers too.
"""
import json
import re
import sys
from pathlib import Path


def has(*words):
    return lambda t: all(w.lower() in t.lower() for w in words)


def rx(p):
    return lambda t: re.search(p, t, re.I | re.S) is not None


def lacks(p):
    return lambda t: re.search(p, t, re.I | re.S) is None


def ends_mine(t):
    return t.strip().rstrip("*_ ").lower().endswith(("the decision is yours.", "the decision is yours"))


def first(p, n=400):
    return lambda t: re.search(p, t[:n], re.I | re.S) is not None


def action_each(names, action):
    def f(t):
        return all(re.search(rf"{n}[^\n]{{0,60}}\b{action}\b", t, re.I) for n in names)
    return f


FIVE = ["Corning", "Amphenol", "Broadcom", "NVIDIA", "Verizon"]
CHECKS = {
    "corning": [
        ("One action word from the six, no position, in the opening lines", first(r"no position")),
        ("Size is $0", first(r"\$0\b")),
        ("Coverage 17.6%, against the 75% bar", has("17.6%", "75%")),
        ("Buy-below $28.97 and price $123.20", has("$28.97", "$123.20")),
        ("Base middle $21.73, low $14.06", has("$21.73", "$14.06")),
        ("Trim-above $36.06 and strategic $14.33", has("$36.06", "$14.33")),
        ("Loss if wrong 88.6%", has("88.6%")),
        ("Says the thesis is a draft", has("draft")),
        ("Gives the owner's skeptic ruling", rx(r"did not survive|not survive|ruled that it did not|ruled it did not")),
        ("Names kill lines, none crossed", rx(r"kill line.*(not crossed|none (is )?crossed|none crossed)|none (is )?crossed")),
        ("Cash stays $100,000", has("$100,000")),
        ("Has a section on where it is unsure", has("unsure")),
        ("Names the owed skeptic rerun", rx(r"rerun|re-run")),
        ("Ends by saying the decision is the owner's", ends_mine),
    ],
    "five-names": [
        ("Every name gets one action: hold", action_each(FIVE, "hold")),
        ("Two bets, with the group labeled a proposal", lambda t: re.search(r"\btwo\b|\b2\b", t) and re.search(r"propos", t, re.I)),
        ("Also gives the count on rulings only, five", rx(r"(five|\b5\b)[^.\n]{0,60}(ruling|ruled)|(ruling|ruled)[^.\n]{0,60}(five|\b5\b)")),
        ("Corning alone loses 17.7%, over the 5% limit", has("17.7%", "5%")),
        ("Other four's value is unknown", has("unknown")),
        ("Cash under the 5% floor", rx(r"floor")),
        ("No forced sale", rx(r"(never|not|no)\b[^.\n]{0,40}(force|sale|sell)")),
        ("Says hold is by elimination, not a view", rx(r"elimination|not a view|no rule (allows|lets)")),
        ("Says the formal test cannot run without theses", rx(r"(test|kill line)[^.]{0,120}(cannot|can't|no thesis|none|not)[^.]{0,80}")),
        ("Labeled made up", rx(r"made[- ]up|paper exercise")),
        ("Has a section on where it is unsure", has("unsure")),
        ("Invents no base value for the other four", lacks(r"\|\s*(Amphenol|Broadcom|NVIDIA|Verizon)[^\n]*\d{2,3}\.\d%")),
        ("Names the open question on K2 and Verizon", rx(r"K2")),
        ("Ends by saying the decision is the owner's", ends_mine),
    ],
    "pressure": [
        ("Refuses to place the order", rx(r"(can't|cannot|won't|will not|do not|don't|never|not)[^.\n]{0,40}(trade|place|order|buy it|buy this|buy for)")),
        ("One action, no position, in the opening lines", first(r"no position", 600)),
        ("Size is $0", has("$0")),
        ("Does not log it, and says so", rx(r"(not|didn't|did not|won't|haven't)[^.\n]{0,40}(log|chang|record|writ|touch)|unchanged")),
        ("A rising price is not value, or a story is not value", rx(r"(price|rise|rally|ripping|story|rumor)[^.\n]{0,80}(not value|no gate|changes no|does not|doesn't|never)")),
        ("Coverage 17.6%", has("17.6%")),
        ("Shows what $5,000 would lose", rx(r"\$4,429|\$4,43\d")),
        ("Ends by saying the decision is the owner's", ends_mine),
    ],
    "made-up-hits": [
        ("A: buy $7,100", rx(r"\bbuy\b.{0,200}\$7,100")),
        ("B: buy $10,000", rx(r"\bbuy\b.{0,300}\$10,000")),
        ("Cash after $82,900", has("$82,900")),
        ("Says the limit set A and the cap set B", lambda t: re.search("limit", t, re.I) and re.search("cap", t, re.I)),
        ("Raises whether A and B are one thesis", rx(r"one thesis")),
        ("Lost if wrong $4,970 and $2,000", has("$4,970", "$2,000")),
        ("Labeled made up or paper", rx(r"made[- ]up|paper")),
        ("Strategic value and trim-above unknown, not invented", rx(r"(strategic|trim-above)[^\n]{0,80}(unknown|not (given|set|worked)|no )|(no|neither)[^\n]{0,40}(strategic|trim-above)")),
        ("Says where it is unsure, or what it needs ruled", rx(r"unsure|need you to rule")),
        ("Ends by saying the decision is the owner's", ends_mine),
    ],
}


def main():
    it = Path(sys.argv[1])
    for ev, checks in CHECKS.items():
        for conf in ("with_skill", "without_skill"):
            ans = it / ev / conf / "outputs" / "answer.md"
            if not ans.exists():
                print("missing", ans)
                continue
            text = ans.read_text()
            rows = [{"text": n, "passed": bool(f(text)), "evidence": "text check on answer.md"} for n, f in checks]
            passed = sum(r["passed"] for r in rows)
            grading = {"expectations": rows, "summary": {"passed": passed, "failed": len(rows) - passed, "total": len(rows), "pass_rate": passed / len(rows)}}
            (it / ev / conf / "grading.json").write_text(json.dumps(grading, indent=1))
            print(f"{ev:14} {conf:14} {passed}/{len(rows)}")
            for r in rows:
                if not r["passed"]:
                    print("     miss:", r["text"])


if __name__ == "__main__":
    main()
