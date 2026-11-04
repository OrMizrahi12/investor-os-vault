"""Draw demo.html: the hunt's funnel, where each candidate stopped, and the paper portfolio with its cash.

    .venv/bin/python -I sensors/demo/draw.py
    .venv/bin/python -I sensors/demo/test_demo.py

No network. The sums for the book are pm.py's and the note's. Keep the page on this computer, as the other pages are.
A lesson, not advice.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".claude/skills/portfolio-manager/scripts"))
sys.path.insert(0, str(ROOT / "dashboard"))
import pm  # noqa: E402

PICK = json.loads((HERE / "cache/pick.json").read_text())
INPUTS = json.loads((ROOT / ".claude/skills/portfolio-manager/assets/hunt-2026-11-03.json").read_text())
BOOK = pm.run(INPUTS)
RUN = json.loads((ROOT / "sensors/radar/runs/2026-11-03-03.json").read_text())
DECISION = (ROOT / "Journal/decisions/2026-11-03 Demo portfolio.md").read_text()
NOTE = (ROOT / "Portfolio/Paper portfolio.md").read_text()
cash = float(re.search(r"^cash: (\d+)", NOTE, re.M).group(1))

lead_rows = sum(len(s["leads"]) for s in RUN["screen"]["steps"])
skipped = sum(len(PICK["skips"][k]) for k in ("on map", "rejection log", "watchlist"))
ranked, no_rev = len(PICK["have"]), len(PICK["miss"])
companies = ranked + no_rev
tested = ["AGPU", "BLZE", "KGS", "KOPN", "POWL"]
ratio = {r["ticker"]: r["ratio"] for r in PICK["have"]}

# ---------- word claims are tested before they are written ----------
assert (lead_rows, skipped, ranked, no_rev, companies) == (117, 17, 96, 3, 99)
assert [r["ticker"] for r in PICK["have"] if r["ticker"] not in ("IREN", "ABCL")][:5] == tested
assert [r["ticker"] for r in PICK["have"]][:7] == ["AGPU", "IREN", "BLZE", "KGS", "KOPN", "ABCL", "POWL"]
assert all(r["action"] == "no position" and r["size_usd"] == 0 for r in BOOK["rows"])
assert (BOOK["cash"], BOOK["cash_after"], BOOK["positions"]) == (100000, 100000, 0) and cash == 100000
powl = BOOK["rows"][0]
assert powl["ticker"] == "POWL"
assert f'{powl["coverage_pct"]:.1f}' == "32.2" and f'{powl["buy_below"]:.2f}' == "70.06"

Q_P = "https://www.sec.gov/Archives/edgar/data/80420/000008042026000107/powl-20260630.htm"
K_P = "https://www.sec.gov/Archives/edgar/data/80420/000008042025000152/powl-20250930.htm"
SA = "https://stockanalysis.com/stocks/powl/"
Q_K = "https://www.sec.gov/Archives/edgar/data/1767042/000176704226000055/kgs-20260630.htm"
F = "https://data.sec.gov/api/xbrl/companyfacts/CIK{:010d}.json"
facts = lambda cik: f'<a href="{F.format(cik)}">SEC company facts, retrieved Nov. 3, 2026</a>'

CO = [
 dict(t="AGPU", n="Axe Compute", lead="Contract liabilities $0.8M to $60.8M, on $0.1M of revenue", stop="Gate 1", g1="fail",
      g1w=f'Losses in all 8 years SEC has in FY2018 to FY2025, so 8 profitable years of 10 can no longer be reached. FY2025 lost $233.1M (calc., {facts(1446159)}).', g2w="", again="After the 10-K, about Mar. 2027 (my estimate)"),
 dict(t="BLZE", n="Backblaze", lead="Remaining performance obligations $76.5M to $396.0M, on $145.8M of revenue", stop="Gate 1", g1="fail",
      g1w=f'Losses in all 6 years on file, FY2020 to FY2025, so 8 of 10 can no longer be reached (calc., {facts(1462056)}).', g2w="", again="After the 10-K, about Mar. 2027 (my estimate)"),
 dict(t="KGS", n="Kodiak Gas Services", lead="Remaining performance obligations $1,632.9M to $2,643.2M, on $1,308.1M of revenue", stop="Gate 1", g1="fail",
      g1w=f'Debt $2,725.3M is 5.7× twelve-month operating cash of $478.9M, over the bar of 4×. On FY2025\'s $599.7M it is still 4.5× (calc., <a href="{Q_K}">10-Q, filed Aug. 7, 2026</a>; {facts(1767042)}).', g2w="", again="After the 10-K, about Feb. 2027 (my estimate)"),
 dict(t="KOPN", n="Kopin", lead="Remaining performance obligations $12.2M to $40.3M, on $39.3M of revenue", stop="Gate 1", g1="fail",
      g1w=f'Profit in 1 of 10 years, FY2016 to FY2025 (calc., {facts(771266)}).', g2w="", again="After the 10-K, about Apr. 2027 (my estimate)"),
 dict(t="POWL", n="Powell Industries", lead="Remaining performance obligations $1.8B to $2.4B, on $1,104.3M of revenue", stop="Gate 2", g1="pass",
      g1w=f'Profit in 8 of 10 years, no borrowings, twelve-month free cash flow $244.0M (calc., <a href="{Q_P}">10-Q, filed Aug. 4, 2026</a>; {facts(80420)}).',
      g2w=f'Base middle $52.55 against $163.34, 32.2%. Even the high covers only 33.5%. Buy-below $70.06. With deposits left in, a what-if, 51.3%. A proposal on reported earnings (calc., <a href="{K_P}">10-K, filed Nov. 19, 2025</a>; <a href="{SA}">StockAnalysis close, Nov. 3, 2026, 4:00 PM EST</a>).', again="After the 10-K, about Nov. 2026 (my estimate)"),
]
assert [c["t"] for c in CO] == tested

STAGES = [("Lead rows on the radar", "Two quarter steps, after what the radar hides.", lead_rows, f"31 more were hidden as possibly not new growth."),
          ("Companies after skips", "Off our map, the rejection log and the watchlist.", companies, f"{skipped} rows skipped."),
          ("With a revenue figure", "Rise on one line ÷ latest year's revenue.", ranked, f"{no_rev} had no figure: Cerebras and two Goldman Sachs filers."),
          ("Top five, US", "The pick rule. No price and no appeal.", 5, "IREN and AbCellera skipped as not US."),
          ("Past Gate 1", "Here and stronger, on the record.", 1, "AGPU, BLZE, KGS and KOPN stopped here."),
          ("Past Gate 2", "Base value covers at least 75%.", 0, "POWL stopped here, at 32.2%."),
          ("Gate 3, thesis, skeptic", "Nothing reached them, so none ran.", 0, "Not run. That is the gates working, not a gap."),
          ("Positions", "Sized by Rules/sizing.md.", 0, "No idea passed every gate, so no money moved.")]


def bar(n):
    width = 100 * n / lead_rows
    if not n:
        return '<div class="zero">0</div>'
    return f'<div class="fill" style="width:{width:.1f}%"></div><b>{n}</b>'


funnel = "".join(f'<div class="st"><div class="g"><b>{html.escape(a)}</b><span>{html.escape(b)}</span></div><div class="b">{bar(n)}</div><div class="o">{html.escape(o)}</div></div>' for a, b, n, o in STAGES)


def cell(state, word):
    mark = {"pass": "✓", "fail": "✕", "none": "–"}[state]
    return f'<td class="c {state}"><span aria-hidden="true">{mark}</span> {word}</td>'


grid = ""
for c in CO:
    g2 = cell("fail", "Fail") if c["t"] == "POWL" else cell("none", "Not run")
    grid += (f'<tr><th scope="row"><a href="#{c["t"].lower()}">{c["t"]}</a> <span>{c["n"]}</span></th><td class="num">{ratio[c["t"]]:.2f}</td>'
             + cell(c["g1"], "Pass" if c["g1"] == "pass" else "Fail") + g2 + cell("none", "Not run") * 3 + '<td class="num">$0</td></tr>')

cards = ""
for c in CO:
    two = f'<p><b>Gate 2, fail.</b> {c["g2w"]}</p>' if c["g2w"] else ""
    cards += (f'<article class="co" id="{c["t"].lower()}"><h3>{c["n"]} <span class="tk">{c["t"]}</span> <span class="res">Stopped at {c["stop"]}</span></h3>'
              f'<p class="lead">{c["lead"]}.</p><p><b>Gate 1, {"pass" if c["g1"] == "pass" else "fail"}.</b> {c["g1w"]}</p>{two}<p class="note">Look again: {c["again"]}.</p></article>')

share = cash / (cash + 0)
view = re.search(r"## My view\n(.*?)(?=\n## )", DECISION, re.S).group(1)
said = {k: re.search(rf"\*\*{k}:\*\* (.*)", view).group(1).strip() for k in ("Action", "Size", "One main reason")}
then = re.search(r"## What I then decided\n\n(.*?)(?=\n## )", DECISION, re.S).group(1).strip()

CSS = (HERE.parent / "cash/tokens.css").read_text() + """
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}h1{font-size:25px;line-height:1.25;margin:0 0 10px;font-weight:650}h2{font-size:19px;margin:36px 0 6px;font-weight:650}h3{font-size:15.5px;margin:0 0 4px;font-weight:650}
p{margin:0 0 10px;max-width:78ch}.lede{color:var(--ink-2);font-size:16px}a{color:var(--link)}.note{font-size:13px;color:var(--muted)}
.card,.co{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}.co{scroll-margin-top:12px}.co:target{outline:2px solid var(--s1)}
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:16px 0}.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px}.tile b{display:block;font-size:24px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.2}.tile span{font-size:13px;color:var(--ink-2)}
.st{display:grid;grid-template-columns:230px minmax(0,1fr) 260px;gap:0 16px;align-items:center;padding:8px 0;border-bottom:1px solid var(--grid)}.st:last-child{border:0}.g b{display:block;font-size:14px}.g span,.o{font-size:12.5px;color:var(--ink-2)}
.b{display:flex;align-items:center;gap:8px;min-width:0}.fill{height:20px;background:var(--s1);border-radius:4px;min-width:3px}.b b{font-size:18px;font-variant-numeric:tabular-nums}.zero{font-size:18px;font-weight:650;color:var(--muted)}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;min-width:720px}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--grid);vertical-align:top}thead th{font-size:12.5px;color:var(--ink-2);border-bottom:1px solid var(--axis);font-weight:600}tbody th{font-weight:600}tbody th span{font-weight:400;color:var(--ink-2);display:block;font-size:12px}.num{text-align:right;font-variant-numeric:tabular-nums}
.c{white-space:nowrap}.c.pass{font-weight:600}.c.fail{font-weight:650;color:var(--s2)}.c.none{color:var(--muted)}
.tk{font-weight:500;color:var(--muted);font-size:13px}.res{font-size:12px;font-weight:600;border:1px solid var(--axis);border-radius:999px;padding:1px 9px;margin-left:6px;white-space:nowrap}.lead{color:var(--ink-2);font-size:13.5px}
.book{position:relative;height:34px;border-radius:6px;background:var(--s0);margin:30px 0 16px}.tick{position:absolute;top:-6px;bottom:-6px;width:2px;background:var(--ink)}.tick span{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);font-size:12px;white-space:nowrap;color:var(--ink-2)}.booklabel{color:#fff;font-weight:650;position:absolute;right:12px;top:6px;font-size:14px}
@media (max-width:760px){.st{grid-template-columns:1fr;gap:4px}.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}h1{font-size:22px}}
"""

PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Demo portfolio</title><style>{CSS}</style></head><body><main>
<h1>No idea passed every gate, so the demo portfolio stays $100,000 in cash.</h1>
<p class="lede">The screen proposed five US candidates. Four fell at Gate 1 and one at Gate 2. No thesis or skeptic's review ran, because nothing reached them. A lesson on paper with made-up money, not advice.</p>
<div class="tiles"><div class="tile"><b>{lead_rows}</b><span>Lead rows on the radar</span></div><div class="tile"><b>5</b><span>Tested, by the pick rule</span></div><div class="tile"><b>0</b><span>Positions</span></div><div class="tile"><b>${cash:,.0f}</b><span>Cash, {share:.0%} of the portfolio (calc.)</span></div></div>

<h2>The funnel, from leads to positions</h2>
<p class="note">Bars to scale. From the <a href="sensors/radar/runs/2026-11-03-03.json">radar's run of Nov. 3, 2026</a>. Leads are things to read, never picks. Details: <code>Research/2026-11-03 Hunt triage.md</code>.</p>
<div class="card">{funnel}</div>

<h2>Where each candidate stopped</h2>
<p class="note">A company stops at its first failed gate. A rejection means no research hours for now. It does not say a stock will fall, and it is not a sell. Gates are from <code>Research/2026-11-03 Triage.md</code>.</p>
<div class="card tw"><table><thead><tr><th scope="col">Candidate</th><th scope="col" class="num">Rise ÷ revenue (calc.)</th><th scope="col">Gate 1</th><th scope="col">Gate 2</th><th scope="col">Gate 3</th><th scope="col">Thesis</th><th scope="col">Skeptic</th><th scope="col" class="num">Money</th></tr></thead><tbody>{grid}</tbody></table></div>
{cards}

<h2>The portfolio and its cash</h2>
<p class="note">From <code>Portfolio/Paper portfolio.md</code>, sized by <code>pm.py</code>. Made-up money. It says nothing about what I really own.</p>
<div class="card"><div class="book" role="img" aria-label="Cash is 100% of the portfolio. The normal line is at 15% and the floor at 5%."><div class="tick" style="left:5%"><span>Floor 5%</span></div><div class="tick" style="left:15%"><span>Normal 15%</span></div><span class="booklabel">Cash {share:.0%}</span></div>
<p>Level: <b>above normal</b>, on <code>Rules/cash.md</code> (over 15%). {BOOK["positions"]} positions, {BOOK["groups_count"]} shared groups, {BOOK["bets_with_proposed"]} bets (calc.). With no position there is nothing to size, no exposure to share and no loss if wrong to add up.</p>
<p>0 positions is under the 5 in rule 2, and nothing there forces a buy. If cash stays above 50% for 24 months in a row from Nov. 3, 2026, <code>Rules/cash.md</code> asks whether my search is wide enough. It never loosens the buy test.</p></div>

<h2>My view, taken first</h2>
<p class="note">The coach wrote this down before I saw any result: <code>Journal/decisions/2026-11-03 Demo portfolio.md</code>. On action, today's result fits my words only if "passes" means every gate in <code>Rules/sizing.md</code>. The same no-buy does not test my reason, because two other gates give $0 at any price.</p>
<div class="card"><p><b>Action:</b> {html.escape(said["Action"])}</p><p><b>Size:</b> {html.escape(said["Size"])}</p><p><b>One main reason:</b> {html.escape(said["One main reason"])}</p><p><b>What I then decided:</b> {html.escape(then)}</p></div>

<h2>What this does not say</h2>
<p>It does not say the bars are right, that these stocks will fall, or that no good idea exists. Only 5 of the {ranked} ranked companies were tested. Powell's base is a proposal on reported earnings, and the fit check did not run in full. With 15 leads triaged now and none reaching research (calc., 9 + 1 + 5), this hunt also gives no evidence on how the thesis and skeptic stages work on a new company.</p>
</main></body></html>"""
(ROOT / "demo.html").write_text(PAGE)
print("demo.html", len(PAGE))
