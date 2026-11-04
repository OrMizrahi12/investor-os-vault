"""Concentration lesson, step 3: draw concentration.html from cache/results.json.

    .venv/bin/python -I sensors/concentration/draw.py

No network. Keep the page on this computer, because its numbers come from a copy of Yahoo's prices.
"""
import csv
import html as H
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "cache/results.json").read_text())
LOG = json.loads((HERE / "cache/prepare_log.json").read_text())
OUT = HERE.parent.parent / "concentration.html"
S = R["sizes"]
MAIN = ["1", "5", "10", "20", "30"]
NAME = {"1": "1 stock", "5": "5 stocks", "10": "10 stocks", "20": "20 stocks", "30": "30 stocks"}
IN_RULE = {"5", "10", "20"}

WIKI = "https://en.wikipedia.org/w/index.php?title=List_of_S%26P_500_companies&oldid=747382003"
PRICES = "https://huggingface.co/datasets/defeatbeta/yahoo-finance-data"
CHECK = "https://huggingface.co/datasets/finsaber-team/FINSABER-V2-Data"
YAHOO = "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html"
SRC_PRICES = f'<a href="{PRICES}">price copy, updated Nov. 3, 2026</a>'
SRC_WIKI = f'<a href="{WIKI}">company list, Nov. 2, 2016</a>'


def tag(key, text, x=None):
    extra = f' data-x="{x}"' if x else ""
    return f'<b data-k="{key}"{extra}>{text}</b>'


def get(key):
    node = R
    for part in key.split("."):
        node = node[part]
    return float(node)


def pct(key, d=1):
    return tag(key, f"{get(key):.{d}f}%")


def fall(key, d=1):
    return tag(key, f"{abs(get(key)):.{d}f}%")


def day(iso):
    y, m, d = iso.split("-")
    names = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
    return f"{names[int(m) - 1]} {int(d)}, {y}"


def money(key):
    return tag(key, f"${round(get(key) * 10000, -2):,.0f}", x=10000)


def plain_money(m):
    return f"${round(m * 10000, -2):,.0f}"


med = {k: S[k]["vol"]["p50"] for k in S}
floor = R["all"]["vol"]
room = med["1"] - floor


def gone(k):
    return f'<span data-w="gone{k}">{(med["1"] - med[k]) / room * 100:.0f}%</span>'


def nice(v, d=1):
    return f"{'−' if v < 0 else ''}{abs(v):.{d}f}"


# ---------- word claims are tested before they are written ----------
assert (med["10"] - med["15"]) / 5 > 0.1 > (med["15"] - med["20"]) / 5
assert (med["20"] - med["30"]) / 10 < 0.05
width = {k: S[k]["cagr"]["p95"] - S[k]["cagr"]["p5"] for k in S}
assert all(width[a] > width[b] for a, b in zip(MAIN, MAIN[1:]))
assert width["30"] / width["20"] < 0.85, "the range still narrows past 20"
assert all(S[k]["crash20"]["p95"] < 0 for k in MAIN[1:]), "nearly all portfolios fell"
assert all(abs(S[k]["crash20"]["p50"] - R["all"]["crash20"]) < 0.5 for k in MAIN)
assert S["30"]["crash20"]["max"] < 0
assert R["sector"]["Energy"]["10"]["vol"]["p50"] > med["1"]
never = R["other_rules"]["never"]
assert never["30"]["cagr"]["p95"] > S["30"]["cagr"]["p95"] + 3
assert all(S[k]["lost_money"] < 0.2 for k in ("5", "10", "20", "30"))
tip_rows = []

# ---------- chart A: swing against holdings ----------
GRID = sorted(int(k) for k in S)


def chart_a():
    W, H_, L, Rt, T, B = 1000, 470, 58, 26, 34, 52
    x = lambda n: L + (W - L - Rt) * math.log(n) / math.log(100)
    ymax = 55
    y = lambda v: T + (H_ - T - B) * (1 - v / ymax)
    p = [f'<svg viewBox="0 0 {W} {H_}" role="img" aria-label="Typical yearly swing against number of holdings. The line falls fast from 1 to 5 holdings and flattens near 20.">']
    p.append(f'<rect x="{x(5):.1f}" y="{T}" width="{x(10) - x(5):.1f}" height="{H_ - T - B}" class="rule1"/>')
    p.append(f'<rect x="{x(10):.1f}" y="{T}" width="{x(20) - x(10):.1f}" height="{H_ - T - B}" class="rule2"/>')
    p.append(f'<text x="{x(7.07):.1f}" y="{T + 16}" text-anchor="middle" class="rl">Rule: 5 to 10</text>')
    p.append(f'<text x="{x(14.14):.1f}" y="{T + 16}" text-anchor="middle" class="rl">up to 20</text>')
    for v in range(0, 56, 10):
        p.append(f'<line x1="{L}" x2="{W - Rt}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/><text x="{L - 8}" y="{y(v) + 4:.1f}" text-anchor="end" class="ax">{v}%</text>')
    for n in (1, 2, 3, 5, 10, 20, 30, 50, 100):
        p.append(f'<line x1="{x(n):.1f}" x2="{x(n):.1f}" y1="{H_ - B}" y2="{H_ - B + 5}" class="tick"/><text x="{x(n):.1f}" y="{H_ - B + 20}" text-anchor="middle" class="ax">{n}</text>')
    p.append(f'<text x="{(L + W - Rt) / 2}" y="{H_ - 8}" text-anchor="middle" class="ax">Number of stocks held (each step to the right multiplies the count)</text>')
    top = " ".join(f'{x(n):.1f},{y(S[str(n)]["vol"]["p95"]):.1f}' for n in GRID)
    low = " ".join(f'{x(n):.1f},{y(S[str(n)]["vol"]["p5"]):.1f}' for n in reversed(GRID))
    p.append(f'<polygon points="{top} {low}" class="band"/>')
    p.append(f'<line x1="{L}" x2="{W - Rt}" y1="{y(floor):.1f}" y2="{y(floor):.1f}" class="floor"/>')
    p.append(f'<text x="{L + 8}" y="{y(floor) + 18:.1f}" class="lab halo">All {R["n_stocks"]} stocks together: {floor:.1f}%. Spreading out stops here, well above zero.</text>')
    line = " ".join(f'{x(n):.1f},{y(med[str(n)]):.1f}' for n in GRID)
    p.append(f'<polyline points="{line}" class="line"/>')
    for k in MAIN:
        n, v = int(k), med[k]
        p.append(f'<circle cx="{x(n):.1f}" cy="{y(v):.1f}" r="5" class="dot"/>')
        p.append(f'<text x="{x(n) + (10 if n == 1 else 0):.1f}" y="{y(v) - 12:.1f}" text-anchor="{"start" if n == 1 else "middle"}" class="lv halo">{v:.1f}%</text>')
    p.append(f'<text x="{x(1) + 8:.1f}" y="{y(S["1"]["vol"]["p95"]) + 4:.1f}" class="lab halo">Middle 90% of portfolios (shaded)</text>')
    edges = [L] + [(x(a) + x(b)) / 2 for a, b in zip(GRID, GRID[1:])] + [W - Rt]
    for i, n in enumerate(GRID):
        s = S[str(n)]
        tip = f"<b>{n} stock{'s' if n > 1 else ''}</b><br>Typical swing {s['vol']['p50']:.1f}%<br>Middle 90%: {s['vol']['p5']:.1f}% to {s['vol']['p95']:.1f}%"
        p.append(f'<rect x="{edges[i]:.1f}" y="{T}" width="{edges[i + 1] - edges[i]:.1f}" height="{H_ - T - B}" class="hit" data-tip="{H.escape(tip)}"/>')
    p.append("</svg>")
    return "".join(p)


# ---------- range rows: charts B and C ----------
def ranges(metric, lo, hi, ref, ref_label, step, right, aria, unit="%"):
    W, row, L, Rt, T, B = 1000, 58, 96, 210, 40, 40
    H_ = T + B + row * len(MAIN)
    x = lambda v: L + (W - L - Rt) * (v - lo) / (hi - lo)
    p = [f'<svg viewBox="0 0 {W} {H_}" role="img" aria-label="{H.escape(aria)}">']
    a, b = T + row, T + row * 4
    p.append(f'<rect x="{L}" y="{a}" width="{W - L - Rt}" height="{b - a}" class="rule2"/>')
    p.append(f'<text x="{L + 8}" y="{a + 14}" class="rl">Our rule: 5 to 10, up to 20</text>')
    v = lo
    while v <= hi + 1e-9:
        p.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T}" y2="{H_ - B}" class="{"zero" if v == 0 else "grid"}"/><text x="{x(v):.1f}" y="{H_ - B + 20}" text-anchor="middle" class="ax">{nice(v, 0)}{unit}</text>')
        v += step
    p.append(f'<line x1="{x(ref):.1f}" x2="{x(ref):.1f}" y1="{T - 8}" y2="{H_ - B}" class="floor"/><text x="{x(ref):.1f}" y="{T - 14}" text-anchor="middle" class="lab">{ref_label}</text>')
    for i, k in enumerate(MAIN):
        s = S[k][metric]
        cy = T + row * i + row / 2 + 4
        cls = "in" if k in IN_RULE else "out"
        p.append(f'<text x="{L - 10}" y="{cy + 4:.1f}" text-anchor="end" class="lv">{NAME[k]}</text>')
        p.append(f'<rect x="{x(s["p5"]):.1f}" y="{cy - 4}" width="{x(s["p95"]) - x(s["p5"]):.1f}" height="8" rx="4" class="r90 {cls}"/>')
        p.append(f'<rect x="{x(s["p25"]):.1f}" y="{cy - 8}" width="{x(s["p75"]) - x(s["p25"]):.1f}" height="16" rx="4" class="r50 {cls}"/>')
        p.append(f'<rect x="{x(s["p50"]) - 2:.1f}" y="{cy - 13}" width="4" height="26" rx="2" class="mid"/>')
        p.append(f'<text x="{W - Rt + 12}" y="{cy + 4:.1f}" class="lab">{right(k)}</text>')
        tip = f"<b>{NAME[k]}</b><br>Middle 90%: {nice(s['p5'])}% to {nice(s['p95'])}%<br>Middle 50%: {nice(s['p25'])}% to {nice(s['p75'])}%<br>Typical: {nice(s['p50'])}%"
        p.append(f'<rect x="{L}" y="{T + row * i}" width="{W - L - Rt}" height="{row}" class="hit" data-tip="{H.escape(tip)}"/>')
    p.append("</svg>")
    return "".join(p)


def legend_ranges():
    return ('<ul class="legend"><li><span class="key k90"></span>Middle 90% of portfolios</li><li><span class="key k50"></span>Middle 50%</li>'
            '<li><span class="key kmid"></span>Typical (median)</li><li><span class="key kout"></span>Gray: outside our rule</li></ul>')


# ---------- chart D: sectors ----------
def chart_d():
    rows = sorted(R["sector"].items(), key=lambda kv: kv[1]["10"]["vol"]["p50"])
    W, row, L, Rt, T, B = 1000, 30, 190, 40, 44, 40
    H_ = T + B + row * len(rows)
    lo, hi = 0, 40
    x = lambda v: L + (W - L - Rt) * (v - lo) / (hi - lo)
    p = [f'<svg viewBox="0 0 {W} {H_}" role="img" aria-label="Typical swing of ten stocks all from one sector, against ten random stocks and one single stock.">']
    for v in range(0, 41, 10):
        p.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T}" y2="{H_ - B}" class="grid"/><text x="{x(v):.1f}" y="{H_ - B + 20}" text-anchor="middle" class="ax">{v}%</text>')
    for v, label, anchor in ((med["10"], f"10 random stocks: {med['10']:.1f}%", "end"), (med["1"], f"1 random stock: {med['1']:.1f}%", "start")):
        p.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T - 8}" y2="{H_ - B}" class="floor"/><text x="{x(v) + (6 if anchor == "start" else -6):.1f}" y="{T - 14}" text-anchor="{anchor}" class="lab">{label}</text>')
    for i, (name, d) in enumerate(rows):
        s = d["10"]
        cy = T + row * i + row / 2
        v = s["vol"]["p50"]
        p.append(f'<text x="{L - 10}" y="{cy + 4:.1f}" text-anchor="end" class="lab">{H.escape(name)}</text>')
        p.append(f'<line x1="{x(0):.1f}" x2="{x(v):.1f}" y1="{cy}" y2="{cy}" class="stem"/>')
        p.append(f'<circle cx="{x(v):.1f}" cy="{cy}" r="6" class="dot"/><text x="{x(v) + 12:.1f}" y="{cy + 4:.1f}" class="lv halo">{v:.1f}%</text>')
        tip = f"<b>{H.escape(name)}</b><br>Ten stocks from {d['count']} in this sector<br>Typical swing {v:.1f}%<br>Fall in early 2020: {nice(s['crash20']['p50'])}%"
        p.append(f'<rect x="{L}" y="{T + row * i}" width="{W - L - Rt}" height="{row}" class="hit" data-tip="{H.escape(tip)}"/>')
    p.append("</svg>")
    return "".join(p)


# ---------- tables ----------
def table_main():
    rows = []
    for k in MAIN:
        s = S[k]
        rows.append(f'<tr><th scope="row">{NAME[k]}{" <span class=rule-mark>rule</span>" if k in IN_RULE else ""}</th><td class="n">{s["vol"]["p50"]:.1f}%</td><td class="n">{s["vol"]["p5"]:.1f}% to {s["vol"]["p95"]:.1f}%</td><td class="n">{gone(k) if k != "1" else "0%"}</td><td class="n">{nice(s["cagr"]["p5"])}% to {nice(s["cagr"]["p95"])}%</td><td class="n">{width[k]:.1f}</td><td class="n">{nice(s["dd"]["p50"])}%</td></tr>')
    a = R["all"]
    rows.append(f'<tr><th scope="row">All {R["n_stocks"]}</th><td class="n">{a["vol"]:.1f}%</td><td class="n">one result</td><td class="n">100%</td><td class="n">{a["cagr"]:.1f}%</td><td class="n">0</td><td class="n">{nice(a["dd"])}%</td></tr>')
    return ('<div class="wrap"><table><thead><tr><th>Holdings</th><th class="n">Typical swing</th><th class="n">Swing, middle 90%</th><th class="n">Removable swing gone</th><th class="n">Yearly result, middle 90%</th><th class="n">Width, points</th><th class="n">Typical worst fall</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def table_step():
    steps = [(1, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 50), (50, 100)]
    rows = []
    for a, b in steps:
        cut = (med[str(a)] - med[str(b)]) / (b - a)
        wa, wb = width[str(a)], width[str(b)]
        rows.append(f'<tr><th scope="row">{a} to {b}</th><td class="n">{"under 0.01" if cut < 0.005 else f"{cut:.2f}"}</td><td class="n">{(wa - wb) / (b - a):.2f}</td></tr>')
    return ('<div class="wrap narrow"><table><thead><tr><th>Going from</th><th class="n">Swing cut per added stock, points</th><th class="n">Result range cut per added stock, points</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def table_mistake():
    worst = R["stocks"]["min_mult"] - 1
    rows = []
    for k in MAIN:
        w = 1 / int(k)
        rows.append(f'<tr><th scope="row">{NAME[k]}</th><td class="n">{w * 100:.1f}%</td><td class="n">−{w * 100:.1f}%</td><td class="n">−{abs(worst) * w * 100:.1f}%</td></tr>')
    return ('<div class="wrap narrow"><table><thead><tr><th>Holdings</th><th class="n">Size of each position</th><th class="n">If one goes to zero</th><th class="n">If one does as badly as the worst here</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def table_rules():
    rows = []
    for k in MAIN:
        y, n, d = S[k], never[k], R["other_rules"]["daily"][k]
        rows.append(f'<tr><th scope="row">{NAME[k]}</th><td class="n">{nice(y["cagr"]["p5"])}% to {nice(y["cagr"]["p95"])}%</td><td class="n">{nice(n["cagr"]["p5"])}% to {nice(n["cagr"]["p95"])}%</td><td class="n">{nice(d["cagr"]["p5"])}% to {nice(d["cagr"]["p95"])}%</td></tr>')
    return ('<div class="wrap narrow"><table><thead><tr><th>Holdings</th><th class="n">Back to equal each year (main test)</th><th class="n">Bought equal, never touched</th><th class="n">Back to equal each day</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def table_sector():
    rows = []
    for name, d in sorted(R["sector"].items(), key=lambda kv: kv[1]["10"]["vol"]["p50"]):
        s = d["10"]
        rows.append(f'<tr><th scope="row">{H.escape(name)}</th><td class="n">{d["count"]}</td><td class="n">{s["vol"]["p50"]:.1f}%</td><td class="n">{nice(s["cagr"]["p5"])}% to {nice(s["cagr"]["p95"])}%</td><td class="n">{nice(s["crash20"]["p50"])}%</td></tr>')
    s = S["10"]
    rows.append(f'<tr><th scope="row">Any sector (random)</th><td class="n">{R["n_stocks"]}</td><td class="n">{s["vol"]["p50"]:.1f}%</td><td class="n">{nice(s["cagr"]["p5"])}% to {nice(s["cagr"]["p95"])}%</td><td class="n">{nice(s["crash20"]["p50"])}%</td></tr>')
    return ('<div class="wrap"><table><thead><tr><th>Ten stocks from</th><th class="n">Stocks to draw from</th><th class="n">Typical swing</th><th class="n">Yearly result, middle 90%</th><th class="n">Fall in early 2020, typical</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def table_check():
    rows = []
    for k in MAIN:
        a, b = R["check"]["sizes"][k]["kept"], R["check"]["sizes"][k]["all"]
        rows.append(f'<tr><th scope="row">{NAME[k]}</th><td class="n">{nice(a["cagr"]["p5"])}%, {nice(a["cagr"]["p50"])}%, {nice(a["cagr"]["p95"])}%</td><td class="n">{nice(b["cagr"]["p5"])}%, {nice(b["cagr"]["p50"])}%, {nice(b["cagr"]["p95"])}%</td><td class="n">{a["vol"]["p50"]:.1f}% / {b["vol"]["p50"]:.1f}%</td></tr>')
    return ('<div class="wrap"><table><thead><tr><th>Holdings</th><th class="n">Survivors only: low, typical, high</th><th class="n">With vanished names: low, typical, high</th><th class="n">Typical swing, survivors / with vanished</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def names_table():
    with open(HERE / "cache/universe.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    cells = "".join(
        f'<tr><td>{H.escape(r["name"])}</td><td>{H.escape(r["ticker"])}</td><td>{H.escape(r["symbol"]) if r["symbol"] != r["ticker"] else ""}</td><td>{H.escape(r["sector"])}</td></tr>'
        for r in rows
    )
    return f'<div class="wrap tall"><table><thead><tr><th>Company, as listed in 2016</th><th>Ticker in 2016</th><th>Ticker now, if changed</th><th>Sector in 2016</th></tr></thead><tbody>{cells}</tbody></table></div>'


STYLE = """
/* Layout: one reading column, charts wider than the text, conclusion first. */
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--s0:#8f8e85;--s1:#2a78d6;--tint:rgba(42,120,214,.13);--tint2:rgba(42,120,214,.07)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#77766f;--s1:#3987e5;--tint:rgba(57,135,229,.22);--tint2:rgba(57,135,229,.11)}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#77766f;--s1:#3987e5;--tint:rgba(57,135,229,.22);--tint2:rgba(57,135,229,.11)}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px max(16px,env(safe-area-inset-right,0px)) 48px max(16px,env(safe-area-inset-left,0px))}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}
h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
p,ul.txt{margin:0 0 10px;max-width:75ch}ul.txt{padding-left:20px}ul.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
b[data-k]{font-weight:inherit}
a{color:var(--link)}a:focus-visible,summary:focus-visible{outline:2px solid var(--link);outline-offset:2px}
.note{font-size:13.5px;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:80ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:5px}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:14px;height:10px;margin-right:7px;vertical-align:0;border-radius:3px}
.k90{background:var(--s1);opacity:.45}.k50{background:var(--s1)}.kmid{background:var(--ink);width:4px;height:14px;vertical-align:-2px}.kout{background:var(--s0)}
.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:640px;height:auto;font:13px system-ui,-apple-system,"Segoe UI",sans-serif}
svg text{fill:var(--ink-2)}svg .lv{fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}svg .ax{fill:var(--muted)}svg .rl{fill:var(--link);font-weight:600}svg .lab{fill:var(--ink-2)}
svg .halo{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
.rule1{fill:var(--tint)}.rule2{fill:var(--tint2)}.grid{stroke:var(--grid);stroke-width:1}.zero{stroke:var(--axis);stroke-width:1}.tick{stroke:var(--axis)}
.floor{stroke:var(--ink-2);stroke-width:1.5;stroke-dasharray:5 4}.band{fill:var(--s1);opacity:.18}.line{fill:none;stroke:var(--s1);stroke-width:2.5;stroke-linejoin:round}
.dot{fill:var(--s1);stroke:var(--surface);stroke-width:2}.stem{stroke:var(--axis);stroke-width:1.5}
.r90.in{fill:var(--s1);opacity:.45}.r50.in{fill:var(--s1)}.r90.out{fill:var(--s0);opacity:.5}.r50.out{fill:var(--s0)}.mid{fill:var(--ink)}
.hit{fill:transparent;cursor:crosshair}.hit:hover{fill:var(--tint2)}
figure{margin:0}figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:85ch}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.14)}#tip b{font-weight:650}
.wrap{overflow-x:auto;margin-top:10px}.wrap.narrow{max-width:760px}.wrap.tall{max-height:520px;overflow-y:auto}.wrap.tall td{white-space:normal}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600;white-space:nowrap}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}thead .n{white-space:normal}
.rule-mark{font-size:11px;font-weight:600;color:var(--link);border:1px solid var(--link);border-radius:4px;padding:0 4px;margin-left:4px;letter-spacing:.02em}
details{margin:10px 0}summary{cursor:pointer;font-weight:600}
footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--border);color:var(--muted);font-size:13px}
"""

c20 = [day(x) for x in R["crash20_dates"]]
b22 = [day(x) for x in R["bear22_dates"]]
check_end = day(R["check"]["end"])
st = R["stocks"]
hw = R["hold_a_winner"]
n = R["n_stocks"]
miss = LOG["companies_no_full_history"]
worst_pct = abs(st["min_mult"] - 1) * 100
energy = R["sector"]["Energy"]["10"]
tech = R["sector"]["Information Technology"]["10"]
staples = R["sector"]["Consumer Staples"]["10"]
off = LOG["check_off_by_more"]


def cite():
    return f"calc., from {SRC_PRICES} and {SRC_WIKI}"


def Cite():
    return f"Calc., from {SRC_PRICES} and {SRC_WIKI}"


chk = R["check"]["sizes"]
sector_mids = [d["10"]["cagr"]["p50"] for d in R["sector"].values()]
sector_gap = max(sector_mids) - min(sector_mids)
size_gap = S["30"]["cagr"]["p50"] - S["1"]["cagr"]["p50"]
assert sector_gap > size_gap > 0 and min(sector_mids) == R["sector"]["Consumer Staples"]["10"]["cagr"]["p50"] and max(sector_mids) == R["sector"]["Information Technology"]["10"]["cagr"]["p50"]
drop_mid = [chk[k]["kept"]["cagr"]["p50"] - chk[k]["all"]["cagr"]["p50"] for k in MAIN[1:]]
drop_low = [chk[k]["kept"]["cagr"]["p5"] - chk[k]["all"]["cagr"]["p5"] for k in MAIN[1:]]
drop_vol = [abs(chk[k]["kept"]["vol"]["p50"] - chk[k]["all"]["vol"]["p50"]) for k in MAIN[1:]]
assert max(drop_vol) < 0.4 and min(drop_mid) > 0 and min(drop_low) > 0
assert S["6"]["lost_money"] < 0.05 and 2 < (med["1"] - med["5"]) / 4 < 2.3 and 0.025 < (med["25"] - med["30"]) / 5 < 0.035
assert all(21.5 < never[k]["cagr"]["p95"] < 23.5 for k in ("5", "10", "20", "30"))
assert all(0 < S[k]["cagr"]["p5"] - never[k]["cagr"]["p5"] < 1 for k in ("5", "10", "20", "30"))


page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Why 5 to 20 Holdings</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>{STYLE}</style></head><body><main>
<h1>Why we hold 5 to 20 stocks</h1>
<p class="lede">The numbers back the rule at both ends, with one warning. Five stocks remove most of the risk that spreading out can remove. Past about 15 to 20, more stocks barely calm the swings. But the range of ten-year results keeps narrowing past 20, so this test does not make 20 a wall. That limit rests on how many companies we can know well, which no price test can measure.</p>
<p class="note">A lesson, not advice, and no stock here is a pick. Nothing here says what to buy, hold or sell. The portfolios are random: this tests the counting, not anyone's choosing.</p>

<div class="answer"><strong>What ten years of daily prices show</strong> ({n} large US companies, Nov. 3, 2016 to Nov. 2, 2026, {R['draws']:,} random portfolios at each size)
<ul>
<li><strong>1 to 5 stocks does the most.</strong> The typical yearly swing falls from {pct('sizes.1.vol.p50')} to {pct('sizes.5.vol.p50')}. That is {gone('5')} of the swing spreading out can remove.</li>
<li><strong>5 to 10 still helps, 10 to 20 less so.</strong> Ten stocks reach {gone('10')}, twenty reach {gone('20')}, thirty reach {gone('30')}. This fits a rule of 5 to 10, up to 20 for good reason.</li>
<li><strong>Swing stops improving first.</strong> Past 15 stocks, each one added takes less than 0.1 of a point off the swing.</li>
<li><strong>The range of results narrows for longer.</strong> The middle 90% of yearly results is {pct('sizes.5.cagr.p5')} to {pct('sizes.5.cagr.p95')} at 5 stocks, {pct('sizes.20.cagr.p5')} to {pct('sizes.20.cagr.p95')} at 20 and {pct('sizes.30.cagr.p5')} to {pct('sizes.30.cagr.p95')} at 30.</li>
<li><strong>Spreading out does not stop a market fall.</strong> In early 2020 the typical portfolio fell about {tag('all.crash20', f"{abs(R['all']['crash20']):.0f}%")} at every size.</li>
</ul></div>

<h2>Risk against the number of holdings</h2>
<p>"Swing" means how far a portfolio's value typically moves up or down in a year. In statistics it is the yearly standard deviation of daily returns. A lower line means a calmer ride, not a better result.</p>
<div class="card"><figure><div class="scroll">{chart_a()}</div>
<figcaption>Line: the median portfolio at each size. Dots: the five sizes you asked about. Hover for values. Equal weight, back to equal once a year, dividends counted, no costs or tax. All figures {cite()}.</figcaption></figure></div>

<h2>The spread of results at each size</h2>
<p>This is the same test, measured by what you ended with. Each row shows yearly growth over the ten years. The right column shows what $10,000 became for the middle 90% of portfolios.</p>
<div class="card">{legend_ranges()}<figure><div class="scroll">{ranges('cagr', -10, 30, R['all']['cagr'], f"All {n} stocks: {R['all']['cagr']:.1f}% a year", 10, lambda k: f"{plain_money(S[k]['mult']['p5'])} to {plain_money(S[k]['mult']['p95'])}", 'Ten-year yearly growth for random portfolios at 1, 5, 10, 20 and 30 stocks. The range narrows as holdings rise.')}</div>
<figcaption>Single-stock row: each of the {n} stocks once. Other rows: {R['draws']:,} random portfolios each. Same rules as above. {Cite()}.</figcaption></figure></div>
<p>{tag('all.mult', f"{R['all']['mult']:.2f}", None)}× is what all {n} together made, so $10,000 became {money('all.mult')}. A 5-stock portfolio at the low end of its range made {money('sizes.5.mult.p5')}, about half of that, by the luck of the draw alone. Five stocks is the edge of the rule, not a safe place.</p>
{table_main()}
<p class="note">"Removable swing gone" compares each size with the two ends: 0% at one stock, 100% at all {n}. Typical worst fall is the median portfolio's largest drop from a high in the ten years. Calc.</p>

<h2>Where adding more stops helping</h2>
<p>The swing and the range of results give two different answers, and both matter.</p>
{table_step()}
<ul class="txt" style="margin-top:12px">
<li><strong>Swing:</strong> the first four added stocks take about 2 points each. By 15 to 20 it is under 0.1 per stock. By 25 to 30 it is about 0.03. That is the flat part of the first chart.</li>
<li><strong>Range of results:</strong> it narrows more slowly. Going from 20 to 30 stocks still cuts its width by {(1 - width['30'] / width['20']) * 100:.0f}%. Going from 10 to 20 cuts it by {(1 - width['20'] / width['10']) * 100:.0f}%.</li>
<li><strong>What the two together say:</strong> past 20, you gain little calm. You do gain some certainty of ending near the average, but that is not what a concentrated investor is trying to do.</li>
</ul>

<h2>What spreading out protects you from</h2>
<p><strong>One company's bad luck or your one mistake.</strong> Of the {n} stocks, {tag('stocks.lost_money', st['lost_money'])} lost money over the ten years even in a strong market, and {tag('stocks.lost_half', st['lost_half'])} lost more than half. Among single stocks, {pct('sizes.1.lost_money')} lost money. At 5 stocks, {pct('sizes.5.lost_money')} of portfolios did. From 6 stocks up, about none did (but see the warning on survivors below).</p>
<p>This is what <code>rules.md</code> means by "one mistake cannot sink the portfolio". Worst here means a {worst_pct:.0f}% loss over the ten years. These sums assume equal positions. A larger position sized on a strong thesis takes a larger hit.</p>
{table_mistake()}

<h2>What it does not protect you from</h2>
<p><strong>A market fall.</strong> From {c20[0]} to {c20[1]}, all {n} stocks together fell {fall('all.crash20')}. Most of the fall was shared. Adding stocks narrowed the range around that figure but did not move it. At 30 stocks, every one of the {S['30']['portfolios']:,} portfolios fell, by at least {fall('sizes.30.crash20.max')}.</p>
<div class="card">{legend_ranges()}<figure><div class="scroll">{ranges('crash20', -70, 20, R['all']['crash20'], f"All {n} stocks: {nice(R['all']['crash20'])}%", 10, lambda k: f"typical {nice(S[k]['crash20']['p50'])}%", 'Fall in early 2020 for random portfolios at each size. The typical fall is about 40 percent at every size.')}</div>
<figcaption>Change in value from {c20[0]} to {c20[1]}, the worst fall of the all-stock basket in 2020. {Cite()}.</figcaption></figure></div>
<p>Stocks also move together more when it counts. The average pair of stocks had a correlation of {tag('corr_outside_crash20', f"{R['corr_outside_crash20']:.2f}")} outside that fall and {tag('corr_crash20', f"{R['corr_crash20']:.2f}")} during it (1.00 means moving in lockstep). The same holds in 2022: from {b22[0]} to {b22[1]} the basket fell {fall('all.bear22')}, and 20-stock portfolios typically fell {fall('sizes.20.bear22.p50')}. The typical worst fall over the ten years was {fall('sizes.5.dd.p50')} at 5 stocks and {fall('sizes.30.dd.p50')} at 30.</p>
<p><strong>A shared bet.</strong> Twenty names with one shared reason to fall are not twenty separate risks. Ten stocks drawn from a single sector can swing more than one random stock. Ten energy stocks had a typical swing of {pct('sector.Energy.10.vol.p50')}, against {pct('sizes.1.vol.p50')} for one random stock and {pct('sizes.10.vol.p50')} for ten random stocks. They fell {fall('sector.Energy.10.crash20.p50')} in early 2020.</p>
<div class="card"><figure><div class="scroll">{chart_d()}</div>
<figcaption>Ten stocks from one sector, using each company's 2016 sector label. Sectors with fewer than 20 stocks are left out. 5,000 draws each. {Cite()}. Past sector results, not a view on any sector.</figcaption></figure></div>
{table_sector()}
<p style="margin-top:12px">For the typical result, which sector you were in mattered more than how many names you held. Ten stocks' typical yearly result ran from {pct('sector.Consumer Staples.10.cagr.p50')} in consumer staples to {pct('sector.Information Technology.10.cagr.p50')} in information technology, a gap of {sector_gap:.1f} points. Going from 1 to 30 random stocks moved it only {size_gap:.1f}. This test sorts by old sector labels only. It cannot see a theme that cuts across sectors, such as many companies leaning on the same customers.</p>
<p><strong>Paying too much or a wrong idea you hold everywhere.</strong> Random draws cannot test these directly. If the same mistake sits behind every position, the count of positions does not help. Our buy test and the skeptic's review are the guard there, not the number of holdings.</p>

<h2>What it costs</h2>
<ul class="txt">
<li><strong>The very best outcomes.</strong> With the yearly reset, the top of the range falls from {pct('sizes.1.cagr.p95')} a year at 1 stock to {pct('sizes.5.cagr.p95')} at 5, {pct('sizes.20.cagr.p95')} at 20 and {pct('sizes.30.cagr.p95')} at 30. In money, $10,000 at the top of the range goes from {money('sizes.1.mult.p95')} to {money('sizes.5.mult.p95')}, {money('sizes.20.mult.p95')} and {money('sizes.30.mult.p95')}.</li>
<li><strong>Your best idea counts for less.</strong> The top {st['top_count']} stocks made {pct('stocks.top_share_of_gain', 0)} of all the gain, each growing at least {tag('stocks.top_cutoff_mult', f"{st['top_cutoff_mult']:.1f}")}×. More holdings raise the chance of owning one: {pct('hold_a_winner.1', 0)} at 1 stock, {pct('hold_a_winner.5', 0)} at 5, {pct('hold_a_winner.10', 0)} at 10, {pct('hold_a_winner.20', 0)} at 20, {pct('hold_a_winner.30', 0)} at 30. But a winner is then a smaller share of the portfolio.</li>
<li><strong>Time and knowledge.</strong> Each extra company is another set of filings to read and another thesis to watch. This test cannot measure that. It is the reason <code>rules.md</code> gives for keeping the count small.</li>
</ul>
<p><strong>It did not cost return here.</strong> The typical result went up with more stocks, from {pct('sizes.1.cagr.p50')} a year at 1 to {pct('sizes.5.cagr.p50')} at 5 and {pct('sizes.30.cagr.p50')} at 30, because the typical stock lags the average, and a portfolio moves toward the average as it grows. Only {tag('stocks.beat_basket', st['beat_basket'])} of the {n} stocks beat the basket of all {n}. A random stock is not a chosen one, though. A skilled picker's 30th idea may be worse than the 5th, and this test cannot see that.</p>

<h2>How the holding rule changes this</h2>
<p>You asked for equal weight, so the main test resets to equal once a year. Our rules do not rebalance, so the middle column below is closer to how we hold. The low end is a little lower. The top end hardly shrinks: it stays between 21.5% and 23.5% a year from 5 to 30 stocks, because one rare winner left alone can grow to dominate the portfolio. So under our way of holding, the cost in best outcomes is smaller than the chart above shows.</p>
{table_rules()}
<p class="note" style="margin-top:8px">Middle 90% of yearly results over the ten years. {R['draws']:,} draws per size, calc.</p>

<h2>What this test cannot say</h2>
<ul class="txt">
<li><strong>Survivors only.</strong> The {n} are the companies with a whole ten-year price record. {len(miss)} of the 500 companies listed in 2016 have none in the data, and we did not check why each is missing. That flatters every number here. A second check is below.</li>
<li><strong>One decade, a strong one.</strong> All {n} together grew {pct('all.cagr')} a year. In a flat or falling decade, more portfolios would likely lose money. "About none lost money" belongs to this decade.</li>
<li><strong>Hindsight.</strong> The list is from Nov. 2016, not today's winners, so it was fixed before the ten years began. That removes the choosing part of hindsight, but not the survivor problem above.</li>
<li><strong>Random, equal, and fully invested.</strong> We choose stocks, size them by thesis and hold cash. Unequal positions act like fewer holdings, so sizing up on a few ideas means less spreading than the count suggests.</li>
<li><strong>No costs and no tax.</strong> Resetting each year would have some of both.</li>
<li><strong>Past prices.</strong> Nothing here is a forecast.</li>
</ul>
<p><strong>The survivor check.</strong> A second public copy of prices, ending {check_end}, keeps most companies that later vanished ({R['check']['names_gone_early']} of its {R['check']['names_all']} names stop early). Their money sits idle until the next yearly reset. From 5 stocks up, adding them lowers the typical result by {min(drop_mid):.1f} to {max(drop_mid):.1f} points a year and the low end by {min(drop_low):.1f} to {max(drop_low):.1f}. Typical swing moves by less than 0.4. So the lesson holds, and the levels above are a little too kind.</p>
{table_check()}
<p class="note" style="margin-top:8px">Nov. 3, 2016 to {check_end}. 5,000 draws per size, middle 90% as low and high. Calc., from the <a href="{CHECK}">second copy, updated May 21, 2026</a>. Its source is not stated on its page and {LOG['check_series_cut_for_faults']} of its series were cut at a fault, so it is used only as this check.</p>

<h2 id="sources">Where the data came from</h2>
<ul class="txt">
<li><strong>The named set:</strong> the {SRC_WIKI}, a Wikipedia page revision, retrieved Nov. 3, 2026. It is not S&amp;P's own record, and its text says the list was current as of July 1, 2016. One row per company, matched by SEC ID so renamed companies stay in. {n} used.</li>
<li><strong>Prices:</strong> the {SRC_PRICES}, on Hugging Face (licence ODC-BY), retrieved Nov. 3, 2026. Daily closes, with dividends added back. Split-adjusted.</li>
<li><strong>Yahoo:</strong> that file is someone else's copy of Yahoo's data. We sent Yahoo no request. Our own Yahoo script stayed at one ticker, as you decided on Nov. 3. But this data began at Yahoo, for {n} tickers, and Yahoo's <a href="{YAHOO}">terms, updated Nov. 1, 2026</a>, limit copying. You ruled on Nov. 3, 2026 that this copy fits your Yahoo decision and that the page stays local. The other free bulk files I found were also Yahoo copies, ended too early, or needed a key or a login. This page stays on this computer.</li>
</ul>
<p><strong>Repairs and checks:</strong></p>
<ul class="txt">
<li>Dropped: {LOG['companies_dropped_for_faults'][0][1]} ({LOG['companies_dropped_for_faults'][0][2]}) and {LOG['companies_dropped_for_faults'][1][1]} ({LOG['companies_dropped_for_faults'][1][2]}).</li>
<li>Fixed: Bank of New York Mellon's new ticker carried a different fund's history before Dec. 1, 2025, so its old ticker fills that part. {LOG['dividends_resplit']} dividends were restated by a rule, because the file mixes split-adjusted and unadjusted amounts.</li>
<li>Compared to the second copy, {LOG['check_within_5pct']} of {LOG['check_compared']} stocks matched within 5% over 9.2 years. The other {len(off)} differ by more: {', '.join(off)}. We did not trace each one and left them as they are.</li>
<li>Corning's ten-year total return matched our own saved Yahoo file within 0.1%. A separate script, sharing no code with the simulation, redrew the portfolios and matched the results within its limits. Numbers in these sentences are filled in from the results, and that script spot-checks them.</li>
</ul>
<details><summary>The {n} companies in the set (none is a pick)</summary>{names_table()}</details>
<details><summary>The {len(miss)} listed companies with no whole ten-year record</summary><p>{H.escape(', '.join(m[1] for m in miss))}.</p></details>
<footer>Built Nov. 3, 2026 by <code>sensors/concentration/</code>. Seed {R['seed']}, so a rerun gives the same numbers. Keep on this computer. A lesson, not advice. No stock here is a pick.</footer>
</main>
<div id="tip" hidden></div>
<script>
const tip=document.getElementById('tip');
document.querySelectorAll('.hit').forEach(el=>{{
  el.addEventListener('pointermove',e=>{{tip.innerHTML=el.dataset.tip;tip.hidden=false;
    const w=tip.offsetWidth,h=tip.offsetHeight;
    tip.style.left=Math.min(innerWidth-w-8,e.clientX+14)+'px';tip.style.top=Math.max(8,e.clientY-h-10)+'px';}});
  el.addEventListener('pointerleave',()=>{{tip.hidden=true;}});
}});
</script></body></html>
"""
OUT.write_text(page)
print("wrote", OUT, len(page))
