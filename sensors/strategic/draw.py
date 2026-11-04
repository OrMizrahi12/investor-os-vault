"""Builds strategic.html from model.py. Takes no flags and writes when run. The method and chances were approved Nov. 3, 2026, and the method is in Rules/when-to-trim.md.

    .venv/bin/python sensors/strategic/draw.py
"""

import html
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as m  # noqa: E402

ROOT = HERE.parent.parent
SEC = "https://www.sec.gov/Archives/edgar/data/24741/"
FOOL = "https://www.fool.com/earnings/call-transcripts/"


def a(url, text):
    return f'<a href="{url}">{text}</a>'


q10 = a(SEC + "000002474126000279/glw-20260930.htm", "10-Q, filed Oct. 29, 2026")
k25 = a(SEC + "000002474126000124/glw-20251231.htm", "10-K, filed Feb. 12, 2026")
q3r = a("https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm", "Q3 release, Oct. 27, 2026")
q2r = a("https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000253/glw-20260728xex99xq22026.htm", "Q2 release, July 28, 2026")
q1r = a(SEC + "000002474126000198/glw-20260328xex991xq12026.htm", "Q1 release, Apr. 28, 2026")
q3c = a(FOOL + "2026/10/27/corning-glw-q3-2026-earnings-call-transcript/", "Q3 call, Oct. 27, 2026, third-party transcript")
q2c = a("https://www.investing.com/news/transcripts/earnings-call-transcript-corning-beats-q2-2026-estimates-but-shares-sink-93CH-4817120", "Q2 call, July 28, 2026, third-party transcript")
q1c = a(FOOL + "2026/04/28/corning-glw-q1-2026-earnings-transcript/", "Q1 call, Apr. 28, 2026, third-party transcript")
spring = a("https://www.marketscale.com/industries/business-services/corning-upgrades-and-extends-springboard-plan-outlines-new-phase-of-accelerating-growth.md", "Springboard release, May 5, 2026, MarketScale copy")
meta = a("https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/", "Meta post, Jan. 27, 2026")
vz = a("https://www.verizon.com/about/news/verizon-corning-broadband-ai-fiber-agreement", "Verizon release, Sept. 8, 2026")
att = a("https://www.prnewswire.com/news-releases/att-and-corning-team-up-to-engineer-the-connected-world-with-fiber-302892879.html", "AT&amp;T and Corning release, Sept. 29, 2026")
attc = a("https://www.earningswhispers.com/transcript/T/Q32026", "AT&amp;T Q3 call, Oct. 21, 2026, third-party transcript")
hen = a("https://finance.eastmoney.com/a/202610203900316315.html", "Eastmoney, Oct. 20, 2026")
pap = a("https://www.thepaper.cn/newsDetail_forward_34352456", "The Paper, Oct. 28, 2026")
proc = a("https://www.whitehouse.gov/presidential-actions/2026/08/adjusting-imports-of-polysilicon-and-its-derivatives-into-the-united-states/", "Proclamation, Aug. 6, 2026")
t18 = a("https://www.sec.gov/Archives/edgar/data/1992243/000121390025077036/ea0253426-8k_t1energy.htm", "T1 Energy 8-K, Aug. 15, 2025")
yh = a("https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&amp;interval=1d", "Yahoo through yfinance, fetched Nov. 2, 2026")
aaa = a("https://fred.stlouisfed.org/series/AAA", "FRED AAA, downloaded Nov. 3, 2026")


def d2(x):
    return ("−" if x < 0 else "") + f"${abs(x):,.2f}"


def sg(x):
    return ("−" if x < 0 else "+") + f"${abs(x):,.2f}"


def bn(x):
    return ("−" if x < 0 else "") + f"${abs(x):,.0f}M"


def pc(x, dp=0):
    return f"{x * 100:.{dp}f}%"


def date(iso):
    y, mo, day = iso.split("-")
    return f"{['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'][int(mo) - 1]} {int(day)}, {y}"


def esc(s):
    return html.escape(s, quote=True)


S = m.scenarios()
BY = {x["key"]: x for x in S}
C = m.compare()
b, strat, trim, price = C["base"], C["strategic"], C["trim"], C["price"]
buy = C["buy"]
alltrue = m.all_true()
stretch = m.stretch()
needed = m.multiple_needed()
mult = m.multiple()
t0, SENS = m.sensitivities()
lad = m.ladder()
closes = m.base_model.closes()
close = dict(closes)
peak = max(closes, key=lambda r: r[1])
since16 = [c for d, c in closes if d >= "2016-01-01"]
above = sum(c > trim for c in since16)
between = sum(buy <= c <= trim for c in since16)
below = sum(c < buy for c in since16)
last_at = [d for d, c in closes if c <= trim][-1]
gap_meta = close["2026-01-27"] - close["2026-01-26"]
g_rec = m.base_model.growth()["ni"]
base_cash_2030 = 1256 * (1 + g_rec) ** m.T2030
q3_ni4 = 4 * 680
cross_years = math.log(q3_ni4 / 1256) / math.log(1 + g_rec)
sum_up = sum(x["ev"] for x in S if x["key"] != "rival")
sens_vals = [v for _, v in SENS]
low_s, high_s = min(sens_vals), max(sens_vals)
glass_margin = m.Q3_NI["Glass"] / m.Q3_SALES["Glass"]
opt_run = 4 * m.Q3_SALES["Optical"]

NAMES = dict(signed="1. Signed fiber deals ship", plan="2. The rest of the high-confidence plan", scaleup="3. Optical scale-up fills the gap to $40 billion",
             solar="4. Solar reaches its goal, with profit", display="5. Display glass price rises hold", rival="Downside: rival fiber capacity cuts the margin")
SHORT = dict(signed="1. Signed deals ship", plan="2. High-confidence plan", scaleup="3. Scale-up to $40 billion", solar="4. Solar goal", display="5. Display price", rival="Rival capacity")

ROWS = {
    "signed": dict(
        what=f"Meta, two unnamed hyperscalers, Verizon, AT&amp;T and two other Q3 deals become sales by the end of 2028. Adds {bn(lad['signed'])} a year: {bn(m.DEALS_CEILING)} at their ceilings over six years, of which I treat {pc(m.NEW_SHARE)} as new.",
        why=f"<b>For:</b> both sides name Meta, Verizon and AT&amp;T ({meta}; {vz}; {att}). The CFO speaks of \"the committed volume\" ({q3c}). <b>Against:</b> Meta's figure is \"up to\", no contract is filed, and AT&amp;T plans capital spending \"roughly $1 billion lower\" a year ({attc}).",
        when="Meta's impact starts in 2027. Verizon's term starts Jan. 2027. Final read at Q4 2028 results, early 2029 (my estimate).",
        wrong=f"Optical sales times four under {bn(opt_run + lad['signed'])} at Q4 2028 (calc.). A customer cuts or reprices a deal."),
    "plan": dict(
        what=f"The core sales run rate reaches the $35 billion high-confidence plan by the end of 2030 ({spring}). Adds {bn(lad['plan'])} a year, after taking out the parts counted in rows 1, 4 and 5.",
        why=f"<b>For:</b> it is Corning's own lower plan, recent goals were met early, and core EPS was never below guidance in 19 quarters (<code>people.html</code>). <b>Against:</b> the last four-year plan was missed. Of 18 goals, 6 met and 6 missed (my count, <code>people.html</code>). No share of the plan under contract is given ({spring}). It needs four more years of data center building.",
        when="Checkpoint: the $27 billion high-confidence run rate for the end of 2028, read early 2029. Final read early 2031 (my estimates).",
        wrong="Run rate under $27 billion at Q4 2028. Hyperscalers cut capital spending and deals slip."),
    "scaleup": dict(
        what=f"Fiber replaces copper inside GPU racks and carries sales from $35 billion to the $40 billion internal plan. Adds {bn(lad['scaleup'])} a year. Capped there, because the release does not say whether the $10 billion Photonics stream sits inside the $40 billion ({spring}).",
        why=f"<b>For:</b> the CEO expects scale-up \"to begin to accelerate\" in 2028, with fibers per GPU going from about 16 to 160 ({q3c}). <b>Against:</b> \"100% of the current scale of architectures are copper\" ({q3c}), and timing is \"very difficult to predict\" ({q2c}). It also needs row 2 to hold.",
        when="First signs in 2028. Final read early 2031 (my estimates).",
        wrong="No scale-up volume shipping by the end of 2028, or copper holds through 2030."),
    "solar": dict(
        what=f"Solar reaches the \"more than $3 billion\" stream ({q3r}), earning the group's Q3 net margin of {pc(m.GROUP_MARGIN, 1)} (calc.), since the goal is profit above the corporate average ({q1c}). Adds {bn(lad['solar'])} of sales and {bn(BY['solar']['ni'])} of profit a year, from a $7M Q3 loss.",
        why=f"<b>For:</b> the tariff starts Dec. 4, 2026 ({proc}), and Q3 sales times four are 58% of the goal (calc., {q3r}). <b>Against:</b> the ramp runs \"at a slower pace than anticipated\" ({q3r}). Solar is \"below our corporate operating margin\" ({q3c}). T1's wafer agreement \"is subject to certain conditions\" ({t18}).",
        when="Solar margin in the first half of 2027. No date on the goal. End of 2029 is my estimate.",
        wrong="Solar still loses money at the end of 2027, or the tariff floors or credits are cut."),
    "display": dict(
        what=f"A 5% price rise on {bn(m.DISPLAY_FY25)} of FY2025 Display sales ({k25}) holds. The 5% is my assumption, because Corning says \"we are not disclosing the specific amount\" ({q3c}). Adds {bn(lad['display'])} before tax and {bn(BY['display']['ni'])} after, at Glass's {pc(m.GLASS_TAX)} tax rate (calc., {q10}).",
        why=f"<b>For:</b> the CFO says rises take effect in Q4 2026 and are \"really geared around 2027 and beyond\" ({q3c}). <b>Against:</b> they \"address a weaker yen environment\" ({q3c}), so they may only win back a cost. TV, notebook and phone markets are weak ({q3r}).",
        when="Glass Innovations results through 2027, read early 2028 (my estimate).",
        wrong=f"Glass net margin under Q3's {pc(glass_margin, 1)} through 2027 (calc., {q3r})."),
    "rival": dict(
        what=f"Rival plants from late 2028 pull the Optical margin on the added sales from {pc(m.OPT_MARGIN, 1)} in Q3 back to {pc(m.OPT_MARGIN_LOW, 1)}, its Q4 2025 level (calc., {q10}; {q1r}). It applies to the {bn(BY['rival']['sales'])} of sales rows 1 to 3 add on average (calc.). You did not ask for this row. I added it so the sum is not all upside.",
        why=f"<b>For:</b> Hengtong's CTO warns of a turn after 2028 ({hen}), and prices are expected to fall after 2028 ({pap}). <b>Against:</b> long deals may hold price, but their price terms are unknown.",
        when="Late 2028 and after. These are rivals' plans.",
        wrong=f"Optical net margin holds at {pc(m.OPT_MARGIN, 1)} or better through 2029."),
}


def tile(v, k):
    return f'<div class="tile"><div class="tv">{v}</div><div class="tk">{k}</div></div>'


# ---- Chart 1: the stack.
L, R, HI = 268, 986, 130


def X(v):
    return L + v / HI * (R - L)


def stack():
    rh, T = 40, 44
    rows = 1 + len(S) + 3
    H = T + rows * rh + 34
    bottom = T + rows * rh
    o = []
    for v in range(0, 131, 10):
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{T - 8}" y2="{bottom}" stroke="var(--grid)"/>')
        o.append(f'<text x="{X(v):.1f}" y="{bottom + 18}" text-anchor="middle" class="ax">${v}</text>')
    o.append(f'<line x1="{L}" x2="{R}" y1="{bottom}" y2="{bottom}" stroke="var(--axis)"/>')
    y = T

    def label(name, sub=""):
        o.append(f'<text x="{L - 12}" y="{y + 11}" text-anchor="end" class="nm">{name}</text>')
        if sub:
            o.append(f'<text x="{L - 12}" y="{y + 26}" text-anchor="end" class="ax">{sub}</text>')

    # Base.
    label("Base value, middle", "Approved method, range shown")
    tip = esc(f"<b>Base value</b><br>Low {d2(b['low'])}<br>Middle {d2(b['mid'])}<br>High {d2(b['high'])}<br>Calc., base.html")
    o.append(f'<rect x="{X(0):.1f}" y="{y}" width="{X(b["mid"]) - X(0):.1f}" height="20" rx="4" fill="var(--ink)"/>')
    o.append(f'<line x1="{X(b["low"]):.1f}" x2="{X(b["high"]):.1f}" y1="{y + 28}" y2="{y + 28}" stroke="var(--d2)" stroke-width="2"/>')
    o.append(f'<text x="{X(b["mid"]) - 8:.1f}" y="{y + 15}" text-anchor="end" class="lv" style="fill:var(--surface)">{d2(b["mid"])}</text>')
    o.append(f'<rect x="{X(0):.1f}" y="{y - 4}" width="{X(b["high"]) - X(0) + 50:.1f}" height="36" fill="transparent" data-tip="{tip}"/>')
    y += rh
    cum = b["mid"]
    for s in S:
        n = cum + s["ev"]
        neg = s["ev"] < 0
        label(SHORT[s["key"]], f"{pc(s['p'])} chance, {sg(s['full'])} if it happens")
        x0, x1 = sorted((X(cum), X(n)))
        ghost_end = cum + s["full"]
        gx0, gx1 = sorted((X(cum), X(ghost_end)))
        o.append(f'<rect x="{gx0:.1f}" y="{y + 7}" width="{gx1 - gx0:.1f}" height="6" rx="3" fill="var(--d1)"/>')
        o.append(f'<rect x="{x0:.1f}" y="{y}" width="{max(x1 - x0, 2):.1f}" height="20" rx="4" fill="{"var(--s2)" if neg else "var(--s1)"}"/>')
        o.append(f'<line x1="{X(cum):.1f}" x2="{X(cum):.1f}" y1="{y - rh + 20}" y2="{y}" stroke="var(--axis)" stroke-dasharray="2 2"/>')
        if s["key"] == "signed":  # to the right it would cross the trim-above line
            o.append(f'<text x="{min(x0, gx0) - 8:.1f}" y="{y + 15}" text-anchor="end" class="lv halo">{sg(s["ev"])}</text>')
        else:
            o.append(f'<text x="{max(x1, gx1) + 8:.1f}" y="{y + 15}" class="lv halo">{sg(s["ev"])}</text>')
        tip = esc(f"<b>{NAMES[s['key']]}</b><br>{sg(s['full'])} a share if it happens<br>× {pc(s['p'])} chance<br>= {sg(s['ev'])} in the stack<br>Running total {d2(n)}. Calc.; the chance is my judgment.")
        o.append(f'<rect x="{min(x0, gx0) - 4:.1f}" y="{y - 4}" width="{max(x1, gx1) - min(x0, gx0) + 60:.1f}" height="30" fill="transparent" data-tip="{tip}"/>')
        cum = n
        y += rh
    # Total.
    label("Base plus strategic", "The trim-above")
    o.append(f'<rect x="{X(0):.1f}" y="{y}" width="{X(trim) - X(0):.1f}" height="20" rx="4" fill="var(--s3)"/>')
    o.append(f'<text x="{X(trim) + 8:.1f}" y="{y + 15}" class="lv halo">{d2(trim)}</text>')
    tip = esc(f"<b>Base plus strategic</b><br>{d2(b['mid'])} + {d2(strat)} = {d2(trim)}<br>{pc(C['cover'])} of the price. Calc.")
    o.append(f'<rect x="{X(0):.1f}" y="{y - 4}" width="{X(trim) - X(0) + 60:.1f}" height="28" fill="transparent" data-tip="{tip}"/>')
    y += rh
    label("If all five come true", "No chance applied, no rival cut")
    o.append(f'<rect x="{X(0):.1f}" y="{y}" width="{X(alltrue) - X(0):.1f}" height="20" rx="4" fill="var(--d1)"/>')
    o.append(f'<text x="{X(alltrue) + 8:.1f}" y="{y + 15}" class="lv halo">{d2(alltrue)}</text>')
    tip = esc(f"<b>If all five come true</b><br>{d2(alltrue)}, not a forecast. Still below the price. Calc.")
    o.append(f'<rect x="{X(0):.1f}" y="{y - 4}" width="{X(alltrue) - X(0) + 60:.1f}" height="28" fill="transparent" data-tip="{tip}"/>')
    y += rh
    label("Price", "Close of Nov. 2, 2026")
    o.append(f'<rect x="{X(0):.1f}" y="{y}" width="{X(price) - X(0):.1f}" height="20" rx="4" fill="var(--s2)"/>')
    o.append(f'<text x="{X(price) - 8:.1f}" y="{y + 15}" text-anchor="end" class="on">{d2(price)}</text>')
    tip = esc(f"<b>Price</b><br>{d2(price)}, {C['times']:.1f} times base plus strategic. Calc.")
    o.append(f'<rect x="{X(0):.1f}" y="{y - 4}" width="{X(price) - X(0):.1f}" height="28" fill="transparent" data-tip="{tip}"/>')
    # Marker lines.
    o.append(f'<line x1="{X(trim):.1f}" x2="{X(trim):.1f}" y1="26" y2="{bottom}" stroke="var(--s3)" stroke-width="2"/>')
    o.append(f'<text x="{X(trim) + 6:.1f}" y="22" class="lv">Trim-above {d2(trim)}</text>')
    o.append(f'<line x1="{X(price):.1f}" x2="{X(price):.1f}" y1="26" y2="{bottom}" stroke="var(--s2)" stroke-width="2"/>')
    o.append(f'<text x="{X(price) - 6:.1f}" y="22" text-anchor="end" class="lv">Price {d2(price)}</text>')
    return f'<svg viewBox="0 0 1000 {H}" role="img" aria-label="Value stack from base value of {d2(b["mid"])} up through five scenarios and one downside to {d2(trim)}, against a price of {d2(price)}.">{"".join(o)}</svg>'


# ---- Chart 2: the price against the two lines.
def price_chart():
    pts = [(d, c) for d, c in closes if d >= "2024-01-01"]
    pts = pts[::5] + ([pts[-1]] if pts[-1] != pts[::5][-1] else [])
    if peak[0] >= "2024-01-01" and peak not in pts:
        pts = sorted(pts + [peak])
    top = math.ceil(peak[1] / 50) * 50
    W, H, l, r, t, bt = 1000, 380, 56, 830, 20, 340
    x = lambda i: l + i / (len(pts) - 1) * (r - l)
    y = lambda v: bt - v / top * (bt - t)
    o = []
    for v in range(0, top + 1, 50):
        o.append(f'<line x1="{l}" x2="{r}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--grid)"/>')
        o.append(f'<text x="{l - 8}" y="{y(v) + 4:.1f}" text-anchor="end" class="ax">${v}</text>')
    yrs = {}
    for i, (d, _) in enumerate(pts):
        yrs.setdefault(d[:4], i)
    for yr, i in yrs.items():
        o.append(f'<text x="{x(i):.1f}" y="{bt + 20}" text-anchor="middle" class="ax">{yr}</text>')
    o.append(f'<line x1="{l}" x2="{r}" y1="{bt}" y2="{bt}" stroke="var(--axis)"/>')
    for v, c, lab, dash, dy in ((buy, "var(--d2)", f"Buy-below {d2(buy)}", "4 3", 14), (trim, "var(--s3)", f"Trim-above {d2(trim)}", "", -6)):
        o.append(f'<line x1="{l}" x2="{r}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{c}" stroke-width="2" stroke-dasharray="{dash}"/>')
        o.append(f'<text x="{r + 8}" y="{y(v) + dy + 4:.1f}" class="lv">{lab}</text>')
    o.append(f'<text x="{r + 8}" y="{y(pts[-1][1]) + 4:.1f}" class="lv">Price {d2(price)}</text>')
    path = " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f} {y(c):.1f}" for i, (_, c) in enumerate(pts))
    o.append(f'<path d="{path}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>')
    o.append(f'<circle cx="{x(len(pts) - 1):.1f}" cy="{y(pts[-1][1]):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>')
    ip = [i for i, q in enumerate(pts) if q == peak][0]
    o.append(f'<circle cx="{x(ip):.1f}" cy="{y(peak[1]):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>')
    o.append(f'<text x="{x(ip) - 8:.1f}" y="{y(peak[1]) + 4:.1f}" text-anchor="end" class="lv halo">{d2(peak[1])}, June 29, 2026</text>')
    w = (r - l) / (len(pts) - 1)
    for i, (d, c) in enumerate(pts):
        tip = esc(f"<b>{d}</b><br>Close {d2(c)}<br>{c / trim:.1f} times the trim-above")
        o.append(f'<rect x="{x(i) - w / 2:.1f}" y="{t}" width="{w:.1f}" height="{bt - t}" fill="transparent" data-tip="{tip}"/>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Corning weekly close since January 2024 against the trim-above and the buy-below.">{"".join(o)}</svg>'


# ---- Chart 3: what moves the trim-above.
def sens_chart():
    rows = sorted(SENS, key=lambda r: r[1]) + [("All five true, chances ignored", alltrue), ("Every favorable reading at once", stretch)]
    T, rh = 34, 28
    bottom = T + rh * len(rows)
    H = bottom + 30
    l = 340
    x = lambda v: l + v / HI * (R - l)
    o = []
    for v in range(0, 131, 10):
        o.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T - 6}" y2="{bottom}" stroke="var(--grid)"/>')
        o.append(f'<text x="{x(v):.1f}" y="{bottom + 18}" text-anchor="middle" class="ax">${v}</text>')
    o.append(f'<line x1="{x(trim):.1f}" x2="{x(trim):.1f}" y1="20" y2="{bottom}" stroke="var(--s3)" stroke-width="2"/>')
    o.append(f'<text x="{x(trim) + 6:.1f}" y="16" class="lv">Trim-above {d2(trim)}</text>')
    o.append(f'<line x1="{x(price):.1f}" x2="{x(price):.1f}" y1="20" y2="{bottom}" stroke="var(--s2)" stroke-width="2"/>')
    o.append(f'<text x="{x(price) - 6:.1f}" y="16" text-anchor="end" class="lv">Price {d2(price)}</text>')
    for i, (n, v) in enumerate(rows):
        yy = T + rh * i + 12
        x0, x1 = sorted((x(trim), x(v)))
        o.append(f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{yy}" y2="{yy}" stroke="var(--d1)" stroke-width="2"/>')
        o.append(f'<circle cx="{x(v):.1f}" cy="{yy}" r="5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>')
        o.append(f'<text x="{l - 12}" y="{yy + 4}" text-anchor="end" class="nm">{html.escape(n)}</text>')
        o.append(f'<text x="{x(v) + 10:.1f}" y="{yy + 4}" class="lv halo">{d2(v)}</text>')
        tip = esc(f"<b>{n}</b><br>Trim-above {d2(v)}<br>{sg(v - trim)} against the approved figure. Calc.")
        o.append(f'<rect x="{l:.1f}" y="{yy - 12}" width="{R - l}" height="24" fill="transparent" data-tip="{tip}"/>')
    return f'<svg viewBox="0 0 1000 {H}" role="img" aria-label="The trim-above under each change of assumption, against the price.">{"".join(o)}</svg>'


def scenario_table():
    h = '<thead><tr><th>Scenario</th><th>What would happen</th><th class="num">Adds a share if it does</th><th class="num">Chance</th><th class="num">Value</th><th>Why that chance</th><th>When we would know</th><th>What would prove it wrong</th></tr></thead>'
    body = []
    for s in S:
        r = ROWS[s["key"]]
        body.append(f'<tr><th>{NAMES[s["key"]]}</th><td>{r["what"]}</td><td class="num">{sg(s["full"])}</td><td class="num">{pc(s["p"])}</td><td class="num"><b>{sg(s["ev"])}</b></td><td>{r["why"]}</td><td>{r["when"]}</td><td>{r["wrong"]}</td></tr>')
    body.append(f'<tr class="hl"><th>Strategic value</th><td colspan="3">The five scenarios add {d2(sum_up)}. The downside takes off {d2(-BY["rival"]["ev"])}.</td><td class="num"><b>{d2(strat)}</b></td><td colspan="3">Calc. The chances are my judgment. The vault holds no base rate for them.</td></tr>')
    return f'<div class="wrap"><table class="tight wide">{h}<tbody>{"".join(body)}</tbody></table></div>'


def working_table():
    h = '<thead><tr><th>Scenario</th><th class="num">New sales a year</th><th class="num">New profit a year</th><th class="num">× 13.3 votes</th><th class="num">Years away</th><th class="num">Worth today at 9%</th><th class="num">Capital, today</th><th class="num">Net</th><th class="num">÷ 871M shares</th></tr></thead>'
    body = []
    for s in S:
        if s["key"] == "rival":
            body.append(f'<tr><th>{SHORT[s["key"]]}</th><td class="num">{bn(s["sales"])} at risk</td><td class="num">{bn(s["ni"])}</td><td class="num">{bn(s["gross"])}</td><td class="num">{s["t"]:.2f}</td><td class="num">{bn(s["pv"])}</td><td class="num">none</td><td class="num">{bn(s["dollars"])}</td><td class="num">{sg(s["full"])}</td></tr>')
        else:
            body.append(f'<tr><th>{SHORT[s["key"]]}</th><td class="num">{bn(s["sales"])}</td><td class="num">{bn(s["ni"])}</td><td class="num">{bn(s["gross"])}</td><td class="num">{s["t"]:.2f}</td><td class="num">{bn(s["pv"])}</td><td class="num">{bn(-s["kpv"]) if s["kpv"] else "none"}</td><td class="num">{bn(s["dollars"])}</td><td class="num">{sg(s["full"])}</td></tr>')
    return f'<div class="wrap"><table class="tight">{h}<tbody>{"".join(body)}</tbody></table></div>'


def deals_table():
    body = "".join(f'<tr><th>{html.escape(n)}</th><td class="num">{bn(v)}</td><td>{html.escape(w)}</td></tr>' for n, v, w in m.DEALS)
    return f'<div class="wrap"><table class="tight"><thead><tr><th>Deal</th><th class="num">Total used</th><th>Basis</th></tr></thead><tbody>{body}<tr class="hl"><th>Per year over six years</th><td class="num">{bn(m.DEALS_CEILING)}</td><td>Calc. Six years is Verizon\'s stated term, used for all. {pc(m.NEW_SHARE)} new gives {bn(lad["signed"])}.</td></tr></tbody></table></div>'


def checks_table():
    rows = [
        ("Deals, plants and targets are the same dollars", "<b>Fixed.</b>", f"One ladder, from the Q3 run rate of {bn(m.RUN_RATE)} to $40 billion. Its five steps add to {bn(sum(lad.values()))}, the whole gap and no more (calc.). Plants, tariffs and interim targets add nothing of their own."),
        ("A catalyst already in the reported numbers", "<b>Fixed.</b>", f"Every step starts above Q3 times four. The $20 billion target, the 20% margin goal, tax credits, Apple and Lumen are out. The Q4 forecast is not reported, so it is not treated as held."),
        ("Earnings in the base", "<b>Clear.</b>", f"The highest earnings in the base are {bn(m.base_model.TTM_NORMAL_NI)}, twelve months to Sept. 30, 2026. Q3 net income times four is {bn(q3_ni4)} (calc., {q3r}). The steps start from Q3, so they sit above every base figure."),
        ("Growth in the base", "<b>Clear.</b>", f"The base's cash vote grows {pc(g_rec, 2)} a year. From {bn(1256)} that is {bn(base_cash_2030)} at the end of 2030. It would take {cross_years:.0f} years to reach Q3's level (calc.), so it does not reach the scenarios' dollars."),
        ("Customer deposits", "<b>Clear.</b>", f"The base takes deposits out. No scenario counts one. The $1.0 billion deposit is repaid as customers \"purchase the committed volume\" ({q3c}), so it is a loan, not value."),
        ("NVIDIA warrants and shares", "<b>Clear, one unknown.</b>", f"All figures use 871M diluted shares. The 15M warrant at $180 is outside that count ({q10}), and it brings in $2.7 billion if used, so at any value under $180 it is left out. Whether the 3M pre-funded warrant is inside the 871M is not split out. It would move value by about 0.3% (calc.)."),
        ("Anything the price holds", "<b>Clear, by design.</b>", f"No scenario reads the price. A test moves it and the value stays put. No rival or past multiple is used, because those carry the market's mood. The multiple is the base's own vote, {mult:.1f}x. The two items that turn on the price, the Samsung buyback and the share program, are out."),
        ("Subtracting what the price already pays for", "<b>Not done, on purpose.</b>", f"Every scenario was public before this close. Taking it off value because the market knows it would make value depend on the price, and the comparison would prove nothing. Instead, compare: the price pays {d2(C['implied'])} above base, and strategic value is {d2(strat)}, or {pc(C['share'])} of that (calc.). The close the day before the Meta post, {d2(close['2026-01-26'])}, was already {close['2026-01-26'] / trim:.1f} times this value. That day's rise of {d2(gap_meta)} is more than the whole strategic value (calc., {yh})."),
        ("Chances that depend on each other", "<b>Clear.</b>", "Chances fall as the ladder rises: 70%, 40%, 20%, so a higher step never beats the one under it. An AI slowdown would hit them together. That widens the outcomes, but it does not change a sum of chance-weighted values."),
        ("Capital charged twice", "<b>Clear.</b>", f"Each dollar of new sales carries its segment's assets: {m.OPT_CAPITAL:.2f} for Optical, {m.SOLAR_CAPITAL:.2f} for Solar (calc., {q10}). The share program and capex plan are not charged again."),
    ]
    body = "".join(f"<tr><th>{a_}</th><td>{b_}</td><td>{c_}</td></tr>" for a_, b_, c_ in rows)
    return f'<div class="wrap"><table class="tight"><thead><tr><th>Could be counted twice</th><th>Result</th><th>How</th></tr></thead><tbody>{body}</tbody></table></div>'


def map_table():
    order = [m.SIGNED, m.PLAN, m.SCALE, m.SOLAR, m.DISPLAY, m.RIVAL, m.OUT_NUM, m.OUT_PRICE, m.OUT_NOSIZE, m.OUT_EMPTY, m.OUT_COST]
    body = []
    for o in order:
        names = sorted(n for n, v in m.MAP.items() if v[0] == o)
        for i, n in enumerate(names):
            body.append(f'<tr><th>{o if i == 0 else ""}</th><td>{html.escape(n)}</td><td>{html.escape(m.MAP[n][1])}</td></tr>')
    return f'<div class="wrap"><table class="tight"><thead><tr><th>Where it went</th><th>Catalyst note</th><th>Why</th></tr></thead><tbody>{"".join(body)}</tbody></table></div>'


counted = sum(1 for v in m.MAP.values() if v[0].startswith("Scenario") or v[0] == m.RIVAL)
left_out = len(m.MAP) - counted

PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Corning Strategic Value</title><style>{(HERE / "style.css").read_text()}
.wide{{min-width:1180px}}
details{{margin:10px 0}}summary{{cursor:pointer;font-weight:600}}
</style></head><body><main>
<h1>Corning's strategic value</h1>
<p class="lede"><b>Trim above {d2(trim)}, approved Nov. 3, 2026.</b> Base value of {d2(b['mid'])} plus strategic value of {d2(strat)} comes to {d2(trim)}. The {d2(price)} close is {C['times']:.1f} times that. Even if all five scenarios come true, the stack reaches {d2(alltrue)}. All figures are calc. I proposed the chances on judgment, and you kept them.</p>
<div class="tiles">{tile(d2(b['mid']), "Base value, middle")}{tile(sg(strat), "Strategic value")}{tile(d2(trim), f"Base plus strategic, {pc(C['cover'])} of the price")}{tile(d2(price), "Close, Nov. 2, 2026, the latest saved")}</div>
<div class="callout"><b>Saved in <code>Rules/when-to-trim.md</code>, with the figures in the Corning note.</b> This gives <b>no trim recommendation today</b>: no rise has taken the price through the line lately, no thesis is written, and no holding is on file. No investing decision. The Corning decision of Nov. 2 stands: no buy.</div>

<h2>The value stack</h2>
<p>Each blue step is a scenario's value times its chance. The gray line behind it is what it adds if it happens. Hover over any row for the sum.</p>
<ul class="legend"><li><span class="key" style="background:var(--ink)"></span>Base value</li><li><span class="key" style="background:var(--s1)"></span>Scenario × chance</li><li><span class="key" style="background:var(--d1)"></span>If it happens, or all five</li><li><span class="key" style="background:var(--s2)"></span>Downside and price</li><li><span class="key" style="background:var(--s3)"></span>Base plus strategic</li></ul>
<div class="card scroll"><figure>{stack()}<figcaption>Base value from <code>base.html</code>. Price: {yh}. Today's close was not in when this was built, so the price sensor was not run. Rows are in the scenario table below. The base's line under its bar is its range, {d2(b['low'])} to {d2(b['high'])}.</figcaption></figure></div>

<h2>The scenarios</h2>
<p>I picked these from the 38 notes because each has a dated source, a size I can tie to a filed number, dollars not yet reported, a date to check and a way to be wrong. The vault has no definition of "rational speculation", so that test is mine. {counted} notes feed the rows below and {left_out} are left out, each listed further down.</p>
{scenario_table()}

<h2>How each dollar figure is built</h2>
<p>The same yardstick as the base, on new dollars only: new profit × the base's three votes, brought back to today at 9%, less the capital to build it, ÷ 871M shares.</p>
<ul class="notes">
<li><b>The {mult:.1f}x:</b> 40% ÷ 9%, 40% the cash sum at record growth of {pc(g_rec, 2)}, 20% ÷ the Aaa yield of 6.12% for Oct. 2026 ({aaa}). All calc. It treats new cash as equal to new profit.</li>
<li><b>Optical margin:</b> {pc(m.OPT_MARGIN, 1)}, Q3 segment net income of $532M on sales of $2,379M (calc., {q10}). That is before corporate costs, so it may flatter. It is also a shortage-year margin. Row 2 gives all its sales that margin, though some may come from other segments.</li>
<li><b>Capital:</b> segment assets per dollar of twelve-month sales: $5,039M on {bn(m.TTM_SALES['Optical'])} for Optical, $3,166M on {bn(m.TTM_SALES['Solar'])} for Solar (calc., {q10}; {q1r}), spent halfway to the date. The CFO says agreements fund \"the majority\" of capital ({q3c}), but he also says \"we return that cash\", so I charge it all. Solar also carries the $132M earn-out liability ({q10}).</li>
<li><b>No growth above that:</b> the rules cap growth forever at 3%, so a plan that keeps growing after 2030 gets little credit. Long deals ending and rival plants cut the other way.</li>
</ul>
{working_table()}
<details><summary>Signed deals, row by row</summary>{deals_table()}<p class="foot">Sources: {meta}; {q1r}; {vz}; {att}; {q3r}. "$2 billion" for "multibillion" and six years for every deal are my assumptions, because the terms are not filed. Amazon is not added, since it may be one of the two unnamed deals.</p></details>

<h2>Did I count anything twice?</h2>
<p>I checked each way it could happen. One gap runs the other way.</p>
{checks_table()}
<div class="callout"><b>One gap, an undercount.</b> The base's middle stands on FY2025 earnings. The scenarios start at Q3 2026. Profit earned between the two is in the reported numbers, so by your instruction it is not a scenario, and it is not in the base's middle either. The base's own high case shows its size: {d2(b['high'] - b['mid'])} a share (calc.). It closes when the FY2026 10-K lifts the base's middle, about Feb. 2027 (my estimate). The scenarios must then be re-measured from the newer quarter. Until then, {d2(trim)} leans low, and {d2(b['high'] + strat)} is the same sum on the base's high. You chose the middle on Nov. 3, 2026.</div>
<details><summary>Where each of the 38 catalyst notes went</summary>{map_table()}</details>

<h2>The trim-above against the price</h2>
<div class="card scroll"><figure>{price_chart()}<figcaption>Weekly closes, not adjusted for dividends ({yh}). Both lines are today's figures, drawn back for scale. They are not what value was on those dates.</figcaption></figure></div>
<ul class="notes">
<li><b>Band:</b> the buy-below of {d2(buy)} and the trim-above of {d2(trim)} are {pc(trim / buy - 1)} apart (calc.).</li>
<li><b>How often:</b> since Jan. 2016 the close was above {d2(trim)} on {above:,} of {len(since16):,} days, or {pc(above / len(since16))}. It was between the lines on {between:,} and under the buy-below on {below:,} (calc.). Every close since {date(last_at)} has been above it. So today's line would have said "consider trimming" for over two years straight. You approved the line with this shown.</li>
<li><b>Direction:</b> the rule speaks of "a rise". The price has fallen from {d2(peak[1])} on June 29, 2026 to {d2(price)}, and it is still above the line. You kept the word "a rise" on Nov. 3, 2026. So being above is not enough: the rule speaks only when a rise takes the price through the line. At these prices it stays silent until the price falls under the line and comes back, or a refresh lifts the line past the price.</li>
</ul>

<h3>What moves the trim-above</h3>
<div class="card scroll"><figure>{sens_chart()}<figcaption>One change at a time, except the last two rows. Single changes run from {d2(low_s)} to {d2(high_s)}. "Every favorable reading" takes the base's high, all five true, the {pc(m.OPT_INCREMENTAL, 1)} margin added over the last year (calc., {q10}), no capital charge, the 3% cap and no rival cut. It reaches {d2(stretch)}. That is not a forecast.</figcaption></figure></div>
<p>No change here reaches the price. With all five true and capital charged, the price needs about {needed:.0f}x new profit, against {mult:.1f}x on the base's votes (calc.). That says what the price asks for. It does not say the price is wrong, and the rules' 3% cap is itself a choice that keeps value low for a company that really does keep growing.</p>

<h2>The rule as saved</h2>
<div class="prop"><p><b>In <code>Rules/when-to-trim.md</code>, saved Nov. 3, 2026, in these words or close to them:</b></p>
<ul>
<li><b>Strategic value is worked out this way:</b> for each scenario from the catalyst notes, take only what is not in the base value or the reported numbers. New profit × the base's votes, brought back at 9%, less the capital to build it, per diluted share. Multiply by its chance and add them up. Downsides count too.</li>
<li><b>Value</b> for trimming is the middle of the base range plus strategic value. <b>The trim-above price</b> is that value.</li>
<li><b>Refresh</b> after each 10-Q and 10-K, from the newest quarter. A chance changes only on a dated event, never on a price move.</li>
<li>If a rise takes the price above the line and the thesis holds, consider trimming. That means selling part, never the whole. A broken thesis stays a separate case.</li>
<li>Changing the method needs my approval. Strategic value still never counts toward covering the price. The buy-below stays {d2(buy)}.</li>
</ul></div>

<h2>What this does not say</h2>
<ul class="notes">
<li>It does not say Corning will fall, or that it is a trim or a sell. The price can stay above value for years, and rule 6 acts on the thesis.</li>
<li>The chances are my opinion, not facts. The $2 billion, six years, 75% new and 5% display figures are my assumptions, with no source. Targets are targets, and every scenario is a forecast, not a result.</li>
<li><b>Left out because they cannot be sized:</b> hollow-core fiber, the China duty, germanium and the EU commitments. <b>Not taken off:</b> outside owners' share of Solar, which the filings do not split, and corporate costs on new sales.</li>
<li>The Q3 call quotes come from a third-party transcript, and the "committed volume", "majority" and "return that cash" lines were read through a summarizing fetch on Nov. 3, 2026. The Springboard release is a copy on MarketScale. None was checked against a filing.</li>
</ul>
<p class="foot">Built Nov. 3, 2026 from <code>sensors/strategic/</code>. Local only: it holds a Yahoo price, and <code>sensors/prices/prices.py</code> says nothing built from it should be published.</p>
</main>
<div id="tip" hidden></div>
<script>
const tip=document.getElementById('tip');
function show(e,t){{tip.innerHTML=t;tip.hidden=false;const r=tip.getBoundingClientRect();let x=e.clientX+14,y=e.clientY+14;if(x+r.width>innerWidth-8)x=e.clientX-r.width-14;if(y+r.height>innerHeight-8)y=e.clientY-r.height-14;tip.style.left=x+'px';tip.style.top=y+'px'}}
document.querySelectorAll('[data-tip]').forEach(n=>{{n.addEventListener('mousemove',e=>show(e,n.dataset.tip));n.addEventListener('mouseleave',()=>tip.hidden=true)}});
</script></body></html>
"""
(ROOT / "strategic.html").write_text(PAGE)
print("wrote strategic.html", len(PAGE), "above", above, len(since16), "between", between, "below", below, "last", last_at, "cross", cross_years, "cash2030", base_cash_2030, "counted", counted, left_out)
