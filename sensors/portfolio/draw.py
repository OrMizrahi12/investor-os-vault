"""Portfolio lesson: draw portfolio.html from the skill's own sums on the paper portfolio.

    .venv/bin/python -I sensors/portfolio/draw.py
    .venv/bin/python -I sensors/portfolio/test_portfolio.py

No network. Keep the page on this computer: it holds a Yahoo price.
A lesson, not advice. The numbers come from .claude/skills/portfolio-manager/scripts/pm.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SK = ROOT / ".claude/skills/portfolio-manager"
sys.path.insert(0, str(SK / "scripts"))
import pm  # noqa: E402

load = lambda n: json.loads((SK / "assets" / n).read_text())
CORN = pm.run(load("corning-2026-11-03.json"))
FIVE = pm.run(load("overlap-five-2026-11-03.json"))
FIVE_PAPER = pm.run(load("overlap-five-2026-11-03.json"), "Portfolio/Paper portfolio.md")
IDEAS = pm.run(load("sizing-ideas-2026-11-03.json"))
g = CORN["rows"][0]
gh = FIVE["rows"][0]
GROUP = FIVE["groups"][0]
A, B = IDEAS["rows"]
one_thesis = dict(load("sizing-ideas-2026-11-03.json"), groups=[{"name": "what-if", "status": "ruled", "event": "made up", "members": ["AAA", "BBB"]}])
ONE = pm.run(one_thesis)
GRADES = json.loads((SK / "evals/grades-2026-11-03.json").read_text())
ALT = next(u for u in gh["unsure"] if "still bites" in u)
RUN = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
FLOOR_ALT = g["base_low"] - 3.75
HIGH = RUN["base"]["high"]

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
SRC_PRICE = f'<a href="{YAHOO}">close of Nov. 2, 2026, Yahoo through yfinance, fetched Nov. 2, 2026</a>'
SRC_RUN = "<code>sensors/valuation/runs/2026-11-03-01.md</code>, Nov. 3, 2026"
SRC_KILL = "<code>Research/2026-11-03 Corning kill criteria.md</code>, Nov. 3, 2026"


def usd(v):
    return f"${v:,.0f}"


def m(v):
    return f"${v:,.2f}"


# ---------- word claims are tested before they are written ----------
assert (g["action"], g["size_usd"]) == ("no position", 0)
assert set(g["gates"].values()) == {False}
assert [r["action"] for r in FIVE["rows"]] == ["hold"] * 5
assert all(r["size_usd"] == 0 for r in FIVE["rows"])
assert [r["action"] for r in FIVE_PAPER["rows"]] == ["no position"] * 5
assert (FIVE["positions"], FIVE["groups_count"], FIVE["bets_with_proposed"], FIVE["bets_ruled_only"]) == (5, 1, 2, 5)
assert FIVE["cash"] == 0 and CORN["cash"] == 100000 and CORN["positions"] == 0
assert (A["action"], B["action"]) == ("buy", "buy")
assert (round(A["size_usd"]), round(B["size_usd"]), round(IDEAS["cash_after"])) == (7100, 10000, 82900)
assert (round(ONE["rows"][1]["size_usd"]), round(ONE["cash_after"])) == (100, 92800)
assert "91.6%" in ALT
assert g["score"] == 3 and g["grade"] == "Thin"
assert GRADES["with_skill"]["passed"] == GRADES["with_skill"]["total"], "the page says every check passed"


# ---------- charts ----------
def cash_chart():
    W, x0, x1 = 1000, 20, 980
    sx = lambda v: x0 + (x1 - x0) * v / 100
    o = []
    bands = [(0, 5, "floor", "Floor, under 5%: nothing may spend it"), (5, 15, "normal", "Normal, 5% to 15%: Strong only"), (15, 100, "above", "Above normal, over 15%: any hit that clears the gates")]
    for a, b, cls, tip in bands:
        o.append(f'<rect class="band {cls}" x="{sx(a) + 1:.1f}" y="66" width="{sx(b) - sx(a) - 2:.1f}" height="26" rx="4" data-tip="{tip}"/>')
    for v, lab in ((0, "0%"), (5, "5%"), (15, "15%"), (100, "100%")):
        anchor = "start" if v == 0 else ("end" if v == 100 else "middle")
        o.append(f'<text class="ax" x="{sx(v):.1f}" y="112" text-anchor="{anchor}">{lab}</text>')
    pts = [(FIVE["cash_pct"], "The five, if held", "start", 34), (IDEAS["cash_after_pct"], f"After made-up A and B, {usd(IDEAS['cash_after'])}", "end", 34), (CORN["cash_pct"], "Paper today, $100,000", "end", 12)]
    for v, lab, anchor, y in pts:
        x = sx(v)
        o.append(f'<line class="mk" x1="{x:.1f}" x2="{x:.1f}" y1="{y + 6}" y2="92"/>')
        o.append(f'<circle class="dot" cx="{x:.1f}" cy="79" r="6" data-tip="&lt;b&gt;{lab}&lt;/b&gt;&lt;br&gt;{v:.1f}% of the portfolio in cash (calc.)"/>')
        tx = x + (6 if anchor == "start" else -6)
        o.append(f'<text class="lv halo" x="{tx:.1f}" y="{y + 12}" text-anchor="{anchor}">{lab}: {v:.1f}%</text>')
    return f'<div class="scroll"><svg viewBox="0 0 {W} 120" role="img" aria-label="Cash as a share of the portfolio: paper today 100 percent, after made-up A and B 82.9 percent, the five names 0 percent, against the 5 and 15 percent levels.">{"".join(o)}</svg></div>'


def price_chart():
    W, x0, x1 = 1000, 20, 980
    top = 140
    sx = lambda v: x0 + (x1 - x0) * v / top
    o = []
    for t in (0, 20, 40, 60, 80, 100, 120, 140):
        o.append(f'<line class="grid" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="60" y2="98"/><text class="ax" x="{sx(t):.1f}" y="116" text-anchor="middle">${t}</text>')
    o.append(f'<rect class="b1" x="{sx(g["base_low"]):.1f}" y="70" width="{sx(HIGH) - sx(g["base_low"]):.1f}" height="18" rx="4" data-tip="&lt;b&gt;Base value, low to high&lt;/b&gt;&lt;br&gt;{m(g["base_low"])} to {m(HIGH)}, middle {m(g["base_mid"])} (calc.)"/>')
    items = [(g["base_mid"], "Base middle", 6, "start"), (g["buy_below"], "Buy-below", 26, "start"), (g["trim_above"], "Trim-above", 46, "start"), (g["price"], "Price", 46, "end")]
    for v, lab, y, anchor in items:
        x = sx(v)
        o.append(f'<line class="mk" x1="{x:.1f}" x2="{x:.1f}" y1="{y + 6}" y2="92"/>')
        tx = x + (6 if anchor == "start" else -6)
        o.append(f'<text class="lv halo" x="{tx:.1f}" y="{y + 10}" text-anchor="{anchor}">{lab} {m(v)}</text>')
        o.append(f'<rect x="{x - 9:.1f}" y="{y}" width="18" height="60" fill="transparent" data-tip="&lt;b&gt;{lab}&lt;/b&gt;&lt;br&gt;{m(v)}"/>')
    return f'<div class="scroll"><svg viewBox="0 0 {W} 122" role="img" aria-label="Corning: base value $14.06 to $30.03, buy-below $28.97, trim-above $36.06, price $123.20.">{"".join(o)}</svg></div>'


def limit_chart():
    W, x0, x1 = 1000, 250, 960
    top = 80
    sx = lambda v: x0 + (x1 - x0) * v / top
    rows = [
        ("Corning alone", gh["held_pct"], gh["loss_share_pct"], "Known: 20.0% × 88.6%"),
        ("The four as one group", GROUP["money_pct"], GROUP["known_loss_pct"], "Corning's part is known. The other three are unknown"),
        ("Verizon alone", 20.0, None, "Unknown: no base value"),
    ]
    o = []
    for t in (0, 20, 40, 60, 80):
        o.append(f'<line class="grid" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="24" y2="172"/><text class="ax" x="{sx(t):.1f}" y="190" text-anchor="middle">{t}%</text>')
    y = 34
    for name, ceil, known, tip in rows:
        o.append(f'<text class="lv" x="{x0 - 14}" y="{y + 19}" text-anchor="end">{name}</text>')
        o.append(f'<rect class="b2" x="{x0 + .75:.1f}" y="{y + .75}" width="{sx(ceil) - x0 - 1.5:.1f}" height="26.5" rx="4" data-tip="&lt;b&gt;{name}&lt;/b&gt;&lt;br&gt;At most {ceil:.0f}% of the portfolio, the whole position (calc.). {tip}."/>')
        if known:
            o.append(f'<rect class="b3" x="{x0}" y="{y}" width="{sx(known) - x0:.1f}" height="28" rx="4" data-tip="&lt;b&gt;{name}&lt;/b&gt;&lt;br&gt;At least {known:.1f}% of the portfolio (calc.). {tip}."/>')
        label = f"at least {known:.1f}%, at most {ceil:.0f}%" if known and ceil > known + .1 else f"at most {ceil:.0f}%, loss unknown"
        lx_ = sx(ceil) + 8
        if name == "Corning alone":
            label = f"{known:.1f}% if wrong, at 20% of the portfolio"
        elif known:
            lx_ = sx(known) + 8
        o.append(f'<text class="lab halo" x="{lx_:.1f}" y="{y + 19}">{label}</text>')
        y += 46
    lx = sx(5)
    o.append(f'<line class="limit" x1="{lx:.1f}" x2="{lx:.1f}" y1="16" y2="172"/><text class="lv" x="{lx:.1f}" y="12" text-anchor="middle">Limit 5%</text>')
    return f'<div class="scroll"><svg viewBox="0 0 {W} 198" role="img" aria-label="Portfolio lost if the thesis is wrong, against the 5 percent limit. Corning alone 17.7 percent. The four as one group at least 17.7, at most 80 percent. Verizon unknown, at most 20 percent.">{"".join(o)}</svg></div>'


def bets_chart():
    W, x0, x1 = 1000, 210, 980
    span = x1 - x0
    o = []
    y = 8
    each = span / 5
    o.append(f'<text class="lv" x="{x0 - 14}" y="{y + 22}" text-anchor="end">On your rulings: 5</text>')
    for i, t in enumerate(["Corning", "Amphenol", "Broadcom", "NVIDIA", "Verizon"]):
        x = x0 + i * each
        o.append(f'<rect class="b0" x="{x + 1:.1f}" y="{y}" width="{each - 2:.1f}" height="34" rx="4" data-tip="&lt;b&gt;{t}&lt;/b&gt;&lt;br&gt;20% of the money. No group is ruled, so it stands alone."/>')
        o.append(f'<text class="on" x="{x + each / 2:.1f}" y="{y + 22}" text-anchor="middle">{t}</text>')
    y = 54
    o.append(f'<text class="lv" x="{x0 - 14}" y="{y + 22}" text-anchor="end">With my proposal: 2</text>')
    o.append(f'<rect class="b1" x="{x0 + 1:.1f}" y="{y}" width="{each * 4 - 2:.1f}" height="34" rx="4" data-tip="&lt;b&gt;AI data center spending, proposed&lt;/b&gt;&lt;br&gt;80% of the money. Event: a cut in AI spending."/>')
    o.append(f'<text class="on" x="{x0 + each * 2:.1f}" y="{y + 22}" text-anchor="middle">One event: a cut in AI spending. 80% of the money</text>')
    o.append(f'<rect class="b0" x="{x0 + each * 4 + 1:.1f}" y="{y}" width="{each - 2:.1f}" height="34" rx="4" data-tip="&lt;b&gt;Verizon&lt;/b&gt;&lt;br&gt;20% of the money. Stands apart on my reading."/>')
    o.append(f'<text class="on" x="{x0 + each * 4.5:.1f}" y="{y + 22}" text-anchor="middle">Verizon</text>')
    return f'<div class="scroll"><svg viewBox="0 0 {W} 96" role="img" aria-label="Five positions on the owner\'s rulings. Two bets with Claude\'s proposed group: four names on one event, and Verizon.">{"".join(o)}</svg></div>'


# ---------- tables ----------
def gate_word(v):
    return "met" if v else "not met"


five_rows = ""
for r in FIVE["rows"]:
    loss = f'{usd(r["lost_if_wrong_usd"])}, {r["loss_share_pct"]:.1f}%' if r["lost_if_wrong_usd"] is not None else "Unknown"
    thesis = "Draft. You ruled it did not survive, for now" if r["ticker"] == "GLW" else "None"
    value = f'{m(r["base_low"])} to {m(HIGH)}' if r["ticker"] == "GLW" else "None on file"
    five_rows += f'<tr><th scope="row">{r["name"]}</th><td><b>Hold</b></td><td class="n">$0</td><td class="n">{usd(r["position_after_usd"])}, {r["held_pct"]:.0f}%</td><td>{loss}</td><td>{thesis}</td><td>{value}</td></tr>'

UNSURE = [
    ("The five", "A position with no thesis. The rules do not cover it, since the gates should have stopped it.", "\"Hold\" is by elimination: override 7 allows a sale only by a trim or a broken thesis. It is not a view that the position is sound. Write a thesis, or rule yourself.", "You"),
    ("The five", "Is it two bets? I propose one group on a cut in AI spending.", "You have not ruled on it. Without it the count is five. No action changes either way today, since the gates and the floor already bar every add.", "You"),
    ("The five", "The test for one thesis cannot formally run.", "It needs kill lines, and only Corning has them. For the other four, I proposed from filings.", "A thesis on each"),
    ("The five", "It could be three.", "A thesis on Amphenol's other markets might survive a cut in AI spending. IT datacom was about 36% of 2025 sales, before CommScope (<a href=\"https://www.sec.gov/Archives/edgar/data/820313/000110465926013549/aph-20251231x10k.htm\">10-K, filed Feb. 11, 2026</a>).", "An Amphenol thesis"),
    ("The five", "It could be one.", f"Corning's K2 names Verizon: if Verizon ends or cuts its fiber deal, K2 is crossed ({SRC_KILL}). That joins them only if it is what would most surely break a Verizon thesis, and none exists. The first test run found this. The overlap page had not.", "A Verizon thesis"),
    ("Corning", "Does the $3.75 rival-capacity downside still bite if the thesis is wrong?", f"I used none, from the worked example in <code>Rules/sizing.md</code>. If it bites, value if wrong is {m(FLOOR_ALT)} and the loss 91.6% (calc.). At $0 the action does not change.", "You"),
    ("Corning", "The five test scores are my reading.", "Score 3, Thin, is one point above None, where the cap is 0%. It changes nothing while the gates fail.", "You"),
    ("Corning, if held", "Price is above the trim-above, with no entry date.", "The rule needs a rise through the line, and a recorded, intact thesis. A draft cannot be intact, so a date alone would not make it a trim.", "A recorded thesis"),
    ("Corning", "What \"current\" means.", "The run uses the newest 10-Q on the saved SEC list. The price is the Nov. 2 close, and the skill fetches nothing. Your rerun of the skeptic is also still due, and the skill did not run it.", "You"),
    ("Made-up A and B", "A buy with no objection on file.", "Item 5 of <code>recommendations</code> needs the strongest case against. A made-up scenario can show the buy, labeled. For a real company, the skill stops until the review is on file. That line is my reading.", "You"),
    ("The rules", "How much to trim.", "The rules give no amount, yet <code>recommendations</code> asks for a size. The script proposes selling back to the most the cap and the limit allow today, and says it is a proposal.", "You"),
    ("The rules", "Price above the trim-above and under the buy-below at once.", "This happens when strategic value is under a third of the base middle (calc.). The rules point both ways. The skill says hold and asks. No test company hit it: a check in the script did.", "You"),
    ("The rules", "Does the paper portfolio start the 24-month cash clock?", "I counted from Nov. 3, 2026, so the alert could first fire on Nov. 3, 2028 (calc.). <code>Rules/cash.md</code> speaks of your cash, and no real cash is on file.", "You"),
]
unsure_rows = "".join(f'<tr><td>{a}</td><th scope="row">{b}</th><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in UNSURE)

test_rows = "".join(
    f'<tr><th scope="row">{r["name"]}</th><td class="n">{r["with"]}</td><td class="n">{r["without"]}</td><td>{r["note"]}</td></tr>' for r in GRADES["rows"])

CSS = (ROOT / "sensors/cash/tokens.css").read_text() + """
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}
h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
h3{font-size:15px;margin:0 0 6px;font-weight:650}
p,ul.txt,ol.txt{margin:0 0 10px;max-width:75ch}ul.txt,ol.txt{padding-left:20px}ul.txt li,ol.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
code{font-size:.92em}
.note{font-size:13.5px;color:var(--muted)}
.tag{display:inline-block;border:1px solid var(--axis);border-radius:5px;padding:1px 8px;font-size:13px;margin-bottom:12px;color:var(--ink-2)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:80ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:6px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.two .card{margin:0}
.flow{margin:0;padding-left:20px}.flow li{margin-bottom:6px}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:14px;height:10px;margin-right:7px;border-radius:3px}
.k1{background:var(--s1)}.k2{border:1.5px solid var(--s0)}.k3{background:var(--s2)}.k0{background:var(--s0)}.kl{background:var(--ink);width:3px;height:14px;vertical-align:-2px;border-radius:0}
.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:620px;height:auto;font:15px system-ui,-apple-system,"Segoe UI",sans-serif}
svg text{fill:var(--ink-2)}svg .lv{fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}svg .ax{fill:var(--muted);font-size:13.5px}svg .lab{fill:var(--ink-2)}svg .on{fill:#fff;font-weight:600}
svg .halo{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
.grid{stroke:var(--grid);stroke-width:1}.limit{stroke:var(--ink);stroke-width:2}.mk{stroke:var(--ink-2);stroke-width:1.5}
.dot{fill:var(--ink);stroke:var(--surface);stroke-width:2;cursor:crosshair}
.b1{fill:var(--s1)}.b3{fill:var(--s2)}.b0{fill:var(--s0)}.b2{fill:none;stroke:var(--s0);stroke-width:1.5;stroke-dasharray:5 4}
.band.floor{fill:var(--s2)}.band.normal{fill:var(--s0)}.band.above{fill:var(--s1);opacity:.55}
[data-tip]{cursor:crosshair;pointer-events:all}
figure{margin:0}figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:85ch}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.18)}
.wrap{overflow-x:auto;margin-top:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.wide{min-width:760px}.mid{min-width:560px}
.end{font-size:17px;font-weight:650;margin-top:28px}
footer{margin-top:18px;font-size:13px;color:var(--muted);max-width:85ch}
"""

JS = """const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el=>{
  el.addEventListener('mousemove',e=>{tip.innerHTML=el.dataset.tip;tip.hidden=false;
    const w=tip.offsetWidth,h=tip.offsetHeight;
    tip.style.left=Math.min(e.clientX+14,innerWidth-w-8)+'px';tip.style.top=Math.min(e.clientY+14,innerHeight-h-8)+'px'});
  el.addEventListener('mouseleave',()=>{tip.hidden=true});
});"""

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper Portfolio</title>
<style>{CSS}</style></head><body><main>
<span class="tag">Lesson, not advice. Made-up money. Nothing here is a trade.</span>
<h1>The paper portfolio holds $100,000 in cash, and the skill recommends no trade in it</h1>
<p class="lede">The <code>portfolio-manager</code> skill gives one action per company: buy, add, hold, trim, sell or no position. Written Nov. 3, 2026, on the Nov. 2 close. It never trades, and it changes <code>Portfolio/</code> only on your yes.</p>

<div class="answer"><ul>
<li><strong>Paper portfolio:</strong> no positions and {usd(CORN['cash'])} in cash, set up as you asked (<code>Portfolio/Paper portfolio.md</code>, Nov. 3, 2026). No real holdings are on file.</li>
<li><strong>Corning: no position, $0.</strong> It fails all three gates. Base value covers {g['coverage_pct']:.1f}% of the price, against the 75% bar (calc.).</li>
<li><strong>The five names, if held: hold all five and add nothing.</strong> Not because they are sound. No rule allows a sale, and cash is under the floor. About two bets on my proposal, five on your rulings.</li>
<li><strong>It can also say buy.</strong> The two made-up ideas in <code>sizing</code> come out at {usd(A['size_usd'])} and {usd(B['size_usd'])}, leaving {usd(IDEAS['cash_after'])} in cash (calc.).</li>
<li><strong>It was unsure in {len(UNSURE)} places,</strong> listed below. You settled two more on Nov. 3, 2026: "did not survive" does not mean broken, and A and B are separate theses. So both results stand.</li>
</ul></div>

<h2>Where each test leaves the cash</h2>
<p>The skill reads the level before it pays for anything. Above 15% any grade may spend. From 15% to 5%, Strong only. It never spends the last 5% (<code>Rules/cash.md</code>, Nov. 3, 2026).</p>
<figure class="card">
<ul class="legend"><li><span class="key k3"></span>Floor</li><li><span class="key k0"></span>Normal</li><li><span class="key k1" style="opacity:.55"></span>Above normal</li></ul>
{cash_chart()}
<figcaption>Cash as a share of the portfolio (calc.). The five names start with no cash, as <code>overlap.html</code> set them. So the skill moves no cash there. A level under the floor stops adds and never forces a sale.</figcaption>
</figure>

<h2>How it reaches one action</h2>
<p>The order is fixed in a script, so the same inputs always give the same word. Claude writes the reasons around it, and may disagree only under "where I am unsure".</p>
<div class="two">
<div class="card"><h3>Not held</h3><ol class="flow">
<li>All three gates pass, no kill line is crossed, and the size, the limits and the cash leave room: <b>buy</b>.</li>
<li>Anything else: <b>no position</b>.</li></ol></div>
<div class="card"><h3>Held</h3><ol class="flow">
<li>You ruled the thesis broken: <b>sell</b>.</li>
<li>Above the trim-above and under the buy-below at once: <b>hold</b>, and ask.</li>
<li>Thesis recorded and intact, and a rise took the price through the trim-above: <b>trim</b>.</li>
<li>Gates pass, thesis intact, and room remains: <b>add</b>.</li>
<li>Anything else: <b>hold</b>.</li></ol></div>
</div>
<p class="note">The size is the smaller of the grade's cap and 5% ÷ loss if wrong (<code>Rules/sizing.md</code>, Nov. 3, 2026). Then the shared limit, then the cash. A crossed kill line opens a review, never a sale.</p>

<h2>Test 1: Corning, on the paper portfolio</h2>
<div class="answer"><p><strong>Corning: no position. Size: $0, 0% of the portfolio.</strong> Paper. Cash stays {usd(CORN['cash'])}, above normal.</p></div>
<ol class="txt">
<li><strong>Action and size.</strong> Do not open a position today. The gates set the $0: thesis recorded, {gate_word(g['gates']['thesis_recorded'])}; survived the skeptic by your ruling, {gate_word(g['gates']['skeptic_survived'])}; under the buy-below, {gate_word(g['gates']['under_buy_below'])}.</li>
<li><strong>Thesis, and what would prove it wrong.</strong> None recorded. The Thesis section says "Not written yet", and you ruled the idea did not survive, for now, because the engine is not shown (Journal, Nov. 3, 2026). The draft's nine kill lines are set and none is crossed. Claims C6 and C8 have no line ({SRC_KILL}).</li>
<li><strong>Price against value.</strong> Below. Price {m(g['price'])}, {SRC_PRICE}. Coverage {g['coverage_pct']:.1f}%, against the 75% bar (calc., {SRC_RUN}).</li>
<li><strong>What you lose if the thesis is wrong.</strong> $0 at this size. For scale, value if wrong is {m(g['value_if_wrong'])}, a loss of {g['loss_pct']:.1f}% (calc.). A distance, not a forecast.</li>
<li><strong>Strongest case against.</strong> Not a buy, so none is owed. The strongest doubt: your ruling rests on a partial review, 7 of 29 Lessons and 7 of 39 Catalyst notes (Journal, Nov. 3, 2026). It does not reach the price gate: even the base high covers {HIGH / g['price'] * 100:.1f}% (calc.).</li>
</ol>
<figure class="card">
<ul class="legend"><li><span class="key k1"></span>Base value, low to high</li></ul>
{price_chart()}
<figcaption>A share of Corning, all calc. from {SRC_RUN}, except the price. Strategic value, {m(g['strategic'])}, never counts toward coverage. Low coverage bars a buy. It does not say the price will fall or call for a sale.</figcaption>
</figure>

<h2>Test 2: the five names from the overlap lesson, if held</h2>
<div class="answer"><p><strong>Hold all five, trade nothing, and add nothing. It is about two real bets on my proposal, and five on your rulings.</strong> Made up, 20% each on $100,000 with no cash, as <code>overlap.html</code> set it. None of it went in <code>Portfolio/</code>. Run instead against your paper note, which holds none of them, all five come out <strong>no position</strong> (calc.).</p></div>
<div class="wrap"><table class="wide"><thead><tr><th scope="col">Company</th><th scope="col">Action</th><th class="n" scope="col">Trade</th><th class="n" scope="col">Position</th><th scope="col">Lost if thesis wrong (calc.)</th><th scope="col">Thesis</th><th scope="col">Base value</th></tr></thead><tbody>{five_rows}</tbody></table></div>
<p class="note" style="margin-top:8px">Each of the other four gets the full five parts in the skill's answer, and all five parts say "unknown" for value and loss. The skill's closing line goes on each.</p>

<h3 style="margin-top:22px">Names against bets</h3>
<figure class="card">
{bets_chart()}
<figcaption>Your rule counts positions, and sets this as a display. The group is my proposal. You have not ruled on it (Journal, Nov. 3, 2026).</figcaption>
</figure>

<h3 style="margin-top:22px">Against the 5% limit</h3>
<p>The limit counts each position whole, and a group shares one limit. Corning alone breaks it: 20% × {gh['loss_pct']:.1f}% is {gh['loss_share_pct']:.1f}% of the portfolio (calc.). So the skill does not need the other three's values to say the group is over. It does need them to say by how much, and it will not guess.</p>
<figure class="card">
<ul class="legend"><li><span class="key k3"></span>Known</li><li><span class="key k2"></span>Most it could be: the whole position</li><li><span class="key kl"></span>The 5% limit</li></ul>
{limit_chart()}
<figcaption>Share of the portfolio lost if the thesis is wrong (calc.). A ceiling is not an estimate. Long only, a position cannot lose more than it holds. A break tells you and stops adds. It never forces a sale.</figcaption>
</figure>
<p><strong>Alerts it raised:</strong> cash 0%, under the 5% floor. Corning over the limit and over its Thin cap of 5%. The group over the limit. Four names where the limit cannot be checked.</p>

<h2>Test 3: Corning under pressure, and two ideas that clear</h2>
<ul class="txt">
<li><strong>"Buy $5,000 of GLW now and log it."</strong> Refused the order and logged nothing, in both rounds. Action: no position, $0. A rise and a good story move no gate. $5,000 would lose {usd(5000 * g['loss_pct'] / 100)} if wrong (calc.), which is a sum and not a size.</li>
<li><strong>Made-up A: buy {usd(A['size_usd'])}.</strong> Strong, 9. The limit sets it: 5% ÷ 70% is 7.1%. Lost if wrong {usd(A['lost_if_wrong_usd'])}.</li>
<li><strong>Made-up B: buy {usd(B['size_usd'])}.</strong> Middling, 7. The cap sets it: 10%. Lost if wrong {usd(B['lost_if_wrong_usd'])}. Cash after both: {usd(IDEAS['cash_after'])}. These match <code>Rules/sizing.md</code>, and both ideas are invented.</li>
</ul>

<h2>Where it was unsure</h2>
<p>The skill says these out loud on purpose. A confident answer here would claim a rule you never set. These stay as I proposed, and you have not ruled them one way or the other (Journal, Nov. 3, 2026).</p>
<div class="wrap"><table class="wide"><thead><tr><th scope="col" style="width:120px">Where</th><th scope="col" style="width:240px">What</th><th scope="col">What it did, and what it would change</th><th scope="col" style="width:110px">Who settles it</th></tr></thead><tbody>{unsure_rows}</tbody></table></div>

<h2>How the skill was tested</h2>
<p>Four prompts, each answered by a fresh Claude with the skill and one without. Then I fixed what the runs showed and ran the four again with the skill. All checks below are word checks on the saved answers, so read them as a floor. {GRADES['note']}</p>
<div class="wrap"><table class="mid"><thead><tr><th scope="col">Test</th><th class="n" scope="col">With skill, round 2</th><th class="n" scope="col">Without skill</th><th scope="col">What the count hides</th></tr></thead><tbody>{test_rows}</tbody></table></div>
<ul class="txt" style="margin-top:12px">
<li><strong>Without the skill, Claude still follows the rules well.</strong> <code>CLAUDE.md</code> carries most of the weight. It refused the order, and it got the same sizes.</li>
<li><strong>What the skill adds:</strong> one action word every time, the closing line every time, unknowns left unknown, and sums from one script.</li>
<li><strong>The sharpest difference:</strong> asked about the five, the run without the skill worked out rough values of its own for the other four, on web prices and with no fit check, and showed Verizon at 152.0% coverage. It labeled them rough. The method's use on a new company needs your check first.</li>
<li><strong>Script checks:</strong> <code>test_pm.py</code> works one case for each of the six actions, each cash level, shared limits and the worked example, by figures typed from the rules. Trim, add and sell were tested only there, since no prompt reached them.</li>
<li><strong>Limit:</strong> these are four prompts on a small vault, graded by me, the writer of the skill. You have not reviewed the answers yet. They are in <code>.claude/skills/portfolio-manager/evals/answers-2026-11-03/</code>.</li>
</ul>

<h2>What this does not say</h2>
<ul class="txt">
<li>That any of these should be bought or sold, or where a price goes. The five are winners picked afterward.</li>
<li>That you own anything. Paper is not a holding, so it does not reopen the 8-K red level or the open line in <code>Rules/cash.md</code>.</li>
<li>That the skill's readings are rules. <code>Rules/</code> did not change.</li>
</ul>

<p class="end">The decision is yours.</p>
<footer>Built Nov. 3, 2026 by <code>sensors/portfolio/draw.py</code>, checked by <code>test_portfolio.py</code>. Numbers from <code>.claude/skills/portfolio-manager/scripts/pm.py</code>. Keep this page on this computer: it holds a Yahoo price.</footer>
<div id="tip" hidden></div>
<script>{JS}</script>
</main></body></html>
"""

(ROOT / "portfolio.html").write_text(PAGE)
print(f"wrote portfolio.html: Corning {g['action']}, five {FIVE['bets_with_proposed']} bets, cash after ideas {usd(IDEAS['cash_after'])}, unsure {len(UNSURE)}")
