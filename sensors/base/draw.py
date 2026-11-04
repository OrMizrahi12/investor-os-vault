"""Builds base.html from model.py. Takes no flags and writes when run. The method was approved Nov. 3, 2026, and it is in Rules/when-to-buy.md.

    .venv/bin/python sensors/base/draw.py
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as m  # noqa: E402

SEC = "https://www.sec.gov/Archives/edgar/data/24741/"
K25 = SEC + "000002474126000124/glw-20251231.htm"
K18 = SEC + "000002474119000016/glw-20181231x10k.htm"
Q10 = SEC + "000002474126000279/glw-20260930.htm"
Q3R = "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&amp;interval=1d"
AAAU = "https://fred.stlouisfed.org/series/AAA"


def a(url, text):
    return f'<a href="{url}">{text}</a>'


k25, k18, q10 = a(K25, "10-K, filed Feb. 12, 2026"), a(K18, "10-K, filed Feb. 12, 2019"), a(Q10, "10-Q, filed Oct. 29, 2026")
q3r, yh = a(Q3R, "Q3 release, Oct. 27, 2026"), a(YAHOO, "Yahoo through yfinance, fetched Nov. 2, 2026")
fred = a(AAAU, "FRED AAA, downloaded Nov. 3, 2026")


def d2(x):
    return f"${x:,.2f}"


def d0(x):
    return f"${x:,.0f}"


def pc(x, dp=0):
    s = f"{abs(x) * 100:.{dp}f}%"
    return ("−" + s) if x < 0 else s


def signed(x, dp=0):
    s = f"{abs(x) * 100:.{dp}f}%"
    if round(abs(x) * 100, dp) == 0:
        return s
    return ("−" if x < 0 else "+") + s


def date(iso):
    y, mo, day = iso.split("-")
    return f"{['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'][int(mo) - 1]} {int(day)}, {y}"


an, gr, tags = m.anchors(), m.growth(), m.past_tags()
ms = m.methods()
by = {x["key"]: x for x in ms}
base = m.combine(ms)
bb = m.buy_below(base["mid"])
price = m.PRICE
cov = {k: v / price for k, v in base.items()}
mos_today = (base["mid"] - price) / base["mid"]
mos_bb = (base["mid"] - bb) / base["mid"]
mos_bb_high = (base["high"] - bb) / base["high"]
under = m.days_under(bb)
need_price = m.need(price, m.CASH_HIGH / m.SHARES, .09)
need_bb_hi, need_bb_mid = m.need(bb, m.CASH_HIGH / m.SHARES, .09), m.need(bb, m.CASH_MID / m.SHARES, .09)
fcf10 = sum(m.FCF.values()) / 10
credits = 172 + 87
credit_eps = credits / m.SHARES
credit_mid = (an["mid"] - credit_eps) / m.RATE
ttm_mid = .4 * an["high"] / m.RATE + .4 * by["cash"]["mid"] + .2 * an["high"] / m.AAA
ttm_bb = ttm_mid / m.MOST
times = price / bb
peak = max(m.closes(), key=lambda r: r[1])
pts = dict(L=262, R=986, lo=0, hi=130)


def X(v):
    return pts["L"] + (v - pts["lo"]) / (pts["hi"] - pts["lo"]) * (pts["R"] - pts["L"])


def esc(s):
    return html.escape(s, quote=True)


def hero():
    out = []
    rows = [("earn", "40% of the vote", "Normal earnings, no growth", "from normal.html"),
            ("cash", "40% of the vote", "Cash sum, record growth", "from worth.html"),
            ("bond", "20% of the vote", "Normal earnings at the Aaa yield", "from multiples.html"),
            ("past", "No vote", "Own past tag on normal earnings", "from multiples.html"),
            ("parts", "No vote", "Parts at rival multiples", "from parts.html")]
    T, rh = 58, 46
    ruler_y = T + rh * len(rows) + 4
    base_y = ruler_y + 58
    H = base_y + 62
    for v in range(0, 131, 10):
        out.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{T - 8}" y2="{base_y + 26}" stroke="var(--grid)"/>')
        out.append(f'<text x="{X(v):.1f}" y="{base_y + 44}" text-anchor="middle" class="ax">${v}</text>')
    out.append(f'<line x1="{pts["L"]}" x2="{pts["R"]}" y1="{base_y + 26}" y2="{base_y + 26}" stroke="var(--axis)"/>')
    # The two prices, under the rows.
    for v, c, lab, anchor, dx in ((bb, "var(--s3)", f"Buy below {d2(bb)}", "start", 6), (price, "var(--s2)", f"Price {d2(price)}", "end", -6)):
        out.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="26" y2="{base_y + 26}" stroke="{c}" stroke-width="2"/>')
        out.append(f'<text x="{X(v) + dx:.1f}" y="22" text-anchor="{anchor}" class="lv">{lab}</text>')
    for i, (k, vote, name, src) in enumerate(rows):
        r, y = by[k], T + rh * i
        fill = "var(--s1)" if r["w"] else "var(--d1)"
        out.append(f'<text x="{pts["L"] - 14}" y="{y + 9}" text-anchor="end" class="nm">{name}</text>')
        out.append(f'<text x="{pts["L"] - 14}" y="{y + 25}" text-anchor="end" class="ax">{vote}, {src}</text>')
        x0, x1 = X(r["low"]), X(r["high"])
        tip = esc(f"<b>{name}</b><br>Low {d2(r['low'])}<br>Middle {d2(r['mid'])}<br>High {d2(r['high'])}<br>{vote}. Calc.")
        out.append(f'<rect x="{x0:.1f}" y="{y}" width="{x1 - x0:.1f}" height="16" rx="4" fill="{fill}" opacity="{1 if r["w"] else .8}"/>')
        out.append(f'<rect x="{X(r["mid"]) - 1.5:.1f}" y="{y - 4}" width="3" height="24" rx="1.5" fill="var(--ink)" stroke="var(--surface)" stroke-width="1"/>')
        out.append(f'<text x="{x0 - 6:.1f}" y="{y + 13}" text-anchor="end" class="lv halo">{d0(r["low"])}</text>')
        out.append(f'<text x="{x1 + 6:.1f}" y="{y + 13}" class="lv halo">{d0(r["high"])}</text>')
        out.append(f'<rect x="{x0 - 30:.1f}" y="{y - 8}" width="{x1 - x0 + 60:.1f}" height="32" fill="transparent" data-tip="{tip}"/>')
    # Reverse sum: ticks, no band.
    out.append(f'<text x="{pts["L"] - 14}" y="{ruler_y + 9}" text-anchor="end" class="nm">Growth each price needs</text>')
    out.append(f'<text x="{pts["L"] - 14}" y="{ruler_y + 25}" text-anchor="end" class="ax">No vote, a test, from priced-in.html</text>')
    out.append(f'<line x1="{X(10):.1f}" x2="{X(130):.1f}" y1="{ruler_y + 22}" y2="{ruler_y + 22}" stroke="var(--axis)" stroke-dasharray="3 3"/>')
    for p in (bb, 50, 75, 100, price):
        n = m.need(p, m.CASH_HIGH / m.SHARES, .09)
        tip = esc(f"<b>At {d2(p)}</b><br>Needs {pc(n, 1)} a year for ten years, then 3%, from $1.73 at 9%. Calc. A requirement, not a forecast.")
        out.append(f'<circle cx="{X(p):.1f}" cy="{ruler_y + 22}" r="5" fill="var(--d2)" stroke="var(--surface)" stroke-width="2"/>')
        out.append(f'<text x="{X(p):.1f}" y="{ruler_y + 11}" text-anchor="middle" class="lv halo">{pc(n, 1)}</text>')
        out.append(f'<rect x="{X(p) - 22:.1f}" y="{ruler_y}" width="44" height="34" fill="transparent" data-tip="{tip}"/>')
    # Base range.
    out.append(f'<text x="{pts["L"] - 14}" y="{base_y + 8}" text-anchor="end" class="nm b">Base value</text>')
    out.append(f'<text x="{pts["L"] - 14}" y="{base_y + 24}" text-anchor="end" class="ax">The three votes combined</text>')
    x0, x1 = X(base["low"]), X(base["high"])
    tip = esc(f"<b>Base value</b><br>Low {d2(base['low'])}<br>Middle {d2(base['mid'])}<br>High {d2(base['high'])}<br>Calc.")
    out.append(f'<rect x="{x0:.1f}" y="{base_y - 4}" width="{x1 - x0:.1f}" height="22" rx="4" fill="var(--ink)"/>')
    out.append(f'<rect x="{X(base["mid"]) - 1.5:.1f}" y="{base_y - 8}" width="3" height="30" rx="1.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="1"/>')
    out.append(f'<text x="{x0 - 6:.1f}" y="{base_y + 12}" text-anchor="end" class="lv halo">{d0(base["low"])}</text>')
    out.append(f'<rect x="{x0:.1f}" y="{base_y - 8}" width="{x1 - x0:.1f}" height="30" fill="transparent" data-tip="{tip}"/>')
    tx = X(base["high"]) + 38
    out.append(f'<text x="{tx:.1f}" y="{base_y + 12}" class="lv halo">{d0(base["low"])} to {d0(base["high"])}, middle {d0(base["mid"])}</text>')
    return f'<svg viewBox="0 0 1000 {H}" role="img" aria-label="Each method\'s value range per share on one axis from $0 to $130, with the base range, the buy-below price and the last close.">{"".join(out)}</svg>'


def coverage():
    L, R, W = 20, 980, 960
    S = lambda share: L + share * W  # noqa: E731
    y = 56
    o = [f'<rect x="{L}" y="{y}" width="{W}" height="30" rx="4" fill="var(--d1)" opacity=".55"/>',
         f'<rect x="{L}" y="{y}" width="{cov["mid"] * W:.1f}" height="30" rx="4" fill="var(--s1)"/>',
         f'<rect x="{S(cov["low"]):.1f}" y="{y + 36}" width="{(cov["high"] - cov["low"]) * W:.1f}" height="6" rx="3" fill="var(--ink)"/>',
         f'<text x="{S(cov["high"]) + 8:.1f}" y="{y + 44}" class="ax">Base range covers {pc(cov["low"])} to {pc(cov["high"])}</text>',
         f'<text x="{S(cov["mid"]) - 6:.1f}" y="{y + 20}" text-anchor="end" class="on" style="fill:#fff">{pc(cov["mid"])}</text>',
         f'<text x="{(S(cov["mid"]) + S(m.MOST)) / 2:.1f}" y="{y + 20}" text-anchor="middle" class="lv">{pc(1 - cov["mid"])} of the price rests on what is not proven</text>',
         f'<line x1="{S(m.MOST):.1f}" x2="{S(m.MOST):.1f}" y1="{y - 10}" y2="{y + 42}" stroke="var(--s3)" stroke-width="2"/>',
         f'<text x="{S(m.MOST):.1f}" y="{y - 16}" text-anchor="middle" class="lv">The bar: {pc(m.MOST)}</text>',
         f'<rect x="{L}" y="{y}" width="{W}" height="30" fill="transparent" data-tip="{esc(f"<b>Coverage at {d2(price)}</b><br>Base middle {d2(base["mid"])} ÷ price = {pc(cov["mid"], 1)}. Calc.")}"/>']
    return f'<svg viewBox="0 0 1000 110" class="mini" role="img" aria-label="Base value covers {pc(cov["mid"])} of the price, against a bar of {pc(m.MOST)}.">{"".join(o)}</svg>'


def history():
    rows = [r for r in m.closes() if r[0] >= "2016-01-01"]
    wk = rows[::5] + [rows[-1]]
    L, R, T, B = 50, 930, 20, 270
    n, top = len(wk) - 1, (int(max(c for _, c in wk)) // 20 + 1) * 20
    XX = lambda i: L + i / n * (R - L)  # noqa: E731
    YY = lambda v: B - v / top * (B - T)  # noqa: E731
    o = []
    for v in range(0, top + 1, 20):
        o.append(f'<line x1="{L}" x2="{R}" y1="{YY(v):.1f}" y2="{YY(v):.1f}" stroke="{"var(--axis)" if v == 0 else "var(--grid)"}"/>')
        o.append(f'<text x="{L - 8}" y="{YY(v) + 4:.1f}" text-anchor="end" class="ax">${v}</text>')
    seen = set()
    for i, (d, _) in enumerate(wk):
        y = d[:4]
        if y not in seen and int(y) % 2 == 0:
            o.append(f'<text x="{XX(i):.1f}" y="{B + 18}" text-anchor="middle" class="ax">{y}</text>')
        seen.add(y)
    path = "M" + "L".join(f"{XX(i):.1f},{YY(c):.1f}" for i, (_, c) in enumerate(wk))
    o.append(f'<path d="{path}" fill="none" stroke="var(--s1)" stroke-width="2"/>')
    o.append(f'<line x1="{L}" x2="{R}" y1="{YY(bb):.1f}" y2="{YY(bb):.1f}" stroke="var(--s3)" stroke-width="2"/>')
    o.append(f'<text x="{R + 6}" y="{YY(bb) + 4:.1f}" class="lv">{d0(bb)}</text>')
    o.append(f'<text x="{XX(int(n * .5)):.1f}" y="{YY(bb) + 18:.1f}" class="lv halo">Buy below, today\'s level, {d2(bb)}</text>')
    o.append(f'<text x="{R + 6}" y="{YY(price) + 4:.1f}" class="lv">{d0(price)}</text>')
    for i, (d, c) in enumerate(wk):
        o.append(f'<rect x="{XX(i) - (R - L) / n / 2:.1f}" y="{T}" width="{(R - L) / n:.1f}" height="{B - T}" fill="transparent" data-tip="<b>{date(d)}</b><br>Close {d2(c)}"/>')
    return f'<svg viewBox="0 0 1000 300" role="img" aria-label="Corning weekly closes since 2016 with the buy-below line.">{"".join(o)}</svg>'


def method_rows():
    words = {
        "earn": ("What it does", "Normal earnings ÷ 9%. A business that stays the same size forever. Earnings come from the adjustments you confirmed.",
                 "Trust most. Every input is filed, and nothing grows. Weak spot: the 9% is my judgment, and it gives no credit for any growth."),
        "cash": ("", f"Owner cash grown forever at a rate the record reached: {pc(0)}, {pc(gr['ni'], 1)} and {pc(.03)}, from {d2(m.CASH_LOW / m.SHARES)}, {d2(m.CASH_MID / m.SHARES)} and {d2(m.CASH_HIGH / m.SHARES)} a share, all with deposits out. The ÷ formula on <code>worth.html</code>, with one growth rate.",
                 "Trust most. Cash is harder to flatter than profit. Weak spots: the filing does not split the deposits line, the middle reading is an estimate, and capex holds growth spending nobody can split out."),
        "bond": ("", f"Normal earnings ÷ {pc(m.AAA, 2)}. The price at which they yield what a top-grade bond pays.",
                 "Trust some. The rate is sourced, not my judgment. But it asks nothing extra for risk, so it is generous, and it shares its earnings with the first row. Hence the smaller vote."),
        "past": ("", f"What the market paid for a dollar of normal earnings at ten year ends: {tags['low']:.1f}x at the lowest, {tags['median']:.1f}x at the median.",
                 f"No vote. Those were real prices, but a price holds hopes. Aaa averaged 3.92% at those dates against {pc(m.AAA, 2)} now. The last three tags are {tags['tags'][2023]:.0f}x, {tags['tags'][2024]:.0f}x and {tags['tags'][2025]:.0f}x, set by the story this rule keeps out."),
        "parts": ("", "The sum on <code>parts.html</code> as built, per share on 871M. Low, middle and high rival multiples on twelve-month profit.",
                  "No vote. Rival prices hold those rivals' own targets and deals, which is what you asked to keep out. All rest on one free site, checked against no filing. Optical is 60% of the middle case."),
    }
    out = []
    for r in ms:
        w = words[r["key"]]
        out.append(f'<tr><th>{r["name"]}</th><td>{w[1]}</td><td class="num">{d0(r["low"])}</td><td class="num">{d0(r["mid"])}</td><td class="num">{d0(r["high"])}</td><td class="num">{pc(r["w"]) if r["w"] else "None"}</td><td>{w[2]}</td></tr>')
    out.append(f'<tr><th>Growth each price needs</th><td>The sum on <code>priced-in.html</code>, run at the price. It gives a growth rate, not a value.</td><td class="num">·</td><td class="num">·</td><td class="num">·</td><td class="num">None</td><td>No vote. It is the same sum as the cash row run backwards, so counting it would count that row twice. It tests the answer instead: see section 5.</td></tr>')
    out.append(f'<tr class="hl"><th>Base value</th><td>The three votes, weighted, at low, middle and high.</td><td class="num">{d0(base["low"])}</td><td class="num">{d0(base["mid"])}</td><td class="num">{d0(base["high"])}</td><td class="num">100%</td><td>Approved Nov. 3, 2026.</td></tr>')
    return "".join(out)


def sens_rows():
    out = []
    for label, w in [("Approved: 40, 40, 20", None), ("Normal earnings only", dict(earn=1)), ("Earnings and cash, half each", dict(earn=1, cash=1)),
                     ("Give own past tag 10%", dict(earn=.35, cash=.35, bond=.2, past=.1)), ("Give past tag and parts 10% each", dict(earn=.3, cash=.3, bond=.2, past=.1, parts=.1)),
                     ("All five equal", dict(earn=1, cash=1, bond=1, past=1, parts=1))]:
        c = m.combine(ms, w)
        cl = ' class="hl"' if w is None else ""
        out.append(f'<tr{cl}><th>{label}</th><td class="num">{d0(c["low"])}</td><td class="num">{d2(c["mid"])}</td><td class="num">{d0(c["high"])}</td><td class="num">{pc(c["mid"] / price)}</td><td class="num">{d2(m.buy_below(c["mid"]))}</td></tr>')
    for r in (.08, .10, .11):
        c = m.combine(m.methods(r))
        out.append(f'<tr><th>Same votes, rate {pc(r)} and not 9%</th><td class="num">{d0(c["low"])}</td><td class="num">{d2(c["mid"])}</td><td class="num">{d0(c["high"])}</td><td class="num">{pc(c["mid"] / price)}</td><td class="num">{d2(m.buy_below(c["mid"]))}</td></tr>')
    return "".join(out)


def most_rows():
    out = []
    for most, name in ((.51, "51%, just over half"), (.60, "60%"), (2 / 3, "Two thirds"), (.75, "75%, approved"), (.90, "90%"), (1.0, "100%, price at base")):
        b = m.buy_below(base["mid"], most)
        u = m.days_under(b)
        hi, md = m.need(b, m.CASH_HIGH / m.SHARES, .09), m.need(b, m.CASH_MID / m.SHARES, .09)
        cl = ' class="hl"' if most == .75 else ""
        out.append(f'<tr{cl}><th>{name}</th><td class="num">{d2(b)}</td><td class="num">{signed((base["mid"] - b) / base["mid"])}</td><td class="num">{signed((base["low"] - b) / b)}</td><td class="num">{pc(hi, 1)}</td><td class="num">{pc(md, 1)}</td><td class="num">{date(u["last"])}</td><td class="num">{pc(u["since16"] / u["of16"])}</td></tr>')
    return "".join(out)


ttm_rows = "".join(f'<tr><th>{k}</th><td class="num">{v[0]:+,}</td><td class="num">{v[1]:+,}</td><td class="num">{v[2]:+,}</td><td class="num">{m.TTM_ADJ[k]:+,}</td></tr>'.replace("-", "−") for k, v in m.TTM_ITEMS.items())
CSS = (m.ROOT / "sensors/parts/style.css").read_text() + """
svg .nm{fill:var(--ink);font-weight:600}svg .b{font-weight:700}
.prop{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--s3);border-radius:10px;padding:12px 16px;margin:10px 0;max-width:80ch}
.was{border-left-color:var(--d1)}.prop p:last-child{margin-bottom:0}.prop ul{margin:6px 0;padding-left:18px}
.wrap{margin-bottom:14px}
.lab{font-size:12.5px;color:var(--muted);margin-bottom:4px}
"""

PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Corning Base Value</title><style>{CSS}</style></head><body><main>
<h1>Corning's base value</h1>
<p class="lede"><b>Corning's proven base value comes to {d0(base["low"])} to {d0(base["high"])} a share, {d0(base["mid"])} in the middle. At {d2(price)} it covers {pc(cov["mid"])} of the price (all calc.).</b> "Most" now means <b>{pc(m.MOST)}</b>, which makes the buy-below price <b>{d2(bb)}</b> today. The price is {times:.1f} times that. So nothing here would change our answer on Corning: no buy.</p>
<div class="callout"><b>Approved Nov. 3, 2026, and saved in <code>Rules/when-to-buy.md</code>.</b> I proposed the weights, the 9% and the 75% on judgment, and you approved them. This is not a buy, sell or trim recommendation, and it does not say the price is wrong. It says how much of the price the record can carry.</div>
<div class="tiles">
<div class="tile"><div class="tv">{d0(base["low"])} to {d0(base["high"])}</div><div class="tk">Base range, middle {d2(base["mid"])} (calc.)</div></div>
<div class="tile"><div class="tv">{d2(price)}</div><div class="tk">Last saved close, {yh}. Today's close is not in</div></div>
<div class="tile"><div class="tv">{pc(cov["mid"])}</div><div class="tk">Share of the price covered. {pc(cov["low"])} to {pc(cov["high"])} across the range (calc.)</div></div>
<div class="tile"><div class="tv">{d2(bb)}</div><div class="tk">Buy-below: {d2(base["mid"])} ÷ {pc(m.MOST)} (calc.)</div></div>
</div>

<h2>1. The methods side by side</h2>
<div class="card"><ul class="legend"><li><span class="key" style="background:var(--s1)"></span>Votes in the base value</li><li><span class="key" style="background:var(--d1)"></span>On the axis, no vote</li><li><span class="key" style="background:var(--ink)"></span>Base range</li><li><span class="key" style="background:var(--s3)"></span>Buy-below</li><li><span class="key" style="background:var(--s2)"></span>Price</li></ul>
<div class="scroll"><figure>{hero()}</figure></div>
<figcaption>Dollars a share, on 871M diluted shares. The tick in each band is its middle. The percents are the yearly growth each price needs for ten years. All calc. Hover for figures.</figcaption></div>
<p>Only the three lowest bands use nothing but Corning's own record and a stated rate. The two highest bands sit higher because they use market prices, not because Corning earns more in them. That gap is the point of the rule.</p>

<h2>2. Which I trust, and why</h2>
<div class="wrap"><table class="tight"><thead><tr><th>Method</th><th>What it does</th><th class="num">Low</th><th class="num">Mid</th><th class="num">High</th><th class="num">Vote</th><th>Why that vote</th></tr></thead><tbody>{method_rows()}</tbody></table></div>
<p class="foot">Calc. Sources: <code>normal.html</code>, <code>worth.html</code>, <code>multiples.html</code>, <code>parts.html</code>, <code>priced-in.html</code>. Aaa: {pc(m.AAA, 2)} for Oct. 2026, {fred}. Parts per share differ slightly from market value's 861.4M shares ({q10}), and parts are as you confirmed them, with $1.0 billion of deposit money still in cash.</p>

<h2>3. What counts as proven</h2>
<p><b>The earnings.</b> Three figures, each already earned. The low is the ten-year normal average. The middle is the last audited year. The high is the last twelve months, which are in the numbers but unaudited and one strong run.</p>
<div class="wrap"><table style="max-width:760px"><thead><tr><th>Normal earnings</th><th class="num">$M</th><th class="num">A share</th><th>Used as</th></tr></thead><tbody>
<tr><th>Ten-year average, FY2016 to FY2025 (<code>normal.html</code>)</th><td class="num">{sum(m.NORMAL_NI.values()) / 10:,.0f}</td><td class="num">{d2(an["low"])}</td><td>Low</td></tr>
<tr><th>FY2025 ({k25})</th><td class="num">{m.NORMAL_NI[2025]:,}</td><td class="num">{d2(an["mid"])}</td><td>Middle. Also the high of the ten years</td></tr>
<tr><th>Twelve months to Sept. 30, 2026, new here</th><td class="num">{m.TTM_NORMAL_NI:,}</td><td class="num">{d2(an["high"])}</td><td>High</td></tr>
</tbody></table></div>
<p><b>Two checks on the middle.</b> The ten-year normal margin of {pc(an["margin"], 1)} on twelve-month sales of ${m.TTM_SALES:,}M gives {d2(an["margin_eps"])} a share. Owner cash gives {d2(an["owner_eps"])}: ${m.OCF:,}M of operating cash, less ${m.LINE}M of deposits line, ${m.UPKEEP_CEILING}M of capex at its ten-year low as a rough ceiling on upkeep, ${m.STOCK_PAY}M of stock pay, ${m.LEASES}M of lease principal and ${m.RECEIVABLES}M more receivables sold (all calc., {k25}; {q10}). Both land under {d2(an["mid"])}, not over it.</p>
<p><b>The twelve-month figure.</b> Corrected Nov. 3, 2026, with your approval: it first left out the $22M loss on investments in nine months of 2026, which gave $2,029M and a base high of $29.83. Reported ${m.TTM_NI:,}M, or $2.47 a share, plus the three kinds of item you confirmed for normal earnings, at FY2025 less nine months of 2025 plus nine months of 2026 (calc., {k25}; {q10}; {q3r}). The release shows no net income effect for nine-month 2026 debt translation, only $1M before tax.</p>
<div class="wrap"><table style="max-width:640px"><thead><tr><th>Net income effect, $M</th><th class="num">FY2025</th><th class="num">9M 2025</th><th class="num">9M 2026</th><th class="num">12 months</th></tr></thead><tbody>{ttm_rows}</tbody></table></div>
<p><b>The growth.</b> The record, FY2016 to FY2025: free cash flow {pc(gr["fcf"], 2)} a year in dollars, normal net income {pc(gr["ni"], 1)}, free cash flow per share {pc(gr["fcf_sh"], 1)} with buybacks funded partly by a stake sale and borrowing, sales {pc(gr["sales"], 1)} (calc., {k18}; {k25}). The cash row caps at 3%. Sales growth does not count, because sales are not what owners receive, and ten years of them left cash flat.</p>
<p><b>What is kept out:</b> the $20, $30 and $40 billion run-rate targets, Q3 × 4, deposits as cash, signed deals not yet shipped, and any growth above the record.</p>

<h2>4. Combining them</h2>
<p>I weight the low, middle and high of the three votes: 40%, 40%, 20%. That gives <b>{d2(base["low"])} to {d2(base["high"])}, middle {d2(base["mid"])}</b> (calc.). Counting the zero-vote rows lifts it, and they lift it by bringing market prices in, which is what the rule keeps out. The 9% matters too.</p>
<div class="wrap"><table style="max-width:820px"><thead><tr><th>If instead</th><th class="num">Low</th><th class="num">Middle</th><th class="num">High</th><th class="num">Covers</th><th class="num">Buy-below at 75%</th></tr></thead><tbody>{sens_rows()}</tbody></table></div>
<p class="foot">Calc. Even all five equal covers under a third of the price, so no choice in this table changes the answer on Corning today.</p>

<h2>5. Margin of safety, and the number for "most"</h2>
<div class="card"><div class="scroll"><figure>{coverage()}</figure></div></div>
<p><b>Today there is no margin of safety.</b> It is the gap between value and price, as a share of value. At {d2(price)} the gap is {signed(mos_today)}: the price is {price / base["mid"]:.1f} times the base middle, and it would have to fall {pc(1 - base["mid"] / price)} to reach it (calc.).</p>
<p><b>One thing to see clearly: "covers most" is not a margin of safety.</b> Below 100%, you pay more than the proven value. At {d2(bb)} the margin against the middle is still {signed(mos_bb)}, and only against the top of the range is it {signed(mos_bb_high, 1)}. A true cushion starts under {d2(base["mid"])}. <code>margin-of-safety.html</code> draws the ideal as buying below proven value, and our rule says "most". So the proposal keeps the rule's word and sets out the cost: at the buy-below, up to a quarter of what you pay is a bet on what is not proven.</p>
<div class="wrap"><table class="tight"><thead><tr><th>"Most" means</th><th class="num">Buy-below</th><th class="num">Margin on middle</th><th class="num">Fall to low</th><th class="num">Growth needed, from $1.73</th><th class="num">From $1.44</th><th class="num">Last close under it</th><th class="num">Days under, since 2016</th></tr></thead><tbody>{most_rows()}</tbody></table></div>
<p class="foot">Calc. Growth is for ten years, then 3%, at 9%. Closes from {yh}. Past prices are set against today's level, and the business earned less then, so the last two columns show how often a level was reached and not what the rule would have said that day.</p>
<p><b>Why 75%.</b> Three reasons:</p>
<ul class="notes">
<li><b>It keeps the price inside the base range.</b> {d2(bb)} is under the {d2(base["high"])} top. Two thirds, at {d2(m.buy_below(base["mid"], 2 / 3))}, is above it, so even our best proven case would not cover the price.</li>
<li><b>The growth it needs stays near the record.</b> From $1.73 it needs {pc(need_bb_hi, 1)}, under the {pc(gr["fcf_sh"], 1)} that free cash flow per share did. From $1.44 it needs {pc(need_bb_mid, 1)}, which only sales reached, at {pc(gr["sales"], 1)}. Two thirds needs {pc(m.need(m.buy_below(base["mid"], 2 / 3), m.CASH_HIGH / m.SHARES, .09), 1)} and {pc(m.need(m.buy_below(base["mid"], 2 / 3), m.CASH_MID / m.SHARES, .09), 1)}, above every rate on the record from $1.44. Today's price needs {pc(need_price, 1)} from $1.73.</li>
<li><b>It can happen.</b> Corning last closed under it on {date(under["last"])}, and spent {pc(under["since16"] / under["of16"])} of days since 2016 there. 100% last happened on {date(m.days_under(base["mid"])["last"])}, near the 2020 low.</li>
</ul>
<p>At {d2(bb)} normal FY2025 earnings would yield {pc(an["mid"] / bb, 2)}, about what Aaa pays. <b>What you lose if the thesis is wrong:</b> {pc(1 - base["mid"] / bb)} to the base middle and {pc(1 - base["low"] / bb)} to the low, more if the market overshoots (calc.).</p>
<div class="card"><div class="scroll"><figure>{history()}</figure></div><figcaption>Corning weekly close since 2016, unadjusted, with the buy-below line, which is today's and is not a past level. {yh}.</figcaption></div>
<p>The price has fallen {pc(1 - price / peak[1])} from its {d2(peak[1])} close on {date(peak[0])} (calc., same source). No part of the base range rests on the price, so that fall moved none of the three votes. It is still {times:.1f} times the buy-below.</p>

<h2>6. The case against this method</h2>
<div class="grid3" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
<div class="pn"><div class="pt">It is too harsh</div><ul class="notes" style="padding-left:16px;margin:4px 0">
<li>A rule like this would likely have kept you out of the rise from about {d0(bb)} on {date(under["last"])} to {d2(price)}. That is {times:.1f} times, before dividends. It is the rule's cost, and it is large.</li>
<li>If FY2026 normal earnings match the twelve months' {d2(an["high"])}, the middle becomes about {d2(ttm_mid)} and the buy-below {d2(ttm_bb)} (calc.). The method follows results, a year late.</li>
<li>The cash readings carry growth capex with almost no growth. No filing splits upkeep from growth.</li>
<li>At 8% the buy-below is {d2(m.buy_below(m.combine(m.methods(.08))["mid"]))}. 9% has no source.</li>
<li>It may bar most good businesses. It was built on one company. Test it on another before trusting it.</li>
</ul></div>
<div class="pn"><div class="pt">It is too generous</div><ul class="notes" style="padding-left:16px;margin:4px 0">
<li>The middle uses FY2025, the best of ten years. FY2023 and FY2024 were $0.63 and $0.66 (<code>normal.html</code>). At the buy-below, the low of the range covers only {pc(base["low"] / bb)}.</li>
<li>FY2025 earnings hold ${credits}M of pre-tax 45X and 48D credits ({k25}), up to {d2(credit_eps)} a share (calc.). The after-tax amount is unknown. Without them the first row's middle is about {d2(credit_mid)}.</li>
<li>Ten-year free cash flow averaged ${fcf10:,.0f}M, or {d2(fcf10 / m.SHARES)} a share, under every starting reading used (calc., {k18}; {k25}).</li>
<li>The Aaa row asks nothing for risk, and it has 20% of the vote.</li>
<li>871M shares ignores the $2 billion share program, unsold through Sept. 30, 2026 ({q10}).</li>
</ul></div></div>

<h2>7. The rule change, saved Nov. 3, 2026</h2>
<p>You approved these edits and they are saved. "Before" is the old wording.</p>
<div class="lab"><code>Rules/when-to-buy.md</code>, first bullet. Before:</div>
<div class="prop was"><p><b>Recommend a buy only when the proven base value covers most of the price.</b></p></div>
<div class="lab">Now:</div>
<div class="prop"><p><b>Recommend a buy only when the proven base value covers at least 75% of the price.</b> Coverage is the middle of the base range ÷ the price. The buy-below price is that middle ÷ 0.75. Being under it is required, and it is not enough: a thesis and the skeptic's review still come first.</p></div>
<div class="lab"><code>Rules/when-to-buy.md</code>, third bullet. Before:</div>
<div class="prop was"><p><b>Until we build a valuation method together, say that base value is not defined yet and make no buy recommendation.</b> Do not choose a method yourself.</p></div>
<div class="lab">Now:</div>
<div class="prop"><p><b>Base value is worked out this way, and only this way:</b></p><ul>
<li><b>Earnings:</b> normal earnings on today's diluted shares. Low is the ten-year average, middle the last audited year, high the last twelve months.</li>
<li><b>Cash:</b> free cash flow with customer deposits out. Growth forever at no more than the company's own record, and never above 3%.</li>
<li><b>Votes:</b> 40% normal earnings ÷ 9%, 40% the cash sum at 9%, 20% normal earnings ÷ the Aaa yield.</li>
<li><b>No vote, always shown:</b> past multiples, rival multiples and the growth the price needs. Targets, unshipped deals and annualized quarters never count.</li>
<li><b>Refresh</b> after each 10-Q and 10-K. The 9% reopens if Aaa moves a point from 6.12%. Changing the method needs my approval. A new company needs its own check that the method fits.</li></ul></div>
<div class="lab"><code>Rules/when-to-trim.md</code>, second bullet. Now:</div>
<div class="prop"><p><b>Base value is defined in <code>when-to-buy</code>, and strategic value is not. Until we define it, say that value is not defined yet and make no trim recommendation based on value.</b> Flag the question to me instead. Do not choose a method yourself.</p></div>
<div class="lab"><code>Rules/skill-overrides.md</code>, item 5. Now:</div>
<div class="prop"><p><b>Price tests stay off except inside the method in <code>when-to-buy</code>.</b> No 22.5, price ceiling, 8.5 + 2g, net-net or bargain test, and no "price at which it qualifies" other than the buy-below price. A market-value size floor may run, because it uses the price as a size only.</p></div>
<p class="foot">Also changed: the 75% line in <code>Templates/Company.md</code>, the base value property and rule line in <code>Companies/Corning.md</code>, and the wording the dashboard and its test use for "not defined". <code>rules.md</code> and the six rules do not change. Older pages stay as dated records.</p>

<h2>8. What you approved</h2>
<ul class="notes">
<li><b>75% for "most".</b> A true cushion, as drawn on <code>margin-of-safety.html</code>, still starts only under {d2(base["mid"])}.</li>
<li><b>9%,</b> Aaa plus about three points. My judgment, with no source. It closes an item left open since <code>priced-in.html</code>.</li>
<li><b>The votes:</b> 40, 40, 20, and none for past tags, parts or the reverse sum.</li>
<li><b>The earnings:</b> ten-year, FY2025 and twelve months as low, middle and high, and the new {d2(an["high"])}.</li>
<li><b>The growth cap of 3%.</b></li>
</ul>
<p><b>What it does not say:</b> that Corning is overpriced, that it will fall, or that it would be a buy at {d2(bb)}. There is no thesis yet, and strategic value is still undefined, so trims stay barred. The Corning decision of Nov. 2 stands.</p>
<p class="foot"><b>Keep this page on this computer.</b> It uses Yahoo's price, and <code>sensors/prices/prices.py</code> says nothing built from it should be published. Written Nov. 3, 2026. The price is the Nov. 2 close, because the market was still open and the sensor asks Yahoo only once a day.</p>
</main><div id="tip" hidden></div>
<script>
const tip=document.getElementById('tip');
function show(e,t){{tip.innerHTML=t;tip.hidden=false;const r=tip.getBoundingClientRect();let x=e.clientX+14,y=e.clientY+14;if(x+r.width>innerWidth-8)x=e.clientX-r.width-14;if(y+r.height>innerHeight-8)y=e.clientY-r.height-14;tip.style.left=x+'px';tip.style.top=y+'px'}}
document.querySelectorAll('[data-tip]').forEach(n=>{{n.addEventListener('mousemove',e=>show(e,n.dataset.tip));n.addEventListener('mouseleave',()=>tip.hidden=true)}});
</script></body></html>
"""
(m.ROOT / "base.html").write_text(PAGE)
print("wrote base.html", len(PAGE))
