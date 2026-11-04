"""Cash lesson, step 3: draw cash-reserve.html from cache/results.json. No network.

    .venv/bin/python -I sensors/cash/draw.py
    .venv/bin/python -I sensors/cash/test_cash.py

Keep the page on this computer: Shiller's file carries S&P data and states no licence.
Rules/cash.md: approved by the owner, Nov. 3, 2026, as a fixed 15% with no gauge. A lesson, not advice, and not a market forecast.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
R = json.loads((HERE / "cache/results.json").read_text())
OUT = ROOT / "cash-reserve.html"
TOKENS = (HERE / "tokens.css").read_text()

SHILLER = '<a href="https://shillerdata.com/">Shiller, ie_data.xls, file dated Oct. 6, 2026, fetched Nov. 3, 2026</a>'
TREASURY = '<a href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&amp;field_tdr_date_value=2026">Treasury daily bill rates, through Nov. 2, 2026, fetched Nov. 3, 2026</a>'
DAMO = '<a href="https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html">Damodaran, Historical Returns, Jan. 2026, fetched Nov. 3, 2026</a>'
MULTPL = '<a href="https://www.multpl.com/shiller-pe/table/by-month">Multpl, read Nov. 3, 2026</a>'
MONTHS = "Jan. Feb. March April May June July Aug. Sept. Oct. Nov. Dec.".split(" ")
PAPER = 100_000


def usd(v):
    return f"${v:,.0f}"


def pct(v, d=1):
    return f"{v * 100:.{d}f}%"


def sign(v, d=1):
    return f"{v * 100:+.{d}f}%".replace("-", "−")


def mon(t):
    y, m = t.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


W = R["window"]
T = R["today"]
D0 = R["decade_2000"]
FIX = R["mixes"]["window"]["fixed"]
FIX2 = R["mixes"]["since_2000"]["fixed"]
BAND = R["mixes"]["window"]["band"]
BAND2 = R["mixes"]["since_2000"]["band"]
SERIES = R["series"]
CHECK = R["check"]
sp_end, bill_end, cpi_end = (W[k] * PAPER for k in ("sp", "bill", "cpi"))
GAP = sp_end - bill_end
BUY_POWER = W["bill"] / W["cpi"] - 1
ZERO_MONTHS = sum(s["rate"] < 0.25 for s in SERIES)
RATE_NOW = 4.13  # 13-week coupon equivalent, Nov. 2, 2026; test_cash.py reads it from the file
WAITS = {w["years"]: w for w in R["waits"]}
BB = {(b["years"], b["band"]): b for b in R["by_band"]}
Y = {y["year"]: y for y in R["years"]}
TIME = R["band_time"]


# ---------- the ladder, Rules/cash.md ----------
def walk(ideas, cash=30_000, port=PAPER):
    """Pay each hit, best score first, down to 15%, or to the 5% floor for a Strong thesis."""
    out = []
    for name, grade, size in ideas:
        stop = (5 if grade == "Strong" else 15) * port / 100
        pay = min(size, max(cash - stop, 0))
        out.append((name, pay))
        cash -= pay
    return out, cash


IDEAS = [("Made-up A", "Strong", 7_100), ("Made-up B", "Middling", 10_000)]
PAID, LEFT = walk(IDEAS)

# ---------- word claims are tested before they are written ----------
assert W["years"] == 20 and sp_end > bill_end > 0 and cpi_end > bill_end
assert W["bill_real_cagr"] < 0 and D0["bill"] > 1 > D0["sp"]
assert WAITS[10]["bills_won"] == 0 and WAITS[5]["bills_won"] < WAITS[1]["bills_won"]
assert ZERO_MONTHS == 108 and len(SERIES) == 241
assert T["cape"] > Y[2022]["jan"] > Y[2020]["jan"] and T["cape"] < Y[2000]["jan"]
assert Y[2000]["next_bill"] > Y[2000]["next_sp"] and all(Y[y]["next_sp"] > Y[y]["next_bill"] for y in (2008, 2020, 2022))
assert 20 <= Y[2020]["low"] < 30 and 20 <= Y[2022]["low"] < 30 and 20 <= R["low_2000_2003"]["cape"] < 30 and Y[2008]["low"] < 20
assert T["last_below_20"] == "2011-09" and T["last_below_30"] == "2023-10"
assert BAND["end"] < FIX["15"]["end"] and BAND2["end"] > FIX2["15"]["end"] and abs(BAND["worst"] - FIX["15"]["worst"]) < 1e-9
assert BB[(1, "High")]["share"] - BB[(1, "Low")]["share"] < .05
assert BB[(5, "High")]["share"] > BB[(5, "Middle")]["share"] > BB[(5, "Low")]["share"]
assert BB[(10, "High")]["share"] > BB[(10, "Middle")]["share"] > BB[(10, "Low")]["share"]
assert [p for _, p in PAID] == [7_100, 7_900] and LEFT == 15_000
assert CHECK["worst_year"] == 2024
assert abs(CHECK["shiller_sp"] / CHECK["damodaran_sp"] - 1) < .02 and abs(CHECK["treasury_bill"] / CHECK["damodaran_bill"] - 1) < .01
assert R["underwater_months"] == 57


# ---------- charts ----------
def x_scale(n, x0, x1):
    return lambda i: x0 + (x1 - x0) * i / (n - 1)


def path(vals, xs, ys):
    return "M" + "L".join(f"{xs(i):.1f},{ys(v):.1f}" for i, v in enumerate(vals))


def year_ticks(times, every):
    out = []
    for i, t in enumerate(times):
        y, m = t.split("-")
        if m == "01" and int(y) % every == 0:
            out.append((i, y))
    return out


def growth_chart():
    w, h, l, r, t, b = 1000, 400, 64, 150, 16, 30
    xs = x_scale(len(SERIES), l, w - r)
    top = 900_000
    ys = lambda v: h - b - (h - b - t) * v / top
    grid = "".join(f'<line class="grid" x1="{l}" x2="{w - r}" y1="{ys(v):.1f}" y2="{ys(v):.1f}"/><text class="ax" x="{l - 8}" y="{ys(v) + 4:.1f}" text-anchor="end">{"$" + format(v // 1000) + "K" if v else "$0"}</text>' for v in range(0, top + 1, 200_000))
    times = [s["t"] for s in SERIES]
    ticks = "".join(f'<text class="ax" x="{xs(i):.1f}" y="{h - 8}" text-anchor="middle">{y}</text>' for i, y in year_ticks(times, 4))
    sp = path([s["sp"] for s in SERIES], xs, ys)
    bill = path([s["bill"] for s in SERIES], xs, ys)
    cpi = path([s["cpi"] for s in SERIES], xs, ys)
    n = len(SERIES) - 1
    # hover data
    data = [{"t": mon(s["t"]), "a": round(s["sp"]), "b": round(s["bill"]), "c": round(s["cpi"]), "r": round(s["rate"], 2)} for s in SERIES]
    labels = (f'<text class="lv halo" x="{xs(n) + 8:.1f}" y="{ys(sp_end) + 4:.1f}">{usd(sp_end)}</text><text class="lab halo" x="{xs(n) + 8:.1f}" y="{ys(sp_end) + 20:.1f}">S&amp;P 500, dividends in</text>'
              f'<text class="lv halo" x="{xs(n) + 8:.1f}" y="{ys(cpi_end) - 12:.1f}">{usd(cpi_end)}</text><text class="lab halo" x="{xs(n) + 8:.1f}" y="{ys(cpi_end) + 3:.1f}">to keep up with prices</text>'
              f'<text class="lv halo" x="{xs(n) + 8:.1f}" y="{ys(bill_end) + 22:.1f}">{usd(bill_end)}</text><text class="lab halo" x="{xs(n) + 8:.1f}" y="{ys(bill_end) + 37:.1f}">Treasury bills</text>')
    return f'''<svg id="g1" viewBox="0 0 {w} {h}" role="img" aria-label="$100,000 from {mon(W['start'])} to {mon(W['end'])}: S&amp;P 500 with dividends {usd(sp_end)}, Treasury bills {usd(bill_end)}, prices {usd(cpi_end)}.">
{grid}{ticks}<path d="{cpi}" fill="none" stroke="var(--s0)" stroke-width="2" stroke-dasharray="5 4"/><path d="{bill}" fill="none" stroke="var(--s2)" stroke-width="2"/><path d="{sp}" fill="none" stroke="var(--s1)" stroke-width="2"/>{labels}
<line id="g1x" class="cross" x1="0" x2="0" y1="{t}" y2="{h - b}" visibility="hidden"/><rect class="hit" x="{l}" y="{t}" width="{w - r - l}" height="{h - b - t}" data-l="{l}" data-w="{w - r - l}"/></svg>''', data


def rate_chart():
    w, h, l, r, t, b = 1000, 170, 64, 150, 12, 28
    xs = x_scale(len(SERIES), l, w - r)
    ys = lambda v: h - b - (h - b - t) * v / 6
    grid = "".join(f'<line class="grid" x1="{l}" x2="{w - r}" y1="{ys(v):.1f}" y2="{ys(v):.1f}"/><text class="ax" x="{l - 8}" y="{ys(v) + 4:.1f}" text-anchor="end">{v}%</text>' for v in (0, 2, 4, 6))
    times = [s["t"] for s in SERIES]
    ticks = "".join(f'<text class="ax" x="{xs(i):.1f}" y="{h - 8}" text-anchor="middle">{y}</text>' for i, y in year_ticks(times, 4))
    p = path([s["rate"] for s in SERIES], xs, ys)
    last = SERIES[-1]["rate"]
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="The 13-week bill rate each month. It sat under 0.25% in {ZERO_MONTHS} of {len(SERIES)} months.">{grid}{ticks}<path d="{p}" fill="none" stroke="var(--s2)" stroke-width="2"/><text class="lv halo" x="{xs(len(SERIES) - 1) + 8:.1f}" y="{ys(last) + 4:.1f}">{last:.2f}%</text><text class="lab halo" x="{xs(len(SERIES) - 1) + 8:.1f}" y="{ys(last) + 19:.1f}">{mon(SERIES[-1]['t'])} average</text></svg>'''


def gauge_chart():
    G = R["gauge"]
    w, h, l, r, t, b = 1000, 390, 44, 96, 14, 30
    xs = x_scale(len(G), l, w - r)
    top = 50
    ys = lambda v: h - b - (h - b - t) * v / top
    bands = (f'<rect x="{l}" y="{ys(top):.1f}" width="{w - r - l}" height="{ys(30) - ys(top):.1f}" fill="var(--s2)" opacity=".09"/>'
             f'<rect x="{l}" y="{ys(20):.1f}" width="{w - r - l}" height="{ys(0) - ys(20):.1f}" fill="var(--s1)" opacity=".09"/>'
             f'<text class="lab" x="{w - r + 8}" y="{ys(40):.1f}">High</text><text class="ax" x="{w - r + 8}" y="{ys(40) + 16:.1f}">30 and up</text>'
             f'<text class="lab" x="{w - r + 8}" y="{ys(25) + 4:.1f}">Middle</text><text class="ax" x="{w - r + 8}" y="{ys(25) + 20:.1f}">20 to 30</text>'
             f'<text class="lab" x="{w - r + 8}" y="{ys(10):.1f}">Low</text><text class="ax" x="{w - r + 8}" y="{ys(10) + 16:.1f}">under 20</text>')
    grid = "".join(f'<line class="grid" x1="{l}" x2="{w - r}" y1="{ys(v):.1f}" y2="{ys(v):.1f}"/><text class="ax" x="{l - 8}" y="{ys(v) + 4:.1f}" text-anchor="end">{v}</text>' for v in range(0, top + 1, 10))
    times = [g["t"] for g in G]
    ticks = "".join(f'<text class="ax" x="{xs(i):.1f}" y="{h - 8}" text-anchor="middle">{y}</text>' for i, y in year_ticks(times, 4))
    start = times.index(W["start"])
    win = (f'<line x1="{xs(start):.1f}" x2="{xs(start):.1f}" y1="{ys(top):.1f}" y2="{ys(0):.1f}" stroke="var(--axis)" stroke-dasharray="4 4"/>'
           f'<text class="ax halo" x="{xs(start) + 6:.1f}" y="{ys(top) + 14:.1f}">the twenty years start, {mon(W["start"])}</text>')
    marks = [("2000-01", f"Jan. 2000: {Y[2000]['jan']:.1f}", 8, -8), ("2008-11", f"Nov. 2008: {Y[2008]['low']:.1f}", -40, 18),
             ("2020-03", f"March 2020: {Y[2020]['low']:.1f}", -40, 20), ("2022-01", f"Jan. 2022: {Y[2022]['jan']:.1f}", -44, -10),
             ("2022-10", f"Oct. 2022: {Y[2022]['low']:.1f}", 0, 20), (T["month"], f"{T['cape']:.1f}", 8, 4)]
    by_t = {g["t"]: g["cape"] for g in G}
    dots = ""
    for m, label, dx, dy in marks:
        i = times.index(m)
        dots += f'<circle cx="{xs(i):.1f}" cy="{ys(by_t[m]):.1f}" r="4.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/><text class="lv halo" x="{xs(i) + dx:.1f}" y="{ys(by_t[m]) + dy:.1f}">{label}</text>'
    p = path([g["cape"] for g in G], xs, ys)
    data = [{"t": mon(g["t"]), "a": round(g["cape"], 1)} for g in G]
    return f'''<svg id="g2" viewBox="0 0 {w} {h}" role="img" aria-label="Shiller CAPE monthly from Jan. 2000 to {mon(T['month'])}, with the three bands.">{bands}{grid}{ticks}{win}<path d="{p}" fill="none" stroke="var(--s1)" stroke-width="2"/>{dots}
<line id="g2x" class="cross" x1="0" x2="0" y1="{t}" y2="{h - b}" visibility="hidden"/><rect class="hit" x="{l}" y="{t}" width="{w - r - l}" height="{h - b - t}" data-l="{l}" data-w="{w - r - l}"/></svg>''', data


def ladder_chart():
    w, h, l, r, t, b = 1000, 104, 16, 24, 8, 34
    top = 40
    xs = lambda v: l + (w - r - l) * v / top
    out = "".join(f'<line class="grid" x1="{xs(v):.1f}" x2="{xs(v):.1f}" y1="{t}" y2="{h - b}"/><text class="ax" x="{xs(v):.1f}" y="{h - 12}" text-anchor="middle">{v}%</text>' for v in range(0, top + 1, 5))
    y, bh = t + 4, h - t - b - 8
    parts = [("b0", 0, 5, "The floor", "Never spent on a buy."), ("b3", 5, 15, "5% to 15% of the portfolio", "Only a Strong thesis may spend this part."),
             ("b1", 15, top, "Cash above 15%", "Any hit that clears the gates may spend this part.")]
    for cls, a_, b_, head, body in parts:
        gap = 2 if b_ < top else 0
        out += f'<rect class="{cls}" data-tip="&lt;b&gt;{head}&lt;/b&gt;&lt;br&gt;{body}" x="{xs(a_):.1f}" y="{y}" width="{xs(b_) - xs(a_) - gap:.1f}" height="{bh}" rx="3"/>'
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Cash as a share of the portfolio: under 5% is never spent on a buy, 5% to 15% only a Strong thesis may spend, above 15% any hit that clears the gates may spend.">{out}</svg>'


G1, D1 = growth_chart()
G2, D2 = gauge_chart()


# ---------- tables ----------
def wait_rows():
    out = ""
    for n, x in WAITS.items():
        out += (f'<tr><th scope="row"><span style="white-space:nowrap">{n} year{"s" if n > 1 else ""}</span></th><td class="n">{x["bills_won"]} of {x["starts"]}</td><td class="n">{pct(x["share"], 0)}</td>'
                f'<td class="n">{usd(x["sp_median"] * PAPER)}</td><td class="n">{usd(x["bill_median"] * PAPER)}</td><td class="n">{usd(x["sp_worst"] * PAPER)}</td></tr>')
    return out


def year_rows():
    out = ""
    for y in (2000, 2008, 2020, 2022):
        v = Y[y]
        nxt = f'{v["next_years"]:g} years to {mon(v["next_end"])}'
        out += (f'<tr><th scope="row">{y}</th><td class="n">{v["jan"]:.1f}</td><td class="n">{v["high"]:.1f}<small>{mon(v["high_m"])}</small></td><td class="n">{v["low"]:.1f}<small>{mon(v["low_m"])}</small></td>'
                f'<td class="n">{sign(v["next_sp"])}</td><td class="n">{sign(v["next_bill"])}</td><td><small>{nxt}</small></td></tr>')
    out += f'<tr class="total"><th scope="row">Today</th><td class="n">{T["cape"]:.1f}<small>{mon(T["month"])}</small></td><td class="n">n/a</td><td class="n">n/a</td><td class="n">unknown</td><td class="n">unknown</td><td><small>not a forecast</small></td></tr>'
    return out


def band_rows():
    out = ""
    for name, sub in (("Low", "under 20"), ("Middle", "20 to 30"), ("High", "30 and up")):
        c = [BB[(n, name)] for n in (1, 5, 10)]
        out += (f'<tr><th scope="row">{name}<small>{sub}</small></th><td class="n">{pct(TIME["window"][name], 0)}</td><td class="n">{pct(TIME["since_1881"][name], 0)}</td>'
                + "".join(f'<td class="n">{pct(x["share"], 0)}<small>of {x["starts"]} starts</small></td>' for x in c) + "</tr>")
    return out


def cost_rows():
    top = FIX["0"]["end"]
    out = ""
    for p in ("0", "5", "15", "25", "50"):
        v = FIX[p]
        out += (f'<tr><th scope="row">{p}%</th><td class="n">{usd(v["end"])}</td><td class="n">{"none" if p == "0" else "−" + usd(top - v["end"])}</td>'
                f'<td class="n">{pct(v["cagr"])}</td><td class="n">{sign(v["worst"])}</td></tr>')
    out += (f'<tr class="total"><th scope="row">The bands, rejected<small>5%, 15%, 25%</small></th><td class="n">{usd(BAND["end"])}</td><td class="n">−{usd(top - BAND["end"])}</td>'
            f'<td class="n">{pct(BAND["cagr"])}</td><td class="n">{sign(BAND["worst"])}</td></tr>')
    return out


def walk_rows():
    return "".join(f'<tr><th scope="row">{n}</th><td>{g}</td><td class="n">{usd(z)}</td><td class="n">{usd(p)}</td></tr>' for (n, g, z), (_, p) in zip(IDEAS, PAID))


CSS = """*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}
h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
h3{font-size:15.5px;margin:20px 0 4px;font-weight:650}
p,ul.txt,ol.txt{margin:0 0 10px;max-width:75ch}ul.txt,ol.txt{padding-left:20px}.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}code{font-size:.92em}
.note{font-size:13.5px;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:80ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:5px}
.word{border-left:3px solid var(--axis);padding:2px 0 2px 14px;margin:14px 0;max-width:75ch}.word p{margin:0 0 6px}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:14px;height:10px;margin-right:7px;border-radius:3px}.k0{background:var(--s0)}.k1{background:var(--s1)}.k3{background:var(--s2)}
.kd{height:0;border-top:2px dashed var(--s0);border-radius:0;vertical-align:3px}
.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:640px;height:auto;font:13px system-ui,-apple-system,"Segoe UI",sans-serif}
svg text{fill:var(--ink-2)}svg .lv{fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}svg .ax{fill:var(--muted)}svg .lab{fill:var(--ink-2)}
svg .halo{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
.grid{stroke:var(--grid);stroke-width:1}.cross{stroke:var(--axis);stroke-width:1}.hit{fill:transparent;cursor:crosshair}
.b1{fill:var(--s1)}.b3{fill:var(--s2)}.b0{fill:var(--s0)}
figure{margin:0}figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:85ch}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.14)}
.wrap{overflow-x:auto;margin-top:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600}
th small,td small{display:block;font-weight:400;color:var(--muted);font-size:12px;line-height:1.35}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}thead .n{white-space:normal}
.total th,.total td{font-weight:650;border-top:1px solid var(--axis)}.total small{font-weight:400}
footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--border);color:var(--muted);font-size:13px}
"""

JS = """const tip=document.getElementById('tip');
document.querySelectorAll('.scroll.end').forEach(el=>{el.scrollLeft=el.scrollWidth}); // on a narrow screen, open on the newest months
function place(e){const w=tip.offsetWidth,h=tip.offsetHeight;tip.style.left=Math.min(e.clientX+14,innerWidth-w-8)+'px';tip.style.top=Math.max(8,e.clientY-h-10)+'px'}
document.querySelectorAll('[data-tip]').forEach(el=>{
  el.addEventListener('mousemove',e=>{tip.innerHTML=el.dataset.tip;tip.hidden=false;place(e)});
  el.addEventListener('mouseleave',()=>{tip.hidden=true});
});
const fmt=v=>'$'+v.toLocaleString('en-US');
function cross(id,data,html){
  const svg=document.getElementById(id),r=svg.querySelector('.hit'),x=svg.querySelector('.cross');
  const l=+r.dataset.l,w=+r.dataset.w;
  r.addEventListener('mousemove',e=>{
    const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());
    const i=Math.max(0,Math.min(data.length-1,Math.round((p.x-l)/w*(data.length-1))));
    const px=l+w*i/(data.length-1);x.setAttribute('x1',px);x.setAttribute('x2',px);x.setAttribute('visibility','visible');
    tip.innerHTML=html(data[i]);tip.hidden=false;place(e)});
  r.addEventListener('mouseleave',()=>{tip.hidden=true;x.setAttribute('visibility','hidden')});
}
cross('g1',D1,d=>`<b>${d.t}</b><br>S&amp;P 500, dividends in: ${fmt(d.a)}<br>Treasury bills: ${fmt(d.b)}<br>To keep up with prices: ${fmt(d.c)}<br><small>Bill rate that month: ${d.r}%</small>`);
cross('g2',D2,d=>`<b>${d.t}</b><br>Gauge: ${d.a}`);"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cash Reserve Lesson</title>
<style>
{TOKENS}{CSS}</style></head><body><main>
<h1>Cash is a position, and it has a price</h1>
<p class="lede">Cash pays for the right to say no. Over the last twenty years that right was expensive. This page shows what it cost, what one gauge of the market said, and the reserve you approved.</p>
<p class="note"><strong>A lesson, not advice, and not a market forecast.</strong> You approved <code>Rules/cash.md</code> on Nov. 3, 2026, as a fixed 15% with no gauge. All history is before tax and costs. Stay on this computer: the Shiller file carries S&amp;P data and states no licence.</p>

<div class="answer"><strong>The three answers</strong> (all calc.)
<ul>
<li><strong>What waiting cost:</strong> $100,000 from {mon(W['start'])} to {mon(W['end'])} became {usd(bill_end)} in Treasury bills and {usd(sp_end)} in the S&amp;P 500 with dividends. Prices rose so much that it took {usd(cpi_end)} to stand still, so bills lost {pct(-BUY_POWER)} of their buying power.</li>
<li><strong>The gauge today:</strong> the Shiller CAPE reads {T['cape']:.1f} ({mon(T['month'])}), higher than {pct(T['rank_all'])} of months since {T['first'][:4]}. In Jan. 2000 it read {Y[2000]['jan']:.1f}, and cash beat stocks over the next five years. In Jan. 2022 it read {Y[2022]['jan']:.1f}, and stocks won by a wide margin. A high reading did not say what came next.</li>
<li><strong>The rule you approved:</strong> keep 15% of the portfolio as normal, and never spend the last 5% on a buy. Only a thesis graded Strong may spend below 15%. The market's level plays no part, because the gauge did not earn its place.</li>
</ul></div>

<h2>1. What cash earned against the S&amp;P 500</h2>
<div class="card"><figure>
<ul class="legend"><li><span class="key k1"></span>S&amp;P 500, dividends in</li><li><span class="key k3"></span>Treasury bills</li><li><span class="key kd"></span>What kept up with prices</li></ul>
<div class="scroll end">{G1}</div>
<figcaption>$100,000 at the start, nothing added. Stocks fell {pct(-W['sp_worst'], 0)} to {mon(W['sp_worst_month'])} and took {R['underwater_months']} months to get back, on monthly averages. Calc. from {SHILLER} and {TREASURY}.</figcaption></figure></div>

<div class="wrap"><table>
<thead><tr><th scope="col">{mon(W['start'])} to {mon(W['end'])}</th><th class="n" scope="col">$100,000 became</th><th class="n" scope="col">A year</th><th class="n" scope="col">A year, after prices</th><th class="n" scope="col">Worst fall, after prices for bills</th></tr></thead>
<tbody><tr><th scope="row">S&amp;P 500, dividends in</th><td class="n">{usd(sp_end)}</td><td class="n">{pct(W['sp_cagr'])}</td><td class="n">{pct(W['sp_real_cagr'])}</td><td class="n">{sign(W['sp_worst'])}</td></tr>
<tr><th scope="row">Treasury bills, 13 weeks</th><td class="n">{usd(bill_end)}</td><td class="n">{pct(W['bill_cagr'])}</td><td class="n">{sign(W['bill_real_cagr'])}</td><td class="n">{sign(W['bill_real_worst'])}<small>to {mon(W['bill_real_worst_month'])}</small></td></tr>
<tr><th scope="row">Prices (CPI)</th><td class="n">{usd(cpi_end)}</td><td class="n">{pct(W['cpi_cagr'])}</td><td class="n">n/a</td><td class="n">n/a</td></tr></tbody></table></div>

<div class="word"><p><strong>Opportunity cost, in plain words.</strong> It is what your money could have earned doing the next best thing. It never shows on a statement. Your cash balance only goes up, so waiting feels free. It was not: the gap here is {usd(GAP)} on $100,000 (calc.).</p></div>

<h3>Bills pay what the day pays</h3>
<div class="card"><figure><div class="scroll end">{rate_chart()}</div>
<figcaption>Average 13-week rate each month. It sat under 0.25% in {ZERO_MONTHS} of {len(SERIES)} months. It was {RATE_NOW:.2f}% on Nov. 2, 2026. Calc. from {TREASURY}.</figcaption></figure></div>

<h3>What waiting cost, by how long you waited</h3>
<p>Take every start month in the twenty years. Wait in bills, or own the index, for the same stretch. Waiting "won" if bills ended ahead, so you could have bought more later.</p>
<div class="wrap"><table>
<thead><tr><th scope="col">Wait</th><th class="n" scope="col">Waiting won</th><th class="n" scope="col">Share</th><th class="n" scope="col">$100,000 in the index, middle case</th><th class="n" scope="col">$100,000 in bills, middle case</th><th class="n" scope="col">$100,000 in the index, worst case</th></tr></thead>
<tbody>{wait_rows()}</tbody></table></div>
<p class="note" style="margin-top:8px">Start months overlap, so these are not separate tests. Calc. from the same two sources.</p>

<h3>Three fair objections to that picture</h3>
<ul class="txt">
<li><strong>The window flatters stocks.</strong> It starts a year before one crash and runs through a long rise. From Jan. 2000 to Dec. 2009, bills made {sign(D0['bill'] - 1)} and the S&amp;P 500 {sign(D0['sp'] - 1)} (calc., {SHILLER}; {DAMO}). Waiting won that whole decade.</li>
<li><strong>Over all the years we can test, waiting won more often.</strong> Since 1928, bills beat stocks over five years in {pct(R['waits_long'][3]['share'], 0)} of start months, against {pct(WAITS[5]['share'], 0)} in these twenty (calc., same sources).</li>
<li><strong>The S&amp;P 500 is a yardstick, not your alternative.</strong> Override 6 bars an index core. Your real alternative is your own stocks, and nobody can know that return in advance.</li>
</ul>

<h2>2. One gauge of the whole market</h2>
<p><strong>The gauge is the Shiller CAPE:</strong> the S&amp;P 500's price divided by ten years of earnings, averaged and adjusted for prices. You already use the same idea: your base low is a ten-year average of normal earnings. It says how much the market pays for what companies have earned. It says nothing about when that changes.</p>
<div class="card"><figure>
<div class="scroll end">{G2}</div>
<figcaption>Monthly, from Jan. 2000. The chart starts before your twenty years, because you asked about 2000. The bands are the ones tested and rejected, chosen with hindsight. Calc. from {SHILLER}; his October price is the Oct. 2 close.</figcaption></figure></div>

<div class="wrap"><table>
<thead><tr><th scope="col">Year</th><th class="n" scope="col">Gauge, January</th><th class="n" scope="col">Year's high</th><th class="n" scope="col">Year's low</th><th class="n" scope="col">S&amp;P 500, from that January</th><th class="n" scope="col">Bills, same stretch</th><th scope="col">Stretch</th></tr></thead>
<tbody>{year_rows()}</tbody></table></div>
<p class="note" style="margin-top:8px">Calc. from {SHILLER} and, for 2000 and 2001, {DAMO}; Treasury after that. A second copy, {MULTPL} through a summarizing fetch, gives 43.77, 30.99 and 36.94 for January of 2000, 2020 and 2022, and 40.13 on Oct. 30, 2026, the newest reading found. Its terms were not read.</p>

<ul class="txt">
<li><strong>The lows did not reach Low.</strong> The gauge's low was {R['low_2000_2003']['cape']:.1f} in {mon(R['low_2000_2003']['month'])}, {Y[2020]['low']:.1f} in {mon(Y[2020]['low_m'])} and {Y[2022]['low']:.1f} in {mon(Y[2022]['low_m'])}. Only 2008 to 2011 went under 20, and the last month under 20 was {mon(T['last_below_20'])}. Anyone waiting for that reading has waited fifteen years.</li>
<li><strong>The yardstick has moved.</strong> The median since {T['first'][:4]} is {T['median_all']:.1f}. The median of the last twenty years is {T['median_window']:.1f}. The gauge has been at 30 or more every month since {mon(T['last_below_30'])}. Shiller's own notes say buybacks may affect the level of the CAPE (<a href="http://www.econ.yale.edu/~shiller/data.htm">Shiller's data page, undated, retrieved Nov. 3, 2026</a>). This page cannot say how much of the higher readings is real change.</li>
</ul>

<h3>Did the gauge sort what came next?</h3>
<p>Since 1928, how often bills beat the S&amp;P 500 from each band:</p>
<div class="wrap"><table>
<thead><tr><th scope="col">Gauge at the start</th><th class="n" scope="col">Time there, last 20 years</th><th class="n" scope="col">Time there, since {T['first'][:4]}</th><th class="n" scope="col">Bills won, next 1 year</th><th class="n" scope="col">Bills won, next 5 years</th><th class="n" scope="col">Bills won, next 10 years</th></tr></thead>
<tbody>{band_rows()}</tbody></table></div>
<p style="margin-top:10px"><strong>Claude's reading:</strong> over one year it sorted almost nothing. Over five and ten years it sorted more, and your rule 1 holds for five. But the High row is thin. Its ten-year starts come from 1929 and 1997 to 2002, so it is close to two events. Its five-year starts add 2017 to 2021. Calc. from {SHILLER}, {TREASURY} and {DAMO}. Before 2002 each month's bill rate is that year's average.</p>

<div class="word"><p><strong>Fear of missing out, in plain words.</strong> It is the urge to buy because a price is rising and other people are getting rich, not because the value is there. It feels like a reason, but it is only a feeling about other people's gains.</p>
<p>It has a twin: fear of a crash, which says "wait" for the same empty reason. A high gauge can feed the second one. Your buy-below answers both, because it never asks how you feel. Corning closed at $123.20 on Nov. 2, 2026, 4.3 times its $28.97 buy-below (calc., <code>sensors/valuation/runs/2026-11-03-01.md</code>, Nov. 3, 2026; <a href="https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&amp;interval=1d">Yahoo through yfinance, fetched Nov. 2, 2026</a>). Rule 4's job is to make saying no cheap to live with. It does not make it free.</p></div>

<h2>3. The rule: normal 15%, floor 5%, no gauge</h2>
<p>Full text: <code>Rules/cash.md</code>. The figures are a judgment, not a measured result.</p>
<div class="card"><figure>
<ul class="legend"><li><span class="key k0"></span>The floor: never spent on a buy</li><li><span class="key k3"></span>Only a Strong thesis may spend it</li><li><span class="key k1"></span>Any hit that clears the gates may spend it</li></ul>
<div class="scroll">{ladder_chart()}</div>
<figcaption>Cash as a share of the portfolio. Hover for what each part may do.</figcaption></figure></div>

<ul class="txt">
<li><strong>Why these figures.</strong> The floor, 5%, is the Thin cap: one small position, always payable, and rule 4's "always". Normal, 15%, is the floor plus one Middling position at its 10% cap. They come from `Rules/sizing.md`, not from the data.</li>
</ul>

<h3>When a buy-below is hit</h3>
<ol class="txt">
<li><strong>Check it is a real hit.</strong> Refresh value from the newest 10-Q or 10-K. Then the three gates in `Rules/sizing.md`. A falling price can get ahead of filed numbers.</li>
<li><strong>Size it.</strong> The approved method gives the most it can be. No schedule and no averaging in.</li>
<li><strong>Pay from cash above 15%.</strong> Any grade.</li>
<li><strong>From 15% down to the floor: Strong only.</strong> Thin and Middling stop at 15% and buy smaller, or not at all.</li>
<li><strong>Several hits at once:</strong> highest score first, then highest coverage.</li>
<li><strong>Refill only from new money,</strong> interest, dividends, trims or the sale of a broken thesis. Never sell a sound position to refill.</li>
</ol>

<h3>A walk on paper</h3>
<p>$100,000 portfolio, $70,000 in made-up positions, $30,000 cash. Made-up A (Strong, $7,100) and Made-up B (Middling, $10,000) from <code>sizing.html</code> hit on the same day. Both are invented, and so is the holding of $70,000.</p>
<div class="wrap"><table>
<thead><tr><th scope="col">Idea</th><th scope="col">Grade</th><th class="n" scope="col">Sizing allows</th><th class="n" scope="col">It buys</th></tr></thead>
<tbody>{walk_rows()}</tbody></table></div>
<p class="note" style="margin-top:8px">All calc. A goes first, on score. B stops at 15%, so it buys {usd(PAID[1][1])}, not $10,000. Cash left: {usd(LEFT)}. With the gauge at today's reading, B would have bought $0. That was the gauge's price, and you declined to pay it.</p>

<h3>What the reserve itself would have cost</h3>
<div class="wrap"><table>
<thead><tr><th scope="col">Reserve in bills</th><th class="n" scope="col">$100,000 became</th><th class="n" scope="col">Against no reserve</th><th class="n" scope="col">A year</th><th class="n" scope="col">Worst fall</th></tr></thead>
<tbody>{cost_rows()}</tbody></table></div>
<p class="note" style="margin-top:8px">{mon(W['start'])} to {mon(W['end'])}, the rest in the S&amp;P 500, reset once a year. Calc. <strong>This is a sum, not a plan.</strong> Resetting means selling, which override 7 bars, and it holds an index, which override 6 bars. It leaves out what the cash could have bought at a hit, which is the point of holding it.</p>
<ul class="txt">
<li><strong>The bands did not earn their place.</strong> Against a fixed 15%, they ended {usd(FIX['15']['end'] - BAND['end'])} behind in these twenty years and {usd(BAND2['end'] - FIX2['15']['end'])} ahead since Jan. 2000 (calc.). The worst fall from {mon(W['start'])} was the same, because the gauge read Middle going into 2008. So you took the fixed 15%.</li>
<li><strong>The big cost is not the reserve.</strong> Cash has no ceiling in your rules, because what is not bought stays cash. At a 50% loss if wrong, a position is 10%, so five positions leave 50% in cash even with the reserve met. In this sum 50% cash ended at {usd(FIX['50']['end'])}, against {usd(FIX['15']['end'])} at 15%. So the rule adds a review, not a push: if cash stays above 50% for 24 months, Claude asks whether your search is wide enough. It never loosens the buy test.</li>
</ul>

<h2>4. What you decided, Nov. 3, 2026</h2>
<ol class="txt">
<li><strong>A fixed 15%, with no gauge.</strong> The gauge did not earn its place, so override 5 needs no exception, and rule 6 stands untouched.</li>
<li><strong>`Rules/sizing.md` now says "Pay only as `Rules/cash.md` allows."</strong> It used to say "Pay only from cash above the reserve", which would have barred spending the reserve.</li>
<li><strong>The review stays:</strong> cash above 50% for 24 months in a row raises a question about your search, and never loosens the buy test.</li>
<li><strong>Claude's reading, for you to correct:</strong> that this also keeps the 5% floor and Strong only below 15%, since you changed neither.</li>
<li><strong>Still open: your cash today.</strong> <code>Portfolio/</code> has no holdings or cash on file, so this page does not say where you stand.</li>
</ol>
<p class="note">The value-investing skill differs in two places: it runs several market tests, and it turns them into a place in a 25% to 75% stock band with a ten-year return estimate. Neither was used.</p>

<h2>How this was built</h2>
<ul class="txt">
<li><strong>Stocks:</strong> Shiller's real total return series, turned back into dollars with his CPI ({SHILLER}). His prices are monthly averages, so the worst fall and the wait to recover are smoother than daily figures. His Sept. and Oct. CPI are estimates.</li>
<li><strong>Bills:</strong> the 13-week coupon-equivalent rate, averaged by month and rolled monthly ({TREASURY}). Before 2002, Damodaran's yearly average ({DAMO}).</li>
<li><strong>Second copy:</strong> for 2007 to 2025 Shiller's stocks grew {CHECK['shiller_sp']:.2f} times and Damodaran's {CHECK['damodaran_sp']:.2f} times. Bills grew {CHECK['treasury_bill']:.3f} times and {CHECK['damodaran_bill']:.3f} times (calc.). Single years differ by up to {pct(CHECK['worst_year_gap'])}, in {CHECK['worst_year']}, because Shiller's are monthly averages and Damodaran's run from year end to year end.</li>
<li><strong>Terms:</strong> FRED limits scripts and caching (<a href="https://fred.stlouisfed.org/legal/">FRED terms, undated, retrieved Nov. 2, 2026</a>), so nothing was scripted from it. Damodaran's bill sheet is itself drawn from FRED. Neither Shiller's page nor Damodaran's states a licence, and Shiller's disclaimer says the data is not a forecast or advice. A <a href="https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-bill-rates">data.gov record, undated, retrieved Nov. 3, 2026</a>, lists Treasury's bill rates as CC0, through a search summary. Treasury's own page was not found saying so.</li>
<li><strong>Left out:</strong> tax, fund fees and trading costs. This history is one market, the U.S., so it says nothing about how others did.</li>
</ul>

<footer>Built by <code>sensors/cash/draw.py</code> on Nov. 3, 2026 and checked by <code>sensors/cash/test_cash.py</code>. A lesson, not advice, and not a market forecast. Nothing here is a recommendation to buy or sell.</footer>
<div id="tip" hidden></div>
</main><script>
const D1={json.dumps(D1, separators=(",", ":"))};
const D2={json.dumps(D2, separators=(",", ":"))};
{JS}
</script></body></html>
"""
HTML = HTML.replace("`Rules/cash.md`", "<code>Rules/cash.md</code>").replace("`Rules/sizing.md`", "<code>Rules/sizing.md</code>").replace("`when-to-buy`", "<code>when-to-buy</code>")
OUT.write_text(HTML)
print("wrote", OUT, len(HTML))
print(PAID, LEFT)
