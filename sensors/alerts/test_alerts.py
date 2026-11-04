"""Check alerts.html and Rules/alerts.md by working the figures out again.

    .venv/bin/python -I sensors/alerts/test_alerts.py

Shares no code with analyze.py or draw.py. Reads the saved filing list, releases and prices directly.
"""
import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "alerts.html").read_text()
rule = (ROOT / "Rules/alerts.md").read_text()
claude = (ROOT / "CLAUDE.md").read_text()
GLW = ROOT / "sensors/edgar/cache/CIK0000024741"
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


# Status
check("rule says approved", "approved by me, Nov. 3, 2026" in rule)
check("CLAUDE.md loads it", "@Rules/alerts.md" in claude)
check("the rule says only a Red goes to the phone", "a Red goes to my phone through Telegram" in rule and "Nothing else sends an alert" in rule)
check("the rule keeps Orange in the Journal", "limit breaks. | Journal, next time I open it |" in rule)
check("the rule no longer says nothing sends", "Nothing sends an alert" not in rule)
check("the schedule stays off", "No schedule for the Yahoo close" in rule)
check("page says approved and Red only", "APPROVED. ONLY RED GOES TO THE PHONE" in page)
check("page no longer says nothing is automated", "NOTHING AUTOMATED" not in page and "Nothing is automated" not in page and "go out at once" not in page)
check("page links the phone page", 'href="phone.html"' in page and (ROOT / "phone.html").exists())
check("page and rule name hindsight", "hindsight" in page and "hindsight" in rule)
check("dates in link text are written out", not re.search(r"filed \d{4}-", page))
check("no external script", not re.search(r'<script[^>]+src=', page))

# Filing counts from the list itself
rows = [json.loads(line) for line in open(GLW / "filings.jsonl")]
win = [r for r in rows if "2024-11-03" <= r["filed"] < "2026-11-03"]
forms = collections.Counter(r["form"] for r in win)
check("403 filings", len(win) == 403)
ins = sum(forms[f] for f in ("4", "4/A", "144", "3", "3/A"))
check("344 insider forms", ins == 344)
check("85%", round(ins / 403 * 100) == 85)
eights = [r for r in win if r["form"] == "8-K"]
check("22 8-Ks", len(eights) == 22)
flags = {"1.01", "2.01", "2.02", "5.02", "3.02", "7.01", "8.01"}
check("21 flagged", sum(bool(set(r["items"].split(",")) & flags) for r in eights) == 21)
check("7 notices are 7.01 alone", sum(r["items"] == "7.01" for r in eights) == 7)
check("8 results", sum("2.02" in r["items"] for r in eights) == 8)
check("the only 1.02 sits with a 1.01", all("1.01" in r["items"] for r in eights if "1.02" in r["items"]))
check("no Red item in the window", not any(set(r["items"].split(",")) & {"1.03", "2.04", "2.06", "3.01", "4.02", "5.01"} for r in eights))
dotted = [r for r in rows if r["form"] in ("8-K", "8-K/A") and r["filed"] >= "2004-10-01" and "." in r["items"]]
check("279 dotted 8-Ks", len(dotted) == 279)
reds = [r for r in dotted if set(r["items"].split(",")) & {"1.03", "2.04", "2.06", "3.01", "4.02", "5.01"} or ("1.02" in r["items"] and "1.01" not in r["items"])]
check("3 Red items since 2004", [r["filed"][:4] for r in sorted(reds, key=lambda r: r["filed"])] == ["2004", "2005", "2006"])

# Tally by hand: 27 = 9 + 2 + 1 + 15
check("Orange 27", 9 + 2 + 1 + 15 == 27)
check("12 of 27 surfaced by sensors", 9 + 2 + 1 == 12 and "surface 12 of the 27" in rule and "surface 12 of the" in page)
check("Info 401", (403 - 22 - 2 - 1) + 13 + 10 == 401)
check("page counts 27 and 401", "27 Oranges and 401 Info" in page and "27 Oranges and 401 Info" in rule)

# Quarters from the saved releases themselves
docs = GLW / "documents"
for name, needle in [("0001628280-25-002912-glw-20241231xex99xq42024.htm", "1,368"), ("0001628280-25-020470-glw-20250429xex991.htm", "1,355"),
                     ("0000024741-26-000273-glw-20261027xex99xq32026.htm", "2,379")]:
    check(f"{needle} in {name[:20]}", needle in (docs / name).read_text(errors="replace"))
ocf = [1052, 362, 1717, 1061]; cap = [432, 332, 422, 545]; dep = [317, -171, 880, -70]
check("K5 today is 1,505", sum(ocf) - sum(cap) - sum(dep) == 1505)
margins = [(175, 1246), (194, 1368), (201, 1355), (247, 1566), (295, 1652), (305, 1701)]
check("K3 reads low through Q4 2025", all(round(a / b * 100, 1) <= 17.9 for a, b in margins))
check("K3 clears on Q1 2026", round(387 / 1846 * 100, 1) > 17.9)
sales = [1246, 1368, 1355, 1566, 1652, 1701, 1846, 2072, 2379]
falls = [i for i in range(1, len(sales)) if sales[i] < sales[i - 1]]
check("Optical fell once, Q1 2025", falls == [2])

# Prices
close = [(r["date"], float(r["close"])) for r in csv.DictReader(open(ROOT / "sensors/prices/cache/GLW/2026-11-02.csv"))]
w = [c for c in close if c[0] >= "2024-11-03"]
check("500 trading days", len(w) == 500)
top = max(w, key=lambda c: c[1])
check("high 255.69 June 29", top[0] == "2026-06-29" and f"{top[1]:.2f}" == "255.69")
check("down 52%", round((1 - w[-1][1] / top[1]) * 100) == 52)
check("never at or under trim-above", min(c for _, c in w) > 36.06)
check("last under 28.97", [d for d, c in close if c < 28.97][-1] == "2023-12-06")
check("last under 36.06", [d for d, c in close if c < 36.06][-1] == "2024-05-29")

# Drill by hand
sh = 5000 / w[0][1]
c = dict(w)["2025-08-01"]
check("drill first over 5%", 5.0 < sh * (c - 14.06) / (95000 + sh * c) * 100 < 5.05)
c = dict(w)["2025-05-02"]
check("drill under 5% before", sh * (c - 14.06) / (95000 + sh * c) * 100 < 5)

# Rule and page agree, and no rule was weakened
for word in ["R1", "R4", "O1", "O16", "I1", "I12"]:
    check(f"map has {word}", f"| {word} |" in rule and f">{word}<" in page)
check("no sale from an alert", "No alert sells anything" in rule and "No alert sells anything" in page)
check("no recommendation in an alert", "no recommendation" in rule and "gives no recommendation" in page)
check("trim needs a rise and a holding", "A rise takes the close above it, on a position I hold" in rule)
check("names the Nov. 2 decision", "This replaces my decision of Nov. 2, 2026 on no red level" in rule and "On Nov. 2 you decided" in page)
check("price move alone stays out", "a price move alone" in rule and "a price move alone" in page)
for url in re.findall(r'href="(https?://[^"]+)"', page):
    check_ok = " " not in url
    if not check_ok:
        check("link " + url, False)

print("\nFAILS:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
