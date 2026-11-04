"""Decisions lesson: draw decisions.html from the Corning valuation run and the saved close.

    .venv/bin/python -I sensors/decisions/draw.py

Pulls nothing. The two cases on the page are made up. Keep the page on this
computer, since it holds a Yahoo price.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "decisions.html"
run = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
LOW, MID = run["base"]["low"], run["base"]["mid"]
BUY, TRIM, STRAT = MID / 0.75, MID + run["strategic"], run["strategic"]
RUN_CLOSE = run["price"]["close"]
with open(ROOT / "sensors/prices/cache/GLW/2026-11-03.csv") as f:
    last = list(csv.DictReader(f))[-1]
assert last["date"] == "2026-11-03"
CLOSE = float(last["close"])

# The made-up cases. Base and lines are held at their Nov. 3, 2026 figures.
SHARES, COST, CASH = 400, 25.0, 90_000
P1, P2 = 100.0, 20.0
AXIS = 140


def usd(x):
    return f"${x:,.0f}"


def px(x):
    return f"${x:,.2f}"


def pct(x):
    return f"{x * 100:.1f}%"


def case(price):
    pos = SHARES * price
    total = CASH + pos
    loss = (price - LOW) / price
    lost = pos * loss
    return dict(price=price, pos=pos, total=total, share=pos / total, cov=MID / price, loss=loss, lost=lost, lost_share=lost / total)


start, c1, c2 = case(COST), case(P1), case(P2)
start_pos = SHARES * COST
keep = int(5 / 90 * 1000) / 10 / 100 * c1["total"]  # 5% / 90 on the grid, floored to 0.1%
sell = c1["pos"] - keep
keep_lost = keep * c1["loss"]
room = 0.10 * c2["total"] - c2["pos"]

Q3 = '<a href="https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm">Q3 release, Oct. 27, 2026</a>'
TENQ = '<a href="https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm">10-Q, filed Oct. 29, 2026</a>'
CALL = '<a href="https://www.fool.com/earnings/call-transcripts/2026/10/27/corning-glw-q3-2026-earnings-call-transcript/">Q3 call, Oct. 27, 2026, third-party transcript, read through a summarizing fetch</a>'
TENK = '<a href="https://www.sec.gov/Archives/edgar/data/24741/000002474126000124/glw-20251231.htm">10-K, filed Feb. 12, 2026</a>'
YAHOO = '<a href="https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&amp;interval=1d">Yahoo through yfinance, saved Nov. 3, 2026</a>'
META = '<a href="https://www.sec.gov/Archives/edgar/data/1326801/000162828026066773/meta-20260930.htm">Meta 10-Q, filed Oct. 22, 2026</a>'
AMZN = '<a href="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000040/amzn-20260930.htm">Amazon 10-Q, filed Oct. 30, 2026</a>'
MSFT = '<a href="https://www.sec.gov/Archives/edgar/data/789019/000119312526436133/msft-20260930.htm">Microsoft 10-Q, filed Oct. 28, 2026</a>'
RUNFILE = "<code>sensors/valuation/runs/2026-11-03-01.md</code>, Nov. 3, 2026"
KILL = "<code>Research/2026-11-03 Corning kill criteria.md</code>, Nov. 3, 2026"
MADE = '<span class="made">Made up</span>'

KILL_ROWS = [
    ("K1", "C2: Signed deals become firm sales.", "Optical net sales for Q4 2027 at or below $2,379M.", "Only Q4 2027, about late Jan. 2028", f"$2,379M, Q3 2026 ({Q3})"),
    ("K2", "C2: Signed deals become firm sales.", "AT&amp;T, Amazon, Lumen, Meta, Microsoft, NVIDIA, Verizon or Zayo ends its deal or says it was reduced, stated by either side with a date.", "Any time", f"None found ({CALL}). Not exhaustive."),
    ("K3", "C3: Corning's pricing and margin hold.", "Optical margin at or below 17.9% for two quarters running, through Q4 2030.", "About late Apr. 2027", f"22.4%, Q3 2026, calc. ({TENQ})"),
    ("K4", "C4: The plan gets met, a target of $27B by 2028 and $35B by 2030.", "Q4 2028 core sales × 4 under $27,000M.", "Only Q4 2028, about late Jan. 2029", f"$20,324M, calc. ({Q3})"),
    ("K5", "C5: Cash follows sales, and customers fund the plants.", "Deposit-out cash for the 12 months to Sept. 30, 2027 under $1,505M.", "Only that period, about late Oct. 2027", f"$1,505M, calc. ({TENK}; {TENQ})"),
    ("K6", "C5: Cash follows sales, and customers fund the plants.", "More than zero shares sold under the $2 billion at-the-market program, in any 10-Q or 10-K.", "Next about Feb. 2027", f"0 through Sept. 30, 2026 ({TENQ})"),
    ("K7", "C7: Optical scale-up starts in 2028.", "Corning names a year after 2028 or drops 2028, or has not said it accelerated by the Q4 2028 call.", "Any call, to about late Jan. 2029", f"\"We continue to believe that strongly\", on 2028 ({CALL})"),
    ("K8", "C2: Signed deals become firm sales.", "Optical net sales lower than the quarter before, two quarters running, through Q4 2030.", "About late Apr. 2027", f"$2,379M, up from $2,072M ({Q3})"),
    ("K9", "C1: Fiber stays short through 2028.", "Combined capital spending of Meta, Amazon and Microsoft lower than the quarter before, two quarters running, through Q4 2030.", "About Apr. 25 to May 2, 2027", f"$150,568M, up from $120,126M, calc. ({META}; {AMZN}; {MSFT})"),
]


def x(v):
    return f"{v / AXIS * 100:.2f}%"


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--s0:#8f8e85;--s1:#2a78d6;--s2:#eb6834;--tint1:rgba(42,120,214,.10);--tint0:rgba(143,142,133,.14)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#77766f;--s1:#3987e5;--s2:#d95926;--tint1:rgba(57,135,229,.16);--tint0:rgba(119,118,111,.20)}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#77766f;--s1:#3987e5;--s2:#d95926;--tint1:rgba(57,135,229,.16);--tint0:rgba(119,118,111,.20)}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}
h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
h3{font-size:16px;margin:0 0 6px;font-weight:650}
p,ul.txt{margin:0 0 10px;max-width:75ch}ul.txt{padding-left:20px}ul.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
a{color:var(--link);overflow-wrap:anywhere}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
code{font-size:.92em;overflow-wrap:anywhere}
.note{font-size:13.5px;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:85ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:5px}
.made{display:inline-block;border:1.5px dashed var(--s2);border-radius:4px;padding:0 6px;font-size:12px;font-weight:650;white-space:nowrap;color:var(--ink)}
.real{display:inline-block;border:1.5px solid var(--s1);border-radius:4px;padding:0 6px;font-size:12px;font-weight:650;white-space:nowrap}
.paper{border:1.5px dashed var(--s2)}
.cases{display:grid;grid-template-columns:1fr 1fr;gap:12px}.cases .card{margin:0;min-width:0}
.verdict{font-weight:650;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
.kv th{font-weight:400;color:var(--ink-2);width:48%}.kv td{font-variant-numeric:tabular-nums}
@media (max-width:760px){.cases{grid-template-columns:1fr}
.stack thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
.stack tr{display:block;padding:10px 0;border-bottom:1px solid var(--axis)}.stack th,.stack td{display:block;border:0;padding:3px 0}
.stack td[data-l]::before{content:attr(data-l);display:block;font-size:12px;color:var(--muted)}}
.chart{position:relative;padding-top:50px;--dot:14px}
.heads{position:absolute;top:0;left:0;right:0;height:48px;z-index:2}
.head{position:absolute;font-size:12.5px;font-weight:650;background:var(--surface);padding:0 4px;white-space:nowrap;font-variant-numeric:tabular-nums}
.head.a{top:0}.head.b{top:22px}
.plot{position:relative}
.band{position:absolute;top:0;bottom:0}.band.lo{background:var(--tint1)}.band.hi{background:var(--tint0)}
.vline{position:absolute;top:-48px;bottom:0;width:0;border-left:2px solid var(--ink)}
.lane{position:relative;padding:10px 0 2px}
.lane .name{position:relative;z-index:1;width:fit-content;max-width:100%;font-size:13.5px;padding:1px 6px;background:var(--surface);border-radius:4px}
.lane .name .made,.lane .name .real{margin-right:4px}
.track{position:relative;height:30px}
.rail{position:absolute;top:50%;left:0;right:0;border-top:1px solid var(--grid)}
.seg{position:absolute;top:calc(50% - 1px);border-top:2px solid var(--c)}
.dot{z-index:1;position:absolute;top:50%;width:var(--dot);height:var(--dot);margin:calc(var(--dot) / -2) 0 0 calc(var(--dot) / -2);border-radius:50%;background:var(--c);box-shadow:0 0 0 2px var(--surface);cursor:crosshair}
.dot.cost{background:var(--surface);border:2px solid var(--c)}
.dot:focus-visible{outline:2px solid var(--link);outline-offset:2px}
.val{position:absolute;top:50%;transform:translate(calc(-100% - 12px),-50%);font-size:13px;font-weight:650;font-variant-numeric:tabular-nums;white-space:nowrap;background:var(--surface);padding:0 3px;border-radius:3px}
.axis{position:relative;height:24px;border-top:1px solid var(--axis);font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.axis span{position:absolute;top:4px;transform:translateX(-50%)}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:8px 0 0;padding:0;list-style:none;font-size:13px;color:var(--ink-2)}
.key{display:inline-block;width:14px;height:10px;margin-right:7px;border-radius:3px;vertical-align:baseline}
.key.lo{background:var(--tint1);box-shadow:inset 0 0 0 1px var(--s1)}.key.hi{background:var(--tint0);box-shadow:inset 0 0 0 1px var(--s0)}
.key.d{width:10px;height:10px;border-radius:50%;background:var(--ink-2)}.key.c{width:10px;height:10px;border-radius:50%;border:2px solid var(--ink-2)}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.14)}
.road{display:flex;flex-wrap:wrap;align-items:stretch;gap:6px 4px;margin:6px 0 2px}
.step{background:var(--page);border:1px solid var(--border);border-radius:8px;padding:7px 10px;font-size:13.5px;flex:1 1 130px;min-width:0}
.step b{display:block;font-weight:650}
.arrow{align-self:center;color:var(--muted);flex:none}
.fork{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.branch{border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:13.5px;min-width:0}
.branch b{display:block}
.end{border:2px solid var(--ink)}
@media (max-width:560px){.fork{grid-template-columns:1fr}.road{flex-direction:column}.step{flex:none}.arrow{align-self:flex-start;transform:rotate(90deg);margin-left:12px}}
footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--border);color:var(--muted);font-size:13px}
footer p{max-width:none}
"""


def lane(kind, name, price, color, cost=None, tip="", val=""):
    seg = dot_cost = ""
    if cost is not None:
        a, b = sorted((cost, price))
        seg = f'<div class="seg" style="left:{x(a)};width:{(b - a) / AXIS * 100:.2f}%;--c:{color}"></div>'
        dot_cost = f'<div class="dot cost" style="left:{x(cost)};--c:{color}" tabindex="0" data-tip="Paper cost {px(cost)}. Made up." aria-label="Paper cost {px(cost)}, made up"></div>'
    pill = MADE if kind == "made" else '<span class="real">Real</span>'
    return f'''<div class="lane"><div class="name">{pill}{name}</div><div class="track"><div class="rail"></div>{seg}{dot_cost}<div class="dot" style="left:{x(price)};--c:{color}" tabindex="0" data-tip="{tip}" aria-label="{tip}"></div><div class="val" style="left:{x(price)}">{val}</div></div></div>'''


chart = f'''<div class="chart"><div class="heads"><span class="head a" style="left:{x(TRIM)}">Trim-above {px(TRIM)}</span><span class="head b" style="left:{x(BUY)}">Buy-below {px(BUY)}</span></div>
<div class="plot"><div class="band lo" style="left:0;width:{x(BUY)}"></div><div class="band hi" style="left:{x(TRIM)};right:0"></div>
<div class="vline" style="left:{x(BUY)}"></div><div class="vline" style="left:{x(TRIM)}"></div>
{lane("real", f"Today: last saved close {px(CLOSE)}, Nov. 3, 2026. Nothing held.", CLOSE, "var(--s1)", tip=f"Close {px(CLOSE)}, Nov. 3, 2026. Coverage {pct(MID / CLOSE)} (calc.). No position.", val=px(CLOSE))}
{lane("made", f"Case 1: paper cost {px(COST)}, price {px(P1)}. Thesis intact.", P1, "var(--s2)", cost=COST, tip=f"Made up. Price {px(P1)}, {P1 / TRIM:.2f} times the trim-above (calc.).", val=px(P1))}
{lane("made", f"Case 2: paper cost {px(COST)}, price {px(P2)}. K8 crossed.", P2, "var(--s2)", cost=COST, tip=f"Made up. Price {px(P2)}, under the buy-below. Coverage {pct(c2['cov'])} (calc.).", val=px(P2))}
</div>
<div class="axis">{"".join(f'<span style="left:{x(v)}">${v}</span>' for v in (0, 50, 100, 140))}</div></div>
<ul class="legend"><li><span class="key lo"></span>Under the buy-below: gate 3 can pass, and that is all it does</li><li><span class="key hi"></span>Above the trim-above: a trim can apply only to a position held, after a rise through the line, thesis intact</li><li><span class="key d"></span>Price</li><li><span class="key c"></span>Paper cost</li></ul>'''

kill_body = "".join(
    f'<tr><th scope="row" data-l="">{k}</th><td data-l="Claim it tests">{c}</td><td data-l="Crossed when">{t}</td><td data-l="Can fire (my estimates)">{w}</td><td data-l="Latest reading">{r}</td></tr>'
    for k, c, t, w, r in KILL_ROWS
)

html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corning Decision Map</title>
<style>{CSS}</style></head><body><main>
<h1>What would make us add, hold, trim, sell or stop on Corning</h1>
<p class="lede">The thesis decides. The price can only open a question, and a kill line can only open a review. You rule on what follows.</p>
<p class="note"><strong>A lesson, not advice.</strong> It recommends no trade and changes no rule, note or portfolio file. Corning stays no buy. Both cases carry a dashed {MADE} mark: they never happened, and their prices, position and grade are invented.</p>

<div class="answer"><strong>The short answer</strong>
<ul>
<li><strong>Today: no position, $0.</strong> You hold nothing and no thesis is recorded, so there is nothing to add to, hold, trim, sell or reassess. All three buy gates fail.</li>
<li><strong>{MADE} Case 1, thesis intact, price {px(P1)}: consider a trim, and keep the rest.</strong> No whole sale, and no add.</li>
<li><strong>{MADE} Case 2, K8 crossed, price {px(P2)}: stop. Add nothing, read the source and rule the same day.</strong> The low price does not soften it. The rules name no sale until you rule the thesis broken.</li>
<li><strong>No kill line turns a hold into a sell by itself.</strong> You asked to see the lines that do, so this needs saying: each one opens a review, and only your ruling that the thesis is broken can lead to a sale (<code>Rules/alerts.md</code>; {KILL}).</li>
</ul></div>

<h2>The map: what each action needs</h2>
<p>This holds if you own the stock. No row can be reached by a price move alone.</p>
<div class="card"><table class="stack"><thead><tr><th scope="col">Action</th><th scope="col">All of this must be true</th><th scope="col">Rule or line behind it</th><th scope="col">What a price move can do</th></tr></thead><tbody>
<tr><th scope="row">Add</th><td data-l="All of this must be true">Thesis recorded and intact. You ruled it survived the skeptic. Value refreshed from the newest filing, with the price under that buy-below. No Red open on it or its group. The whole position, with the add, stays within the smaller of the grade's cap and 5% ÷ loss, and within any shared limit. The cash level allows it. No schedule and no averaging in.</td><td data-l="Rule or line behind it"><code>sizing</code> gates and hard limit ("including any add"), <code>when-to-buy</code>, <code>cash</code>, Red in <code>alerts</code></td><td data-l="What a price move can do">Pass gate 3, and nothing else</td></tr>
<tr><th scope="row">Hold</th><td data-l="All of this must be true">You own it and no other row applies. This is the normal state, including when the price sits between the two lines.</td><td data-l="Rule or line behind it">Rules 1 and 6, overrides 2 and 7</td><td data-l="What a price move can do">Nothing</td></tr>
<tr><th scope="row">Trim</th><td data-l="All of this must be true">You own it. The thesis is intact. A rise takes the price above the trim-above. Then you consider selling part and keeping the rest.</td><td data-l="Rule or line behind it"><code>when-to-trim</code>, alert O5, override 7</td><td data-l="What a price move can do">Open the question, once per crossing. It is the one action a price can raise, and being above the line is not the test. It can't justify selling the whole position.</td></tr>
<tr><th scope="row">Sell</th><td data-l="All of this must be true">You ruled the thesis broken and, after reassessing the whole position, decided to leave. No other road ends in a whole sale.</td><td data-l="Rule or line behind it">"A broken thesis" in <code>when-to-trim</code>, alerts R1, R2 and R4, override 7</td><td data-l="What a price move can do">Nothing. A broken thesis is reassessed "whatever the price is doing".</td></tr>
<tr><th scope="row">Stop and reassess</th><td data-l="All of this must be true">Any one Red: a kill line K1 to K9 crossed on its own wording and date (R1), a dated fact that contradicts a claim (R2), a presumed-Red 8-K item (R3), or a shared exposure (R4). Read the source the same day, add nothing, then rule.</td><td data-l="Rule or line behind it"><code>alerts</code> R1 to R4, <code>monitoring</code></td><td data-l="What a price move can do">Nothing. A price move alone is never an alert.</td></tr>
</tbody></table></div>
<p class="note">Orange is a smaller stop: read it within a week and before any decision on the stock. A limit or cash breach (O7, O8) only says add nothing. It never forces a sale.</p>

<h2>Applied to today <span class="real">Real</span></h2>
<p><strong>No position, $0. The standing decision is unchanged:</strong> "We decided not to buy Corning today" (Journal, Nov. 2, 2026), and "the thesis stays a draft, and Corning stays no buy" (Journal, Nov. 3, 2026).</p>
<div class="card"><table class="stack"><thead><tr><th scope="col">Action</th><th scope="col">Today</th><th scope="col">Why</th></tr></thead><tbody>
<tr><th scope="row">Add or open</th><td data-l="Today">No</td><td data-l="Why">All three gates fail. Gate 1: the Thesis section says "Not written yet" (<code>Companies/Corning.md</code>, last checked Nov. 3, 2026). Gate 2: you ruled the draft did not survive the skeptic, for now (Journal, Nov. 3, 2026). Gate 3: the {px(CLOSE)} close of Nov. 3, 2026 ({YAHOO}) is over the {px(BUY)} buy-below (calc., {RUNFILE}), with coverage {pct(MID / CLOSE)} against the 75% bar (calc.).</td></tr>
<tr><th scope="row">Hold</th><td data-l="Today">Nothing to hold</td><td data-l="Why">No holding is on file. The paper portfolio is $100,000 in cash and no positions (<code>Portfolio/Paper portfolio.md</code>, Nov. 3, 2026). No real holdings or cash are on file.</td></tr>
<tr><th scope="row">Trim</th><td data-l="Today">Nothing to trim</td><td data-l="Why">The close is {CLOSE / TRIM:.2f} times the {px(TRIM)} trim-above (calc., {RUNFILE}). That means nothing here: O5 applies only to a position you hold.</td></tr>
<tr><th scope="row">Sell</th><td data-l="Today">Nothing to sell</td><td data-l="Why">Low coverage bars a buy. It does not call for a sale, and rule 3 bars a short.</td></tr>
<tr><th scope="row">Stop and reassess</th><td data-l="Today">Nothing open</td><td data-l="Why">Nine lines, none crossed, as read on Nov. 3, 2026 ({KILL}). The Journal holds no Red or Orange (calc., <code>data.journal_alerts</code>, run Nov. 4, 2026). The lines were not read again today. With no holding, a Red would only reopen the draft.</td></tr>
</tbody></table></div>
<p><strong>What would change this:</strong> a thesis you record, your ruling that it survived the skeptic, and a value refreshed from the next filing with the price under that buy-below. All three, with no line crossed. A lower price alone gives only the third. Still due: the skeptic's rerun with the fixed guard, your decision of Nov. 3, 2026. It did not run here.</p>
<p class="note">The lines and the {pct(MID / RUN_CLOSE)} coverage in the run use the Nov. 2 close of {px(RUN_CLOSE)}. This page uses the newer saved close for the price only. The newest filing on the saved SEC list is the 10-Q the run uses, and Aaa is still 6.12% for Oct. 2026 (<a href="https://fred.stlouisfed.org/series/AAA">FRED AAA, downloaded Nov. 3, 2026</a>). The close was not refreshed on Nov. 4: you run that sensor by hand.</p>

<h2>The price against our two lines</h2>
<p>The top lane is real. The two below it are {MADE}.</p>
<div class="card">{chart}</div>
<p class="note">Both lines: base middle {px(MID)} ÷ 0.75 = {px(BUY)}, and {px(MID)} + strategic value {px(STRAT)} = {px(TRIM)} (calc., {RUNFILE}). The cases hold them still. In real life each 10-Q and 10-K refreshes them, so a crossing in Case 2 could move them.</p>

<h2>The two cases {MADE}</h2>
<div class="card paper"><h3>The same made-up start for both {MADE}</h3>
<p>Suppose you had recorded a thesis, ruled that it survived the skeptic, and graded it 6, Middling, with a 10% cap. At a made-up {px(COST)}, coverage is {pct(start["cov"])} and the loss if wrong is {pct(start["loss"])}, or 50 on the grid. So 5% ÷ 50% = 10%, which matches the cap: {SHARES} paper shares, {usd(start_pos)}, and {usd(CASH)} left in cash (all calc.). <strong>None of that is true of Corning today.</strong></p>
<p class="note">Value if wrong is the real base low, {px(LOW)} (calc., {RUNFILE}). As in <code>sizing</code>'s example, it leaves out the $3.75 rival-capacity downside. Whether that still bites is your ruling. Sums leave out tax, and the cases ignore interest on the cash.</p></div>
<div class="cases">
<div class="card paper"><h3>Case 1: thesis intact, price far above the trim line {MADE}</h3>
<p class="verdict">Decision: consider a trim. Keep the rest. No add.</p>
<table class="kv"><tbody>
<tr><th scope="row">Price {MADE}</th><td>{px(P1)}, {P1 / TRIM:.2f} × trim-above</td></tr>
<tr><th scope="row">Position</th><td>{usd(c1["pos"])}, {pct(c1["share"])} of {usd(c1["total"])}</td></tr>
<tr><th scope="row">Coverage</th><td>{pct(c1["cov"])}, so gate 3 fails</td></tr>
<tr><th scope="row">Loss if wrong</th><td>{pct(c1["loss"])}, or {usd(c1["lost"])}</td></tr>
<tr><th scope="row">That loss, of the portfolio</th><td>{pct(c1["lost_share"])}, over the 5% limit</td></tr>
</tbody></table>
<ul class="txt" style="margin-top:10px">
<li><strong>What fired:</strong> O5 once, when the rise crossed {px(TRIM)}, and O7 at the refresh. Going from $40 to {px(P1)} adds no new O5.</li>
<li><strong>Why trim is open:</strong> you hold it, a rise went through the line, and the thesis is intact (<code>when-to-trim</code>). The rule says "consider". You may still hold.</li>
<li><strong>Why no whole sale:</strong> "a higher price alone is never a reason to sell the whole position". "Far above" adds no extra step.</li>
<li><strong>Why no add:</strong> gate 3 fails and O7 says add nothing.</li>
<li><strong>The limit forces nothing:</strong> at {pct(c1["lost_share"])} it only alerts you (<code>sizing</code>, your decision 3).</li>
<li><strong>The amount is not in the rules.</strong> The skill's own reading, a proposal, would sell {usd(sell)} and keep {usd(keep)}, which loses {pct(keep_lost / c1["total"])} if wrong (calc.).</li>
</ul></div>
<div class="card paper"><h3>Case 2: kill line crossed, price below the buy-below {MADE}</h3>
<p class="verdict">Decision: stop and reassess. Add nothing. Hold until you rule.</p>
<table class="kv"><tbody>
<tr><th scope="row">Price {MADE}</th><td>{px(P2)}, under {px(BUY)}</td></tr>
<tr><th scope="row">Position</th><td>{usd(c2["pos"])}, {pct(c2["share"])} of {usd(c2["total"])}</td></tr>
<tr><th scope="row">Coverage</th><td>{pct(c2["cov"])}, so gate 3 passes</td></tr>
<tr><th scope="row">Loss if wrong</th><td>{pct(c2["loss"])}, or {usd(c2["lost"])}</td></tr>
<tr><th scope="row">That loss, of the portfolio</th><td>{pct(c2["lost_share"])}, under the 5% limit</td></tr>
</tbody></table>
<ul class="txt" style="margin-top:10px">
<li><strong>What fired:</strong> Suppose Optical sales fall two quarters running. That is K8, so R1, a Red, on your phone. No such fall has happened.</li>
<li><strong>Why no add:</strong> a Red bars it, though the price passes gate 3. Without the crossing, the same numbers would leave room for {usd(room)} (calc.). The crossing takes that away.</li>
<li><strong>Why no automatic sale:</strong> K8 tests C2, and a crossing opens a review. K8 fired twice before, and both times Optical sales passed the starting figure seven quarters later (calc., {KILL}).</li>
<li><strong>If you rule C2 holds:</strong> hold, and the add question can reopen, gates first.</li>
<li><strong>If you rule the thesis broken:</strong> reassess the whole position, whatever the price is doing. Being under the buy-below is no reason to stay, and a sale here refills cash (<code>cash</code>).</li>
</ul></div>
</div>

<h2>The kill lines, and how a hold can become a sell</h2>
<p><strong>Nine lines can start this road. None can finish it.</strong> Your ruling is the step between.</p>
<div class="card"><div class="road">
<div class="step"><b>Hold</b>Thesis on record</div><div class="arrow" aria-hidden="true">→</div>
<div class="step"><b>A line is crossed</b>On its own wording and date</div><div class="arrow" aria-hidden="true">→</div>
<div class="step"><b>Red, at once</b>Add nothing to it or its group</div><div class="arrow" aria-hidden="true">→</div>
<div class="step"><b>You read the source</b>The same day</div><div class="arrow" aria-hidden="true">→</div>
<div class="step end"><b>You rule</b>Does the claim still hold, and why?</div>
</div>
<div class="fork"><div class="branch"><b>The claim holds</b>Back to hold. The dated event may move a grade or a chance.</div>
<div class="branch"><b>It is broken</b>Reassess the whole position, whatever the price. A sale is now open to you, not automatic.</div></div></div>
<p class="note">These lines belong to a draft thesis that is not approved. You set them on Nov. 3, 2026, and a thesis you record could change them. None is crossed, as read that day ({KILL}). Dates in the "can fire" column are that note's estimates.</p>
<div class="card"><table class="stack"><thead><tr><th scope="col">Line</th><th scope="col">Claim it tests</th><th scope="col">Crossed when</th><th scope="col">Can fire (estimates)</th><th scope="col">Latest reading</th></tr></thead><tbody>{kill_body}</tbody></table></div>
<ul class="txt">
<li><strong>A pass proves nothing,</strong> and most lines are years from their test.</li>
<li><strong>Two claims have no line.</strong> C6 (Glass and Solar do not drag) and C8 (growth outlives the plan, 2031 to 2036). You decided C6 gets one on Solar's segment result, but its threshold and date are not set (<code>Rules/alerts.md</code>, Nov. 3, 2026). Until then, a slow slip can only reach O15.</li>
<li><strong>A review can start without a line:</strong> R2 (a dated fact against a claim), R3 (certain 8-K items) and R4 (a shared exposure).</li>
</ul>

<h2>Where the rules leave it to you</h2>
<ul class="txt">
<li><strong>Add has no rule of its own.</strong> The map builds it from <code>when-to-buy</code>, <code>sizing</code>'s "including any add", and <code>cash</code>. That is also how the <code>portfolio-manager</code> skill reads it. It is a reading, for you to correct.</li>
<li><strong>"Reassess" is not "sell".</strong> The rule says reassess the whole position. The skill reads your ruling as a whole sale, and says that this is its reading.</li>
<li><strong>How much must break?</strong> No rule says whether one broken claim breaks the whole thesis, or how many it takes. You rule.</li>
<li><strong>Trim size and timing.</strong> No rule sets the amount, or says whether a trim inside five years needs more reason under rule 1.</li>
<li><strong>A conflict in <code>Rules/alerts.md</code>.</strong> Its test section says C6 "can never reach Red". R2's row covers claims C1 to C8, so a dated fact against C6 could. This page follows the map: a slow slip goes to O15, and an outright contradiction goes to R2. You settle it.</li>
</ul>

<footer><p>Built Nov. 4, 2026 by <code>sensors/decisions/draw.py</code>, checked by <code>test_decisions.py</code>. All sums are calc. from the valuation run, the saved close and the made-up inputs. Case actions were also run through the skill's <code>pm.py</code> on made-up files. Keep this page on this computer, since it holds a Yahoo price. It does not say that Corning's business is good or bad, or where the price goes. It is not advice, and no order follows from it.</p></footer>
</main><div id="tip" hidden></div>
<script>
(function(){{var t=document.getElementById('tip');
function show(e){{var d=e.target.closest('[data-tip]');if(!d)return;t.textContent=d.getAttribute('data-tip');t.hidden=false;var r=d.getBoundingClientRect();
t.style.left=Math.max(8,Math.min(innerWidth-t.offsetWidth-8,r.left-20))+'px';t.style.top=Math.max(8,r.top-t.offsetHeight-8)+'px';}}
function hide(){{t.hidden=true;}}
document.addEventListener('mouseover',show);document.addEventListener('mouseout',hide);document.addEventListener('focusin',show);document.addEventListener('focusout',hide);}})();
</script></body></html>
'''
OUT.write_text(html)
print(f"wrote {OUT.name}: close {CLOSE:.2f}, buy-below {BUY:.2f}, trim-above {TRIM:.2f}")
