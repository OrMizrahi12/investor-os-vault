"""Draw alerts.html from the alert test. The map was approved by the owner on Nov. 3, 2026.

    .venv/bin/python -I sensors/alerts/analyze.py
    .venv/bin/python -I sensors/alerts/draw.py
    .venv/bin/python -I sensors/alerts/test_alerts.py

No network. Keep the page on this computer, because it holds a Yahoo price.
"""
import datetime as dt
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from alertmap import ITEMS, LINES, MAP  # noqa: E402

ROOT = HERE.parents[1]
R = json.loads((HERE / "cache/results.json").read_text())
T = R["tally"]
OUT = ROOT / "alerts.html"
esc = html.escape
BUY, TRIM = 28.97, 36.06
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
SRC_PRICE = f'<a href="{YAHOO}">Yahoo through yfinance, fetched Nov. 2, 2026</a>'
SRC_RUN = "<code>sensors/valuation/runs/2026-11-03-01.md</code>, Nov. 3, 2026"
LIST = '<a href="https://data.sec.gov/submissions/CIK0000024741.json">EDGAR filing list, retrieved Nov. 2, 2026</a>'

# ---------- word claims are tested before they are written ----------
assert T["red"] == 0 and T["orange"] == 27 and T["info"] == 401
assert T["orange_watcher"] + T["orange_radar"] == 12 and T["orange_person"] == 15
assert T["orange_news"] == 15 and T["orange_letters"] == 2
assert T["first_8k"] == {"Orange": 14, "Info": 8} and T["final_8k"]["Orange"] == 9
assert T["flagged_8k"] == 21 and T["insider"] == 344 and T["filings"] == 403 and T["insider_sales"] == 64 and T["insider_buys"] == 0
assert T["brief_days"] == 148 and T["trading_days"] == 500
assert round(R["high"][1], 2) == 255.69 and round(R["last"][1], 2) == 123.20 and round((1 - R["last"][1] / R["high"][1]) * 100) == 52
assert all(c > TRIM for _, c in R["prices"])
assert round(R["low"][1], 2) == 39.07 and round((R["low"][1] / TRIM - 1) * 100) == 8
assert R["drill_first"]["day"] == "2025-08-01"
assert [q["q"] for q in R["quarters"] if q["k3_cross"]] == ["Q4 2024", "Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
assert [q["q"] for q in R["quarters"] if q["fall"]] == ["Q1 2025"]
assert R["k9_fired"] == ["2023-03-31", "2023-06-30"]
assert R["quarters"][-1]["k5"] == 1505

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--s1:#2a78d6;--mid:#f0efec;--red:#d03b3b;--orange:#ec835a;--info:#8d8b84;--tint-red:rgba(208,59,59,.10);--tint-orange:rgba(236,131,90,.16)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.1);--link:#7fb0ee;--s1:#3987e5;--mid:#383835;--info:#8d8b84;--tint-red:rgba(208,59,59,.2);--tint-orange:rgba(236,131,90,.2)}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.1);--link:#7fb0ee;--s1:#3987e5;--mid:#383835;--tint-red:rgba(208,59,59,.2);--tint-orange:rgba(236,131,90,.2)}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:25px;line-height:1.25;margin:10px 0;font-weight:650;max-width:44ch}
h2{font-size:19px;margin:38px 0 6px;font-weight:650}h3{font-size:16px;margin:0 0 6px;font-weight:650}
p{margin:0 0 10px;max-width:78ch}.lede{color:var(--ink-2)}
a{color:var(--link);overflow-wrap:anywhere}code{font-size:.9em;overflow-wrap:anywhere}b{font-weight:650}
.tag{display:inline-block;font-size:12.5px;font-weight:650;letter-spacing:.04em;padding:2px 9px;border:1.5px dashed var(--ink-2);border-radius:6px;color:var(--ink-2)}
.callout{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--ink-2);border-radius:8px;padding:12px 16px;margin:14px 0;max-width:78ch;font-size:14.5px}.callout p:last-child{margin:0}
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:16px 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;min-width:0}
.tile .n{font-size:34px;line-height:1.1;font-weight:650;font-variant-numeric:tabular-nums}.tile p{margin:6px 0 0;font-size:13.5px;color:var(--ink-2)}
.lv{display:inline-flex;align-items:center;gap:6px;font-weight:650;white-space:nowrap;color:var(--ink)}
.lv i{display:inline-block;width:12px;height:12px;flex:none}.lv.Red i{background:var(--red);border-radius:2px;transform:rotate(45deg)}.lv.Orange i{background:var(--orange);clip-path:polygon(50% 0,100% 100%,0 100%)}.lv.Info i{background:var(--info);border-radius:50%}
.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:12px}.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;font-size:14px;min-width:0}
.card ol,.card ul{margin:6px 0 0;padding-left:18px}.card li{margin-bottom:4px}.card .when{color:var(--ink-2);margin:6px 0}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:8px 12px 8px 0;border-bottom:1px solid var(--border)}thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600}
td{color:var(--ink-2)}td b{color:var(--ink)}.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.nw{white-space:nowrap}
.foot{color:var(--muted);font-size:12.5px}ul.notes{margin:0 0 10px;padding-left:18px;max-width:78ch;font-size:14.5px;color:var(--ink-2)}ul.notes li{margin-bottom:7px}ul.notes b{color:var(--ink)}
.two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:6px 0 8px;padding:0;list-style:none;font-size:13px;color:var(--ink-2)}
details{margin:10px 0}summary{cursor:pointer;color:var(--ink-2);font-size:14px}
#tl{position:relative}#tl svg{display:block;width:100%;min-width:760px;height:auto}
#tl text{font:11px system-ui,sans-serif;fill:var(--muted)}#tl .v{fill:var(--ink);font-weight:600}#tl .lane{fill:var(--ink-2);font-weight:600}
#tl .gl{stroke:var(--grid)}#tl .ax{stroke:var(--axis)}#tl .pr{fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round}#tl .th{stroke:var(--ink-2);stroke-width:1.5;stroke-dasharray:5 4}
#tl .mR{fill:none;stroke:var(--red);stroke-width:2}#tl .mO{fill:var(--orange);stroke:var(--surface);stroke-width:1}#tl .mI{stroke:var(--info);stroke-width:1.5}
#tl .hit{fill:transparent;cursor:default}#tl .hit:focus{outline:none;stroke:var(--link);stroke-width:2}
#tip{position:fixed;display:none;pointer-events:none;background:var(--surface);border:1px solid var(--axis);border-radius:8px;padding:8px 10px;font-size:13px;max-width:320px;z-index:2;box-shadow:0 2px 8px rgba(0,0,0,.14)}
@media (max-width:860px){.tiles,.cards,.two{grid-template-columns:minmax(0,1fr)}.stack thead{display:none}.stack,.stack tbody,.stack tr,.stack th,.stack td{display:block;width:100%}.stack tr{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin-bottom:8px}.stack th,.stack td{border:0;padding:2px 0}}
"""


def level(name):
    return f'<span class="lv {name}"><i aria-hidden="true"></i>{name}</span>'


def nice(iso):
    d = dt.date.fromisoformat(iso)
    mon = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."][d.month - 1]
    return f"{mon} {d.day}, {d.year}"


def link(label, url):
    return f'<a href="{esc(url)}">{esc(label)}</a>'


# ---------- the chart ----------
W, L, RM = 1100, 112, 54
PLOT = W - L - RM
START, END = dt.date(2024, 11, 3), dt.date(2026, 11, 3)


def X(iso):
    return L + (dt.date.fromisoformat(iso) - START).days / (END - START).days * PLOT


P_TOP, P_BOT, P_MAX = 24, 230, 280


def Y(v):
    return P_BOT - v / P_MAX * (P_BOT - P_TOP)


svg = []
for v in (0, 50, 100, 150, 200, 250):
    svg.append(f'<line class="gl" x1="{L}" x2="{W-RM}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end">${v}</text>')
ticks = [("2025-01-01", "Jan. 2025"), ("2025-07-01", "July 2025"), ("2026-01-01", "Jan. 2026"), ("2026-07-01", "July 2026")]
LANES = [("Red", 262), ("Orange, a sensor sees it", 294), ("Orange, only a person", 326), ("Info", 358)]
for iso, lab in ticks:
    svg.append(f'<line class="gl" x1="{X(iso):.1f}" x2="{X(iso):.1f}" y1="{P_TOP}" y2="372"/><text x="{X(iso):.1f}" y="388" text-anchor="middle">{lab}</text>')
pts = " ".join(f"{X(d):.1f},{Y(c):.1f}" for d, c in R["prices"])
svg.append(f'<polyline class="pr" points="{pts}"/>')
svg.append(f'<line class="th" x1="{L}" x2="{W-RM}" y1="{Y(TRIM):.1f}" y2="{Y(TRIM):.1f}"/><text class="v" x="{W-RM-6}" y="{Y(TRIM)-5:.1f}" text-anchor="end">Trim-above $36.06</text>')
svg.append(f'<line class="th" x1="{L}" x2="{W-RM}" y1="{Y(BUY):.1f}" y2="{Y(BUY):.1f}"/><text class="v" x="{W-RM-6}" y="{Y(BUY)+14:.1f}" text-anchor="end">Buy-below $28.97</text>')
hx, hy = X(R["high"][0]), Y(R["high"][1])
svg.append(f'<text class="v" x="{hx-6:.1f}" y="{hy-6:.1f}" text-anchor="end">$255.69, June 29, 2026</text>')
lx, ly = X(R["last"][0]), Y(R["last"][1])
svg.append(f'<text class="v" x="{lx+4:.1f}" y="{ly+4:.1f}">$123.20</text>')
for name, y in LANES:
    svg.append(f'<text class="lane" x="{L-8}" y="{y+4}" text-anchor="end" style="font-size:10.5px">{name.split(",")[0]}</text>')
    if "," in name:
        svg.append(f'<text x="{L-8}" y="{y+15}" text-anchor="end" style="font-size:9.5px">{name.split(", ")[1]}</text>')
    svg.append(f'<line class="ax" x1="{L}" x2="{W-RM}" y1="{y}" y2="{y}" style="opacity:.45"/>')
# run-back Red: an open marker, because it is not one that counts
k3x = X("2025-01-29")
svg.append(f'<rect class="mR" x="{k3x-5:.1f}" y="257" width="10" height="10" transform="rotate(45 {k3x:.1f} 262)"/>')
tips = []
tips.append(("2025-01-29", 262, "Red, run back only", "K3 reads as crossed on Q4 2024: 14.0% and 14.2%. A false Red, since the line was set in Nov. 2026.", ""))
info_days = sorted(set(R["brief_days"]))
for d in info_days:
    svg.append(f'<line class="mI" x1="{X(d):.1f}" x2="{X(d):.1f}" y1="352" y2="364"/>')
for e in R["events"]:
    if e["final"] != "Orange":
        continue
    y = 294 if e["seen"] in ("8-K watcher", "radar") else 326
    x = X(e["date"])
    svg.append(f'<path class="mO" d="M{x:.1f} {y-6} L{x+6:.1f} {y+5} L{x-6:.1f} {y+5} Z"/>')
    tips.append((e["date"], y, "Orange" + (f', {e["claim"]}' if e["claim"] else ""), e["what"], f'8-K, filed {nice(e["date"])}' if e["kind"] == "8-K" else e["label"]))
hits = []
for d, y, head, body, src in tips:
    t = esc(json.dumps({"h": f"{nice(d)}: {head}", "b": body, "s": src}), quote=True)
    hits.append(f'<circle class="hit" cx="{X(d):.1f}" cy="{y}" r="11" data-t="{t}" tabindex="0"/>')
PRICE_JSON = json.dumps(R["prices"][::1])
chart = f"""<div class="wrap" id="tlw"><div id="tl"><svg viewBox="0 0 {W} 396" role="img" aria-label="Corning's close over two years, with both price lines far below it, and every alert by level beneath. The events table below holds the same facts.">
{''.join(svg)}<line id="cx" class="ax" x1="0" x2="0" y1="{P_TOP}" y2="{P_BOT}" style="display:none"/><rect id="pz" x="{L}" y="{P_TOP}" width="{PLOT}" height="{P_BOT-P_TOP}" fill="transparent"/>{''.join(hits)}</svg></div></div><div id="tip"></div>"""

JS = f"""<script>
(function(){{
var P={PRICE_JSON},L={L},PLOT={PLOT},W={W},t0=Date.parse('2024-11-03'),t1=Date.parse('2026-11-03');
var box=document.getElementById('tl'),tip=document.getElementById('tip'),svg=box.querySelector('svg'),cx=document.getElementById('cx'),pz=document.getElementById('pz');
function show(html,ev){{tip.innerHTML=html;tip.style.display='block';var x=ev.clientX+14,y=ev.clientY+14;if(x+tip.offsetWidth>innerWidth-8)x=Math.max(8,ev.clientX-tip.offsetWidth-14);if(y+tip.offsetHeight>innerHeight-8)y=Math.max(8,ev.clientY-tip.offsetHeight-14);tip.style.left=x+'px';tip.style.top=y+'px';}}
function hide(){{tip.style.display='none';cx.style.display='none';}}
function esc(s){{var d=document.createElement('div');d.textContent=s;return d.innerHTML;}}
box.querySelectorAll('.hit').forEach(function(c){{
  function fill(ev){{var d=JSON.parse(c.getAttribute('data-t'));show('<b>'+esc(d.h)+'</b><br>'+esc(d.b)+(d.s?'<br><span class="foot">'+esc(d.s)+'</span>':''),ev);}}
  c.addEventListener('mousemove',fill);c.addEventListener('mouseleave',hide);
  c.addEventListener('focus',function(){{var r=c.getBoundingClientRect();fill({{clientX:r.left,clientY:r.top}});}});c.addEventListener('blur',hide);
}});
pz.addEventListener('mousemove',function(ev){{
  var r=svg.getBoundingClientRect(),vx=(ev.clientX-r.left)/r.width*W,t=t0+(vx-L)/PLOT*(t1-t0),best=P[0];
  P.forEach(function(p){{if(Math.abs(Date.parse(p[0])-t)<Math.abs(Date.parse(best[0])-t))best=p;}});
  var x=L+(Date.parse(best[0])-t0)/(t1-t0)*PLOT;cx.setAttribute('x1',x);cx.setAttribute('x2',x);cx.style.display='';
  show('<b>'+best[0]+'</b><br>Close $'+best[1].toFixed(2),ev);
}});
pz.addEventListener('mouseleave',hide);
var w=document.getElementById('tlw');w.scrollLeft=w.scrollWidth;
}})();
</script>"""

# ---------- tables ----------
map_rows = "".join(f'<tr><th scope="row" class="nw">{i}</th><td>{level(lv)}</td><td><b>{esc(group)}</b><br>{esc(sig)}</td><td>{esc(cond)}</td><td>{esc(who)}</td></tr>' for i, group, sig, cond, lv, who in MAP)
line_rows = "".join(f'<tr><th scope="row">{k}</th><td>{c}</td><td>{esc(red)}</td><td>{esc(step)}</td></tr>' for k, c, red, step in LINES)
item_rows = "".join(f'<tr><th scope="row">{i}</th><td>{level(lv)}</td><td class="num">{R["item_win"].get(i, 0)}</td><td class="num">{R["item_all"].get(i, 0)}</td><td>{esc(what)}</td></tr>'
                    for i, (lv, what) in sorted(ITEMS.items()))


def ev_row(e):
    first = "" if e["first"] == e["final"] else f'<br><span class="foot">First pass {e["first"]}</span>'
    return f'<tr><td class="nw">{nice(e["date"])}</td><td>{level(e["final"])}{first}</td><td>{esc(e["what"])}</td><td>{esc(e["claim"]) or "None"}</td><td>{esc(e["seen"])}</td><td>{link(f'8-K, filed {nice(e["date"])}' if e["kind"] == "8-K" else e["label"], e["url"])}</td></tr>'


orange_rows = "".join(ev_row(e) for e in R["events"] if e["final"] == "Orange")
drop_rows = "".join(ev_row(e) for e in R["events"] if e["final"] == "Info")
q_rows = ""
for q in R["quarters"][2:]:
    k3 = "Reads as crossed" if q["k3_cross"] else ("At or below" if q["k3_low"] else "Above")
    q_rows += (f'<tr><th scope="row">{q["q"]}</th><td class="num">${q["sales"]:,}M{" ↓" if q["fall"] else ""}</td><td class="num">{q["margin"]:.1f}%</td><td>{k3}</td>'
               f'<td class="num">${q["x4"]:,}M</td><td class="num">{"$%s M" % format(q["k5"], ",") if q.get("k5") else "Not summed"}</td><td>{link(*q["src"])}</td></tr>')
q_rows = q_rows.replace(" M<", "M<")
k9_rows = ""
for r in R["k9"][-9:]:
    k9_rows += f'<tr><th scope="row">{nice(r["end"])}</th><td class="num">${r["total"]:,}M{" ↓" if r["fall"] else ""}</td></tr>'
move_rows = ""
HOW = {"filing": "A filing that day or the session before", "news": "News only", "none": "No company event, per one article", "unknown": "Unknown"}
for m in R["top"]:
    src = link(m["label"], m["url"]) if m["url"] else "None"
    move_rows += f'<tr><td class="nw">{nice(m["date"])}</td><td class="num">{m["pct"]:+.1f}%</td><td>{HOW[m["how"]]}</td><td>{esc(m["note"])}</td><td>{src}</td></tr>'
drill_rows = "".join(f'<tr><td class="nw">{nice(d["day"])}</td><td class="num">${d["close"]:.2f}</td><td class="num">{d["loss_pct"]:.2f}%</td><td>{"Over 5%" if d["over"] else "Under 5%"}</td></tr>' for d in R["drill"])

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alert Map</title><style>{CSS}</style></head><body><main>
<span class="tag">APPROVED. ONLY RED GOES TO THE PHONE</span>
<h1>Over two years the map gives 0 Reds, {T["orange"]} Oranges and {T["info"]} Info items on Corning. Fix the news gap before automating anything.</h1>
<p class="lede">Today's sensors would surface 12 of the {T["orange"]} Oranges (calc.). The other {T["orange_news"]} are facts from news and calls no sensor reads. Written version: <a href="Rules/alerts.md"><code>Rules/alerts.md</code></a>. The daily run and the event run have run as Desktop tasks since Nov. 4, 2026. A Red goes to my phone through Telegram as the last step of the run that wrote it (<a href="phone.html"><code>phone.html</code></a>). Nothing else sends an alert, and no investing decision changes: Corning stays no buy.</p>
<div class="callout"><p><b>This is a test with hindsight.</b> The thesis and the kill lines were written on Nov. 3, 2026, so no line existed during these two years. The levels on events are Claude's reading, knowing how things turned out, for you to correct. No position was held. It counts what the map would have raised. It cannot say the alerts would have led to a better decision.</p></div>
<div class="tiles">
<div class="tile">{level("Red")}<div class="n">0</div><p>Fair count. Run back as written, K3 gives 1, a false one. No Red 8-K item was filed.</p></div>
<div class="tile">{level("Orange")}<div class="n">{T["orange"]}</div><p>9 8-Ks, 2 SEC letters, 1 catalyst date, 15 from news and calls. About 1.1 a month, with 19 in 2026 (calc.).</p></div>
<div class="tile">{level("Info")}<div class="n">{T["info"]}</div><p>On {T["brief_days"]} days in the two years, and {T["insider"]} of them are insider forms (calc.).</p></div>
</div>

<h2>What you do at each level</h2>
<p>Red goes to the phone. Orange waits in the Journal until you open it, and Info waits in the daily brief. The other difference is what you owe. Every alert states the condition, source and date, and gives no recommendation. No alert sells anything.</p>
<div class="cards">
<div class="card">{level("Red")}<p class="when"><b>A kill line is hit or the thesis breaks. The same day.</b></p><ol><li>Read the source yourself.</li><li>Add nothing to that position or its group.</li><li>Rule whether the claim still holds, and why.</li><li>If broken, reassess the whole position, whatever the price is doing. The coach goes first.</li></ol><p class="foot" style="margin-top:8px">With no holding, it only reopens the draft. That is all it could do on Corning today.</p></div>
<div class="card">{level("Orange")}<p class="when"><b>The thesis moves, a price zone is entered or a limit breaks. Within a week, and before any decision on that stock.</b></p><ol><li>Say whether a claim moved, and which way.</li><li>A chance or grade may change only on this dated event.</li><li>Buy-below hit: refresh value, run the three gates.</li><li>Trim-above hit: read <code>when-to-trim</code>.</li><li>Limit broken: add nothing. No sale is forced.</li></ol></div>
<div class="card">{level("Info")}<p class="when"><b>Everything else worth a line. Daily brief, only on a day with something new.</b></p><ul><li>Nothing is required. Skim or skip.</li><li>It can never change a chance, a grade or a size.</li><li>It shows where the price stands, never how it moved.</li></ul><p class="foot" style="margin-top:8px">Never an alert: a price move alone, or a source's age alone. Never anywhere: a possible inside tip.</p></div>
</div>

<h2>Two years at a glance</h2>
<p>The close never crossed either line, so no price alert fires. Its low was $39.07, 8% above the trim-above (calc.). Most Oranges come from outside the filings.</p>
<ul class="legend"><li>{level("Orange")} Filled triangle, one alert</li><li><span class="lv Red"><i style="background:none;border:2px solid var(--red)" aria-hidden="true"></i>Red</span> Open diamond, run back only</li><li>{level("Info")} Tick, a day with Info</li></ul>
{chart}
<p class="foot">Close, {SRC_PRICE}. Lines: {SRC_RUN}, today's lines drawn back, since no earlier line exists. Hover or tab to a marker. Every marker is in the tables below.</p>

<h2>The map</h2>
<p>Every signal the vault watches or could watch. Who reads it today shows how much is left to a person.</p>
<div class="wrap"><table class="stack"><thead><tr><th>ID</th><th>Level</th><th>Signal</th><th>Condition</th><th>Who reads it today</th></tr></thead><tbody>{map_rows}</tbody></table></div>

<h3 style="margin-top:24px">Kill lines: Red, and the Orange step before it</h3>
<p class="foot">Lines as set, <code>Research/2026-11-03 Corning kill criteria.md</code>, Nov. 3, 2026. The lines do not change. Only the step before them is new.</p>
<div class="wrap"><table class="stack"><thead><tr><th>Line</th><th>Claim</th><th>Red</th><th>Orange, one step before</th></tr></thead><tbody>{line_rows}</tbody></table></div>

<h3 style="margin-top:24px">8-K items: the first pass, before anyone opens the filing</h3>
<p class="foot">Counts are items on the filing list, not filings, and index counts were not all checked in the filing text. {LIST}. Since 2004 means the {R["dotted"]} 8-Ks since Oct. 2004 that use today's numbers (calc.). Items Corning has never filed still get a level.</p>
<details><summary>Show all {len(ITEMS)} items</summary><div class="wrap"><table class="stack"><thead><tr><th>Item</th><th>First pass</th><th class="num">Two years</th><th class="num">Since 2004</th><th>What reading does</th></tr></thead><tbody>{item_rows}</tbody></table></div></details>

<h2>Where it would have been noisy</h2>
<div class="two"><ul class="notes">
<li><b>Insider forms.</b> {T["insider"]} of {T["filings"]} filings are Forms 3, 4 or 144, or 85% (calc., {LIST}). Of {T["insider_read"]} Forms 4, {T["insider_sales"]} report a sale, {T["insider_grants"]} are director-only grants and {T["insider_buys"]} a market purchase (calc.). The sales alone as Oranges would more than triple the count. So they are one Info line a day.</li>
<li><b>8-K items alone.</b> Your flag list marks {T["flagged_8k"]} of 22 8-Ks, so it sorts nothing (calc.). 7 of the 22 are conference notices. The first pass gives 14 Oranges, and reading drops 5: two director changes, a replaced credit line and two quiet results days.</li>
<li><b>Results days.</b> 6 of 8 stay Orange after reading (calc.). That is a good reason to read them, and a poor sign that Orange sorts them.</li>
<li><b>A Form 25.</b> The one on file looks like a delisting. It is <a href="https://www.sec.gov/Archives/edgar/data/24741/000087666126000439/xslF25X02/primary_doc.xml">3.875% notes due 2026 coming off the exchange, filed May 15, 2026</a>. So it is Info, not Red.</li>
</ul><ul class="notes">
<li><b>K3 run back.</b> The line sits at the level of 2025, so all five reports from Q4 2024 to Q4 2025 read as crossed. Without "one alert per crossing" that is 5 false Reds (calc.). It can first fire on Q1 2027.</li>
<li><b>Q1 falls.</b> Optical fell once in the window, in Q1 2025, and Q1 fell in 7 of 9 years (calc., kill criteria note). K9 fell in 5 of 9 Q1s (calc.). So a lone Q1 fall is Info. Without that, the test adds 1 Orange.</li>
<li><b>News.</b> Of 25 news facts in the vault, Claude would drop 10 after reading (calc.). The real figure would be worse, because the vault holds only what we kept.</li>
<li><b>Dates and leads.</b> The radar lists {T["radar_dates"]} catalyst dates and {T["radar_leads"]} leads on each run, with {T["radar_hidden"]} more leads hidden (<code>sensors/radar/runs/2026-11-03-03.json</code>, Nov. 3, 2026). Repeated daily they bury the rest. So they appear on a change only.</li>
</ul></div>

<h2>Where it would have missed something</h2>
<ul class="notes">
<li><b>Most deals.</b> For the six deals since Nov. 2025, the first Corning filing naming the customer came the same day for NVIDIA, 1 day later for Meta, 28 for AT&amp;T, 49 for Verizon and 50 for Amazon. Zayo was unnamed after 74 days (calc., <code>Companies/Corning.md</code>). No sensor reads news.</li>
<li><b>Calls and customers.</b> K2, K7 and K9 rest on a person. AT&amp;T's "roughly $1 billion lower" came on a call (<a href="https://www.earningswhispers.com/transcript/T/Q32026">AT&amp;T Q3 call, Oct. 21, 2026, third-party transcript</a>).</li>
<li><b>SEC letters.</b> Staff told Corning to remove the adjustment behind most of the gap to core (<a href="https://www.sec.gov/Archives/edgar/data/24741/000000000026002022/filename1.pdf">SEC staff letter, Feb. 26, 2026</a>). The radar lists such letters unread, and we read this one only later (<code>Lessons/Read the SEC letters before explaining a change.md</code>). They also come late: SEC releases them no earlier than 20 business days after a review ends (<a href="https://www.sec.gov/files/divisions/corpfin/cffilingreview.htm">SEC filing review page, undated, retrieved Nov. 3, 2026</a>). This review closed on <a href="https://www.sec.gov/Archives/edgar/data/24741/000000000026004267/filename1.pdf">Apr. 27, 2026</a>, after core changed on Apr. 1, 2026. So O10 explains a change. It cannot warn of one.</li>
<li><b>Investor events.</b> Only the notice is filed, and it is Info. The plan change happens on a webcast (<a href="https://www.sec.gov/Archives/edgar/data/24741/000120677425000133/glw4455141-8k.htm">8-K, filed Mar. 17, 2025</a>; <a href="https://www.sec.gov/Archives/edgar/data/24741/000120677425000358/glw4484671-8k.htm">8-K, filed May 13, 2025</a>).</li>
<li><b>A claim wearing away.</b> Solar went against us on three reports running: "running behind" (<a href="https://www.fool.com/earnings/call-transcripts/2026/04/28/corning-glw-q1-2026-earnings-transcript/">Q1 call, Apr. 28, 2026, third-party transcript</a>), a wafer plant shutdown (<a href="https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000253/glw-20260728xex99xq22026.htm">Q2 release, July 28, 2026</a>) and "a slower pace than anticipated" (<a href="https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm">Q3 release, Oct. 27, 2026</a>). C6 has no kill line, so it can never reach Red. O15 is there for this.</li>
<li><b>The price, on purpose.</b> The close fell 52% from June 29 to Nov. 2, 2026 (calc., {SRC_PRICE}). The map says nothing about that, as rule 6 asks. I9 still shows where the price stands against the lines.</li>
</ul>

<h3 style="margin-top:20px">An outside check: the 16 largest one-day moves</h3>
<p>A test of misses only. A price move never raises an alert. {T["moves_filing"]} had a filing that day or the session before, {T["moves_news"]} had news only, {T["moves_none"]} had no company event according to one article each, and {T["moves_unknown"]} are unknown (calc.). Claude ran three searches, so unknown does not mean nothing happened. One article also ties the Sept. 14 fall in peers to weekend remarks by AI lab leaders. That would be an O2 on C1 if it holds, and it was not checked.</p>
<details><summary>Show the 16 moves</summary><div class="wrap"><table class="stack"><thead><tr><th>Date</th><th class="num">Close to close</th><th>What the record shows</th><th>Note</th><th>Source</th></tr></thead><tbody>{move_rows}</tbody></table></div><p class="foot">Moves are calc., {SRC_PRICE}. The articles are single sources on cause, not filings.</p></details>

<h2>What the test cannot show</h2>
<ul class="notes">
<li><b>Red in a downturn.</b> K8 and K9 never fell two quarters running in these two years. Outside the window K8 fired on Q4 2019 and Q1 2023, and K9 on Q1 2023. Both times K8 fired, Optical sales passed the starting figure seven quarters later (calc., kill criteria note). So a fire opens a review. It does not prove a break.</li>
<li><b>Price alerts.</b> The closes stayed above both lines all window: the low was ${R["low"][1]:.2f} on {nice(R["low"][0])}. The last close under $28.97 was {nice(R["last_under"]["28.97"][0])}, and under $36.06 {nice(R["last_under"]["36.06"][0])} (calc., {SRC_PRICE}). Past lines were not rebuilt, and strategic value did not exist then.</li>
<li><b>Aaa.</b> No alert: it stayed within {T["aaa_far"]} points of 6.12% (calc., <a href="https://fred.stlouisfed.org/series/AAA">FRED AAA, downloaded Nov. 3, 2026</a>). A near miss, measured from an anchor set at the end of the window.</li>
<li><b>Sizing, cash and shared exposures.</b> No position or group was on file, so only a drill below. <code>Portfolio/</code> holds no real holdings.</li>
<li><b>Item-based Reds.</b> None in the window. Across {R["dotted"]} 8-Ks since Oct. 2004, three would fire: impairments in <a href="https://www.sec.gov/Archives/edgar/data/24741/000002474104000467/form8k.txt">2004</a> and <a href="https://www.sec.gov/Archives/edgar/data/24741/000002474105000549/sept218k.txt">2005</a>, and a restatement in <a href="https://www.sec.gov/Archives/edgar/data/24741/000002474106000199/q1068k.txt">2006</a> (calc.).</li>
</ul>
<details><summary>The kill lines, quarter by quarter</summary>
<div class="wrap"><table class="stack"><thead><tr><th>Quarter</th><th class="num">Optical sales (K1, K8)</th><th class="num">Optical margin, calc.</th><th>K3, run back</th><th class="num">Core × 4, calc. (K4)</th><th class="num">Deposit-out cash, 12 months, calc. (K5)</th><th>Source</th></tr></thead><tbody>{q_rows}</tbody></table></div>
<p class="foot">↓ means lower than the quarter before. 2024 margins use the old segments, and 2025 on uses the recast figures. K1, K4 and K5 test only on their dates, so these are readings. K5's line is today's figure, so every earlier quarter sits under it. K2, K6 and K7 did not fire: no customer said a deal shrank, no shares were sold, and 2028 was not dropped.</p>
<h3 style="margin-top:16px">K9: Meta, Amazon and Microsoft combined</h3><div class="wrap" style="max-width:380px"><table><thead><tr><th>Quarter end</th><th class="num">Capital spending, calc.</th></tr></thead><tbody>{k9_rows}</tbody></table></div>
<p class="foot">Filed cash flow lines, <a href="https://data.sec.gov/api/xbrl/companyfacts/CIK0001326801.json">Meta</a>, <a href="https://data.sec.gov/api/xbrl/companyfacts/CIK0001018724.json">Amazon</a> and <a href="https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json">Microsoft</a> SEC company facts, saved Nov. 3, 2026. The total matches <code>Catalysts/Cut in AI spending.md</code>.</p>
</details>
<details><summary>A drill for the limit: a made-up position</summary>
<p><b>Made up. The gates would have barred this buy, and it recommends nothing.</b> $5,000 of Corning at ${R["prices"][0][1]:.2f}, the first close in the window, on a $100,000 paper book, valued at today's $14.06 base low. Checked at each 10-Q and 10-K, as <code>Rules/sizing.md</code> says. It breaks the 5% limit once, at the {nice(R["drill_first"]["day"])} refresh. One Orange, then quiet, and no sale is forced.</p>
<div class="wrap" style="max-width:520px"><table><thead><tr><th>Refresh</th><th class="num">Close</th><th class="num">Lost if wrong, share of book</th><th>Limit</th></tr></thead><tbody>{drill_rows}</tbody></table></div><p class="foot">All calc. Close, {SRC_PRICE}. Base low, {SRC_RUN}.</p></details>

<h2>Every alert, with its source</h2>
<h3>The {T["orange"]} Oranges</h3>
<div class="wrap"><table class="stack"><thead><tr><th>Date</th><th>Level</th><th>What</th><th>Claim</th><th>Seen by</th><th>Source</th></tr></thead><tbody>{orange_rows}</tbody></table></div>
<details><summary>The {T["info_8k"]} 8-Ks and {T["info_news"]} news facts that end as Info</summary><div class="wrap"><table class="stack"><thead><tr><th>Date</th><th>Level</th><th>What</th><th>Claim</th><th>Seen by</th><th>Source</th></tr></thead><tbody>{drop_rows}</tbody></table></div>
<p class="foot">The other {T["info_filings"]} Info items are filings counted from the {LIST}: {T["insider"]} insider forms, 8 10-Qs and 10-Ks, and {T["info_filings"]-T["insider"]-8} others. The 424B5 of Sept. 11, 2026 merges with the share program's Orange.</p></details>

<h2>What you decided, Nov. 3, 2026</h2>
<div class="wrap"><table class="stack"><thead><tr><th>Question</th><th>Your decision</th></tr></thead><tbody>
<tr><th scope="row">Red before you own anything? On Nov. 2 you decided on no red level in the 8-K watcher while no holding is on file.</th><td>Yes. With nothing held, a Red only reopens the draft.</td></tr>
<tr><th scope="row">Which items are Red?</th><td>1.03, 2.04, 2.06, 3.01, 4.02, 5.01, and 1.02 with no 1.01. About one fire in seven years here (calc.).</td></tr>
<tr><th scope="row">A lone Q1 fall on K8 or K9 as Info?</th><td>Yes. The lines stay as set.</td></tr>
<tr><th scope="row">Close the news gap?</th><td>A weekly web search for each company with a thesis, by the playbook, read before any Orange goes out. Not set up yet.</td></tr>
<tr><th scope="row">SEC letters?</th><td>You approved adding UPLOAD to the radar's list, on Claude's wrong premise. The radar already lists them, so nothing is added. They need a reading, as in O10.</td></tr>
<tr><th scope="row">A kill line for C6?</th><td>Yes, on Solar's segment result. Its threshold and date are not set, so there is no line yet.</td></tr>
<tr><th scope="row">A schedule for the close?</th><td>No, for now. So O4 and O5 compare only when someone saves a close, and a crossing between those days can go unseen.</td></tr>
</tbody></table></div>
<p class="foot" style="margin-top:12px">One line in <code>CLAUDE.md</code> loads the rule. The two runs apply the map as Desktop tasks, with no one watching. A run that does not happen writes nothing and sends nothing. <code>dashboard/test_dashboard.py</code> bars alerts on price, so it would need changing if the dashboard shows O4 or O5. Keep this page on this computer, since it holds a Yahoo price and Moody's data. Tests: <code>sensors/alerts/test_alerts.py</code>.</p>
</main>{JS}</body></html>"""
OUT.write_text(page)
print("wrote", OUT.name, len(page))
