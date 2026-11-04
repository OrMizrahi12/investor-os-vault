"""Check cash-reserve.html and Rules/cash.md by working every figure out again.

    .venv/bin/python -I sensors/cash/test_cash.py

Shares no code with analyze.py or draw.py, and uses no pandas. Reads cache/*.csv and the Treasury file.
"""
import calendar
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "sensors/cash"
raw_page = (ROOT / "cash-reserve.html").read_text()
page = re.sub(r"<script>.*?</script>", "", raw_page, flags=re.S)
text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page)).replace("&amp;", "&")
rule = (ROOT / "Rules/cash.md").read_text()
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def both(s, in_page=True, in_rule=True):
    if in_page:
        check(f"page has {s}", s in text)
    if in_rule:
        check(f"rule has {s}", s in rule)


rows = []
with open(HERE / "cache/monthly.csv") as f:
    for r in csv.DictReader(f):
        y, m = int(r["year"]), int(r["month"])
        if y >= 1928:
            rows.append(dict(k=y * 12 + m - 1, y=y, m=m, tr=float(r["tr"]), cpi=float(r["cpi"]), cape=float(r["cape"]), rate=float(r["bill_pct"]), src=r["bill_source"]))
bill = 1.0
for i, r in enumerate(rows):
    r["bill"] = bill
    bill *= 1 + r["rate"] / 100 * calendar.monthrange(r["y"], r["m"])[1] / 365
by = {(r["y"], r["m"]): r for r in rows}
S, E_ = by[(2006, 10)], by[(2026, 10)]
win = [r for r in rows if S["k"] <= r["k"] <= E_["k"]]
check("241 months", len(win) == 241)
sp, bl, cp = (E_[c] / S[c] for c in ("tr", "bill", "cpi"))
both(f"${sp * 100000:,.0f}")
both(f"${bl * 100000:,.0f}")
both(f"${cp * 100000:,.0f}")
both(f"{(1 - bl / cp) * 100:.1f}% of their buying power", in_rule=False)
both(f"${(sp - bl) * 100000:,.0f} on $100,000", in_rule=False)
both(f"{(bl ** .05 - 1) * 100:.1f}%", in_rule=False)
both(f"{(sp ** .05 - 1) * 100:.1f}%", in_rule=False)

# worst fall and months under water
peak = 0
worst = 0
for r in win:
    peak = max(peak, r["tr"])
    worst = min(worst, r["tr"] / peak - 1)
both(f"fell {-worst * 100:.0f}% to March 2009", in_rule=False)
peak = win[0]["tr"]
run = longest = 0
for r in win:
    if r["tr"] >= peak:
        peak, run = r["tr"], 0
    else:
        run += 1
        longest = max(longest, run)
both(f"{longest} months to get back", in_rule=False)
below = sum(r["rate"] < .25 for r in win)
both(f"under 0.25% in {below} of 241 months", in_rule=False)

# bill rate on Nov. 2, 2026
with open(HERE / "downloads/bills_2026.csv") as f:
    reader = csv.reader(f)
    head = [h.strip().lower() for h in next(reader)]
    first = next(reader)
check("13-week rate on Nov. 2 is 4.13", first[0] == "11/02/2026" and first[head.index("13 weeks coupon equivalent")] == "4.13")
both("4.13% on Nov. 2, 2026", in_rule=False)


# waiting
def wait(years, rs):
    won = n = 0
    for a in rs:
        b = next((x for x in rs if x["k"] == a["k"] + 12 * years), None)
        if b:
            n += 1
            won += b["bill"] / a["bill"] > b["tr"] / a["tr"]
    return won, n


for yrs in (1, 5, 10):
    won, n = wait(yrs, win)
    both(f"{won} of {n}", in_rule=True)
w5, n5 = wait(5, rows)
both(f"over five years in {w5 / n5 * 100:.0f}% of start months", in_rule=False)

# decade
a, b = by[(2000, 1)], by[(2009, 12)]
both(f"+{(b['bill'] / a['bill'] - 1) * 100:.1f}%")
both(f"−{(1 - b['tr'] / a['tr']) * 100:.1f}%")

# gauge
today = by[(2026, 10)]["cape"]
check("gauge today 40.7", f"{today:.1f}" == "40.7")
both("40.7", in_rule=False)
for y, jan, lo in ((2000, "43.8", "37.3"), (2008, "24.0", "15.3"), (2020, "31.0", "24.8"), (2022, "36.9", "27.1")):
    yr = [r["cape"] for r in rows if r["y"] == y]
    check(f"{y} January", f"{yr[0]:.1f}" == jan)
    check(f"{y} low", f"{min(yr):.1f}" == lo)
    check(f"{y} in table", jan in text and lo in text)
all_cape = []
with open(HERE / "cache/monthly.csv") as f:
    for r in csv.DictReader(f):
        if r["cape"]:
            all_cape.append((int(r["year"]), int(r["month"]), float(r["cape"])))
rank = sum(c < today for _, _, c in all_cape) / len(all_cape)
both(f"{rank * 100:.1f}% of months since 1881", in_rule=False)
under20 = [(y, m) for y, m, c in all_cape if c < 20 and y >= 2000]
check("under 20 since 2000 only 2008 to 2011", min(under20)[0] == 2008 and max(under20) == (2011, 9))
check("low 2000-03 is 21.2 in Feb. 2003", min((r["cape"], r["y"], r["m"]) for r in rows if 2000 <= r["y"] <= 2003)[1:] == (2003, 2) and f"{min(r['cape'] for r in rows if 2000 <= r['y'] <= 2003):.1f}" == "21.2")
both("Sept. 2011", in_rule=False)
under30 = [(r["y"], r["m"]) for r in rows if r["cape"] < 30]
check("last under 30 is Oct. 2023", max(under30) == (2023, 10))
check("Middle going into 2008", 20 <= by[(2007, 10)]["cape"] < 30 and 20 <= by[(2008, 1)]["cape"] < 30)


# forward by band
def band_share(lo, hi, yrs):
    won = n = 0
    for r in rows:
        f = next((x for x in rows[r["k"] - rows[0]["k"]:r["k"] - rows[0]["k"] + 12 * yrs + 1] if x["k"] == r["k"] + 12 * yrs), None)
        if f and lo <= r["cape"] < hi:
            n += 1
            won += (f["tr"] / r["tr"]) ** (1 / yrs) - (f["bill"] / r["bill"]) ** (1 / yrs) < 0
    return won / n, n


hi = [band_share(30, 999, y) for y in (1, 5, 10)]
lo = [band_share(0, 20, y) for y in (1, 5, 10)]
check("High shares 34, 53, 61", [f"{s * 100:.0f}" for s, _ in hi] == ["34", "53", "61"])
check("Low shares 30, 13, 6", [f"{s * 100:.0f}" for s, _ in lo] == ["30", "13", "6"])
check("rule words", "bills won 34% of one-year stretches, 53% of five-year stretches and 61%" in rule and "30%, 13% and 6%" in rule)
check("High 92 and 57 starts", hi[1][1] == 92 and hi[2][1] == 57 and "of 92 starts" in text and "of 57 starts" in text)


# reserve sums
def mix(start, rule_fn):
    rs = [r for r in rows if start["k"] <= r["k"] <= E_["k"]]
    res = rule_fn(rs[0]["cape"])
    st, ca = 1 - res, res
    for i in range(1, len(rs)):
        st *= rs[i]["tr"] / rs[i - 1]["tr"]
        ca *= rs[i]["bill"] / rs[i - 1]["bill"]
        if i % 12 == 0:
            v = st + ca
            res = rule_fn(rs[i - 1]["cape"])
            st, ca = v * (1 - res), v * res
    return (st + ca) * 100000


def bands(c):
    return .05 if c < 20 else .15 if c < 30 else .25


f15, bd = mix(S, lambda c: .15), mix(S, bands)
f15b, bdb = mix(a, lambda c: .15), mix(a, bands)
for p in (0, .05, .15, .25, .5):
    both(f"${mix(S, lambda c, p=p: p):,.0f}", in_rule=False)
both(f"${bd:,.0f}", in_rule=False)
both(f"${f15 - bd:,.0f}")
both(f"${bdb - f15b:,.0f}")
check("bands behind in 20 years, ahead since 2000", bd < f15 and bdb > f15b)


# the ladder
cash = 30000
a_pay = min(7100, cash - 5000)
cash -= a_pay
b_pay = max(0, min(10000, cash - 15000))
cash -= b_pay
check("walk", (a_pay, b_pay, cash) == (7100, 7900, 15000))
for s_ in ("$7,900", "$15,000"):
    both(s_, in_rule=False)
check("sizing caps fit the levels", 5 + 10 == 15)

# second copy
ann = {int(r["year"]): r for r in csv.DictReader(open(HERE / "cache/annual.csv"))}
dsp = dbl = 1.0
for y in range(2007, 2026):
    dsp *= 1 + float(ann[y]["sp500_tr"])
    dbl *= 1 + float(ann[y]["tbill"])
ssp = by[(2025, 12)]["tr"] / by[(2006, 12)]["tr"]
sbl = by[(2025, 12)]["bill"] / by[(2006, 12)]["bill"]
both(f"grew {ssp:.2f} times and Damodaran's {dsp:.2f} times", in_rule=False)
both(f"{sbl:.3f} times and {dbl:.3f} times", in_rule=False)
check("copies agree within 2%", abs(ssp / dsp - 1) < .02 and abs(sbl / dbl - 1) < .01)
check("Corning 4.3 times", f"{123.20 / 28.97:.1f}" == "4.3")

# wording and limits
for s in ("A lesson, not advice, and not a market forecast",):
    both(s)
check("rule is approved, fixed 15%", "approved by me, Nov. 3, 2026: a fixed 15% with no market gauge" in rule)
check("CLAUDE.md loads it", "@Rules/cash.md" in (ROOT / "CLAUDE.md").read_text())
sizing = (ROOT / "Rules/sizing.md").read_text()
check("sizing line changed", "Pay only as `Rules/cash.md` allows" in sizing and "Pay only from cash above the reserve" not in sizing)
check("override 5 has no gauge exception", not re.search("CAPE|gauge", (ROOT / "Rules/skill-overrides.md").read_text()))
check("no gauge line left in the rule's method", "line 25%" not in text and "| 25% |" not in rule)
check("no stray template text", "{" not in re.sub(r"<style>.*?</style>", "", page, flags=re.S))
check("no script from outside", not re.search(r"<script[^>]+src=", raw_page))
print("\nFAILED:" if fails else "\nall passed", fails or "")
raise SystemExit(1 if fails else 0)
