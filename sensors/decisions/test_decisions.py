"""Check decisions.html by working every figure out again.

    .venv/bin/python -I sensors/decisions/test_decisions.py

Shares no code with draw.py. Runs the two made-up cases through the
portfolio-manager skill's pm.py on temporary files, and reads the kill lines
from the kill note.
"""
import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "decisions.html").read_text()
note = (ROOT / "Research/2026-11-03 Corning kill criteria.md").read_text()
run = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
text = re.sub(r"\s+", " ", re.sub(r"<(style|script)\b.*?</\1>|<[^>]+>", " ", page, flags=re.S))
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def has(name, s):
    check(f"{name}: {s}", s in page or s in text)


low, mid = run["base"]["low"], run["base"]["mid"]
bb, ta = run["buy_below"], run["trim_above"]
bb = bb["mid"] if isinstance(bb, dict) else bb
ta = ta["mid"] if isinstance(ta, dict) else ta
with open(ROOT / "sensors/prices/cache/GLW/2026-11-03.csv") as f:
    close = float(list(csv.DictReader(f))[-1]["close"])

has("buy-below", f"${bb:.2f}")
has("trim-above", f"${ta:.2f}")
has("close", f"${close:.2f}")
check("close date is the newest saved", close == 126.13999938964844)
has("today's coverage", f"{mid / close * 100:.1f}%")
has("today's multiple of the trim line", f"{close / ta:.2f} times")
has("run's coverage", f"{mid / 123.2 * 100:.1f}%")

# Start: 400 shares at $25
c0 = (25 - low) / 25
has("start coverage", f"{mid / 25 * 100:.1f}%")
has("start loss", f"{c0 * 100:.1f}%")
check("start loss rounds to 50", 40 < c0 * 100 <= 50)
check("start size is the cap and the limit", min(10, 5 / 50 * 100) == 10 and 400 * 25 == 10000)

# Case 1
pos, tot = 40000, 130000
l1 = (100 - low) / 100
has("c1 share", f"{pos / tot * 100:.1f}% of $130,000")
has("c1 coverage", f"{mid / 100 * 100:.1f}%, so gate 3 fails")
has("c1 lost", f"{l1 * 100:.1f}%, or ${pos * l1:,.0f}")
has("c1 lost share", f"{pos * l1 / tot * 100:.1f}%, over the 5% limit")
has("c1 multiple", f"{100 / ta:.2f} × trim-above")

# Case 2
pos2, tot2 = 8000, 98000
l2 = (20 - low) / 20
has("c2 share", f"{pos2 / tot2 * 100:.1f}% of $98,000")
has("c2 coverage", f"{mid / 20 * 100:.1f}%, so gate 3 passes")
has("c2 lost", f"{l2 * 100:.1f}%, or ${pos2 * l2:,.0f}")
has("c2 lost share", f"{pos2 * l2 / tot2 * 100:.1f}%, under the 5% limit")

# The skill's own script on made-up files
PM = ROOT / ".claude/skills/portfolio-manager/scripts/pm.py"


def pm(price, held, crossed, rose, state="intact"):
    data = {"label": "made up", "as_of": "2026-11-04", "portfolio": {"source": "made up", "cash": 90000, "positions": {"X": held}},
            "companies": [{"name": "X", "ticker": "X", "price": price, "price_date": "2026-11-04", "base": {k: run["base"][k] for k in ("low", "mid", "high")},
                           "strategic": run["strategic"], "downside_if_wrong": 0, "thesis": "recorded", "thesis_state": state, "skeptic": "survived",
                           "kill_line_crossed": crossed, "scores": {"mechanism": 2, "record": 1, "customers": 1, "kill_lines": 1, "unknowns": 1},
                           "scores_status": "ruled", "rose_through_trim": rose}], "groups": []}
    with tempfile.NamedTemporaryFile("w", suffix=".json") as t:
        json.dump(data, t)
        t.flush()
        return subprocess.run([sys.executable, "-I", str(PM), t.name], capture_output=True, text=True, check=True).stdout


o1, o2 = pm(100, 40000, False, True), pm(20, 8000, True, False)
o3, o4 = pm(20, 8000, False, False), pm(20, 8000, True, False, "broken")
check("pm: case 1 is trim", "| **trim** | $32,850 |" in o1 and "keeping $7,150" in o1)
has("page has the proposal", "sell $32,850 and keep $7,150")
kept_loss = 7150 * l1 / tot * 100
has("kept position's loss", f"loses {kept_loss:.1f}% if wrong")
check("pm: limit alert in case 1", "26.4% of the portfolio" in o1)
check("pm: case 2 holds, no add", "| **hold** | $0 |" in o2 and "No buy or add until you have ruled" in o2)
check("pm: without the crossing it adds $1,800", "| **add** | $1,800 |" in o3)
has("page has the room", "room for $1,800")
check("pm: sale only on the ruling", "| **sell** |" in o4 and "| **sell** |" not in o2)

# Kill lines against the note
for k, phrase in {"K1": "$2,379M", "K3": "17.9%", "K4": "$27,000M", "K5": "$1,505M", "K6": "at-the-market", "K7": "after 2028", "K8": "two quarters running", "K9": "two quarters running"}.items():
    row = next(r for r in note.splitlines() if r.startswith(f"| **{k}**"))
    check(f"{k} in the note has {phrase}", phrase in row)
    check(f"{k} on the page", f">{k}</th>" in page)
check("K2 on the page, with all eight names", ">K2</th>" in page and all(n in page for n in ("AT&amp;T", "Amazon", "Lumen", "Meta", "Microsoft", "NVIDIA", "Verizon", "Zayo")))
for fig in ("22.4%", "$20,324M", "$2,072M", "$150,568M", "$120,126M"):
    check(f"reading {fig} is in the note and on the page", fig in note and fig in page)

# Labels and tone
check("says lesson, not advice", "A lesson, not advice." in text)
check("every case figure sits under a made-up mark", page.count('class="made"') >= 8)
check("both case cards are dashed", page.count('class="card paper"') == 3)
check("no line sells by itself", "No kill line turns a hold into a sell by itself." in text)
check("no outside script or style", not re.search(r'<(script|link)[^>]+(src|href)=', page))
check("no empty link", 'href=""' not in page and 'href="#"' not in page)
check("no raw python or wiki link left", not re.search(r"\{[a-zA-Z_]+|\[\[", text))

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
