"""Check sizing.html and Rules/sizing.md by working every figure out again.

    .venv/bin/python -I sensors/sizing/test_sizing.py

Shares no code with draw.py. Reads the base figures from the valuation run and
looks for the expected text in the page and the rule file.
"""
import json
import re
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "sizing.html").read_text()
rule = (ROOT / "Rules/sizing.md").read_text()
run = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def floor_tenth(x):
    return Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_FLOOR)


# Corning, from the run
low, mid, price = run["base"]["low"], run["base"]["mid"], run["price"]["close"]
c_loss = (price - low) / price
check("rule has the test for one thesis", "**The test for one thesis.**" in rule and "**Count the whole position.**" in rule)
check("page has the test", "counted whole" in page)
check("Corning low", f"{low:.2f}" == "14.06")
check("Corning middle", f"{mid:.2f}" == "21.73")
check("Corning price", price == 123.2)
check("Corning loss 88.6%", f"{c_loss * 100:.1f}" == "88.6")
check("Corning coverage 17.6%", f"{mid / price * 100:.1f}" == "17.6")
check("Corning buy-below 28.97", f"{mid / .75:.2f}" == "28.97")
check("run's downside is -3.75", any(abs(s["full"] + 3.75) < 0.005 for s in run["scenarios"]))
check("run says 89% to the low", "89% to the low" in (ROOT / "sensors/valuation/runs/2026-11-03-01.md").read_text())

# Made-up ideas by hand: size = min(cap, 5 / loss rounded up), floor to 0.1
a = 7100; b = 10000
check("A: 5/70 floors to 7.1%", floor_tenth(5 / 70 * 100) == Decimal("7.1"))
check("A: 7.1% is $7,100", a == 7100)
check("A: lost $4,970", round(a * (50 - 15) / 50) == 4970)
check("A: under limit", a * .7 <= 5000)
check("B: cap 10 beats 25", min(10, 5 / 20 * 100) == 10)
check("B: lost $2,000", round(b * (40 - 32) / 40) == 2000)
check("cash $82,900", 100000 - a - b == 82900)
check("both wrong $6,970", 4970 + 2000 == 6970)
check("both zero $17,100", a + b == 17100)
check("A coverage 80%", 40 / 50 == .8)
check("B coverage 95%", 38 / 40 == .95)
check("A under its buy-below", 50 < 40 / .75)
check("B under its buy-below", 40 < 38 / .75)
check("Thin at 90 caps at 5%", min(5, 5 / 90 * 100) == 5)
check("Corning gates-ignored lost $4,429", round(5000 * c_loss) == 4429)
check("alt 3%: A $4,200", floor_tenth(3 / 70 * 100) == Decimal("4.2"))
check("alt 8%: A $11,400", floor_tenth(8 / 70 * 100) == Decimal("11.4"))
check("alt cash", 100000 - 4200 - 10000 == 85800 and 100000 - 11400 - 10000 == 78600)
check("repair 5.3%", f"{(1 / .95 - 1) * 100:.1f}" == "5.3")
check("repair 25%", abs((1 / .8 - 1) * 100 - 25) < 1e-9)
check("A score 9", 2 + 2 + 2 + 1 + 2 == 9)
check("B score 7", 1 + 2 + 1 + 2 + 1 == 7)
check("Corning score 3", 0 + 1 + 1 + 1 + 0 == 3)

check("A doubled: lost $12,070", round(14200 * .85) == 12070)
check("A doubled: 11.3% of $107,100", f"{12070 / 107100 * 100:.1f}" == "11.3")
for s_ in ["$12,070", "11.3%", "$107,100"]:
    check(f"both files have {s_}", s_ in page and s_ in rule)

# peak and the fall, from the price series
peak = max(v for _, v in run["series"])
day = [d for d, v in run["series"] if v == peak][0]
check("peak $255.69 on June 29, 2026", round(peak, 2) == 255.69 and day == "2026-06-29")
fall = (1 - price / peak) * 100
check("fall is 52%", f"{fall:.0f}" == "52")
past = run["no_vote"][0]["low"]
check("past low fall 80%", f"{(1 - past / price) * 100:.0f}" == "80")
check("fall at buy-below 51.5%", f"{(1 - low / (mid / .75)) * 100:.1f}" == "51.5")

# equal dollars: words say it breaks the limit on two of three
eq = {"Corning": 20000 * c_loss, "A": 20000 * .7, "B": 20000 * .2}
check("equal dollars breaks limit on exactly two", sum(v > 5000 for v in eq.values()) == 2)
check("B under the limit at its largest size", 10000 * .2 < 5000)

# figures appear in the page
for s in ["$7,100", "$10,000", "$82,900", "$4,970", "$2,000", "$6,970", "$17,100", "$4,429", "$17,717", "$14,000",
          "$4,000", "88.6%", "70.0%", "20.0%", "17.6%", "$14.06", "$21.73", "$28.97", "$123.20", "$255.69", "$24.70", "51.5%", "$85,800", "$78,600"]:
    check(f"page has {s}", s in page)
# figures appear in the rule file
for s in ["$7,100", "$10,000", "$82,900", "$4,970", "$2,000", "$6,970", "$17,100", "$4,429", "88.6%", "$85,800", "$78,600", "$4,200", "$11,400", "5.3%"]:
    check(f"rule has {s}", s in rule)

# grid cells (dollars on $100,000)
def cell(cap, c):
    return int(floor_tenth(min(cap, 5 / c * 100)) * 1000)


text = re.sub(r"<[^>]+>", " ", page[page.index('<table class="grid-t"'):page.index("Darker means bigger")])
got = [int(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", text)]
want = [cell(cap, c) for cap in (20, 10, 5) for c in range(20, 101, 10)] + [0] * 9
check("all 36 grid cells", got == want)
print("     Strong row:", want[:9])
print("     Middling row:", want[9:18])

# status of the proposal
check("rule says approved, with the date", "approved by me, Nov. 3, 2026" in rule and "PROPOSAL" not in rule)
check("CLAUDE.md loads it", "@Rules/sizing.md" in (ROOT / "CLAUDE.md").read_text())
check("page no longer says proposal", "proposal" not in page.lower())
check("my-rules has no sizing change", "sizing.md" not in (ROOT / "Rules/my-rules.md").read_text())
check("page says lesson, not advice", "A lesson, not advice" in page)
check("portfolio folder holds no made-up position", sorted(p.name for p in (ROOT / "Portfolio").iterdir()) == ["Paper portfolio.md", "README.md"]
      and "Made-up" not in (ROOT / "Portfolio/Paper portfolio.md").read_text())
check("no word 'recommend' as a call on the page", "we recommend" not in page.lower())

print(f"\n{len(fails)} failed" if fails else "\nall passed")
raise SystemExit(1 if fails else 0)
