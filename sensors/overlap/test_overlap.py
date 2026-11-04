"""Check overlap.html by working its figures out again.

    .venv/bin/python -I sensors/overlap/test_overlap.py

Shares no code with analyze.py or draw.py. Reads the saved returns, the rule file and the page.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "overlap.html").read_text()
text = re.sub(r"<script>.*?</script>", " ", page, flags=re.S)
text = re.sub(r"<[^>]+>", " ", text)
text = re.sub(r"\s+", " ", text).replace("&amp;", "&")
rule = (ROOT / "Rules/sizing.md").read_text()
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def has(s):
    check("page says: " + s[:70], s in text)


r = pd.read_parquet(ROOT / "sensors/concentration/cache/returns.parquet")
names = ["GLW", "APH", "AVGO", "NVDA", "VZ"]
x = r[names].to_numpy()
assert x.shape == (2511, 5) and not np.isnan(x).any()
p = x.mean(axis=1)
pv = p.var(ddof=1)

# swing shares, by covariance of each stock with the portfolio
share = [np.cov(x[:, i], p)[0, 1] * 0.2 / pv for i in range(5)]
check("shares add to 1", abs(sum(share) - 1) < 1e-9)
four = sum(share[:4])
has(f"{four * 100:.1f}% of the portfolio's swing")
has(f"{share[4] * 100:.1f}% of the swing")

# bets, by hand
same = x.var(axis=0, ddof=1).mean() / pv
ratio = (x.std(axis=0, ddof=1).mean()) ** 2 / pv
ev = np.linalg.eigvalsh(np.corrcoef(x.T))
eig = ev.sum() ** 2 / (ev ** 2).sum()
check("same swing 2.01", f"{same:.2f}" == "2.01")
check("ratio 1.87", f"{ratio:.2f}" == "1.87")
check("eigen 2.89", f"{eig:.2f}" == "2.89")
has("Prices alone say 1.9 to 3.4")
d = pd.to_datetime(r.index)
mo = pd.DataFrame(x, index=d, columns=names).add(1).groupby([d.year, d.month]).prod().sub(1)
evm = np.linalg.eigvalsh(np.corrcoef(mo.to_numpy().T))
check("monthly eigen is the top, 3.42", f"{evm.sum() ** 2 / (evm ** 2).sum():.2f}" == "3.42")

# correlations
c = np.corrcoef(x.T)
fourp = (c[0, 1] + c[0, 2] + c[0, 3] + c[1, 2] + c[1, 3] + c[2, 3]) / 6
has(f"average pair among the four is {fourp:.2f}")
has(f"Verizon with them is {c[4, :4].mean():.2f}")
mc = np.corrcoef(mo.to_numpy().T)
has(f"Corning with NVIDIA is {c[0, 3]:.2f} daily and {mc[0, 3]:.2f} monthly")
y1 = np.corrcoef(x[d >= "2025-11-03"].T)
has(f"With the four it was −{abs(y1[4, :4].mean()):.2f} in the last year")
y20 = np.corrcoef(x[d.year == 2020].T)
has(f"but {y20[4, :4].mean():.2f} in 2020")

# bad days
b = x[:, :4].mean(axis=1)
worst = np.argsort(b)[:25]
check("all four down on all 25", (x[worst, :4] < 0).all())
has(f"Verizon rose on {(x[worst, 4] > 0).sum()} of them")
others = r.drop(columns=names).mean(axis=1).to_numpy()
check("407 others", r.shape[1] - 5 == 407)
q = (b <= -0.05) & (np.abs(others) <= 0.01)
check("eight quiet falls", q.sum() == 8)
check("first quiet fall July 17, 2024", str(d[q][0].date()) == "2024-07-17")
has("All 8 came on or after July 17, 2024")
q4 = (b <= -0.04) & (np.abs(others) <= 0.01)
has(f"At a 4% cut, {(d[q4] >= '2024-01-01').sum()} of {q4.sum()} came after 2023")

# the worst fall of the four
lv = np.concatenate([[1], np.cumprod(1 + b)])
dd = lv / np.maximum.accumulate(lv) - 1
tr = dd.argmin()
pk = lv[: tr + 1].argmax()
check("worst fall -36.8%", f"{dd[tr] * 100:.1f}" == "-36.8")
check("trough Oct. 14, 2022", str(d[tr - 1].date()) == "2022-10-14")
check("peak Dec. 27, 2021", str(d[pk - 1].date()) == "2021-12-27")
has(f"the worst fall is {abs(dd[tr]) * 80:.1f}% of the whole")
vz22 = np.prod(1 + x[pk:tr, 4]) - 1
has(f"It fell {abs(vz22) * 100:.0f}% in the 2022 fall")

# filings arithmetic
check("NVDA data center 92.5%", f"{89023 / 96221 * 100:.1f}" == "92.5")
check("NVDA hyperscale 50.6%", f"{48710 / 96221 * 100:.1f}" == "50.6")
check("GLW optical 49.0%", f"{2379 / 4855 * 100:.1f}" == "49.0")
check("GLW products add up", 2379 + 1281 + 471 + 436 + 247 + 41 == 4855)
check("VZ consumer 77.0%", f"{26432 / 34313 * 100:.1f}" == "77.0")
check("APH markets add to 100", 36 + 10 + 19 + 15 + 9 + 6 + 5 == 100)
for s in ("92.5%", "50.6%", "49.0%", "77.0%", "$179.2B", "$29B", "$42B", "$56B", "$25B", "About 95%", "$11,926M", "about $9.8B"):
    has(s)

# sizing arithmetic
check("Corning loss 88.6%", f"{(123.20 - 14.06) / 123.20 * 100:.1f}" == "88.6")
has("88.6%")
has(f"lose {0.2 * (123.20 - 14.06) / 123.20 * 100:.1f}% of the portfolio")
has("5 × 5% = 25%")
has("2 × 5% = 10%")
has("6.25% or less")
for L, tot, each, lose, times in ((30, "16.6", "4.1", 24, "4.8"), (50, "10.0", "2.5", 40, "8.0"), (70, "7.1", "1.7", 56, "11.2"), (90, "5.5", "1.3", 72, "14.4")):
    check(f"grid {L}", f"{int(500 / L * 10) / 10:.1f}" == tot and f"{int(500 / L / 4 * 10) / 10:.1f}" == each and 80 * L // 100 == lose and f"{lose / 5:.1f}" == times)
    has(f"{L}% {tot}% {each}% {lose}% {times} times")
has("11.0%")

# the graph, from the notes themselves
notes = {n: (ROOT / f"Companies/{n}.md").read_text() for n in ("Corning", "Amphenol", "Broadcom", "NVIDIA", "Verizon")}
rows = {n: [l for l in t.split("## Typed links")[1].split("\n## ")[0].splitlines() if l.startswith("| ") and "[[" in l] for n, t in notes.items()}
between = sum(1 for n in ("Amphenol", "Broadcom", "NVIDIA", "Verizon") for l in rows[n] if "[[Corning]]" in l)
check("six links run to Corning", between == 6)
for n in ("Amphenol", "Broadcom", "NVIDIA", "Verizon"):
    others_ = [m for m in ("Amphenol", "Broadcom", "NVIDIA", "Verizon") if m != n]
    check(f"{n}: no typed link to the other three", not any(f"[[{m}]]" in l for l in rows[n] for m in others_))

# the rule as approved
check("old bare line is gone", "- Positions that rest on one thesis share one limit, because they fail together.\n" not in rule)
for w in ("**The test for one thesis.**", "**Count the whole position.**", "**Same direction only.**", "**Claude proposes the groups, with the event and its evidence, and I rule.**", "**Each refresh shows names against bets:**"):
    check("rule has " + w[:30], w in rule)
check("the 5% stays", "**If the thesis is wrong, no position may lose more than 5% of the portfolio.**" in rule)
for w in ("The test for one thesis.", "Count the whole position.", "Same direction only."):
    has(w)
has("Approved by the owner, Nov. 3, 2026, counting whole positions, and made.")
check("page no longer says proposed", "Proposed, in its place" not in text and "Not made." not in text)

# the catalyst table against the notes
import glob
cats = {Path(f).stem: Path(f).read_text() for f in glob.glob(str(ROOT / "Catalysts/*.md")) if not f.endswith("README.md")}
check("40 catalyst notes", len(cats) == 40)
cnt = {n: sum(f"[[{n}]]" in t for t in cats.values()) for n in ("Corning", "Amphenol", "Broadcom", "NVIDIA", "Verizon")}
check(f"note counts {cnt}", cnt == dict(Corning=40, Amphenol=2, Broadcom=2, NVIDIA=3, Verizon=1))
for w in ("40 of 40", "One note on 4 of 5"):
    has(w)

# kill line K9, from the filed quarters
q3 = 33942 + 77259 + 39367
q2 = 30116 + 54208 + 35802
check("Q3 sum 150,568", q3 == 150568)
check("Q2 sum 120,126", q2 == 120126)
check("Meta Q3 is nine months less the half", 83055 - (18997 + 30116) == 33942)
check("Q3 up 25.3%", f"{(q3 / q2 - 1) * 100:.1f}" == "25.3")
check("year on year 105.4%", f"{(q3 / 73318 - 1) * 100:.1f}" == "105.4")
kn = (ROOT / "Research/2026-11-03 Corning kill criteria.md").read_text()
mon = (ROOT / "monitor.html").read_text()
note = cats["Cut in AI spending"]
for name, t in (("kill note", kn), ("monitor", mon), ("catalyst note", note)):
    check(name + " has the figures", "$150,568M" in t and "$120,126M" in t)
check("kill note says nine", "The nine lines are set" in kn and "**K9**" in kn and "### K9:" in kn)
check("monitor says nine", "The nine lines are set" in mon and 'id="K9"' in mon)
check("sizing reads nine lines", "nine lines, none crossed, but claims C6 and C8 have no line" in rule)

print("\nFAILED: " + ", ".join(fails) if fails else "\nAll checks pass.")
raise SystemExit(1 if fails else 0)
