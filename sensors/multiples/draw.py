"""Draw multiples.html from saved data. This script makes no network requests.

Run from the project root:
    .venv/bin/python sensors/multiples/draw.py
Every number in the words comes from the data here, not typed by hand, except the
figures in NOTE, each read from Companies/Corning.md and checked by test_multiples.py.
"""

import datetime as dt
import html
import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import multiples as m

OUT = m.ROOT / "multiples.html"
MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
Q = "https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm"
K = "https://www.sec.gov/Archives/edgar/data/24741/000002474126000124/glw-20251231.htm"
K18 = "https://www.sec.gov/Archives/edgar/data/24741/000002474118000010/glw-20171231x10k.htm"
K21 = "https://www.sec.gov/Archives/edgar/data/24741/000143774922003247/glw20211231_10k.htm"
K8 = "https://www.sec.gov/Archives/edgar/data/24741/000120677426000273/glw4631061-8k.htm"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
AAA = "https://fred.stlouisfed.org/series/AAA"
DGS = "https://fred.stlouisfed.org/series/DGS10"
TERMS = "https://stockanalysis.com/terms-of-use/"

# Read from Companies/Corning.md, Nov. 3, 2026. $M unless marked.
NOTE = {
    "fcf_no_line": 1505, "fcf_both": 1256, "fcf_no_received": 971, "stock_pay": 368, "lease_principal": 428,
    "core_q": [0.72, 0.70, 0.78, 0.91], "normal_2025": 1.77, "normal_avg": 1.10,
    "op_leases": 971, "pension": 625, "contract": 2701, "sold": 442, "fx_gain_9m": 212, "investments": 470,
    "diluted_m": 871, "prefunded_m": 3, "warrant_m": 15, "warrant_strike": 180, "conv_m": 115,
}


def e(text):
    return html.escape(str(text), quote=True)


def link(url, text):
    return f'<a href="{e(url)}">{e(text)}</a>'


def nice(text):
    d = dt.date.fromisoformat(text[:10])
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def mon(text):
    d = dt.date.fromisoformat(text[:10])
    return f"{MONTHS[d.month - 1]} {d.year}"


def musd(v):
    v = v / 1e6
    return f"−${abs(v):,.0f}M" if v < 0 else f"${v:,.0f}M"


def x(v, n=1):
    return "n.m." if v is None else f"{v:,.{n}f}x"


def pc(v, n=2):
    return ("−" if v < 0 else "") + f"{abs(v):.{n}f}%"


def eps_fmt(v):
    return ("−" if v < 0 else "") + f"${abs(v):.2f}"


def year_of(p):
    return p["date"][:4]


def t_of(day):
    d = dt.date.fromisoformat(day)
    return d.year + (d.timetuple().tm_yday - 1) / 365.25


def line_chart(cid, label, series, refs, ymin, ymax, ticks, fmt, height=330, zero=False):
    """One y scale. Values above ymax are clipped and labelled at the top edge. None is a gap."""
    W, L, R, T, B = 1000, 54, 196, 30, 34
    x0, x1 = 2016.9, 2026.95
    sx = lambda v: L + (v - x0) / (x1 - x0) * (W - L - R)
    sy = lambda v: T + (ymax - v) / (ymax - ymin) * (height - T - B)
    out = [f'<svg id="{cid}" viewBox="0 0 {W} {height}" role="img" aria-label="{e(label)}">']
    out.append(f'<clipPath id="{cid}c"><rect x="{L}" y="{T}" width="{W - L - R + 6}" height="{height - T - B}"/></clipPath>')
    for tick in ticks:
        y = sy(tick)
        style = 'stroke="var(--axis)"' if (zero and tick == 0) else 'stroke="var(--grid)"'
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" {style}/>')
        out.append(f'<text class="ax" x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{e(fmt(tick))}</text>')
    dates = [d for d, _ in series[0]["points"]]
    for d in dates:
        lab = "Now" if d[:4] == "2026" else "’" + d[2:4]
        out.append(f'<text class="ax" x="{sx(t_of(d)):.1f}" y="{height - 12}" text-anchor="middle">{lab}</text>')
    for ref in refs:
        y = sy(ref["value"])
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--s0)" stroke-width="1.5" stroke-dasharray="{ref["dash"]}"/>')
    labels = []
    for s in series:
        run = []
        for d, v in s["points"]:
            if v is None:
                if len(run) > 1:
                    out.append(f'<polyline clip-path="url(#{cid}c)" fill="none" stroke="var({s["color"]})" stroke-width="2" {s.get("attr", "")} points="{" ".join(run)}"/>')
                run = []
                out.append(f'<text class="ax" x="{sx(t_of(d)):.1f}" y="{sy(ymin) - 6:.1f}" text-anchor="middle">{s.get("gap", "loss")}</text>' if s.get("gaplabel", True) else "")
                continue
            run.append(f"{sx(t_of(d)):.1f},{sy(v):.1f}")
        if len(run) > 1:
            out.append(f'<polyline clip-path="url(#{cid}c)" fill="none" stroke="var({s["color"]})" stroke-width="2" {s.get("attr", "")} points="{" ".join(run)}"/>')
        for d, v in s["points"]:
            if v is None:
                continue
            cx = sx(t_of(d))
            if v > ymax:
                out.append(f'<path d="M{cx - 5:.1f} {T + 7} L{cx:.1f} {T - 1} L{cx + 5:.1f} {T + 7} Z" fill="var({s["color"]})"/>')
                out.append(f'<text class="lv halo" x="{cx:.1f}" y="{T - 6}" text-anchor="middle">{e(fmt(v))}</text>')
            elif s.get("hollow"):
                out.append(f'<circle cx="{cx:.1f}" cy="{sy(v):.1f}" r="5" fill="var(--surface)" stroke="var({s["color"]})" stroke-width="2"/>')
            else:
                out.append(f'<circle cx="{cx:.1f}" cy="{sy(v):.1f}" r="{s.get("r", 4)}" fill="var({s["color"]})" stroke="var(--surface)" stroke-width="2"/>')
        last = [(d, v) for d, v in s["points"] if v is not None][-1]
        if s.get("end"):
            labels.append({"y": sy(min(last[1], ymax)), "text": s["end"], "strong": True})
    for ref in refs:
        labels.append({"y": sy(ref["value"]), "text": ref["label"], "strong": False})
    labels.sort(key=lambda a: a["y"])
    for i in range(1, len(labels)):
        labels[i]["y"] = max(labels[i]["y"], labels[i - 1]["y"] + 17)
    for a in labels:
        cls = "lv" if a["strong"] else "ax"
        out.append(f'<text class="{cls}" x="{W - R + 14}" y="{a["y"] + 4:.1f}">{e(a["text"])}</text>')
    # one hover band per date
    centers = [sx(t_of(d)) for d in dates]
    for i, d in enumerate(dates):
        left = L if i == 0 else (centers[i - 1] + centers[i]) / 2
        right = W - R + 6 if i == len(dates) - 1 else (centers[i] + centers[i + 1]) / 2
        rows = []
        for s in series:
            v = dict(s["points"]).get(d, "absent")
            if v == "absent":
                continue
            rows.append(f'{s["name"]}: {"n.m." if v is None else fmt(v)}')
        tip = f"<b>{nice(d)}</b><br>" + "<br>".join(e(r) for r in rows)
        out.append(f'<rect class="band" data-x="{centers[i]:.1f}" x="{left:.1f}" y="{T}" width="{right - left:.1f}" height="{height - T - B}" fill="transparent" data-tip="{e(tip)}"/>')
    out.append(f'<line class="cross" x1="0" x2="0" y1="{T}" y2="{height - B}" stroke="var(--axis)" visibility="hidden"/>')
    out.append("</svg>")
    return "".join(out)


def legend(items):
    out = []
    for name, color, kind in items:
        if kind == "line":
            key = f'<span class="key" style="background:var({color})"></span>'
        elif kind == "hollow":
            key = f'<span class="key" style="background:var(--surface);border:2px solid var({color});border-radius:50%"></span>'
        else:
            dash = "border-top:2px dashed var(--s0)" if kind == "dash" else "border-top:2px dotted var(--s0)"
            key = f'<span class="key" style="height:0;border-radius:0;{dash};vertical-align:4px"></span>'
        out.append(f"<li>{key}{e(name)}</li>")
    return f'<ul class="legend">{"".join(out)}</ul>'


def strip(rows):
    """Peer strip: one row per company, three panels, each with its own axis."""
    panels = [("pe", "P/E", 0, 60, [0, 20, 40, 60], lambda v: f"{v:.0f}x"),
              ("ev_ebit", "EV/EBIT", 0, 45, [0, 15, 30, 45], lambda v: f"{v:.0f}x"),
              ("fcfy", "Free cash flow yield", -2, 6, [-2, 0, 2, 4, 6], lambda v: ("−" if v < 0 else "") + f"{abs(v):.0f}%")]
    W, label_w, gap, rowh, top = 1000, 196, 22, 30, 44
    pw = (W - label_w - gap * 2 - 14) / 3
    H = top + rowh * len(rows) + 8
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Dot strip of P/E, EV/EBIT and free cash flow yield for Corning and its listed rivals. Values are in the table below.">']
    for i, r in enumerate(rows):
        y = top + rowh * i + rowh / 2
        weight = ' class="lv"' if r["own"] else ""
        out.append(f'<text{weight} x="0" y="{y + 4:.1f}">{e(r["label"])}</text>')
        if i:
            out.append(f'<line x1="0" x2="{W}" y1="{y - rowh / 2:.1f}" y2="{y - rowh / 2:.1f}" stroke="var(--grid)" stroke-opacity=".6"/>')
    for p, (key, title, lo, hi, ticks, fmt) in enumerate(panels):
        px = label_w + p * (pw + gap)
        sx = lambda v: px + (v - lo) / (hi - lo) * pw
        out.append(f'<text class="lv" x="{px:.1f}" y="14">{e(title)}</text>')
        for tk in ticks:
            out.append(f'<line x1="{sx(tk):.1f}" x2="{sx(tk):.1f}" y1="{top - 8}" y2="{H - 6}" stroke="{"var(--axis)" if tk == 0 and lo < 0 else "var(--grid)"}"/>')
            anchor = "start" if tk == lo else ("end" if tk == hi else "middle")
            out.append(f'<text class="ax" x="{sx(tk):.1f}" y="{top - 13}" text-anchor="{anchor}">{e(fmt(tk))}</text>')
        for i, r in enumerate(rows):
            y = top + rowh * i + rowh / 2
            v = r[key]
            color = r["color"]
            shown = (f"{v:.1f}x" if key != "fcfy" else pc(v))
            tip = f'<b>{e(r["label"])}</b><br>{e(title)}: {e(shown)}<br>{e(r["basis"])}'
            cx = sx(v)
            out.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="5.5" fill="{color}" stroke="var(--surface)" stroke-width="2"/>')
            anchor, dx = ("end", -10) if (cx > px + pw - 46 or v < 0) else ("start", 10)
            out.append(f'<text class="halo" x="{cx + dx:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}">{e(shown)}</text>')
            out.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="14" fill="transparent" data-tip="{e(tip)}"/>')
    out.append("</svg>")
    return "".join(out)


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--s0:#8a897f;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#8a897f;--s1:#3987e5;--s2:#d95926;--s3:#199e70}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#8a897f;--s1:#3987e5;--s2:#d95926;--s3:#199e70}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:24px;line-height:1.25;margin:0 0 8px;font-weight:650}
h2{font-size:18px;margin:36px 0 6px;font-weight:650}
h3{font-size:15px;margin:18px 0 4px;font-weight:650}
p{margin:0 0 10px;max-width:75ch}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.callout{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin:14px 0;max-width:75ch}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:12px;height:12px;margin-right:7px;vertical-align:-1px;border-radius:3px}
.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:640px;height:auto;font:12.5px system-ui,-apple-system,"Segoe UI",sans-serif}
svg text{fill:var(--ink-2)}svg .lv{fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}svg .ax{fill:var(--muted)}svg .halo{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round;font-variant-numeric:tabular-nums}
figure{margin:0}figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:80ch}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.12)}
#tip[hidden]{display:none}#tip b{font-weight:650}
.wrap{overflow-x:auto;margin-top:8px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600;white-space:nowrap}
td:last-child:not(.num){min-width:112px}
td{color:var(--ink-2)}.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.hl th,.hl td{background:rgba(127,127,127,.09)}.hl th{padding-left:6px}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.tv{font-size:22px;font-weight:650;font-variant-numeric:tabular-nums}.tk{color:var(--muted);font-size:12.5px}
ul.notes{margin:0 0 10px;padding-left:18px;max-width:80ch}ul.notes li{margin-bottom:6px}
.foot{color:var(--muted);font-size:13px;max-width:80ch}
@media (max-width:760px){.tiles{grid-template-columns:repeat(2,1fr)}}
"""

JS = """
const tip=document.getElementById('tip');
function place(ev){const w=tip.offsetWidth,h=tip.offsetHeight;let a=ev.clientX+14,b=ev.clientY+14;if(a+w>innerWidth-8)a=ev.clientX-w-14;if(b+h>innerHeight-8)b=ev.clientY-h-14;tip.style.left=Math.max(8,a)+'px';tip.style.top=Math.max(8,b)+'px'}
document.querySelectorAll('[data-tip]').forEach(el=>{
  el.addEventListener('pointerenter',ev=>{tip.innerHTML=el.dataset.tip;tip.hidden=false;place(ev);
    const c=el.closest('svg').querySelector('.cross');if(c&&el.dataset.x){c.setAttribute('x1',el.dataset.x);c.setAttribute('x2',el.dataset.x);c.setAttribute('visibility','visible')}});
  el.addEventListener('pointermove',place);
  el.addEventListener('pointerleave',()=>{tip.hidden=true;const c=el.closest('svg').querySelector('.cross');if(c)c.setAttribute('visibility','hidden')});
});
"""


def main():
    d = m.build()
    known, year, today, st, sty = d["known"], d["year"], d["today"], d["stats"], d["stats_year"]
    peers = tomllib.loads((m.HERE / "peers.toml").read_text())["peer"]
    by = {p["name"]: p for p in peers}
    aph = m.amphenol(by["Amphenol"]["price"])
    for p in peers:
        if "eps" in p and abs(p["price"] / p["eps"] - p["pe"]) / p["pe"] > 0.01:
            raise m.Stop(f"{p['name']}: page P/E does not tie to its price over EPS.")

    # --- Figures used in words
    n = NOTE
    px, cap = today["price"], today["cap"] / 1e6
    fcfy_line = n["fcf_no_line"] / cap * 100
    fcfy_both = n["fcf_both"] / cap * 100
    fcfy_recv = n["fcf_no_received"] / cap * 100
    core = sum(n["core_q"])
    above_aaa = sum(p["ey"] > p["aaa"] for p in known)
    above_dgs = sum(p["ey"] > p["dgs"] for p in known)
    last_above = [p for p in known if p["ey"] > p["aaa"]][-1]
    all_ev = today["ev"] / 1e6 + n["op_leases"] + n["pension"] + n["contract"]
    conv = n["conv_m"] * known[4]["price"]
    flip = 100 / st["ey"]["mean"]
    pe_rank = sorted([p["pe"] for p in peers], reverse=True).index(by["Corning"]["pe"]) + 1
    ev_rank = sorted([p["ev_ebit"] for p in peers], reverse=True).index(by["Corning"]["ev_ebit"]) + 1
    fc_rank = sorted([p["fcf_yield"] for p in peers], reverse=True).index(by["Corning"]["fcf_yield"]) + 1
    today_q = link(Q, "10-Q, filed Oct. 29, 2026")
    close_l = link(YAHOO, "Yahoo through yfinance, fetched Nov. 2, 2026")
    aaa_l = link(AAA, "FRED AAA, downloaded Nov. 3, 2026")
    dgs_l = link(DGS, "FRED DGS10, downloaded Nov. 3, 2026")

    # --- Charts
    allp = known + [today]
    def pts(key, rows=allp):
        return [(p["date"], p[key]) for p in rows]

    def chart_pair(cid, label, key, fmt, ymin, ymax, ticks, end_text, extra=None, zero=False):
        series = [{"name": "Known that day", "color": "--s1", "points": pts(key), "end": end_text, "gap": "loss"},
                  {"name": "Full-year results", "color": "--s2", "points": pts(key, year), "r": 3, "attr": 'stroke-dasharray="6 4"', "gaplabel": False}]
        if extra:
            series.append(extra)
        refs = [{"label": f"Average {fmt(st[key]['mean'])}", "value": st[key]["mean"], "dash": "7 5"},
                {"label": f"Median {fmt(st[key]['median'])}", "value": st[key]["median"], "dash": "2 4"}]
        return line_chart(cid, label, series, refs, ymin, ymax, ticks, fmt, zero=zero)

    fx = lambda v: f"{v:.1f}x" if v != int(v) or v > 100 else f"{v:.0f}x"
    fp = lambda v: ("−" if v < 0 else "") + (f"{abs(v):.2f}%" if v != int(v) else f"{abs(v):.0f}%")
    pe_svg = chart_pair("pechart", "Line chart of Corning's P/E at each year end and now, with its average. Values are in the table below.", "pe", fx, 0, 100, [0, 25, 50, 75, 100], f"Now {fx(today['pe'])}")
    ev_svg = chart_pair("evchart", "Line chart of Corning's EV/EBIT at each year end and now, with its average. Values are in the table below.", "ev_ebit", fx, 0, 100, [0, 25, 50, 75, 100], f"Now {fx(today['ev_ebit'])}")
    extra = {"name": "Without the filed deposits line", "color": "--s3", "points": [(today["date"], fcfy_line)], "hollow": True, "end": f"No deposits line {fp(fcfy_line)}"}
    fc_svg = chart_pair("fcchart", "Line chart of Corning's free cash flow yield at each year end and now, with its average. Values are in the table below.", "fcfy", fp, -2, 8, [-2, 0, 2, 4, 6, 8], f"Now {fp(today['fcfy'])}", extra, zero=True)
    ey_series = [{"name": "Corning earnings yield", "color": "--s1", "points": pts("ey"), "end": f"Corning {fp(today['ey'])}"},
                 {"name": "Moody's Aaa bonds", "color": "--s2", "points": pts("aaa"), "end": f"Aaa {fp(today['aaa'])}"},
                 {"name": "10-year Treasury", "color": "--s3", "points": pts("dgs"), "end": f"Treasury {fp(today['dgs'])}"}]
    ey_svg = line_chart("eychart", "Line chart of Corning's earnings yield against Moody's Aaa and the 10-year Treasury. Values are in the table below.", ey_series, [], -4, 10, [-4, -2, 0, 2, 4, 6, 8, 10], fp, height=360, zero=True)

    # --- Peer rows
    def page_row(p):
        return {"label": p["name"] + (", outside page" if p["name"] == "Amphenol" else ""), "pe": p["pe"], "ev_ebit": p["ev_ebit"], "fcfy": p["fcf_yield"], "color": "var(--s0)", "own": False,
                "basis": f"Outside page, read Nov. 3, 2026, {p['currency']} {p['price']:,.2f}"}
    strip_rows = [
        {"label": "Corning, our figures", "pe": today["pe"], "ev_ebit": today["ev_ebit"], "fcfy": today["fcfy"], "color": "var(--s1)", "own": True, "basis": f"Our rules, close {nice(today['date'])}, ${px:.2f}"},
        {"label": "Corning, outside page", "pe": by["Corning"]["pe"], "ev_ebit": by["Corning"]["ev_ebit"], "fcfy": by["Corning"]["fcf_yield"], "color": "var(--s1)", "own": True, "basis": f"Outside page, read Nov. 3, 2026, $ {by['Corning']['price']:.2f}"},
        {"label": "Amphenol, our rules", "pe": aph["pe"], "ev_ebit": aph["ev_ebit"], "fcfy": aph["fcfy"], "color": "var(--s2)", "own": False, "basis": f"SEC filing to {nice(aph['period_end'])}, page price ${aph['price']:.2f}"},
    ] + [page_row(p) for p in peers if p["name"] != "Corning"]

    # --- Tables
    def row(p, hl=False):
        label = "Now, " + nice(p["date"]) if hl else nice(p["date"])
        src = link(p["url"], f"{p['form']}, filed {nice(p['filed'])}")
        return (f'<tr{" class=hl" if hl else ""}><th>{label}</th><td class="num">${p["price"]:.2f}</td>'
                f'<td class="num">{eps_fmt(p["eps"])}</td><td class="num">{musd(p["ebit"])}</td><td class="num">{musd(p["fcf"])}</td>'
                f'<td class="num">{x(p["pe"])}</td><td class="num">{x(p["ev_ebit"])}</td><td class="num">{pc(p["fcfy"])}</td>'
                f'<td class="num">{pc(p["ey"])}</td><td class="num">{pc(p["aaa"])}</td><td class="num">{pc(p["dgs"])}</td><td>{src}</td></tr>')

    def stat_row(name, k):
        return (f'<tr><th>{name}, ten year ends</th><td></td><td></td><td></td><td></td><td class="num">{x(st["pe"][k])}</td><td class="num">{x(st["ev_ebit"][k])}</td>'
                f'<td class="num">{pc(st["fcfy"][k])}</td><td class="num">{pc(st["ey"][k])}</td><td class="num">{pc(st["aaa"][k])}</td><td class="num">{pc(st["dgs"][k])}</td><td>calc.</td></tr>')

    main_rows = "".join(row(p) for p in known) + row(today, True) + stat_row("Average", "mean") + stat_row("Median", "median")
    def ev_row(p, hl=False):
        label = "Now, " + nice(p["date"]) if hl else nice(p["date"])
        return (f'<tr{" class=hl" if hl else ""}><th>{label}</th><td class="num">{p["shares"] / 1e6:,.1f}M</td><td class="num">{musd(p["cap"])}</td><td class="num">{musd(p["debt"])}</td>'
                f'<td class="num">{musd(p["preferred"]) if p["preferred"] else "none"}</td><td class="num">{musd(p["nci"])}</td><td class="num">{musd(-p["cash"])}</td><td class="num"><b>{musd(p["ev"])}</b></td>'
                f'<td>Shares {nice(p["shares_date"])}; balance {nice(p["period_end"])}</td></tr>')
    ev_rows = "".join(ev_row(p) for p in known) + ev_row(today, True)
    def fy_row(p):
        return (f'<tr><th>{p["date"][:4]}</th><td class="num">${p["price"]:.2f}</td><td class="num">{eps_fmt(p["eps"])}</td><td class="num">{musd(p["ebit"])}</td><td class="num">{musd(p["fcf"])}</td><td class="num">{x(p["pe"])}</td><td class="num">{x(p["ev_ebit"])}</td><td class="num">{pc(p["fcfy"])}</td><td class="num">{pc(p["ey"])}</td></tr>')
    fy_rows = "".join(fy_row(p) for p in year)
    fy_rows += (f'<tr class=hl><th>Average</th><td></td><td></td><td></td><td></td><td class="num">{x(sty["pe"]["mean"])}</td><td class="num">{x(sty["ev_ebit"]["mean"])}</td><td class="num">{pc(sty["fcfy"]["mean"])}</td><td class="num">{pc(sty["ey"]["mean"])}</td></tr>'
                f'<tr class=hl><th>Median</th><td></td><td></td><td></td><td></td><td class="num">{x(sty["pe"]["median"])}</td><td class="num">{x(sty["ev_ebit"]["median"])}</td><td class="num">{pc(sty["fcfy"]["median"])}</td><td class="num">{pc(sty["ey"]["median"])}</td></tr>')

    peer_rows = (f'<tr class=hl><th>Corning, our figures</th><td class="num">{x(today["pe"])}</td><td class="num">{x(today["ev_ebit"])}</td><td class="num">{pc(today["fcfy"])}</td><td>Close {nice(today["date"])}, ${px:.2f}. {today_q}. {close_l}.</td></tr>'
                 f'<tr><th>Amphenol, our rules</th><td class="num">{x(aph["pe"])}</td><td class="num">{x(aph["ev_ebit"])}</td><td class="num">{pc(aph["fcfy"])}</td><td>Twelve months to {nice(aph["period_end"])}. {link(aph["url"], "10-Q, filed " + nice(aph["filed"]))}. Price ${aph["price"]:.2f} from the outside page.</td></tr>')
    for p in peers:
        peer_rows += (f'<tr><th>{e(p["name"])}{", outside page" if p["name"] in ("Corning", "Amphenol") else ""}</th><td class="num">{x(p["pe"])}</td><td class="num">{x(p["ev_ebit"])}</td><td class="num">{pc(p["fcf_yield"])}</td>'
                      f'<td>{link(p["base"], "StockAnalysis, read Nov. 3, 2026")}. Price {p["currency"]} {p["price"]:,.2f}. Its EV ÷ its EBIT is {p["ev_b"] / p["ebit_b"]:.1f}x (calc.).</td></tr>')

    yofc = by["YOFC (Hong Kong shares)"]
    yofc_pe = yofc["cap_b"] / yofc["net_income_b"]
    yofc_at_h = yofc["shares_m"] * yofc["price"] / 1000
    fur = by["Furukawa Electric"]
    co = by["Corning"]
    page_debt = 9.17

    lede = (f'At the ${px:.2f} close on {nice(today["date"])}, the latest saved, Corning sat at <b>{x(today["pe"])} earnings</b>, <b>{x(today["ev_ebit"])} EBIT</b> and a <b>{pc(today["fcfy"])} free cash flow yield</b>, '
            f'or {pc(fcfy_line)} without the filed deposits line (all calc.). Flipped, the P/E is a {pc(today["ey"])} earnings yield, against {pc(today["aaa"])} on Moody\'s Aaa and {pc(today["dgs"])} on the 10-year Treasury. '
            f'The ten year-end averages are {x(st["pe"]["mean"])}, {x(st["ev_ebit"]["mean"])} and {pc(st["fcfy"]["mean"])}, and two near-zero profit years pull the first two up. The medians are {x(st["pe"]["median"])}, {x(st["ev_ebit"]["median"])} and {pc(st["fcfy"]["median"])}.')

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corning Price Tags</title><style>{CSS}</style></head><body><main>
<h1>Corning's price tags</h1>
<p class="lede">{lede}</p>
<div class="callout"><b>No buy or sell view.</b> A price tag says what the market pays for what has been reported. It does not say what the business is worth. Base value is not defined yet, so <code>when-to-buy</code> still bars a buy recommendation. These measures are normally off under override 5 in <code>skill-overrides</code>. They were run because I asked, as a picture only, and they are not a valuation method.</div>
<div class="tiles">
<div class="tile"><div class="tk">P/E</div><div class="tv">{x(today["pe"])}</div><div class="tk">${px:.2f} ÷ ${today["eps"]:.2f}. Ten-year average {x(st["pe"]["mean"])}, median {x(st["pe"]["median"])}</div></div>
<div class="tile"><div class="tk">EV/EBIT</div><div class="tv">{x(today["ev_ebit"])}</div><div class="tk">{musd(today["ev"])} ÷ {musd(today["ebit"])}. Average {x(st["ev_ebit"]["mean"])}, median {x(st["ev_ebit"]["median"])}</div></div>
<div class="tile"><div class="tk">Free cash flow yield</div><div class="tv">{pc(today["fcfy"])}</div><div class="tk">{musd(today["fcf"])} ÷ {musd(today["cap"])}. Average {pc(st["fcfy"]["mean"])}, median {pc(st["fcfy"]["median"])}</div></div>
<div class="tile"><div class="tk">Earnings yield</div><div class="tv">{pc(today["ey"])}</div><div class="tk">Aaa {pc(today["aaa"])}. 10-year Treasury {pc(today["dgs"])}</div></div>
</div>

<h2>Each one in plain words</h2>
<p><b>P/E: what you pay for a dollar of profit.</b> The share price divided by the last twelve months' profit per share. ${px:.2f} ÷ ${today["eps"]:.2f} = {x(today["pe"])} (calc., {close_l}; {today_q}). So buyers paid about ${today["pe"]:.0f} for each $1 of reported profit. This is standard GAAP profit, so one-off gains and losses stay in. When profit is near zero, the P/E shoots up. When it is a loss, the P/E means nothing, marked n.m.</p>
<p><b>EV/EBIT: what the whole business costs against its operating profit.</b> P/E looks only at shareholders. Enterprise value also counts what is owed to others. EBIT is profit before interest and tax, and here it is Corning's "Operating income" line. {musd(today["ev"])} ÷ {musd(today["ebit"])} = {x(today["ev_ebit"])} (calc., {today_q}). It ignores how the business is financed, and tax. It also ignores Corning's currency hedge gains, which sit below that line and were ${n["fx_gain_9m"]}M in the nine months of 2026 ({today_q}). They do reach EPS, so the two measures can move apart.</p>
<p><b>Free cash flow yield: cash left over, as a share of what the shares cost.</b> Cash from operations minus spending on plants, divided by market value. {musd(today["fcf"])} ÷ {musd(today["cap"])} = {pc(today["fcfy"])} (calc., {today_q}). Unlike the P/E, higher means you pay less for each dollar. Think of {pc(today["fcfy"])} as ${today["fcfy"]:.2f} of cash a year for each $100 of shares, before any growth or decline. No one hands it to you: the company chooses what to do with it.</p>
<p><b>Earnings yield: the P/E upside down.</b> Profit ÷ price, ${today["eps"]:.2f} ÷ ${px:.2f} = {pc(today["ey"])} (calc.). That puts profit in the same form as a bond yield.</p>

<h2>What goes into enterprise value</h2>
<p>Think of buying the whole company. You pay the shareholders, you take on the debts, and you keep the cash in the till.</p>
<div class="wrap"><table><thead><tr><th>Piece</th><th class="num">Now</th><th>What it is</th></tr></thead><tbody>
<tr><th>Market value of the shares</th><td class="num">{musd(today["cap"])}</td><td>{today["shares"] / 1e6:,.1f}M shares, from the {link(Q, "10-Q cover, as of Oct. 23, 2026")}, × ${px:.2f} (calc.).</td></tr>
<tr><th>+ Debt</th><td class="num">{musd(today["debt"])}</td><td>Long-term debt plus the part due within a year, at book value. Includes finance leases ({link(K, "10-K, filed Feb. 12, 2026")}; {today_q}).</td></tr>
<tr><th>+ Preferred stock</th><td class="num">none</td><td>A prior claim ahead of common shares. ${known[0]["preferred"] / 1e6:,.0f}M at book at the year ends 2016 to 2020, none after.</td></tr>
<tr><th>+ Outside owners' share</th><td class="num">{musd(today["nci"])}</td><td>Noncontrolling interests at book. EBIT counts all of the subsidiaries it covers, such as Hemlock Semiconductor, so the part others own is added. Book value may be far from market value.</td></tr>
<tr><th>− Cash</th><td class="num">{musd(-today["cash"])}</td><td>Cash and equivalents. About 66% is outside the US ({today_q}), and all of it is taken off at full value.</td></tr>
<tr class=hl><th>= Enterprise value</th><td class="num"><b>{musd(today["ev"])}</b></td><td>calc.</td></tr>
</tbody></table></div>
<h3>Left out, with their size</h3>
<p>These are judgment calls, and they matter less than the choice of earnings. None is in the {musd(today["ev"])} above.</p>
<ul class="notes">
<li><b>Operating leases ${n["op_leases"]}M, pensions ${n["pension"]}M, contract liabilities ${n["contract"]:,}M</b> ({today_q}). Contract liabilities are generally non-refundable and settled by delivering product. Adding all three gives {musd(all_ev * 1e6)}, or {all_ev / (today["ebit"] / 1e6):.1f}x EBIT (calc.).</li>
<li><b>Receivables sold ${n["sold"]}M</b> ({today_q}). Cash arrived early, which lowers net debt without counting as debt.</li>
<li><b>Investments ${n["investments"]}M at book</b> ({today_q}). A stricter sum might take these off.</li>
<li><b>Share count.</b> Market value uses shares outstanding. On {n["diluted_m"]}M diluted shares ({today_q}), it is {musd(n["diluted_m"] * px * 1e6)} (calc.). NVIDIA's warrants add {n["prefunded_m"]}M pre-funded shares, and {n["warrant_m"]}M at ${n["warrant_strike"]}, above this close ({link(K8, "8-K, May 6, 2026")}).</li>
<li><b>The old preferred.</b> It converted into {n["conv_m"]}M shares ({link(K21, "10-K, filed Feb. 14, 2022")}). At Dec. 31, 2020 those were worth {musd(conv * 1e6)} (calc.), against ${known[4]["preferred"] / 1e6:,.0f}M at book, so the early EVs run low.</li>
</ul>

<h2>Which earnings: two ways to date a year end</h2>
<p><b>Known that day</b> is the main view, in blue. It uses what was on file on that date, as first filed, so a Dec. 31 figure is the twelve months to Sept. 30. This is the rule I chose for <code>economy.html</code>, because a past yield should not use numbers not yet known. EPS here ties to that rule's own code at all {len(allp)} dates. <b>Full-year results</b>, in orange, use that year's results from the latest 10-K, which were not known until weeks later. They tie to the tables in <code>Companies/Corning.md</code>.</p>

<h2>P/E: {x(today["pe"])} now, against a median of {x(st["pe"]["median"])}</h2>
<div class="card"><figure>{legend([("Known that day", "--s1", "line"), ("Full-year results", "--s2", "line"), ("Average", "--s0", "dash"), ("Median", "--s0", "dot")])}<div class="scroll">{pe_svg}</div>
<figcaption>Year ends 2016 to 2025, then {nice(today["date"])}. The scale stops at 100x, and arrows mark years above it. Gaps are losses: Dec. 2018 in blue, 2017 in orange. Average and median are of the blue points only.</figcaption></figure></div>
<p>Read the average with care. Profit nearly vanished on the trailing figures at Dec. 2024 (${known[8]["eps"]:.2f} a share) and Dec. 2020 (${known[4]["eps"]:.2f}), which gave {x(known[8]["pe"])} and {x(known[4]["pe"])}. A loss at Dec. 2018 drops out altogether. Averaging the yields avoids both problems: {pc(st["ey"]["mean"])}, which flips to {flip:.1f}x (calc.). The low {x(known[0]["pe"])} at Dec. 2016 is flattered by the Dow Corning gain of $2.7 billion, and the 2018 loss comes from the 2017 Tax Act charge ({link(K18, "10-K, filed Feb. 15, 2018")}).</p>
<h3>The same price on other earnings</h3>
<div class="wrap"><table><thead><tr><th>Earnings used</th><th class="num">Per share</th><th class="num">P/E at ${px:.2f}</th><th>Note</th></tr></thead><tbody>
<tr class=hl><th>GAAP, trailing</th><td class="num">${today["eps"]:.2f}</td><td class="num">{x(today["pe"])}</td><td>The main view. {today_q}.</td></tr>
<tr><th>Core, last four quarters</th><td class="num">${core:.2f}</td><td class="num">{x(px / core)}</td><td>Corning's own measure, which leaves out items it picks. Its method changed in 2026 with no restatement. Sum of four quarters, calc. See <code>Companies/Corning.md</code>, Income statement and core.</td></tr>
<tr><th>Normalized, FY2025</th><td class="num">${n["normal_2025"]:.2f}</td><td class="num">{x(px / n["normal_2025"])}</td><td>Our cleaned figure, the high of ten years. A different year from the price. See <code>normal.html</code>.</td></tr>
<tr><th>Normalized, ten-year average</th><td class="num">${n["normal_avg"]:.2f}</td><td class="num">{x(px / n["normal_avg"])}</td><td>Looks back only, so growth since is not in it. Not base value, and not a forecast.</td></tr>
</tbody></table></div>

<h2>EV/EBIT: {x(today["ev_ebit"])} now, against a median of {x(st["ev_ebit"]["median"])}</h2>
<div class="card"><figure>{legend([("Known that day", "--s1", "line"), ("Full-year results", "--s2", "line"), ("Average", "--s0", "dash"), ("Median", "--s0", "dot")])}<div class="scroll">{ev_svg}</div>
<figcaption>Same dates and scale limit as above. The average is pulled up by {x(known[4]["ev_ebit"])} at Dec. 2020, when trailing EBIT was {musd(known[4]["ebit"])}.</figcaption></figure></div>

<h2>Free cash flow yield: {pc(today["fcfy"])} now, or {pc(fcfy_line)} without the deposits line</h2>
<div class="card"><figure>{legend([("Known that day", "--s1", "line"), ("Full-year results", "--s2", "line"), ("Without the filed deposits line, now only", "--s3", "hollow"), ("Average", "--s0", "dash"), ("Median", "--s0", "dot")])}<div class="scroll">{fc_svg}</div>
<figcaption>Here, higher means fewer dollars paid for each dollar of cash. The line is free cash flow as reported, with deposits in. There is no clean ten-year series without them, because the filed line also holds government incentives and the filing does not split them.</figcaption></figure></div>
<p>The {musd(today["fcf"])} includes customer deposits, which are cash now and less cash later. The readings for the same twelve months, from <code>Companies/Corning.md</code> (calc., {link(K, "10-K, filed Feb. 12, 2026")}; {today_q}):</p>
<div class="wrap"><table><thead><tr><th>Reading</th><th class="num">Free cash flow</th><th class="num">Yield</th></tr></thead><tbody>
<tr class=hl><th>As reported</th><td class="num">{musd(today["fcf"])}</td><td class="num">{pc(today["fcfy"])}</td></tr>
<tr><th>Without the whole filed deposits line</th><td class="num">${n["fcf_no_line"]:,}M</td><td class="num">{pc(fcfy_line)}</td></tr>
<tr><th>Both sides of the deposits out, an estimate</th><td class="num">about ${n["fcf_both"]:,}M</td><td class="num">about {pc(fcfy_both)}</td></tr>
<tr><th>Without deposits received</th><td class="num">about ${n["fcf_no_received"]:,}M</td><td class="num">about {pc(fcfy_recv)}</td></tr>
</tbody></table></div>
<p>Not taken off in any row: stock pay of ${n["stock_pay"]}M and finance lease principal of ${n["lease_principal"]}M over the same twelve months. Capex also misses plants taken on through finance leases. <code>Companies/Corning.md</code> covers this under Cash flow.</p>

<h2>Earnings yield against bonds: {pc(today["ey"])}, below both</h2>
<div class="card"><figure>{legend([("Corning earnings yield, known that day", "--s1", "line"), ("Moody's Aaa, December average", "--s2", "line"), ("10-year Treasury, last day", "--s3", "line")])}<div class="scroll">{ey_svg}</div>
<figcaption>Now: Corning at the {nice(today["date"])} close, Aaa for {mon(today["aaa_date"])} ({aaa_l}), Treasury on {nice(today["dgs_date"])} ({dgs_l}). The newest bond figures are a little older than the close.</figcaption></figure></div>
<p>The gap now is {abs(today["ey"] - today["aaa"]):.2f} points to Aaa and {abs(today["ey"] - today["dgs"]):.2f} to the Treasury (calc.). The yield was above Aaa at {above_aaa} of the ten year ends, most recently {nice(last_above["date"])}, and above the Treasury at {above_dgs}. Averages over those ten: Corning {pc(st["ey"]["mean"])}, Aaa {pc(st["aaa"]["mean"])}, Treasury {pc(st["dgs"]["mean"])} (calc.).</p>
<ul class="notes">
<li><b>These are different things.</b> A bond pays a fixed amount and returns its face value if the borrower stays sound. An earnings yield is not a payment: it is one year's reported profit, which can rise or fall, and only part of it is paid out.</li>
<li><b>So a low yield can mean two things.</b> Buyers may expect profit to grow, or they may have paid too much. This chart cannot tell which.</li>
<li><b>Different terms.</b> Aaa covers bonds with maturities of 20 years and above ({link(AAA, "FRED series notes, retrieved Nov. 2, 2026")}), and the Treasury is 10 years. Neither is Corning's own debt.</li>
</ul>

<h2>The numbers behind the charts</h2>
<p>Known that day, so each year end uses the twelve months to the Sept. 30 before it, and "now" uses the twelve months to Sept. 30, 2026. All multiples and yields are calc. The P/E average and median use {st["pe"]["n"]} of 10 year ends, leaving out the loss. Closes are not adjusted for dividends, and no split fell in the period.</p>
<div class="wrap"><table><thead><tr><th>Date</th><th class="num">Close</th><th class="num">Diluted EPS</th><th class="num">EBIT</th><th class="num">Free cash flow</th><th class="num">P/E</th><th class="num">EV/EBIT</th><th class="num">FCF yield</th><th class="num">Earnings yield</th><th class="num">Aaa</th><th class="num">10-yr</th><th>Source</th></tr></thead><tbody>{main_rows}</tbody></table></div>
<h3>Enterprise value, piece by piece</h3>
<div class="wrap"><table><thead><tr><th>Date</th><th class="num">Shares</th><th class="num">Market value</th><th class="num">+ Debt</th><th class="num">+ Preferred</th><th class="num">+ Outside owners</th><th class="num">− Cash</th><th class="num">= EV</th><th>Dates used</th></tr></thead><tbody>{ev_rows}</tbody></table></div>
<h3>Full-year results</h3>
<p>Year-end close against that fiscal year, from the latest 10-K reporting each flow, with shares and balance sheet from the year's first 10-K. All calc. There is no "now" row, because 2026 is not finished.</p>
<div class="wrap"><table><thead><tr><th>Year</th><th class="num">Close</th><th class="num">Diluted EPS</th><th class="num">EBIT</th><th class="num">Free cash flow</th><th class="num">P/E</th><th class="num">EV/EBIT</th><th class="num">FCF yield</th><th class="num">Earnings yield</th></tr></thead><tbody>{fy_rows}</tbody></table></div>

<h2>Corning next to listed rivals</h2>
<p>Corning's P/E on the outside page ranks {pe_rank} of {len(peers)}, its EV/EBIT {ev_rank} of {len(peers)} and its free cash flow yield {fc_rank} of {len(peers)}, all counted from the highest (calc.). That page is one free site, read Nov. 3, 2026. It is a snapshot of different businesses, and the list below says why it is rough.</p>
<div class="card"><figure>{legend([("Corning", "--s1", "line"), ("Amphenol on our rules, from its SEC filing", "--s2", "line"), ("Outside page", "--s0", "line")])}<div class="scroll">{strip(strip_rows)}</div>
<figcaption>Each panel has its own scale. Only the two named "our" rows use our rules. Rivals are those in our notes: Corning names Amphenol, Fujikura, Sumitomo and Prysmian as principal Optical rivals ({link(K, "10-K, filed Feb. 12, 2026")}).</figcaption></figure></div>
<div class="wrap"><table><thead><tr><th>Company</th><th class="num">P/E</th><th class="num">EV/EBIT</th><th class="num">FCF yield</th><th>Source</th></tr></thead><tbody>{peer_rows}</tbody></table></div>

<h2>What could not be compared fairly</h2>
<ul class="notes">
<li><b>No rival has a ten-year record here.</b> Our price sensor holds Corning only, and it was not widened, because Yahoo's terms bar automated collection. So there are no peer averages and no peer lines, only one day's snapshot.</li>
<li><b>Only Corning and Amphenol are built from filings on our rules.</b> The other {len(peers) - 2} rivals rest on one outside page, checked against no filing. Each P/E on that page ties to its price ÷ its EPS, where the page gives EPS (calc.).</li>
<li><b>The page builds EV differently.</b> For Corning it shows debt of ${page_debt}B, which matches {musd(today["debt"])} plus ${n["op_leases"]}M of operating leases (calc.), and leaves out the {musd(today["nci"])} of outside owners. So it gives ${co["ev_b"]}B, on a higher price too. Its EBIT is ${co["ebit_b"]}B against our {musd(today["ebit"])}, for reasons the page does not give.</li>
<li><b>Some page ratios do not tie to the page's own numbers.</b> Furukawa shows {fur["ev_ebit"]:.1f}x EV/EBIT, but its EV ÷ EBIT is {fur["ev_b"] / fur["ebit_b"]:.1f}x (calc.). A second read gave the same printed figures. The strip plots the printed ratio, and the table shows both.</li>
<li><b>YOFC has two share classes at two prices.</b> Its {yofc["pe"]:.1f}x P/E uses the Hong Kong price. All {yofc["shares_m"]:,.0f}M shares at that price would be HK${yofc_at_h:.1f}B, but the page's market value is HK${yofc["cap_b"]:.1f}B, so Claude reads it as pricing the Shanghai shares higher. On that value, the whole company is at {yofc_pe:.1f}x (calc.). The Shanghai page would not open, so this is unchecked.</li>
<li><b>Dates differ.</b> Rival prices run from the Nov. 2 Tokyo close to Nov. 3 quotes, and Corning's page price of ${co["price"]:.2f} is not the ${px:.2f} close. Trailing periods end on different months, and fiscal years end in December for some and March for others.</li>
<li><b>Fast-moving profit makes trailing numbers stale.</b> Fujikura's page shows EBIT of ¥{by["Fujikura"]["ebit_b"]:.0f}B, while its own forecast for the year to March 2027 is operating profit of ¥432B, a forecast and not a result ({link("https://www.ad-hoc-news.de/boerse/news/corporate-news/fujikura-raises-jpy-821-billion-guidance-fujikura-stock-costs-eur-24-59-on-october-21-2026/70381246", "Ad-hoc News, Oct. 21, 2026")}). Its H1 results are due Nov. 10. YOFC's Q3 profit rose 1,741.52% ({link("https://www.21jingji.com/article/20261030/herald/8edb1c9c404bd80e96d53b06eac8bab0.html", "21 Jingji, Oct. 30, 2026")}).</li>
<li><b>Amphenol's deal distorts it.</b> Its debt carries the CommScope purchase in full, closed Jan. 9, 2026, but its twelve months hold only about nine months of that business ({link(aph["url"], "10-Q, filed " + nice(aph["filed"]))}). Its 2-for-1 split of Sept. 2, 2026 also means FY2025 EPS has to be halved before it is added to 2026's. The straight sum gives ${aph["straight_sum"]:.2f}, not ${aph["eps"]:.2f}.</li>
<li><b>These are group multiples, not fiber multiples.</b> Corning also sells display, auto, life science and solar products. Hengtong's optical business was 8.30% of 2025 revenue ({link("https://eu.36kr.com/en/p/3896566703343238", "36Kr, July 15, 2026")}). Prysmian's optical part is about a third of a segment with €566M of Q3 revenue ({link("https://stockanalysis.com/quote/bit/PRY/transcripts/659713-q3-2026/", "Prysmian Q3 call, Oct. 29, 2026, third-party transcript")}; {link("https://www.prysmian.com/sites/www.prysmian.com/files/2026-10/Prysmian%203Q26_Presentation_def.pdf", "Q3 slides, Oct. 29, 2026")}). Our notes hold no rivals for Corning's display, auto, life science or solar lines.</li>
<li><b>Accounting rules differ, and nothing was adjusted for them.</b> Corning and Amphenol report under US rules. The others report under their home rules, which were not read for this page.</li>
<li><b>Deposits may flatter other cash flows too.</b> Corning's are shown above. Prysmian cites about €550M of down payment on a take-or-pay deal ({link("https://stockanalysis.com/quote/bit/PRY/transcripts/659713-q3-2026/", "Prysmian Q3 call, Oct. 29, 2026, third-party transcript")}), and whether it is in the page's cash flow is unknown. So rival yields cannot be cleaned the same way.</li>
<li><b>No bond comparison for rivals.</b> Their home rates differ, and we hold only US series.</li>
</ul>

<h2>How far these numbers were checked</h2>
<ul class="notes">
<li>The ten full-year cash flows tie to the printed filings through the table in <code>Companies/Corning.md</code>. The test also ties the {nice(today["date"])} EPS, EBIT, cash, debt and free cash flow.</li>
<li>The Q3 figures behind the older "known that day" points come from SEC's data as filed. Only the Sept. 2026 10-Q was read in print here. In 2018 the EBIT sum mixes old and new pension accounting, because the prior-year nine months were restated and the prior full year was not.</li>
<li>Outside page figures were read through a fetch tool, not byte for byte.</li>
</ul>

<p class="foot" style="margin-top:24px">Sources: SEC filings through our EDGAR sensor, saved Nov. 2 and 3, 2026. {close_l}, for personal use only, latest close {nice(today["date"])}. {aaa_l}; {dgs_l}. Moody's Aaa data © Moody's Corporation, Moody's Investors Service, Inc., and Moody's Analytics, Inc. Moody's proprietary information, not to be copied or redistributed without its consent ({link(AAA, "FRED series notes, retrieved Nov. 2, 2026")}). Rival figures: short excerpts from StockAnalysis, read Nov. 3, 2026 ({link(TERMS, "its terms, updated Oct. 29, 2026")}).</p>
<p class="foot">Keep this page on this computer. It holds Yahoo and Moody's data. Yahoo's rule: {link("https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html", "Yahoo terms, updated Nov. 1, 2026")}, which bar automated collection without permission. The price fetch is my decision of Nov. 3, 2026.</p>
<div id="tip" hidden></div>
</main><script>{JS}</script></body></html>
"""
    OUT.write_text(page)
    print(f"Wrote {OUT} ({len(page):,} bytes). Now: P/E {today['pe']:.1f}, EV/EBIT {today['ev_ebit']:.1f}, FCF yield {today['fcfy']:.2f}%, Amphenol P/E {aph['pe']:.1f}, EV/EBIT {aph['ev_ebit']:.1f}, FCF {aph['fcfy']:.2f}")


if __name__ == "__main__":
    main()
