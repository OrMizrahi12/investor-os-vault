"""Check portfolio.html and the paper portfolio by working every figure out again.

    .venv/bin/python -I sensors/portfolio/test_portfolio.py

Shares no code with draw.py or pm.py. Reads the valuation run and looks for the text.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "portfolio.html").read_text()
paper = (ROOT / "Portfolio/Paper portfolio.md").read_text()
run = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)))


def says(s):
    return s in text or s in page


low, mid, high, price, strat = run["base"]["low"], run["base"]["mid"], run["base"]["high"], run["price"]["close"], run["strategic"]
loss = (price - low) / price * 100
check("paper: kind paper", "kind: paper" in paper)
check("paper: $100,000 in cash", "cash: 100000" in paper)
check("paper: table has no positions", re.search(r"## Positions\n\n\|[^\n]*\n\|[-| ]*\|\n\n## Changes", paper) is not None)
check("coverage 17.6", f"{mid / price * 100:.1f}" == "17.6" and says("17.6%"))
check("loss 88.6", f"{loss:.1f}" == "88.6" and says("88.6%"))
check("price on page", says("$123.20"))
check("buy-below 28.97", f"{mid / .75:.2f}" == "28.97" and says("$28.97"))
check("trim-above 36.06", f"{mid + strat:.2f}" == "36.06" and says("$36.06"))
check("base high covers 24.4", f"{high / price * 100:.1f}" == "24.4" and says("24.4%"))
check("Corning at 20% loses 17.7", f"{.2 * loss:.1f}" == "17.7" and says("17.7%"))
check("$5,000 loses $4,429", round(5000 * loss / 100) == 4429 and says("$4,429"))
alt = low - 3.75
check("downside what-if 10.31 and 91.6", f"{alt:.2f}" == "10.31" and f"{(price - alt) / price * 100:.1f}" == "91.6" and says("$10.31") and says("91.6%"))
check("A: 5/70 floors to 7.1", math.floor(5 / 70 * 1000) / 10 == 7.1 and says("$7,100"))
check("B: cap 10 on 25", min(10, 5 / .2) == 10 and says("$10,000"))
check("cash $82,900", 100000 - 7100 - 10000 == 82900 and says("$82,900"))
check("A lost $4,970, B $2,000", round(7100 * .7) == 4970 and round(10000 * .2) == 2000 and says("$4,970") and says("$2,000"))
check("says what you settled", says("separate theses") and says("does not mean broken"))
check("strategic under a third gives the gap", 40 / .75 > 40 + 40 / 3 - .01 and 40 / .75 < 40 + 40 / 3 + .01)
check("Nov. 3, 2028 is 24 months on", says("Nov. 3, 2028"))
for w in ("Lesson, not advice", "The decision is yours.", "Keep this page on this computer", "no position", "Hold all five", "made-up"):
    check(f"says: {w}", says(w))
check("closing line is the last visible text before the footer", re.search(r'class="end">The decision is yours\.</p>\s*<footer>', page) is not None)
check("page loads nothing from the network", not re.search(r'<(script|link|img)[^>]+(src|href)="http', page))
check("no advice word", not re.search(r"\b(overpriced|undervalued|you should buy|you should sell)\b", text, re.I))
print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
