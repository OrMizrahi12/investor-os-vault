"""Coach page: draw coach.html from the decision file, the skill's sums and the valuation run.

    .venv/bin/python -I sensors/coach/draw.py
    .venv/bin/python -I sensors/coach/test_coach.py
    .venv/bin/python -I sensors/coach/test_guard.py

No network. Keep the page on this computer: it holds a Yahoo price. A lesson, not advice.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SK = ROOT / ".claude/skills/portfolio-manager"
sys.path.insert(0, str(SK / "scripts"))
import pm  # noqa: E402

LOG = (ROOT / "Journal/decisions/2026-11-03 Corning.md").read_text()
g = pm.run(json.loads((SK / "assets/corning-2026-11-03.json").read_text()), "Portfolio/Paper portfolio.md")["rows"][0]
RUN = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
HIGH = RUN["base"]["high"]
ACTION = re.search(r"\*\*Action:\*\* (.+)", LOG)[1]
SIZE = re.search(r"\*\*Size:\*\* (.+)", LOG)[1]
REASON = re.search(r"\*\*One main reason:\*\* (.+)", LOG)[1]
assert LOG.index("## My view") < LOG.index("## The system's view")
assert (g["action"], g["size_usd"]) == ("no position", 0)
assert set(g["gates"].values()) == {False}

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
SRC_PRICE = f'<a href="{YAHOO}">close of Nov. 2, 2026, Yahoo through yfinance, fetched Nov. 2, 2026</a>'
SRC_RUN = "<code>sensors/valuation/runs/2026-11-03-01.md</code>, Nov. 3, 2026"
Q10 = '<a href="https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm">10-Q, filed Oct. 29, 2026</a>'


def m(v):
    return f"${v:,.2f}"


def box(x, y, title, lines, cls="node"):
    w, h = 215, 92
    on = ' class="on"' if cls == "node hit" else ""
    sub = ' class="on sub"' if cls == "node hit" else ' class="sub"'
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>',
           f'<text class="{"on" if on else "ttl"}" x="{x + 14}" y="{y + 26}" font-weight="650">{title}</text>']
    out += [f'<text{sub} x="{x + 14}" y="{y + 49 + 19 * i}">{t}</text>' for i, t in enumerate(lines)]
    return "".join(out)


def arrow(x1, y1, x2, y2, cls="edge"):
    return f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#head)"/>'


def flow():
    t, b = 50, 196
    o = ['<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="tip"/></marker></defs>']
    o.append(box(10, t, "About to decide", ["buy, add, hold, trim,", "sell or pass"]))
    o.append(box(265, t, "The coach asks three", ["action, size, one reason", "It has read nothing"]))
    o.append(box(520, t, "Your view is written", ["in Journal/decisions/", "Fixed from here on"], "node hit"))
    o.append(box(775, t, "The skill runs", ["portfolio-manager reads", "the vault, pm.py sums"]))
    o.append(box(775, b, "Compare four lines", ["action, size, reason,", "what would change it"]))
    o.append(box(520, b, "Log both", ["one dated file", "says why they differ"]))
    o.append(box(265, b, "You decide", ["Only your words go", "under your decision"]))
    o.append(box(10, b, "Never touched", ["no trade, no Portfolio/,", "no company note"], "node off"))
    for x1, x2 in ((225, 265), (480, 520)):
        o.append(arrow(x1, t + 46, x2 - 2, t + 46))
    o.append(arrow(735, t + 46, 773, t + 46))
    o.append(arrow(882, t + 92, 882, b - 2))
    o.append(arrow(775, b + 46, 737, b + 46))
    o.append(arrow(520, b + 46, 482, b + 46))
    o.append(f'<line class="gate" x1="755" x2="755" y1="26" y2="{t + 92}"/>')
    o.append(f'<text class="lv" x="745" y="30" text-anchor="end">The guard blocks all reading before this line</text>')
    o.append(f'<path class="edge dash" d="M372 {t + 92}V{t + 112}H117V{t + 94}" marker-end="url(#head)"/>')
    o.append(f'<text class="ax" x="245" y="{t + 128}" text-anchor="middle">An answer is missing: it returns only the questions</text>')
    return f'<div class="scroll"><svg viewBox="0 0 1000 300" role="img" aria-label="Flow: you are about to decide, the coach asks three questions having read nothing, your view is written and fixed, the guard then allows reading, the skill runs, the two views are compared, both are logged, and you decide. No trade, Portfolio or company note is touched.">{"".join(o)}</svg></div>'


def price_chart():
    x0, x1, top = 20, 980, 140
    sx = lambda v: x0 + (x1 - x0) * v / top
    o = []
    for t in range(0, 141, 20):
        o.append(f'<line class="grid" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="60" y2="98"/><text class="ax" x="{sx(t):.1f}" y="116" text-anchor="middle">${t}</text>')
    o.append(f'<rect class="b1" x="{sx(g["base_low"]):.1f}" y="70" width="{sx(HIGH) - sx(g["base_low"]):.1f}" height="18" rx="4"/>')
    for v, lab, y, anchor in ((g["base_mid"], "Base middle", 6, "start"), (g["buy_below"], "Buy-below", 26, "start"), (g["trim_above"], "Trim-above", 46, "start"), (g["price"], "Price", 46, "end")):
        x = sx(v)
        o.append(f'<line class="mk" x1="{x:.1f}" x2="{x:.1f}" y1="{y + 6}" y2="92"/>')
        tx = x + (6 if anchor == "start" else -6)
        o.append(f'<text class="lv halo" x="{tx:.1f}" y="{y + 10}" text-anchor="{anchor}">{lab} {m(v)}</text>')
    return f'<div class="scroll"><svg viewBox="0 0 1000 122" role="img" aria-label="Corning: base value {m(g["base_low"])} to {m(HIGH)}, buy-below {m(g["buy_below"])}, trim-above {m(g["trim_above"])}, price {m(g["price"])}.">{"".join(o)}</svg></div>'


CSS = (ROOT / "sensors/cash/tokens.css").read_text() + """
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}
h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
h3{font-size:15px;margin:0 0 6px;font-weight:650}
p,ul.txt{margin:0 0 10px;max-width:75ch}ul.txt{padding-left:20px}ul.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
code{font-size:.92em}
.note{font-size:13.5px;color:var(--muted)}
.tag{display:inline-block;border:1px solid var(--axis);border-radius:5px;padding:1px 8px;font-size:13px;margin-bottom:12px;color:var(--ink-2)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:80ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:6px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.two .card{margin:0}
.big{font-size:17px;font-weight:650;margin:0 0 6px}
.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:620px;height:auto;font:15px system-ui,-apple-system,"Segoe UI",sans-serif}
svg text{fill:var(--ink-2)}svg .lv{fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}svg .ax{fill:var(--muted);font-size:13.5px}svg .on{fill:#fff}svg .sub{font-size:14px}svg .ttl{fill:var(--ink)}
svg .halo{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
.grid{stroke:var(--grid);stroke-width:1}.mk{stroke:var(--ink-2);stroke-width:1.5}.b1{fill:var(--s1)}
.node{fill:var(--surface);stroke:var(--axis);stroke-width:1.25}.node.hit{fill:var(--s1);stroke:var(--s1)}.node.off{fill:none;stroke-dasharray:5 4}
.edge{stroke:var(--ink-2);stroke-width:1.5;fill:none}.dash{stroke-dasharray:5 4}.tip{fill:var(--ink-2)}.gate{stroke:var(--ink);stroke-width:2.5}
figure{margin:0}figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:85ch}
.steps{display:none;margin:0;padding-left:20px}.steps li{margin-bottom:6px}
@media (max-width:680px){.flowsvg{display:none}.steps{display:block}}
.wrap{overflow-x:auto;margin-top:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600}
.wide{min-width:720px}
.end{font-size:17px;font-weight:650;margin-top:28px}
footer{margin-top:18px;font-size:13px;color:var(--muted);max-width:85ch}
"""

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Decision Coach</title>
<style>{CSS}</style></head><body><main>
<span class="tag">Lesson, not advice. Paper portfolio. Nothing here is a trade.</span>
<h1>You and the system both say no position on Corning, for reasons that are not the same</h1>
<p class="lede">The coach takes your view first, then runs the <code>portfolio-manager</code> skill and logs both. Written Nov. 3, 2026, on the Nov. 2 close.</p>

<div class="answer"><ul>
<li><strong>Same action, same size:</strong> no position, $0.</li>
<li><strong>Different reason:</strong> you named the price against value. The system fails three gates, and that is only one of them.</li>
<li><strong>Different trigger:</strong> you would wait for the buy-below. The rules also need a recorded thesis and your ruling that it survived the skeptic.</li>
<li><strong>The review:</strong> the Nov. 2 no-buy was sound but narrow. Its reason said nothing about Corning, and that reason ran out on Nov. 3 while the decision kept its old date. This is Claude's reading, for you to correct.</li>
</ul></div>

<h2>The flow: your view is on file before anything is shown</h2>
<p>A guard enforces the order on the coach's own tools. It cannot stop the session that called the coach from showing you something first. The coach's first call on Corning was the write of your view.</p>
<figure class="card">
<div class="flowsvg">{flow()}</div>
<ol class="steps">
<li>You are about to decide: buy, add, hold, trim, sell or pass.</li>
<li>The coach asks three things: action, size, one main reason. It has read nothing. If an answer is missing, it returns only the questions.</li>
<li><b>Your view is written in <code>Journal/decisions/</code> and fixed from here on.</b> The guard blocks all reading before this point.</li>
<li>The <code>portfolio-manager</code> skill runs.</li>
<li>The coach compares four lines: action, size, reason, what would change it.</li>
<li>It logs both in one dated file, and says why they differ.</li>
<li>You decide. Only your words go under your decision.</li>
</ol>
<p class="note steps">Never touched: no trade, no <code>Portfolio/</code>, no company note.</p>
<figcaption>The guard is <code>.claude/hooks/coach-guard.py</code>. The first write may hold only your view, and later edits cannot change it. A subagent cannot talk to you while it runs, so the main session asks the three questions and passes your words on.</figcaption>
</figure>

<h2>Your view against the system's</h2>
<div class="two">
<div class="card"><h3>Your view, written first</h3>
<p class="big">{ACTION}, {SIZE}</p>
<p>"{REASON}"</p>
<p class="note">Your words, from <code>Journal/decisions/2026-11-03 Corning.md</code>.</p></div>
<div class="card"><h3>The system's view</h3>
<p class="big">No position, $0</p>
<p>All three gates fail: no thesis recorded, no ruling that it survived the skeptic, and a price not under the buy-below.</p>
<p class="note">Paper portfolio. Cash stays $100,000 (calc., <code>pm.py</code>, Nov. 3, 2026). Nothing real is on file.</p></div>
</div>
<div class="wrap"><table class="wide">
<thead><tr><th scope="col">Line</th><th scope="col">You</th><th scope="col">The system</th><th scope="col">Result</th><th scope="col">Why</th></tr></thead>
<tbody>
<tr><th scope="row">Action</th><td>{ACTION}</td><td>No position</td><td>Same</td><td>The same word on different grounds.</td></tr>
<tr><th scope="row">Size</th><td>{SIZE}</td><td>$0</td><td>Same</td><td>The system's $0 comes from the gates.</td></tr>
<tr><th scope="row">Reason</th><td>Price far above worth, on our numbers</td><td>Three gates fail</td><td>Differs: rule, and scope</td><td>Your reason matches gate 3. "Any "no" means no position" (<code>Rules/sizing.md</code>). The method also stops short of "worth": the session approving it says it does not say "that Corning is overpriced or will fall" (Journal, Nov. 3, 2026).</td></tr>
<tr><th scope="row">What would change it</th><td>The buy-below</td><td>A recorded thesis, your ruling, and a price under a refreshed buy-below</td><td>Differs: rule</td><td>"Being under it is required, and it is not enough: a thesis and the skeptic's review still come first" (<code>Rules/when-to-buy.md</code>). Your words do not say whether the other two are part of your view, so nothing is read into them.</td></tr>
</tbody></table></div>

<figure class="card">
{price_chart()}
<figcaption>The bar is base value, low to high. Coverage is {g["coverage_pct"]:.1f}%, against the 75% bar (calc., {SRC_RUN}, on the {Q10}). Price: {SRC_PRICE}. It was not refreshed, since only you run that sensor. Low coverage bars a buy and says nothing else.</figcaption>
</figure>

<div class="answer"><p><strong>The agreement is thin.</strong> It does not test your reason: gates 1 and 2 alone would still give $0 with the price under the buy-below. It is not a second look at value either, because you said "on our numbers" and the system uses the same numbers.</p>
<p><strong>The one question:</strong> if the price were under a refreshed buy-below tomorrow, with the thesis still a draft and the skeptic's ruling unchanged, would you still want no position? The rules already set the system's answer: no position.</p></div>
<p class="note"><strong>Your answer, Nov. 3, 2026:</strong> "Yes, I would still want no position." So the buy-below alone would not move you, and your words do not say what would. Also on file: your rerun of the skeptic with the fixed guard is due, and it did not run here.</p>

<h2>The review: Corning no-buy of Nov. 2, 2026</h2>
<p><strong>The decision:</strong> "We decided not to buy Corning today" (Journal, Nov. 2, 2026). It is the first investing decision in the Journal. <strong>The limit of this review:</strong> the decision is one day old, so it tests the reasoning only and can say nothing about results.</p>
<div class="two">
<div class="card"><h3>What we knew then</h3><ul class="txt">
<li>Base value was not defined, so no share of the price could be shown.</li>
<li>No thesis was written.</li>
<li>No holdings were on file.</li>
<li>Price and earnings history was on file that day: the price up 3.6 times in ten years, with no steady trend in earnings (<code>corning-price-vs-eps.html</code>, retrieved Nov. 2, 2026). The Journal does not say if it came before the decision, and the decision does not use it.</li>
</ul></div>
<div class="card"><h3>What has changed since</h3><ul class="txt">
<li><b>Our knowledge, all on Nov. 3:</b> base value {m(g["base_low"])} to {m(HIGH)}, coverage {g["coverage_pct"]:.1f}% (calc., {SRC_RUN}). A thesis draft and nine kill lines, none crossed (<code>Research/2026-11-03 Corning kill criteria.md</code>, Nov. 3, 2026). A skeptic's review, and your ruling that the idea did not survive, for now (Journal, Nov. 3, 2026).</li>
<li><b>The business, on file: nothing new.</b> The newest 10-Q on the saved SEC list is still the {Q10}. That list was last saved Nov. 2.</li>
<li><b>The price:</b> nothing newer is saved than the Nov. 2 close. It plays no part in the verdict below.</li>
</ul></div>
</div>

<h3 style="margin-top:18px">Was the reasoning sound? Yes, but narrow. Claude's reading, for you to correct.</h3>
<div class="wrap"><table class="wide">
<thead><tr><th scope="col">Test</th><th scope="col">Reading</th><th scope="col">Why</th></tr></thead>
<tbody>
<tr><th scope="row">Did it follow the rule?</th><td>Yes</td><td>With no base value, <code>when-to-buy</code> allows no buy recommendation. That was the whole reason.</td></tr>
<tr><th scope="row">Did it claim only what it knew?</th><td>Yes</td><td>It said "not a view that Corning is a bad business or too expensive". It could have leaned on the price history, and it did not. The {g["coverage_pct"]:.1f}% came a day later, so it could not have backed such a claim on Nov. 2.</td></tr>
<tr><th scope="row">Could it be reopened?</th><td>Yes</td><td>It named the event, "We build the valuation method", and that happened on Nov. 3. It did not name a recorded thesis, though it noted none was written.</td></tr>
<tr><th scope="row">Did it test Corning?</th><td>No</td><td>The same reason would have stopped any company that day. So the later coverage figure earns it no credit: it was right about the method's absence, not about Corning.</td></tr>
<tr><th scope="row">Was the reason kept current?</th><td>Partly</td><td>The method was approved on Nov. 3, and the reason ran out. A search of the Journal found no entry saying the reopen condition was met. 103 sessions before this one name the Corning decision, most often to say it stands (calc., a text count of both files). The new reasons appear only in passing: "Coverage is under 75% and no thesis is written", in the price against value panel session.</td></tr>
<tr><th scope="row">Is it clear what it was?</th><td>Partly</td><td>It says "we decided not to buy". Later entries call it a "no buy recommendation". Under your rules Claude recommends and you decide, and that entry does not say which it was.</td></tr>
</tbody></table></div>

<h3 style="margin-top:18px">Whatever the price did</h3>
<p>The verdict uses no price, so no price move can change it. If Corning had doubled on Nov. 3, halved, or dropped under today's buy-below, on Nov. 2 there was still no base value to compare it with. The reasoning would be just as sound and just as narrow.</p>
<p><strong>Your reason today could not have been given on Nov. 2.</strong> "On our numbers" needs numbers, and those came a day later. So the action stayed the same while the reason under it changed, which the date on the decision hides. <strong>A proposal, not adopted:</strong> when a decision's reopen event happens, write one entry saying so and giving the new reason.</p>

<h2>What went wrong while building this</h2>
<p>The coach's first live run locked itself out of its own log, because of a fault in my guard. Testing a whole run then found a second fault. Your view was written first and did not change. Both are fixed, and the coach then saved its own log. See <code>Lessons/Test a guard through a whole run.md</code>.</p>
<ul class="txt">
<li>The guard blocked 12 calls in the first run: 7 Bash, 3 Read and 2 Edit (a count of the run's record).</li>
<li>The log's word "blind" overstated things, because the coach had read your words. Its input file matches the dated asset exactly, so your words moved no input. The log carries the correction.</li>
<li><strong>Not yet tested:</strong> a fresh coach run on the fixed guard from start to finish. Only the second half ran live, and the rest ran in <code>sensors/coach/test_guard.py</code>.</li>
<li><strong>Routed on your yes, Nov. 3, 2026:</strong> <code>Rules/recommendations.md</code> sends every recommendation through the coach, and the <code>portfolio-manager</code> skill stops without a view on file. These are instructions, not a lock: no hook blocks the skill yet.</li>
</ul>

<p class="end">The decision is yours.</p>
<footer>Stays on this computer, since it holds a Yahoo price. All sums are calc. No order was placed, and <code>Portfolio/</code>, <code>Companies/</code> and <code>Rules/</code> did not change.</footer>
</main></body></html>
"""
(ROOT / "coach.html").write_text(PAGE)
print("wrote coach.html")
