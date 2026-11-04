#!/usr/bin/env python3
"""Check pm.py against figures worked out by hand, one case for each action and each limit.

    .venv/bin/python -I .claude/skills/portfolio-manager/scripts/test_pm.py

The expected numbers are typed from Rules/sizing.md and Rules/cash.md, not computed by pm.py.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import pm  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def co(t="AAA", **kw):
    base = dict(name=t, ticker=t, price=50, price_date="2026-11-03", base={"low": 18, "mid": 40, "high": 60}, strategic=20, downside_if_wrong=3,
                thesis="recorded", thesis_state="intact", skeptic="survived", kill_line_crossed=False, scores_status="ruled",
                scores={"mechanism": 2, "record": 2, "customers": 2, "kill_lines": 1, "unknowns": 2}, rose_through_trim=False)
    base.update(kw)
    return base


def go(companies, cash=100000, positions=None, groups=None):
    return pm.run({"label": "t", "as_of": "2026-11-03", "companies": companies, "groups": groups or [],
                   "portfolio": {"cash": cash, "positions": positions or {}}})


def one(*a, **k):
    return go(*a, **k)["rows"][0]


assets = HERE.parent / "assets"
# The worked example in Rules/sizing.md, on the real paper file
o = pm.run(json.loads((assets / "sizing-ideas-2026-11-03.json").read_text()))
a, b = o["rows"]
check("sizing A buy $7,100", a["action"] == "buy" and round(a["size_usd"]) == 7100)
check("sizing A lost $4,970", round(a["lost_if_wrong_usd"]) == 4970)
check("sizing B buy $10,000", b["action"] == "buy" and round(b["size_usd"]) == 10000)
check("sizing B lost $2,000", round(b["lost_if_wrong_usd"]) == 2000)
check("sizing cash $82,900", round(o["cash_after"]) == 82900)
check("highest score first", o["order"] == ["AAA", "BBB"])

# Corning, real run, paper file
o = pm.run(json.loads((assets / "corning-2026-11-03.json").read_text()))
g = o["rows"][0]
check("Corning no position, $0", g["action"] == "no position" and g["size_usd"] == 0)
check("Corning fails all three gates", set(g["gates"].values()) == {False})
check("Corning coverage 17.6", f'{g["coverage_pct"]:.1f}' == "17.6")
check("Corning loss 88.6", f'{g["loss_pct"]:.1f}' == "88.6")
check("Corning buy-below 28.97", f'{g["buy_below"]:.2f}' == "28.97")
check("Corning trim-above 36.06", f'{g["trim_above"]:.2f}' == "36.06")
check("Corning score 3, Thin", (g["score"], g["grade"]) == (3, "Thin"))
check("paper portfolio is $100,000 cash, no positions", (o["total"], o["cash"], o["positions"], o["kind"]) == (100000.0, 100000.0, 0, "paper"))

# The five, made up
o = pm.run(json.loads((assets / "overlap-five-2026-11-03.json").read_text()))
check("five: all hold", [r["action"] for r in o["rows"]] == ["hold"] * 5)
check("five: all add nothing", all(r["size_usd"] == 0 for r in o["rows"]))
check("five: cash under the floor", o["cash_level"] == "under the floor" and any("floor" in x for x in o["alerts"]))
check("five: 5 names, 2 bets, 5 on rulings only", (o["positions"], o["bets_with_proposed"], o["bets_ruled_only"]) == (5, 2, 5))
gr = o["groups"][0]
check("five: group is 80% of the money", round(gr["money_pct"]) == 80)
check("five: Corning alone 17.7%, others unknown", f'{gr["known_loss_pct"]:.1f}' == "17.7" and gr["unknown_loss"] == ["APH", "AVGO", "NVDA"])
check("five: over limit on Corning alone", gr["over_limit"] is True)
check("five: no alert forces a sale", all("forces a sale" in x for x in o["alerts"]))
check("five: unknowns stay None", o["rows"][1]["loss_pct"] is None and o["rows"][1]["buy_below"] is None)
o2 = pm.run(json.loads((assets / "overlap-five-2026-11-03.json").read_text()), "Portfolio/Paper portfolio.md")
check("five as buys from paper: all no position", [r["action"] for r in o2["rows"]] == ["no position"] * 5)

# The six actions
check("buy", one([co()])["action"] == "buy")
check("no position when gated", one([co(thesis="draft")])["action"] == "no position")
check("no position at $0 size: grade None", one([co(scores={"mechanism": 1, "record": 0, "customers": 0, "kill_lines": 1, "unknowns": 0})])["action"] == "no position")
r = one([co()], cash=95000, positions={"AAA": 5000})
check("add to the whole size: $7,100 less $5,000 held", r["action"] == "add" and round(r["size_usd"]) == 2100)
check("hold when at the size", one([co()], cash=92900, positions={"AAA": 7100})["action"] == "hold")
r = one([co(price=70, base={"low": 18, "mid": 40, "high": 60}, strategic=20, rose_through_trim=True)], cash=80000, positions={"AAA": 20000})
check("trim on a rise through the line with thesis intact", r["action"] == "trim")
check("trim keeps a part", r["trim_to_usd"] and 0 < r["trim_to_usd"] < r["held_usd"])
check("trim flags that rules set no amount", any("no trim amount" in u for u in r["unsure"]))
r = one([co(price=70, rose_through_trim=False)], cash=80000, positions={"AAA": 20000})
check("above the line with no rise through: hold", r["action"] == "hold")
r = one([co(price=70, rose_through_trim=None)], cash=80000, positions={"AAA": 20000})
check("unknown rise: hold, and unsure", r["action"] == "hold" and any("rise took it through" in u for u in r["unsure"]))
r = one([co(price=70, rose_through_trim=True, thesis="draft", thesis_state=None)], cash=80000, positions={"AAA": 20000})
check("no trim on a draft thesis", r["action"] == "hold")
r = one([co(thesis_state="broken")], cash=80000, positions={"AAA": 20000})
check("sell on a thesis you ruled broken, whole position", r["action"] == "sell" and r["size_usd"] == 20000)
r = one([co(kill_line_crossed=True)], cash=80000, positions={"AAA": 5000})
check("crossed kill line: hold, no add, never a sale", r["action"] == "hold")
check("crossed kill line blocks a buy", one([co(kill_line_crossed=True)])["action"] == "no position")

# Exactly one action, always from the list
for r in go([co(), co("BBB", thesis="none", thesis_state=None)])["rows"]:
    check(f'{r["ticker"]}: one action from the list', r["action"] in pm.ACTIONS)

# Grades
G = lambda m, r, c, k, u: pm.grade_of(dict(mechanism=m, record=r, customers=c, kill_lines=k, unknowns=u))
check("score 8 Strong", G(2, 2, 2, 1, 1) == (8, "Strong"))
check("score 8 with a 0 is Thin", G(2, 2, 2, 2, 0) == (8, "Thin"))
check("score 7 Middling", G(2, 2, 1, 1, 1) == (7, "Middling"))
check("score 5 with a 0 is Thin", G(2, 2, 1, 0, 0) == (5, "Thin"))
check("score 3 Thin", G(0, 1, 1, 1, 0) == (3, "Thin"))
check("score 2 None", G(1, 1, 0, 0, 0) == (2, "None"))

# Cash levels, on a Middling at 10% (loss 20% leaves the cap in charge)
mid = dict(price=40, base={"low": 34, "mid": 38, "high": 42}, downside_if_wrong=2, strategic=20,
           scores={"mechanism": 1, "record": 2, "customers": 1, "kill_lines": 2, "unknowns": 1})
stock = {"ZZZ": 80000}
zzz = co("ZZZ", thesis="none", thesis_state=None, scores=None, base=None, price=None, strategic=None)
r = go([co(**mid), zzz], cash=20000, positions=stock)["rows"][0]
check("Middling with 20% cash stops at 15%: pays $5,000", r["action"] == "buy" and round(r["size_usd"]) == 5000)
r = go([co(**mid), zzz], cash=15000, positions={"ZZZ": 85000})["rows"][0]
check("Middling at 15% cash: no position", r["action"] == "no position")
strong = dict(mid, scores={"mechanism": 2, "record": 2, "customers": 2, "kill_lines": 1, "unknowns": 2})
r = go([co(**strong), zzz], cash=15000, positions={"ZZZ": 85000})["rows"][0]
check("Strong at 15% cash spends to the floor: $10,000", r["action"] == "buy" and round(r["size_usd"]) == 10000)
r = go([co(**strong), zzz], cash=5000, positions={"ZZZ": 95000})["rows"][0]
check("Strong never spends the floor", r["action"] == "no position")

# Shared limits
grp = [{"name": "one", "status": "ruled", "event": "e", "members": ["AAA", "BBB"]}]
o = go([co(), co("BBB", **mid)], groups=grp)
r_a, r_b = o["rows"]
check("group: first gets its $7,100", round(r_a["size_usd"]) == 7100)
check("group: second gets the leftover $100 (0.03% ÷ 20%, floored)", round(r_b["size_usd"]) == 100)
check("group: stays inside 5%", (r_a["size_usd"] * .7 + r_b["size_usd"] * .2) <= 5000)
check("group with one member held at an unknown loss blocks a buy",
      go([co(), co("BBB", base=None, price=None, scores=None)], cash=80000, positions={"BBB": 20000},
         groups=[{"name": "one", "status": "proposed", "event": "e", "members": ["AAA", "BBB"]}])["rows"][0]["action"] == "no position")
o = go([co(), co("BBB")], cash=60000, positions={"AAA": 20000, "BBB": 20000}, groups=grp)
check("group limit breach alerts and forces no sale", all(r["action"] != "sell" for r in o["rows"]) and any("Group" in x for x in o["alerts"]))
o = go([co("AAA"), co("BBB"), co("CCC")], cash=40000, positions={"AAA": 20000, "BBB": 20000, "CCC": 20000},
       groups=[{"name": "x", "status": "ruled", "event": "e", "members": ["AAA", "BBB"]}, {"name": "y", "status": "ruled", "event": "e", "members": ["BBB", "CCC"]}])
check("a name in two groups joins them: one bet", o["bets_with_proposed"] == 1)

# The gap: both signals at once
r = one([co(price=50, strategic=5, rose_through_trim=True)], cash=80000, positions={"AAA": 20000})
check("buy-below above trim-above: hold, and asks you", r["action"] == "hold" and any("Your ruling" in u for u in r["unsure"]))
check("that gap needs strategic under a third of the middle", r["buy_below"] > r["trim_above"])

# After the actions: counts and group sums see the buys
o = go([co(), co("BBB", **mid)], groups=grp)
check("counts see the buys: 2 positions, 1 bet", (o["positions"], o["bets_with_proposed"]) == (2, 1))
check("group sum sees the buys, inside 5%", 4.9 < o["groups"][0]["known_loss_pct"] <= 5 and o["groups"][0]["over_limit"] is False)
o = go([co(), co("BBB", **mid)])
check("no group given: says the test was not run", any("was not run" in x for x in o["portfolio_unsure"]))
d = {"label": "t", "as_of": "2026-11-03", "companies": [co()], "portfolio": {"cash": 100000, "positions": {}}, "what_if_size": 5000}
check("what-if size is labeled apart", round(pm.run(d)["rows"][0]["what_if"]["lost"]) == 3500)

o = pm.run(json.loads((assets / "sizing-ideas-2026-11-03.json").read_text()))
check("A and B ruled separate: full sizes, no one-thesis doubt", round(o["rows"][1]["size_usd"]) == 10000 and not any("was not run" in x for x in o["portfolio_unsure"]))

# Readings surfaced
o = pm.run(json.loads((assets / "overlap-five-2026-11-03.json").read_text()))
gl = o["rows"][0]
check("did not survive is not broken, your ruling: hold, and no longer unsure", gl["action"] == "hold" and not any("broken, the action" in u for u in gl["unsure"]))
check("draft above the line: no date makes it a trim", any("cannot be intact" in u for u in gl["unsure"]))
check("run's downside shown: 91.6%", any("91.6%" in u for u in gl["unsure"]))
check("no thesis: no empty kill-line complaint", not any("kill-line reading" in u for u in o["rows"][1]["unsure"]))
check("why names the failed gates", "thesis recorded" in pm.run(json.loads((assets / "corning-2026-11-03.json").read_text()))["rows"][0]["why"])

# Nothing estimated, nothing written
check("rounding 7.1 stays 7.1", pm.floor_tenth(7.1) == 7.1)
check("grid rounds 88.6 up to 90", pm.round_up_loss(88.59) == 90)
check("grid leaves 70 at 70", pm.round_up_loss(70.00000000001) == 70)
paper = ROOT / "Portfolio/Paper portfolio.md"
before = hashlib.sha256(paper.read_bytes()).hexdigest()
out = subprocess.run([sys.executable, "-I", str(HERE / "pm.py"), str(assets / "corning-2026-11-03.json")], capture_output=True, text=True)
check("script runs", out.returncode == 0)
check("script ends with the decision line", out.stdout.strip().endswith("The decision is yours."))
check("script leaves the paper file alone", hashlib.sha256(paper.read_bytes()).hexdigest() == before)
src = (HERE / "pm.py").read_text()
check("script has no write or network call", not any(w in src for w in ("write_text", "open(", "requests", "urllib", "socket")))

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
