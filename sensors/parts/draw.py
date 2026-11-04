"""Builds parts.html from model.py. Takes no flags and writes when run.

    .venv/bin/python sensors/parts/draw.py
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as m

d = m.build()
P, cases = d["P"], d["cases"]
low, mid, high = cases
SEC = "https://www.sec.gov/Archives/edgar/data/24741/"
K25 = SEC + "000002474126000124/glw-20251231.htm"
K24 = SEC + "000162828025005347/glw-20241231.htm"
K23 = SEC + "000143774924003735/glw20231231_10k.htm"
K22 = SEC + "000143774923003123/glw20221231_10k.htm"
K21 = SEC + "000143774922003247/glw20211231_10k.htm"
K20 = SEC + "000156276221000023/glw-20201231x10k.htm"
K19 = SEC + "000002474120000014/glw-20191231x10k.htm"
K18 = SEC + "000002474119000016/glw-20181231x10k.htm"
Q10 = SEC + "000002474126000279/glw-20260930.htm"
Q1R = SEC + "000002474126000198/glw-20260328xex991xq12026.htm"
Q2R = "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000253/glw-20260728xex99xq22026.htm"
Q3R = "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&amp;interval=1d"
NV8K = SEC + "000120677426000273/glw4631061-8k.htm"
META = "https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/"


def a(url, text):
    return f'<a href="{url}">{text}</a>'


def q10():
    return a(Q10, "10-Q, filed Oct. 29, 2026")


def k25():
    return a(K25, "10-K, filed Feb. 12, 2026")


def bn(x, dp=1):
    sign = "−" if x < 0 else ""
    return f"{sign}${abs(x) / 1000:,.{dp}f}B"


def mm(x):
    x = round(x)
    return f"−${-x:,}M" if x < 0 else f"${x:,}M"


def num(x):
    return f"−{-x:,}" if x < 0 else f"{x:,}"


def xx(v):
    return f"{v:.2f}x" if v < 10 else f"{v:.1f}x"


def pct(x):
    return f"{x * 100:.0f}%"


def esc(s):
    return html.escape(s, quote=True)


CSS = open(Path(__file__).resolve().parent / "style.css").read()
COL = dict(Optical="var(--s1)", Glass="var(--s2)", Auto="var(--s3)", Solar="var(--s4)", Life="var(--s5)")
SHORT = dict(Optical="Optical", Glass="Glass", Auto="Automotive", Solar="Solar", Life="Life Sciences + Emerging")


# ---------- the stack
def stack():
    W, L, R, top, gh = 1040, 74, 1016, 50, 92
    H = top + gh * 3 + 30
    MAXV = 150000
    X = lambda v: L + v / MAXV * (R - L)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Three stacked bars of the parts, low, middle and high, against market value and enterprise value. The numbers are in the table below.">']
    for v in range(0, 150001, 25000):
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top - 6}" y2="{H - 26}" stroke="var(--grid)"/>')
        o.append(f'<text class="ax" x="{X(v):.1f}" y="{H - 8}" text-anchor="middle">${v // 1000}B</text>')
    for i, c in enumerate(cases):
        y = top + i * gh + 6
        o.append(f'<text class="lv" x="0" y="{y + 18}">{c["name"]}</text>')
        x0 = 0
        for s in m.SEGS:
            v = c["parts"][s]
            x1, x2 = X(x0), X(x0 + v)
            tip = f'<b>{m.NAME[s]}, {c["name"].lower()} case</b><br>{mm(v)}'
            o.append(f'<rect data-tip="{esc(tip)}" x="{x1:.1f}" y="{y}" width="{max(x2 - x1 - 2, 1):.1f}" height="28" fill="{COL[s]}" rx="2"/>')
            if x2 - x1 > 62:
                o.append(f'<text class="on" x="{x1 + 6:.1f}" y="{y + 19}">{bn(v)}</text>')
            x0 += v
        o.append(f'<text class="lv halo" x="{X(c["gross"]) + 5:.1f}" y="{y + 19}">{bn(c["gross"])} parts</text>')
        y2 = y + 34
        items = [("Costs outside the segments", c["corp"], "var(--d1)"), ("Yen gap", c["yen"], "var(--d1)"),
                 ("Debt less cash", m.DEBT - m.CASH, "var(--d2)"), ("Outside owners", c["nci"], "var(--d2)")]
        right = c["gross"]
        for lab, v, col in items:
            x2, x1 = X(right), X(right - v)
            tip = f'<b>{lab}, {c["name"].lower()} case</b><br>Taken off: {mm(v)}'
            o.append(f'<rect data-tip="{esc(tip)}" x="{x1:.1f}" y="{y2}" width="{max(x2 - x1 - 2, 1):.1f}" height="16" fill="{col}" rx="2"/>')
            right -= v
        tip = f'<b>Sum for the shares, {c["name"].lower()} case</b><br>{mm(c["eq"])}, against market value of {mm(m.MKT)}'
        o.append(f'<circle data-tip="{esc(tip)}" cx="{X(c["eq"]):.1f}" cy="{y2 + 8}" r="6" fill="var(--ink)" stroke="var(--surface)" stroke-width="2"/>')
        o.append(f'<text class="lv halo" x="{X(c["eq"]) - 11:.1f}" y="{y2 + 13}" text-anchor="end">{bn(c["eq"])} for the shares</text>')
    for v, lab, anc, dx in ((m.MKT, f"Market value {bn(m.MKT)}", "end", -4), (m.EV, f"Enterprise value {bn(m.EV)}", "start", 4)):
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top - 22}" y2="{H - 26}" stroke="var(--ink)" stroke-width="2"{" stroke-dasharray=\'5 4\'" if v == m.EV else ""}/>')
        o.append(f'<text class="lv" x="{X(v) + dx:.1f}" y="{top - 28}" text-anchor="{anc}">{lab}</text>')
    o.append("</svg>")
    return "".join(o)


# ---------- each part's range
def ranges():
    rows = [(m.NAME[s], [c["parts"][s] for c in cases], COL[s]) for s in m.SEGS]
    rows += [("Costs outside the segments", [-c["corp"] for c in cases], "var(--d1)"),
             ("Yen gap", [-c["yen"] for c in cases], "var(--d1)"),
             ("Debt less cash", [-(m.DEBT - m.CASH)] * 3, "var(--d2)"),
             ("Outside owners", [-c["nci"] for c in cases], "var(--d2)")]
    W, L, R, top, rh = 1040, 250, 860, 8, 30
    H = top + rh * len(rows) + 30
    X = lambda v: L + (v + 20000) / 100000 * (R - L)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Each part as a range from low to high with a tick at the middle. The numbers are in the table below.">']
    for v in range(-20000, 80001, 20000):
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top}" y2="{H - 26}" stroke="{"var(--axis)" if v == 0 else "var(--grid)"}"/>')
        o.append(f'<text class="ax" x="{X(v):.1f}" y="{H - 8}" text-anchor="middle">{"−" if v < 0 else ""}${abs(v) // 1000}B</text>')
    for i, (lab, vals, col) in enumerate(rows):
        y = top + i * rh
        lo, hi = min(vals), max(vals)
        o.append(f'<text x="0" y="{y + 19}">{lab}</text>')
        tip = f'<b>{lab}</b><br>Low {mm(vals[0])}, middle {mm(vals[1])}, high {mm(vals[2])}'
        o.append(f'<rect x="{min(X(lo), X(hi) - 4):.1f}" y="{y + 7}" width="{max(X(hi) - X(lo), 4):.1f}" height="16" rx="4" fill="{col}" data-tip="{esc(tip)}"/>')
        o.append(f'<rect x="{X(vals[1]) - 1.5:.1f}" y="{y + 3}" width="3" height="24" fill="var(--ink)" pointer-events="none"/>')
        txt = bn(vals[0]) if lo == hi else f"{bn(lo)} to {bn(hi)}"
        o.append(f'<text class="lv" x="{R + 12}" y="{y + 19}">{txt}</text>')
    o.append("</svg>")
    return "".join(o)


# ---------- profit panels
def panel(title, series, note=""):
    W, H, L, R, T, B = 340, 200, 42, 330, 12, 24
    xs = m.YEARS + [2026]
    X = lambda yr: L + (yr - 2016) / 10 * (R - L)
    lo, hi = -400, 1800
    Y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    o = [f'<svg class="mini" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}: segment net income by year. The numbers are in the table below.">']
    for v in (0, 600, 1200, 1800):
        o.append(f'<line x1="{L}" x2="{R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{"var(--axis)" if v == 0 else "var(--grid)"}"/>')
        o.append(f'<text class="ax" x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{f"${v / 1000:.1f}B" if v else "$0"}</text>')
    for yr, lab, anc in ((2016, "’16", "middle"), (2021, "’21", "middle"), (2024, "’24", "middle"), (2026, "12m", "end")):
        o.append(f'<text class="ax" x="{X(yr):.1f}" y="{H - 6}" text-anchor="{anc}">{lab}</text>')
    for pts, col, dash, name in series:
        run = []
        for yr, v in pts:
            run.append(f"{X(yr):.1f},{Y(v):.1f}")
        o.append(f'<polyline points="{" ".join(run)}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"{" stroke-dasharray=\'3 5\'" if dash else ""}/>')
        for yr, v in pts:
            lab = "12 months to Sept. 2026" if yr == 2026 else f"FY{yr}"
            tip = f"<b>{name}</b><br>{lab}: {mm(v)}"
            o.append(f'<circle cx="{X(yr):.1f}" cy="{Y(v):.1f}" r="{2.2 if dash else 3}" fill="{col}"/>')
            o.append(f'<circle data-tip="{esc(tip)}" cx="{X(yr):.1f}" cy="{Y(v):.1f}" r="10" fill="transparent"/>')
        if not dash:
            yr, v = pts[-1]
            o.append(f'<text class="lv halo" x="{X(yr):.1f}" y="{Y(v) + (18 if v < 0 else -8):.1f}" text-anchor="end">{mm(v)}</text>')
    o.append("</svg>")
    return f'<div class="pn"><div class="pt">{title}</div>{"".join(o)}<div class="pnote">{note}</div></div>'


def pts(vals, last=None):
    out = [(y, v) for y, v in zip(m.YEARS, vals) if v is not None]
    if last is not None:
        out.append((2026, last))
    return out


glass = [a_ + b_ for a_, b_ in zip(m.HIST["Display"], m.HIST["Specialty"])]
new_solar25 = sum(m.QNI["Solar"][:4])
new_life25 = sum(m.QNI["Life"][:4])
panels = "".join([
    panel("Optical Communications", [(pts(m.HIST["Optical"], d["ni"]["Optical"]), COL["Optical"], False, "Optical")], "Same segment throughout, as restated in the latest 10-K for each year."),
    panel("Glass Innovations", [(pts(glass, d["ni"]["Glass"]), COL["Glass"], False, "Display + Specialty, now Glass")], "Display plus Specialty Materials (calc.), which is what Glass Innovations combines."),
    panel("Automotive", [(pts(m.HIST["EnvAuto"][:7]), COL["Auto"], True, "Environmental Technologies"),
                         (pts([None] * 7 + m.HIST["EnvAuto"][7:], d["ni"]["Auto"]), COL["Auto"], False, "Automotive")], "Dotted: Environmental Technologies, to 2022. Solid: Automotive, which adds car glass."),
    panel("Solar", [(pts(m.HIST["Hemlock"]), COL["Solar"], True, "Hemlock and Emerging Growth"),
                    ([(2025, new_solar25), (2026, d["ni"]["Solar"])], COL["Solar"], False, "Solar")], "Dotted: Hemlock and Emerging Growth, consolidated from Sept. 2020. Solid: Solar, available from 2025."),
    panel("Life Sciences and Emerging Growth", [(pts(m.HIST["OldLife"]), COL["Life"], True, "Life Sciences, old segment"),
                                                ([(2025, new_life25), (2026, d["ni"]["Life"])], COL["Life"], False, "Life Sciences and Emerging Growth")], "Dotted: the old Life Sciences segment. Solid: the new group, available from 2025."),
])


# ---------- multiples strip
def strip(rows, maxv, ticks, unit_lab, ref=None):
    W, L, R, rh, top = 1040, 170, 1020, 58, 26
    H = top + rh * len(rows) + 28
    X = lambda v: L + min(v, maxv) / maxv * (R - L)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Rival multiples as dots, with the range used as a band. The numbers are in the table below.">']
    for t in ticks:
        o.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{top - 4}" y2="{H - 26}" stroke="var(--grid)"/>')
        o.append(f'<text class="ax" x="{X(t):.1f}" y="{H - 8}" text-anchor="middle">{t}x</text>')
    if ref:
        v, lab = ref
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top - 8}" y2="{H - 26}" stroke="var(--ink)" stroke-dasharray="5 4" stroke-width="2"/>')
        o.append(f'<text class="lv" x="{X(v) + 6:.1f}" y="{top - 10}">{lab}</text>')
    for i, (lab, col, band, used, out) in enumerate(rows):
        y = top + i * rh + 24
        o.append(f'<text x="0" y="{y + 4}">{lab}</text>')
        if band:
            o.append(f'<rect x="{X(band[0]):.1f}" y="{y - 11}" width="{X(band[2]) - X(band[0]):.1f}" height="22" rx="4" fill="{col}" opacity=".22"/>')
            o.append(f'<rect x="{X(band[1]) - 1.5:.1f}" y="{y - 15}" width="3" height="30" fill="var(--ink)"/>')
            o.append(f'<text class="lv halo" x="{X(band[2]) + 12:.1f}" y="{y + 4}">{xx(band[0])} / {xx(band[1])} / {xx(band[2])}</text>')
        for name, v in used:
            tip = f"<b>{name}</b><br>{xx(v)}, used"
            o.append(f'<circle data-tip="{esc(tip)}" cx="{X(v):.1f}" cy="{y}" r="6" fill="{col}" stroke="var(--surface)" stroke-width="2"/>')
        for name, v in out:
            tip = f"<b>{name}</b><br>{xx(v)}, shown but not used"
            o.append(f'<circle data-tip="{esc(tip)}" cx="{X(v):.1f}" cy="{y}" r="5" fill="var(--surface)" stroke="{col}" stroke-width="2"/>')
    o.append("</svg>")
    return "".join(o)


def e(n):
    return (n, P[n]["ev_ebit"])


def s(n):
    return (n, P[n]["ev_sales"])


strip_ebit = strip([
    ("Optical", COL["Optical"], d["mult"]["Optical"], [e(n) for n in m.OPTICAL_SET], [e(n) for n in m.OPTICAL_OUT]),
    ("Glass", COL["Glass"], d["mult"]["Glass"], [e(n) for n in m.GLASS_SET], []),
    ("Automotive", COL["Auto"], d["mult"]["Auto"], [e(n) for n in m.AUTO_SET], [e(n) for n in m.AUTO_OUT]),
], 55, range(0, 56, 10), "EV/EBIT", (38.5, "Corning whole, 38.5x"))
strip_sales = strip([
    ("Solar", COL["Solar"], d["mult"]["Solar"], [s(n) for n in m.SOLAR_SET], []),
    ("Life Sciences + Emerging", COL["Life"], None, [s(n) for n in m.LIFE_SET], []),
], 8, range(0, 9, 2), "EV/sales")


# ---------- tables
rows_parts = []
for sg in m.SEGS:
    margin = d["pre"][sg] / d["sales"][sg]
    if sg == "Life":
        ml = "Mixed, see below"
    else:
        lo, md, hi = d["mult"][sg]
        ml = f"{xx(lo)} / {xx(md)} / {xx(hi)}"
    base = " on sales" if sg == "Solar" else ""
    rows_parts.append(
        f'<tr><th><span class="key" style="background:{COL[sg]}"></span>{m.NAME[sg]}</th><td class="num">{mm(d["sales"][sg])}</td><td class="num">{mm(d["ni"][sg])}</td>'
        f'<td class="num">{mm(d["pre"][sg])}</td><td class="num">{pct(margin)}</td><td class="num">{ml}{base}</td>'
        f'<td class="num">{mm(low["parts"][sg])}</td><td class="num">{mm(mid["parts"][sg])}</td><td class="num">{mm(high["parts"][sg])}</td></tr>')
tot_s, tot_n, tot_p = sum(d["sales"].values()), sum(d["ni"].values()), sum(d["pre"].values())
rows_parts.append(f'<tr class="hl"><th>All parts</th><td class="num">{mm(tot_s)}</td><td class="num">{mm(tot_n)}</td><td class="num">{mm(tot_p)}</td><td class="num">{pct(tot_p / tot_s)}</td><td></td>'
                  f'<td class="num">{mm(low["gross"])}</td><td class="num">{mm(mid["gross"])}</td><td class="num">{mm(high["gross"])}</td></tr>')


def brow(label, f, cls="", note=""):
    return (f'<tr class="{cls}"><th>{label}</th><td class="num">{mm(f(low))}</td><td class="num">{mm(f(mid))}</td><td class="num">{mm(f(high))}</td><td>{note}</td></tr>')


bridge = "".join([
    brow("All parts", lambda c: c["gross"]),
    brow("− Costs outside the segments", lambda c: -c["corp"], note=f"Low: {mm(d['corp_all'])} a year. Middle and high: {mm(d['corp_rec'])}, leaving out charges and legal costs, as if they were one-offs. Each at the blended multiple: {xx(low['blended'])}, {xx(mid['blended'])}, {xx(high['blended'])} (calc.)."),
    brow("− Yen gap", lambda c: -c["yen"], note=f"{mm(d['yen'])} a year, at Glass's multiple. It is mostly yen in Glass (" + q10() + ")."),
    brow("= Sum for the business", lambda c: c["biz"], "hl", f"Compare with enterprise value, {mm(m.EV)}."),
    brow("− Debt", lambda c: -m.DEBT, note="Book value, Sept. 30, 2026 (" + q10() + ")."),
    brow("+ Cash", lambda c: m.CASH, note="You did not list this, but enterprise value takes it off, so the sum must add it. About 66% is outside the US (" + q10() + ")."),
    brow("− Outside owners", lambda c: -c["nci"], note=f"Their {mm(m.GAAP['nci'])} of twelve-month profit, at the blended multiple. Book value is {mm(m.NCI_BOOK)}."),
    brow("= Sum for the shares", lambda c: c["eq"], "hl", f"Compare with market value, {mm(m.MKT)}."),
])

tie = [("Parts, profit before tax", tot_p), ("Currency adjustments in the segment figures", m.L["fx"]), ("Translated earnings contract gains", m.L["tec"]),
       ("Corporate research", m.L["rd"]), ("Amortization of purchased intangibles", m.L["amort"]), ("Other corporate items", m.L["other"]),
       ("Restructuring, pension mark-to-market and similar charges", m.L["charges"]), ("Litigation and regulatory", m.L["legal"]),
       ("Currency on foreign debt", m.L["debt_fx"]), ("Interest, net", m.L["interest"])]
tie_rows = "".join(f'<tr><th>{k}</th><td class="num">{mm(v)}</td></tr>' for k, v in tie)
tie_rows += f'<tr class="hl"><th>= Income before tax, as filed</th><td class="num">{mm(m.GAAP["pretax"])}</td></tr>'

sens_rows = "".join(f'<tr><th>{k}</th><td class="num">{mm(v)}</td><td class="num">{v / m.MKT * 100:.0f}%</td></tr>' for k, v in d["sens"])

q_rows = ""
for sg in m.SEGS:
    q_rows += f"<tr><th>{m.NAME[sg]}</th>" + "".join(f'<td class="num">{num(v)}</td>' for v in m.QNI[sg]) + "</tr>"
y_rows = ""
for lab, key in (("Optical", "Optical"), ("Display", "Display"), ("Specialty Materials", "Specialty"), ("Environmental, then Automotive", "EnvAuto"), ("Life Sciences, old", "OldLife"), ("Hemlock and Emerging Growth", "Hemlock")):
    y_rows += f"<tr><th>{lab}</th>" + "".join(f'<td class="num">{"n/a" if v is None else num(v)}</td>' for v in m.HIST[key]) + "</tr>"

opt_avg = sum(m.HIST["Optical"]) / 10
SA = "https://stockanalysis.com/"


def prow(part, name, kind, why, used):
    p = P[name]
    v = p["ev_ebit"] if kind == "EV/EBIT" else p["ev_sales"]
    src = a(p["url"], f"StockAnalysis, read Nov. 3, 2026")
    return f"<tr><td>{part}</td><th>{name}</th><td class=\"num\">{xx(v)} {kind}</td><td>{used}</td><td>{why}</td><td>{src}</td></tr>"


named_opt = "Named by Corning as a principal Optical rival (" + k25() + ")."
note_opt = "In our notes, not named in Corning's list."
mt_rows = "".join([
    prow("Optical", "YOFC (Hong Kong shares)", "EV/EBIT", note_opt + " Fiber maker. Low end.", "Used"),
    prow("Optical", "Amphenol", "EV/EBIT", named_opt + " On our own rules it is 23.6x (<code>multiples.html</code>).", "Used"),
    prow("Optical", "Furukawa Electric", "EV/EBIT", note_opt + " The page's own EV ÷ EBIT is 27.8x (calc.).", "Used"),
    prow("Optical", "Prysmian", "EV/EBIT", named_opt + " Mostly not optical: see above.", "Used"),
    prow("Optical", "Fujikura", "EV/EBIT", named_opt, "Used"),
    prow("Optical", "STL", "EV/EBIT", note_opt + " High end.", "Used"),
    prow("Optical", "Sumitomo Electric", "EV/EBIT", named_opt + " Left out: see above.", "Not used"),
    prow("Optical", "Hengtong", "EV/EBIT", note_opt + " Left out: see above.", "Not used"),
    prow("Glass", "AGC", "EV/EBIT", "Named for Display and Specialty Materials (" + k25() + "). No note here.", "Used"),
    prow("Glass", "Nippon Electric Glass", "EV/EBIT", "Named for Display and Specialty Materials (" + k25() + "). No note here.", "Used"),
    prow("Glass", "Jenoptik", "EV/EBIT", "Named for Specialty Materials (" + k25() + "). No note here.", "Used"),
    prow("Automotive", "NGK", "EV/EBIT", "Named for Automotive (" + k25() + "). No note here. Its price rose 10.95% on the day read.", "Used"),
    prow("Automotive", "AGC", "EV/EBIT", "Named for Automotive (" + k25() + ").", "Used"),
    prow("Automotive", "Fuyao Glass", "EV/EBIT", "Not named by Corning. Claude's pick, for the car glass side.", "Used"),
    prow("Automotive", "Ibiden", "EV/EBIT", "Named for Automotive (" + k25() + "), but about four times the others. Why was not read, so it is left out and tested above.", "Not used"),
    prow("Solar", "Wacker Chemie", "EV/sales", "Polysilicon oligopoly (" + a("https://faxiangongchang.com/en/reports/china-polysilicon-2026", "Tianxia Gongchang Research, June 24, 2026") + ").", "Used"),
    prow("Solar", "Tokuyama", "EV/sales", "Same source.", "Used"),
    prow("Solar", "T1 Energy", "EV/sales", "In our notes, tied to Corning's solar supply.", "Used"),
    prow("Solar", "OCI Holdings", "EV/sales", "Same source as Wacker.", "Used"),
    prow("Solar", "First Solar", "EV/sales", "Solar technology company (" + a(SA + "stocks/fslr/company/", "StockAnalysis profile, updated Oct. 30, 2026") + "). Claude's pick. High end.", "Used"),
    prow("Life", "Avantor", "EV/EBIT", "Named for Life Sciences (" + k25() + "). Low: this × the old segment's $77M.", "Used"),
    prow("Life", "Avantor", "EV/sales", "Middle: this × sales.", "Used"),
    prow("Life", "Thermo Fisher", "EV/sales", "Named for Life Sciences. High: this × sales, a generous top.", "Used"),
    prow("Life", "Danaher", "EV/sales", "Named for Life Sciences. Above Thermo Fisher, on a part that loses money, so not used.", "Not used"),
])

pct_mid = mid["eq"] / m.MKT
legend = "".join(f'<li><span class="key" style="background:{COL[sg]}"></span>{SHORT[sg]}</li>' for sg in m.SEGS)

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corning Parts</title>
<style>{CSS}</style></head><body><main>
<h1>Corning, valued as the sum of its parts</h1>
<p class="lede"><b>At rival multiples on trailing profit, the parts sum to {bn(low["eq"])} to {bn(high["eq"])} for the shares, with {bn(mid["eq"])} in the middle. Market value is {bn(m.MKT)} at the $123.20 close of Nov. 2, 2026, the latest saved. So the whole range sits below it.</b> All calc. The reason is simple: the market pays 38.5x operating income for Corning (<code>multiples.html</code>), and the rivals used give a blended {xx(mid["blended"])} in the middle, before the costs outside the segments.</p>
<p class="lede">The sum leans on one number. Optical is {pct(mid["parts"]["Optical"] / mid["gross"])} of the parts in the middle case, and its profit rose 80% in a year (<a href="{Q3R}">Q3 release, Oct. 27, 2026</a>). On Q3 × 4 and the highest rival multiple, the high case reaches {bn(d["sens"][3][1])}, above market value. That is arithmetic and not a forecast.</p>
<div class="callout"><b>No buy or sell view.</b> This is a picture I asked for, not our valuation method. None of these figures is base value or strategic value. Base value is not defined yet, so <code>when-to-buy</code> still bars a buy recommendation and <code>when-to-trim</code> a trim based on value. Multiples are normally off under override 5 in <code>skill-overrides</code>, and Claude chose the sets and ranges here. I confirmed them on Nov. 3, 2026. Trailing rival prices do not say what a business is worth. They say what the market pays today for other, mixed businesses.</div>
<div class="tiles">
<div class="tile"><div class="tk">Market value</div><div class="tv">{bn(m.MKT)}</div><div class="tk">861.4M shares × $123.20</div></div>
<div class="tile"><div class="tk">Sum for the shares</div><div class="tv">{bn(mid["eq"])}</div><div class="tk">{bn(low["eq"])} to {bn(high["eq"])}. Middle is {pct(pct_mid)} of market value</div></div>
<div class="tile"><div class="tk">Enterprise value</div><div class="tv">{bn(m.EV)}</div><div class="tk">Outside owners at book</div></div>
<div class="tile"><div class="tk">Sum for the business</div><div class="tv">{bn(mid["biz"])}</div><div class="tk">{bn(low["biz"])} to {bn(high["biz"])}</div></div>
</div>

<h2>The parts stacked, against the market</h2>
<div class="card"><ul class="legend">{legend}<li><span class="key" style="background:var(--d1)"></span>Costs outside segments, yen gap</li><li><span class="key" style="background:var(--d2)"></span>Debt less cash, outside owners</li></ul>
<figure><div class="scroll">{stack()}</div><figcaption>Each case: the parts add to the right, then what comes off runs back to the left and ends at the dot. Compare the dot with market value. Hover for each piece. The low, middle and high cases use the lowest, the median and the highest rival multiple in each set, all at once, which no real day would do.</figcaption></figure></div>

<h2>Each part's range</h2>
<div class="card"><figure><div class="scroll">{ranges()}</div><figcaption>The band runs from lowest to highest. The tick is the middle case. Optical's width alone, {bn(high["parts"]["Optical"] - low["parts"]["Optical"])}, is about the same as all the other parts put together in the middle case ({bn(mid["gross"] - mid["parts"]["Optical"])}).</figcaption></figure></div>
<div class="wrap"><table class="tight"><thead><tr><th>Twelve months to Sept. 30, 2026</th><th class="num">Sales</th><th class="num">Net income</th><th class="num">Before tax</th><th class="num">Margin</th><th class="num">Multiple: low / middle / high</th><th class="num">Low</th><th class="num">Middle</th><th class="num">High</th></tr></thead><tbody>{"".join(rows_parts)}</tbody></table></div>
<p class="foot">All calc. Twelve months = nine months of 2026 (<a href="{Q10}">10-Q, filed Oct. 29, 2026</a>) plus Q4 2025 on the new segments (<a href="{Q1R}">Q1 release, Apr. 28, 2026</a>). Profit before tax is segment net income plus the segment tax line, since rival EV/EBIT multiples are before tax. Q4 2025 tax is FY2025 (<a href="{K25}">10-K, filed Feb. 12, 2026</a>) less nine months of 2025 (10-Q). The filings give Solar and Life Sciences together for that quarter, $8M, so Claude put $8M on Solar, at the stated 21%, and none on Life Sciences. Segment assets at Sept. 30, 2026: Optical $5,039M, Glass $9,865M, Automotive $2,384M, Solar $3,166M, Life Sciences and Emerging Growth $1,408M (10-Q).</p>

<h2>From the parts to the shares</h2>
<div class="wrap"><table><thead><tr><th></th><th class="num">Low</th><th class="num">Middle</th><th class="num">High</th><th>How</th></tr></thead><tbody>{bridge}</tbody></table></div>
<ul class="notes">
<li><b>Costs outside the segments</b> are Corning's unallocated lines over twelve months (calc.): corporate research {mm(-m.L["rd"])}, amortization {mm(-m.L["amort"])}, other corporate items {mm(-m.L["other"])}, charges {mm(-m.L["charges"])} and legal {mm(-m.L["legal"])}. The 10-K and 10-Q group the charges differently, so that split of the {mm(-m.L["other"] - m.L["charges"])} is Claude's reading. Corning says shared costs are allocated differently than they would be for stand-alone reporting (<a href="{Q10}">10-Q, filed Oct. 29, 2026</a>). So stand-alone parts could cost more.</li>
<li><b>The yen gap is the item most easily missed.</b> Segment sales and profit use hedge rates, and before Apr. 1, 2026 used management's long-term rates, not the rates in the filed accounts. Over twelve months that took {mm(-m.L["fx"])} off profit on the way to the filed figures, and {mm(-m.FX_SALES)} off sales. Translated earnings contracts gave back {mm(m.L["tec"])}, below operating income. The net {mm(d["yen"])} is {pct(d["yen"] / d["pre"]["Glass"])} of Glass's profit (all calc.). The method changed on Apr. 1, 2026, so these twelve months mix two ways of measuring (10-Q). How long the gap lasts depends on the yen and on hedges, and this page does not forecast either.</li>
<li><b>Outside owners.</b> They took {mm(m.GAAP["nci"])} of net income over twelve months (calc., <a href="{K25}">10-K, filed Feb. 12, 2026</a>; 10-Q), against {mm(m.NCI_BOOK)} at book. The units with outside owners include Hemlock Semiconductor Operations, in Solar, and US Conec, in Optical (10-Q). Corning held 80.5% of the first at Sept. 2020 (<a href="{K20}">10-K, filed Feb. 12, 2021</a>). The filings do not split the {mm(m.GAAP["nci"])}. It is well above Solar's whole {mm(d["ni"]["Solar"])}, so some likely sits in units that the Solar total nets against wafer and module losses, but that is Claude's reading.</li>
<li><b>The two comparisons differ slightly.</b> Enterprise value, as on <code>multiples.html</code>, holds outside owners at book. So the share comparison is the cleaner of the two.</li>
</ul>

<h2>What would close the gap</h2>
<div class="wrap"><table><thead><tr><th>Test, one change at a time</th><th class="num">Sum for the shares</th><th class="num">Share of market value</th></tr></thead><tbody>{sens_rows}</tbody></table></div>
<ul class="notes">
<li>With everything else at the middle, Optical would need <b>{xx(d["need_ev"])}</b> of its twelve-month profit for the sum for the business to reach enterprise value (calc.). The highest rival used is {xx(d["mult"]["Optical"][2])}.</li>
<li>Q3 2026 × 4 for Optical is {mm(d["q3x4"])} of profit before tax, against {mm(d["pre"]["Optical"])} over twelve months (calc., <a href="{Q10}">10-Q</a>). It is arithmetic and not a forecast, and the rival multiples stay trailing, which flatters it. Some rivals' profit is moving fast too, such as Fujikura's and YOFC's (<code>multiples.html</code>).</li>
<li>Blended multiples are held still in these tests, so outside owners and corporate costs do not move.</li>
</ul>

<h2>Each segment's profit over the years</h2>
<p>Optical is the only line well above its past. Its twelve months of {mm(d["ni"]["Optical"])} are {d["ni"]["Optical"] / opt_avg:.1f} times its FY2016 to FY2025 average of {mm(opt_avg)} (calc.). Glass, as Display plus Specialty, is at its high of the period, only just above FY2025 (calc.). A trailing multiple treats a peak and an ordinary year alike.</p>
<div class="grid3">{panels}</div>
<p class="foot">Segment net income, as filed: after a stated 21% tax and before unallocated items. Not on the same basis across all years. Same scale in every panel. "12m" is the twelve months to Sept. 30, 2026 (calc.). Solid lines are today's segments.</p>
<h3>Today's segments by quarter, net income, $M</h3>
<div class="wrap"><table><thead><tr><th></th>{"".join(f'<th class="num">{q}</th>' for q in m.QUARTERS)}</tr></thead><tbody>{q_rows}</tbody></table></div>
<p class="foot">{a(Q1R, "Q1 release, Apr. 28, 2026")}; {a(Q2R, "Q2 release, July 28, 2026")}; {a(Q3R, "Q3 release, Oct. 27, 2026")}. The 2025 quarters come from the comparison columns. Periods before Apr. 1, 2026 were not recast for the new currency measure, and Corning says Glass's growth would have been higher if they were (<a href="{Q10}">10-Q, filed Oct. 29, 2026</a>).</p>
<h3>Older segments by year, net income, $M</h3>
<div class="wrap"><table><thead><tr><th></th>{"".join(f'<th class="num">{y}</th>' for y in m.YEARS)}</tr></thead><tbody>{y_rows}</tbody></table></div>
<p class="foot">Each year comes from the latest 10-K read that reports it: 2023 to 2025, {a(K25, "filed Feb. 12, 2026")}; 2022, {a(K24, "filed Feb. 13, 2025")}; 2021, {a(K23, "filed Feb. 12, 2024")}; 2020, {a(K22, "filed Feb. 13, 2023")}; 2019, {a(K21, "filed Feb. 14, 2022")}; 2017 and 2018, {a(K19, "filed Feb. 18, 2020")}; 2016, {a(K18, "filed Feb. 12, 2019")}. Automotive replaces Environmental Technologies from 2023, the first year the 10-K shows it: for 2023 the two are $290M and $386M ({a(K24, "10-K, filed Feb. 13, 2025")}). The same recast moved Hemlock and Emerging Growth's 2023 from $15M to $111M, so that row breaks there too. Hemlock was an equity affiliate until Sept. 2020, so its row starts in 2020.</p>

<h2>The multiples used</h2>
<div class="card"><figure><div class="scroll">{strip_ebit}</div><figcaption>EV/EBIT. Filled dots are used. Hollow dots are shown but left out. The band runs from lowest to highest used, and the tick is the median. Figures at the right are low / middle / high. Hover for names.</figcaption></figure></div>
<div class="card"><figure><div class="scroll">{strip_sales}</div><figcaption>EV/sales, for the two parts with too little profit to price. Life Sciences and Emerging Growth uses its own mix: see below.</figcaption></figure></div>
<ul class="notes">
<li><b>Only Optical comes from our notes.</b> Our notes hold no rivals for the other lines, so Claude read 14 more outside pages, and these rivals have no company note yet.</li>
<li><b>Optical: lowest, median and highest of six.</b> Sumitomo is left out because its Info-Communications profit, ¥77.4B in FY2025 (<a href="https://sumitomoelectric.com/jp/sites/japan/files/2026-05/download_documents/20260522ceo.pdf">Sumitomo slides, May 22, 2026</a>), is about 16% of the group EBIT of ¥484.72B on the outside page (calc., periods differ). Hengtong's optical business was 8.30% of 2025 revenue (<a href="https://eu.36kr.com/en/p/3896566703343238">36Kr, July 15, 2026</a>). The rest are mixed too: Prysmian's optical part is about a third of its Digital Solutions segment (<a href="https://stockanalysis.com/quote/bit/PRY/transcripts/659713-q3-2026/">Q3 call, Oct. 29, 2026, third-party transcript</a>). Adding the two back moves the median to {xx(d["alt_med"])}.</li>
<li><b>Glass: lowest, median and highest of three.</b> The rivals earn much less on sales: AGC 7.1%, Nippon Electric Glass 8.1%, Jenoptik 13.1% (calc., EBIT ÷ revenue from the same pages), against {d["pre"]["Glass"] / d["sales"]["Glass"] * 100:.1f}% for Glass before the yen gap. So the market might pay more for Corning's, or those margins might have further to fall. This page cannot say. Schott and Heraeus were not read.</li>
<li><b>Automotive: lowest, median and highest of three.</b> LENS was not read.</li>
<li><b>Solar uses sales, not profit.</b> Its {mm(d["pre"]["Solar"])} of twelve-month profit is too thin for a profit multiple to mean much, and the rivals' EV/EBIT runs from 9.67x to 81.4x. The 10-K names no Solar rival. The middle, {mm(mid["parts"]["Solar"])}, is below the segment's assets of $3,166M.</li>
<li><b>Life Sciences and Emerging Growth loses money, so no profit multiple fits the whole.</b> Low treats the old Life Sciences profit of $77M as all it has, at Avantor's EV/EBIT, with Emerging Growth at nothing. Middle is Avantor's EV/sales. High is Thermo Fisher's. All three rest on Claude's choices, and the part is small either way.</li>
</ul>
<div class="wrap"><table><thead><tr><th>Part</th><th>Rival</th><th class="num">Multiple</th><th></th><th>Why</th><th>Source</th></tr></thead><tbody>{mt_rows}</tbody></table></div>
<p class="foot">Printed ratios from one free outside page, as on <code>multiples.html</code>. Terms: {a(SA + "terms-of-use/", "updated Oct. 29, 2026")}. Rival prices run from the Oct. 30 close to Nov. 3 quotes, and Corning's is the Nov. 2 close. Corning's own 38.5x is from <code>multiples.html</code>.</p>

<h2>What the sum leaves out</h2>
<ul class="notes">
<li><b>Growth and targets.</b> Trailing profit prices none of the plan: a $40 billion run rate by end of 2030 is a target, not a result (<a href="{Q2R}">Q2 release, July 28, 2026</a>), and so is Solar's "more than $3 billion" (<a href="{Q3R}">Q3 release, Oct. 27, 2026</a>). Deals such as Meta's, worth up to $6 billion, a ceiling (<a href="{META}">Meta post, Jan. 27, 2026</a>), show up only as they ship. <code>priced-in.html</code> covers what the price assumes about all of this.</li>
<li><b>The cycle, the other way.</b> Optical's profit is {d["ni"]["Optical"] / opt_avg:.1f} times its ten-year average, so a trailing multiple can also overstate it. Rival fiber capacity is dated from 2028 in <code>rivals.html</code>.</li>
<li><b>Claims not taken off:</b> contract liabilities $2,701M, operating leases $971M, pensions $625M, receivables sold $442M (<a href="{Q10}">10-Q, filed Oct. 29, 2026</a>). Contract liabilities are generally settled by delivering product.</li>
<li><b>Assets not added:</b> investments of $470M at book (10-Q). Precious metals in plant, $2.8 billion at carrying value at Dec. 31, 2025 and "significantly lower than the fair market value" (<a href="{K25}">10-K, filed Feb. 12, 2026</a>). They are needed to run the plants, and the gap is not given.</li>
<li><b>More shares.</b> On 871M diluted shares, market value is $107,307M (calc., 10-Q). NVIDIA holds 3M pre-funded warrants and 15M at $180 (<a href="{NV8K}">8-K, May 6, 2026</a>).</li>
<li><b>Tax credits.</b> $172M of 45X credits cut cost of sales and $87M of 48D credits cut operating expenses in FY2025 (<a href="{K25}">10-K, filed Feb. 12, 2026</a>). Which parts hold them, and how long they last, is not priced here.</li>
<li><b>A real break-up.</b> Tax on a sale, separation costs and lost shared plants and research have no figure here. The sum shows no such cost, and no premium for control. It is not a claim that Corning could be sold for these numbers.</li>
<li><b>What's inside the parts.</b> Hemlock's chip and solar sides, pharma glass and emerging bets are not valued one by one, because the filings give no profit for them. Equity affiliates, $284M at book, count only through segment profit (10-Q).</li>
<li><b>Rival quality.</b> One free site, read through a fetch tool and checked against no filing. Accounting rules differ, EBIT definitions differ, and some page ratios do not tie. See "What could not be compared fairly" on <code>multiples.html</code>. Segment profit is Corning's own measure, and rivals' EBIT is a group figure.</li>
<li><b>One day of multiples.</b> No rival history here, so no sense of whether today's rival prices are high or low.</li>
</ul>

<h2>Does it tie?</h2>
<p>The twelve-month parts tie to the filed accounts exactly, and so do sales: {mm(tot_s)} less {mm(-m.FX_SALES)} is {mm(m.GAAP["sales"])} (calc.). With the tax line added, net income ties too, at {mm(m.GAAP["ni"])}. Operating income of {mm(m.GAAP["oi"])} sits on a different path, since interest and contract gains are below it.</p>
<div class="wrap"><table style="max-width:560px"><tbody>{tie_rows}</tbody></table></div>
<p class="foot">Calc. FY2025 less nine months of 2025 plus nine months of 2026 (<a href="{K25}">10-K, filed Feb. 12, 2026</a>; <a href="{Q10}">10-Q, filed Oct. 29, 2026</a>). Market inputs: <a href="{YAHOO}">Yahoo through yfinance, fetched Nov. 2, 2026</a>; shares at Oct. 23, 2026 and the balance sheet at Sept. 30, 2026 (10-Q).</p>
<p class="foot"><b>Keep this page on this computer.</b> It uses Yahoo's price, and <code>sensors/prices/prices.py</code> says nothing built from it should be published.</p>
</main><div id="tip" hidden></div>
<script>
const tip=document.getElementById('tip');
function show(e,t){{tip.innerHTML=t;tip.hidden=false;const r=tip.getBoundingClientRect();let x=e.clientX+14,y=e.clientY+14;if(x+r.width>innerWidth-8)x=e.clientX-r.width-14;if(y+r.height>innerHeight-8)y=e.clientY-r.height-14;tip.style.left=x+'px';tip.style.top=y+'px'}}
document.querySelectorAll('[data-tip]').forEach(n=>{{n.addEventListener('mousemove',e=>show(e,n.dataset.tip));n.addEventListener('mouseleave',()=>tip.hidden=true)}});
</script></body></html>
"""
(m.ROOT / "parts.html").write_text(PAGE)
print("wrote parts.html", len(PAGE))
