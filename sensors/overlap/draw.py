#!/usr/bin/env python3
"""Build overlap.html: what five paper names share. Pulls nothing.

    .venv/bin/python -I sensors/overlap/draw.py

Reads cache/results.json and the map data inside graph.html. Keep the page on this computer: it rests on a copy of Yahoo's data.
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = json.loads((Path(__file__).resolve().parent / "cache/results.json").read_text())
G = json.loads(re.search(r'const D=(\{"nodes".*?\});?\n', (ROOT / "graph.html").read_text(), re.S).group(1).replace("<\\/", "</"))
TOK = (ROOT / "sensors/cash/tokens.css").read_text()
T = ["GLW", "APH", "AVGO", "NVDA", "VZ"]
NAME = dict(GLW="Corning", APH="Amphenol", AVGO="Broadcom", NVDA="NVIDIA", VZ="Verizon")
FOUR = T[:4]


def a(label, url):
    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'


NV_Q = a("10-Q, filed Aug. 26, 2026", "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm")
NV_K = a("10-K, filed Feb. 25, 2026", "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm")
AV_Q = a("10-Q, filed Sept. 10, 2026", "https://www.sec.gov/Archives/edgar/data/1730168/000173016826000080/avgo-20260802.htm")
AP_Q = a("10-Q, filed Oct. 30, 2026", "https://www.sec.gov/Archives/edgar/data/820313/000110465926120646/aph-20260930x10q.htm")
AP_K = a("10-K, filed Feb. 11, 2026", "https://www.sec.gov/Archives/edgar/data/820313/000110465926013549/aph-20251231x10k.htm")
AP_C = a("Amphenol Q3 call, Oct. 28, 2026, third-party transcript", "https://www.fool.com/earnings/call-transcripts/2026/10/28/amphenol-aph-q3-2026-earnings-call-transcript/")
VZ_Q = a("10-Q, filed Oct. 29, 2026", "https://www.sec.gov/Archives/edgar/data/732712/000073271226000052/vz-20260930.htm")
VZ_L = a("Light Reading, Sept. 8, 2026", "https://www.lightreading.com/data-centers/verizon-loads-up-on-corning-s-fiber-for-network-expansion-and-ai-infrastructure")
VZ_R = a("Verizon release, Sept. 8, 2026", "https://www.verizon.com/about/news/verizon-corning-broadband-ai-fiber-agreement")
GL_Q = a("10-Q, filed Oct. 29, 2026", "https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm")
GL_R = a("Q3 release, Oct. 27, 2026", "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm")
GL_C = a("Q3 call, Oct. 27, 2026, third-party transcript", "https://www.fool.com/earnings/call-transcripts/2026/10/27/corning-glw-q3-2026-earnings-call-transcript/")
GL_8 = a("8-K, May 6, 2026", "https://www.sec.gov/Archives/edgar/data/24741/000120677426000273/glw4631061-8k.htm")
BC_R = a("Corning release, May 13, 2025", "https://investor.corning.com/news-and-events/news/news-details/2025/Corning-Collaborates-with-Broadcom-To-Accelerate-AI-Data-Center-Processing-Capacity/default.aspx")
ME_P = a("Meta post, Jan. 27, 2026", "https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/")
AM_T = a("Telecompetitor, June 8, 2026", "https://www.telecompetitor.com/amazon-strikes-multibillion-dollar-fiber-deal-with-cor")
for e in G["edges"]:
    if e["a"] == "Corning" and e["b"] == "Amazon":
        AM_T = e["src"]
    if e["a"] == "Corning" and e["b"] == "AT&T":
        AT_S = e["src"]
    if e["a"] == "Corning" and e["b"] == "Lumen":
        LU_S = e["src"]
LR = a("Light Reading, Mar. 26, 2026", "https://www.lightreading.com/fttx/bead-winners-fret-over-fiber-costs-lead-times")
TTV = a("joint release on TelecomTV, Aug. 21, 2026", "https://www.telecomtv.com/content/next-gen-telco-infra/zayo-stays-ahead-of-ai-infrastructure-demand-through-long-term-fibre-supply-agreement-with-corning-56118/")
HF = a("public copy of Yahoo's data, updated Nov. 3, 2026", "https://huggingface.co/datasets/defeatbeta/yahoo-finance-data")
HF2 = a("second copy, updated May 21, 2026", "https://huggingface.co/datasets/finsaber-team/FINSABER-V2-Data")
YF = a("Yahoo through yfinance, fetched Nov. 2, 2026", "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d")


def day(iso):
    y, m, d = iso.split("-")
    mon = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."][int(m) - 1]
    return f"{mon} {int(d)}, {y}"


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def sgn(x, d=0):
    return f"{x * 100:+.{d}f}%".replace("-", "−")


def n2(x):
    return f"{x:.2f}".replace("-", "−")


risk = R["risk"]["daily"]
four_risk = sum(risk[t] for t in FOUR)
vz_risk = risk["VZ"]
res_four = sum(R["risk"]["residual"][t] for t in FOUR)
b = R["bets"]
ci = R["ci"]
P = R["pairs"]
falls = R["falls"]
qd = R["quiet_days"]
qc = R["quiet_by_cut"]
f22 = falls[0]

# ---------- exposure table: (key, row name, what kind, shared-by text, {ticker: (level, text)})
ROWS = [
 ("ai", "AI data center spending", "End market", "4 of 5", dict(
  GLW=("Part", f"Optical is 49.0% of Q3 sales (calc.), and the growth comes from Gen AI products. No carrier and enterprise split. {GL_Q}."),
  APH=("Part", f"IT datacom about 36% of 2025 sales, before CommScope ({AP_K}). \"Outsized\" growth and AI strength in Q3. No current share ({AP_Q})."),
  AVGO=("Heavy", f"Chips 70% of the quarter. $179.2B of firm orders, including custom AI accelerators. No AI share of revenue given. {AV_Q}."),
  NVDA=("Heavy", f"Data Center is 92.5% of the quarter's revenue (calc.). {NV_Q}."),
  VZ=("Small", f"Its fiber deal covers broadband and \"AI connections\" ({VZ_L}). The 10-Q never says \"data center\" (calc., word search, {VZ_Q})."))),
 ("buyers", "A few big buyers", "Customers", "3 of 5", dict(
  GLW=("Part", f"Meta up to $6B ({ME_P}), a ceiling. Amazon multibillion ({AM_T})."),
  APH=("Low", f"No customer at 10% or more, 2023 to 2025. {AP_K}."),
  AVGO=("Heavy", f"Top five about 50% of nine-month revenue, not named. {AV_Q}."),
  NVDA=("Heavy", f"Hyperscale 50.6% of the quarter (calc.). Three direct customers 16%, 15% and 13% of the half, not named. {NV_Q}."),
  VZ=("None", f"Consumer is 77.0% of Q3 revenue (calc.). {VZ_Q}."))),
 ("funding", "Who pays for the build", "Customer funding", "3 of 5", dict(
  GLW=("Part", f"A customer put down $1.0B, read as NVIDIA's ({GL_Q}, {GL_8}). The CFO says long-term deals fund most capital ({GL_C})."),
  APH=("None found", f"Its guarantees in the 10-Q are for its own debt. {AP_Q}."),
  AVGO=("Heavy", f"Backstop about $29B and possible customer notes up to $42B. Customers need \"significant capital\". {AV_Q}."),
  NVDA=("Heavy", f"$56B on AI cloud and third-party lease commitments, and $25B of equity commitments, including AI model makers. {NV_Q}."),
  VZ=("None found", f"No such line found. {VZ_Q}."))),
 ("corning", "Corning, on our graph", "Supplier", "5 of 5", dict(
  GLW=("Hub", f"The map was built from its notes: {G['stats']['links'] - G['stats']['off']} of {G['stats']['links']} links touch it. So being the center is partly how we drew it."),
  APH=("Reported", f"Bought its glass through CommScope. May have ended ({LR}). Also a named rival."),
  AVGO=("Small", f"Harnesses and connectors for one switch. No volume stated ({BC_R})."),
  NVDA=("Part", f"$1.0B deposit, $500M of warrants ({GL_Q}, {GL_8}). NVIDIA's own 10-Q never names Corning ({NV_Q})."),
  VZ=("Part", f"80M+ fiber miles, 2027 to 2032. No dollar figure ({VZ_R})."))),
 ("carrier", "Carrier fiber building", "End market", "4 of 5, mostly small", dict(
  GLW=("Part", f"AT&T more than $3B ({AT_S}), Verizon, Lumen."),
  APH=("Small", f"Communications networks about 10% of 2025 sales ({AP_K}), down 28% organically in Q3 ({AP_C})."),
  AVGO=("Small", f"\"Broadband access\" is one of many uses listed. No share. {AV_Q}."),
  NVDA=("None found", f"Only Zayo's 8,000+ mile plan, a target ({TTV})."),
  VZ=("Heavy", f"Bought Frontier for about $9.8B cash, fiber in 31 states. Nine-month capital spending $11,926M. {VZ_Q}."))),
 ("short", "A fiber shortage", "Same event, opposite sides (Claude's reading)", "Not a shared bet", dict(
  GLW=("Gains", f"Sells it. \"Things are tight\" ({GL_C})."),
  APH=("Both", f"Rival, and short of glass itself ({AP_C})."),
  AVGO=("Unknown", "Buys harnesses. Effect not stated."),
  NVDA=("Pays", f"Pays up front for capacity ({GL_Q})."),
  VZ=("Pays", f"Buys 80M+ miles at terms not disclosed ({VZ_R})."))),
 ("tsmc", "TSMC", "Supplier", "2 of 5", dict(
  GLW=("—", "Not in its 10-Q."), APH=("—", "Not in its 10-Q."),
  AVGO=("Heavy", f"About 95% of contract-made wafers. {AV_Q}."),
  NVDA=("Part", f"Wafers from TSMC and Samsung, no shares given. {NV_K}."),
  VZ=("—", "Not in its 10-Q."))),
 ("catalysts", "Catalyst notes", "How many notes link each", "One note on 4 of 5", dict(
  GLW=("40 of 40", "Catalysts/ was built for Corning."),
  APH=("2", "Optical scale-up and Photonics. Cut in AI spending."),
  AVGO=("2", "Optical scale-up and Photonics. Cut in AI spending."),
  NVDA=("3", "NVIDIA partnership and warrants. Three new plants with NVIDIA. Cut in AI spending."),
  VZ=("1", "Verizon fiber deal."))),
 ("market", "The stock market", "Move per 1 point of the market, ten years (calc.)", "5 of 5, sizing leaves it out", {t: (f"{R['beta'][t]:.2f}", "") for t in T}),
]
HI = {"Heavy", "Hub"}
MID = {"Part", "Reported", "Both", "Gains", "Pays"}


def cell(level, text):
    cls = "h" if level in HI else "m" if level in MID else "l"
    if level.replace(".", "").isdigit() or " of " in level:
        cls = "l"
    return f'<td class="c {cls}"><b>{level}</b>{" " + text if text else ""}</td>'


table_rows = "".join(
    f'<tr><th scope="row"><b>{name}</b><span>{kind}</span></th>' + "".join(cell(*cells[t]) for t in T) + f'<td class="sh">{share}</td></tr>'
    for key, name, kind, share, cells in ROWS)
head = "".join(f"<th scope=col>{NAME[t]}</th>" for t in T)

# ---------- graph data
F = [NAME[t] for t in T]
nodes = [dict(id=n["id"], x=n["x"], y=n["y"]) for n in G["nodes"]]
pos = {n["id"]: n for n in nodes}
lit = [dict(a=e["a"], b=e["b"], k=e["k"], what=e["what"], size=e["size"], ev=e["ev"]) for e in G["edges"]
       if (e["a"] in F and e["b"] in F) or ("Zayo" in (e["a"], e["b"]) and ("Corning" in (e["a"], e["b"]) or "NVIDIA" in (e["a"], e["b"])))]
dim = [dict(a=e["a"], b=e["b"]) for e in G["edges"] if not any(l["a"] == e["a"] and l["b"] == e["b"] and l["k"] == e["k"] for l in lit)]
assert len([l for l in lit if "Zayo" not in (l["a"], l["b"])]) == 6
EXPO = {
 "links": dict(label="Links in our graph", note="Solid lines are the links in our notes. Six run between the five, and every one of them touches Corning. Zayo is the one outside name tied to two of them. The dashed lines are links our notes tried and could not support."),
 "ai": dict(label="AI data center spending", hub="AI data center spending", to=dict(Corning=2, Amphenol=2, Broadcom=3, NVIDIA=3), note="Not a link in our graph. It comes from their filings. Thick means heavy, thin means part of the business. Verizon stays dark."),
 "funding": dict(label="Who pays for the build", hub="Customer funding", to=dict(Corning=2, Broadcom=3, NVIDIA=3), note="From filings. Three of them put money or guarantees behind customers' plans, or take customers' money for plants."),
 "tsmc": dict(label="TSMC", hub="TSMC", to=dict(Broadcom=3, NVIDIA=2), note="From filings. It sits inside the AI block, so it narrows that bet and adds no new one."),
 "carrier": dict(label="Carrier fiber", hub="Carrier fiber building", to=dict(Verizon=3, Corning=2, Amphenol=1, Broadcom=1), note="From filings and notes. This is the one exposure that reaches Verizon, and Verizon is the buyer here, so it sits on the other side from Corning."),
}
GD = json.dumps(dict(nodes=nodes, lit=lit, dim=dim, five=F, expo=EXPO), ensure_ascii=False).replace("</", "<\\/")

# ---------- charts
def heat(key, title, n):
    m = R["corr"][key]
    s = 34
    x0, y0 = 58, 26
    out = [f'<svg viewBox="0 0 {x0 + 5 * s + 4} {y0 + 5 * s + 4}" role="img" aria-label="{title}">']
    for i, t in enumerate(T):
        out.append(f'<text class="ax" x="{x0 + i * s + s / 2}" y="{y0 - 8}" text-anchor="middle">{t}</text><text class="ax" x="{x0 - 7}" y="{y0 + i * s + s / 2 + 4}" text-anchor="end">{t}</text>')
        for j in range(5):
            v = m[i][j]
            if i == j:
                out.append(f'<rect x="{x0 + j * s + 1}" y="{y0 + i * s + 1}" width="{s - 2}" height="{s - 2}" rx="3" fill="var(--grid)"/>')
                continue
            alpha = min(abs(v) / 0.8, 1)
            col = "--heat-pos" if v >= 0 else "--heat-neg"
            ink = "#fff" if alpha > .62 else "var(--ink)"
            out.append(f'<g data-tip="<b>{t} and {T[j]}</b>{n2(v)}"><rect x="{x0 + j * s + 1}" y="{y0 + i * s + 1}" width="{s - 2}" height="{s - 2}" rx="3" fill="var(--neutral)"/><rect x="{x0 + j * s + 1}" y="{y0 + i * s + 1}" width="{s - 2}" height="{s - 2}" rx="3" fill="var({col})" opacity="{alpha:.2f}"/><text x="{x0 + j * s + s / 2}" y="{y0 + i * s + s / 2 + 4}" text-anchor="middle" font-size="11" fill="{ink}">{n2(v)}</text></g>')
    out.append("</svg>")
    return f'<figure class="hm"><figcaption class="top"><b>{title}</b> {n}</figcaption>{"".join(out)}</figure>'


def bets_chart():
    rows = [
     ("Stocks needed for the same swing, ten years, daily", b["daily"]["same_swing"], ci["daily"]["same_swing"]),
     ("Same, last year", b["last1"]["same_swing"], ci["last1"]["same_swing"]),
     ("Same, ten years, monthly", b["monthly"]["same_swing"], None),
     ("Diversification ratio squared, ten years, daily", b["daily"]["ratio"], ci["daily"]["ratio"]),
     ("Same, last year", b["last1"]["ratio"], ci["last1"]["ratio"]),
     ("Eigenvalue count, ten years, daily", b["daily"]["eigen"], ci["daily"]["eigen"]),
     ("Same, last year", b["last1"]["eigen"], ci["last1"]["eigen"]),
     ("Same, ten years, monthly", b["monthly"]["eigen"], None),
    ]
    L, W, top, rh = 330, 860, 26, 27
    sx = lambda v: L + (v - 1) / 4 * (W - L - 24)
    h = top + rh * len(rows) + 10
    o = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="Eight price measures of how many real bets the five names are, from 1.87 to 3.42">']
    for v in range(1, 6):
        o.append(f'<line x1="{sx(v)}" x2="{sx(v)}" y1="{top - 6}" y2="{h - 6}" stroke="var(--grid)"/><text class="ax" x="{sx(v)}" y="{top - 12}" text-anchor="middle">{v}{" names" if v == 5 else ""}</text>')
    for i, (lab, v, c) in enumerate(rows):
        y = top + rh * i + 12
        o.append(f'<text class="lb" x="{L - 12}" y="{y + 4}" text-anchor="end">{lab}</text>')
        tip = f"<b>{lab}</b>{v:.2f}" + (f", range {c[0]:.2f} to {c[1]:.2f}" if c else "")
        o.append(f'<g data-tip="{tip}"><rect x="{L - 4}" y="{y - 12}" width="{W - L}" height="24" fill="transparent"/>')
        if c:
            o.append(f'<line x1="{sx(c[0])}" x2="{sx(c[1])}" y1="{y}" y2="{y}" stroke="var(--s1)" stroke-width="2" opacity=".45"/>')
        o.append(f'<circle cx="{sx(v)}" cy="{y}" r="5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/><text class="vl" x="{sx(v) + 11}" y="{y - 6}">{v:.2f}</text></g>')
    o.append("</svg>")
    return "".join(o)


def years_chart():
    Y = R["years"]
    L, W, top, H = 44, 860, 16, 250
    sx = lambda i: L + i / (len(Y) - 1) * (W - L - 118)
    sy = lambda v: top + (0.8 - v) / 1.2 * (H - top - 26)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Average daily correlation by year: the four AI names with each other, and Verizon with the four">']
    for v in (-.4, -.2, 0, .2, .4, .6, .8):
        o.append(f'<line x1="{L}" x2="{W - 118}" y1="{sy(v)}" y2="{sy(v)}" stroke="{"var(--axis)" if v == 0 else "var(--grid)"}"/><text class="ax" x="{L - 7}" y="{sy(v) + 4}" text-anchor="end">{n2(v).replace(".00", ".0") if v else "0"}</text>')
    for k, c, lab in (("four", "--s1", "The four with each other"), ("vz", "--s2", "Verizon with the four")):
        pts = " ".join(f"{sx(i):.1f},{sy(d[k]):.1f}" for i, d in enumerate(Y))
        o.append(f'<polyline points="{pts}" fill="none" stroke="var({c})" stroke-width="2" stroke-linejoin="round"/>')
        o.append(f'<text class="lb" x="{sx(len(Y) - 1) + 10}" y="{sy(Y[-1][k]) + 4}">{lab.split(" with")[0]}</text>')
        for i, d in enumerate(Y):
            o.append(f'<circle cx="{sx(i):.1f}" cy="{sy(d[k]):.1f}" r="4" fill="var({c})" stroke="var(--surface)" stroke-width="2"/>')
    for i, d in enumerate(Y):
        stub = " (to Nov. 2)" if d["year"] == 2026 else ""
        o.append(f'<g data-tip="<b>{d["year"]}{stub}</b>The four: {n2(d["four"])}<br>Verizon with them: {n2(d["vz"])}"><rect x="{sx(i) - 24:.1f}" y="{top}" width="48" height="{H - top - 26}" fill="transparent"/><text class="ax" x="{sx(i):.1f}" y="{H - 8}" text-anchor="middle">{d["year"]}</text></g>')
    o.append("</svg>")
    return "".join(o)


fall_rows = "".join(
    f'<tr><td>{day(f["peak"])} to {day(f["trough"])}</td><td class=n><b>{sgn(f["fall"], 1)}</b></td>' + "".join(f'<td class=n>{sgn(f["names"][t])}</td>' for t in T) + "</tr>" for f in falls)

GRID = [30, 50, 70, 90]
def floor1(x):
    return int(x * 10 + 1e-9) / 10
grid_rows = ""
for L in GRID:
    tot = floor1(500 / L)
    each = floor1(500 / L / 4)
    grid_rows += f'<tr><td class=n>{L}%</td><td class=n>{tot:.1f}%</td><td class=n>{each:.1f}%</td><td class=n>{80 * L / 100:.0f}%</td><td class=n>{80 * L / 100 / 5:.1f} times</td></tr>'

bar_money = [("GLW", 20), ("APH", 20), ("AVGO", 20), ("NVDA", 20), ("VZ", 20)]
def seg(c, w, t):
    return f'<div class="seg {c}" style="flex:{w} 1 0" data-tip="{html.escape(t, quote=True)}"><span>{t.split(":")[0]}</span></div>'
names_bar = "".join(seg("a" if t != "VZ" else "b", 20, f"{t}: 20% of the money") for t in T)
bets_bar = seg("a", 80, "AI data center bet: 80% of the money, four names") + seg("b", 20, "Verizon: 20% of the money, one name")
risk_bar = seg("a", four_risk * 100, f"AI data center bet: {pct(four_risk)} of the swing") + seg("b", vz_risk * 100, f"VZ: {pct(vz_risk)} of the swing")

CSS = """
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
p,ul.txt{margin:0 0 10px;max-width:75ch}ul.txt{padding-left:20px}ul.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
a{color:var(--link)}.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:80ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:6px}
.paper{display:inline-block;font-size:12.5px;color:var(--ink-2);border:1px solid var(--border);border-radius:6px;padding:2px 8px;margin-bottom:10px}
figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:85ch}figcaption.top{margin:0 0 4px;color:var(--ink-2)}figure{margin:0}
svg{display:block;width:100%;height:auto}svg .ax{font-size:11px;fill:var(--muted)}svg .lb{font-size:12px;fill:var(--ink-2)}svg .vl{font-size:11px;fill:var(--ink);font-weight:600}
.bars{display:grid;grid-template-columns:150px 1fr;gap:10px 12px;align-items:center}.bars>b{font-weight:600;font-size:13.5px}.bars small{display:block;color:var(--muted);font-weight:400;font-size:12px}
.bar{display:flex;gap:2px;height:34px}.seg{min-width:3px;display:flex;align-items:center;justify-content:center;font-size:12.5px;font-weight:600;color:#fff;overflow:hidden;white-space:nowrap}.seg:first-child{border-radius:4px 0 0 4px}.seg:last-child{border-radius:0 4px 4px 0}.seg.a{background:var(--s1)}.seg.b{background:var(--s2)}.seg.b span{padding:0 2px}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--ink-2);margin:0 0 10px}.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}.chips button{font:inherit;font-size:13px;color:var(--ink);background:transparent;border:1px solid var(--axis);border-radius:6px;padding:4px 10px;cursor:pointer}.chips button[aria-pressed=true]{background:var(--ink);color:var(--page);border-color:var(--ink)}
.wrap{overflow-x:auto;margin-top:8px}.g{min-width:700px}
table{border-collapse:collapse;font-size:13px;width:100%}th,td{padding:7px 8px;text-align:left;vertical-align:top;border-bottom:1px solid var(--grid)}thead th{font-size:12.5px;font-weight:650;border-bottom:1px solid var(--axis);white-space:nowrap}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
table.x{min-width:980px;font-size:12.5px}table.x tbody th{min-width:128px;font-weight:400}table.x tbody th b{display:block;font-weight:650}table.x tbody th span{color:var(--muted);font-size:11.5px}.c b{display:block;font-weight:650}.c.h{background:var(--c-h)}.c.m{background:var(--c-m)}.c.l{color:var(--ink-2)}.c.l b{color:var(--ink)}td.sh{font-weight:600;min-width:74px}
.hms{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}.hm svg{max-width:360px}
.quote{border-left:3px solid var(--s1);background:var(--tint2);padding:10px 14px;margin:8px 0;max-width:80ch}.quote p{margin:0 0 8px}.quote p:last-child{margin:0}.was{border-left-color:var(--axis);background:transparent;color:var(--ink-2)}
.tag{font-size:12px;font-weight:650;color:var(--muted);margin:12px 0 2px;text-transform:none}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.14);display:none}#tip b{display:block}
:root{--neutral:#f0efec;--heat-pos:#1c5cab;--heat-neg:#c8451b;--c-h:rgba(42,120,214,.20);--c-m:rgba(42,120,214,.08)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){--neutral:#383835;--heat-pos:#3987e5;--heat-neg:#d95926;--c-h:rgba(57,135,229,.30);--c-m:rgba(57,135,229,.12)}}
:root[data-theme="dark"]{--neutral:#383835;--heat-pos:#3987e5;--heat-neg:#d95926;--c-h:rgba(57,135,229,.30);--c-m:rgba(57,135,229,.12)}
@media (max-width:560px){.bars{grid-template-columns:1fr}.seg{font-size:11px}h1{font-size:23px}}
"""

JS = """
const D=/*G*/;
const S=document.getElementById('map'),NS='http://www.w3.org/2000/svg',P=Object.fromEntries(D.nodes.map(n=>[n.id,n]));
const tip=document.getElementById('tip');
function el(t,a,txt){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e}
const dimL=el('g',{}),nodeL=el('g',{}),litL=el('g',{}),hubL=el('g',{}),fiveL=el('g',{});
[dimL,nodeL,litL,hubL,fiveL].forEach(g=>S.appendChild(g));
D.dim.forEach(e=>{if(P[e.a]&&P[e.b])dimL.appendChild(el('line',{x1:P[e.a].x,y1:P[e.a].y,x2:P[e.b].x,y2:P[e.b].y,stroke:'var(--grid)','stroke-width':1}))});
D.nodes.forEach(n=>{if(D.five.includes(n.id))return;nodeL.appendChild(el('circle',{cx:n.x,cy:n.y,r:4,fill:'var(--axis)'}));nodeL.appendChild(el('text',{x:n.x,y:n.y+16,'text-anchor':'middle','font-size':11,fill:'var(--muted)'},n.id))});
const NOPE=[['Broadcom','NVIDIA','No source says they compete'],['Amphenol','NVIDIA','Its CEO would not name customers']];
function draw(key){
 litL.textContent='';hubL.textContent='';fiveL.textContent='';
 const x=D.expo[key];document.getElementById('mapnote').textContent=x.note;
 document.querySelectorAll('.chips button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.k===key));
 let on=new Set();
 if(key==='links'){
  D.five.forEach(n=>on.add(n));
  const seen={};
  D.lit.forEach(e=>{const pk=[e.a,e.b].sort().join();seen[pk]=(seen[pk]||0)+1;const off=(seen[pk]-1)*7;
   const A=P[e.a],B=P[e.b],dx=B.y-A.y,dy=A.x-B.x,L=Math.hypot(dx,dy)||1,ox=dx/L*off,oy=dy/L*off;
   const g=el('g',{'data-tip':`<b>${e.a} and ${e.b}: ${e.k}</b>${e.what.slice(0,190)}${e.what.length>190?'…':''}<br>Size: ${e.size}<br>Evidence: ${e.ev}`});
   g.appendChild(el('line',{x1:A.x+ox,y1:A.y+oy,x2:B.x+ox,y2:B.y+oy,stroke:'transparent','stroke-width':16}));
   g.appendChild(el('line',{x1:A.x+ox,y1:A.y+oy,x2:B.x+ox,y2:B.y+oy,stroke:'var(--s1)','stroke-width':2.5}));
   litL.appendChild(g)});
  NOPE.forEach(([a,b,w])=>{const g=el('g',{'data-tip':`<b>${a} and ${b}: no link</b>${w}`});
   g.appendChild(el('line',{x1:P[a].x,y1:P[a].y,x2:P[b].x,y2:P[b].y,stroke:'transparent','stroke-width':14}));
   g.appendChild(el('line',{x1:P[a].x,y1:P[a].y,x2:P[b].x,y2:P[b].y,stroke:'var(--muted)','stroke-width':1.5,'stroke-dasharray':'5 5'}));litL.appendChild(g)});
  P.Zayo&&litL.appendChild(el('circle',{cx:P.Zayo.x,cy:P.Zayo.y,r:7,fill:'var(--s1)',stroke:'var(--surface)','stroke-width':2}));
 }else{
  const hx=640,hy=232;
  Object.entries(x.to).forEach(([n,w])=>{on.add(n);litL.appendChild(el('line',{x1:hx,y1:hy,x2:P[n].x,y2:P[n].y,stroke:n==='Verizon'?'var(--s2)':'var(--s1)','stroke-width':w*1.8}))});
  const pad=x.hub.length*3.6+14;
  hubL.appendChild(el('rect',{x:hx-pad,y:hy-15,width:pad*2,height:30,rx:6,fill:'var(--ink)'}));
  hubL.appendChild(el('text',{x:hx,y:hy+5,'text-anchor':'middle','font-size':13,'font-weight':650,fill:'var(--page)'},x.hub));
 }
 D.five.forEach(n=>{const p=P[n],l=on.has(n),v=n==='Verizon';
  fiveL.appendChild(el('circle',{cx:p.x,cy:p.y,r:n==='Corning'?17:14,fill:l?(v?'var(--s2)':'var(--s1)'):'var(--surface)',stroke:l?'var(--surface)':'var(--axis)','stroke-width':2}));
  fiveL.appendChild(el('text',{x:p.x,y:p.y-(n==='Corning'?24:21),'text-anchor':'middle','font-size':14.5,'font-weight':650,fill:l?'var(--ink)':'var(--muted)'},n))});
}
const ch=document.querySelector('.chips');
Object.entries(D.expo).forEach(([k,v])=>{const b=document.createElement('button');b.type='button';b.dataset.k=k;b.textContent=v.label;b.onclick=()=>draw(k);ch.appendChild(b)});
draw('links');
document.addEventListener('pointermove',e=>{const t=e.target.closest&&e.target.closest('[data-tip]');if(!t){tip.style.display='none';return}
 tip.innerHTML=t.getAttribute('data-tip');tip.style.display='block';const w=tip.offsetWidth;tip.style.left=Math.max(6,Math.min(innerWidth-w-6,e.clientX+14))+'px';tip.style.top=Math.max(6,e.clientY-tip.offsetHeight-12)+'px'});
"""

PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Five Names, Two Bets</title><style>{TOK}{CSS}</style></head><body><main>
<span class="paper">Made-up paper portfolio. A lesson, not holdings, not picks and not a recommendation.</span>
<h1>Five names, about two real bets</h1>
<p class="lede">Corning, Amphenol, Broadcom, NVIDIA and Verizon, in equal parts. Written Nov. 3, 2026. Prices through {day(R['end'])}.</p>
<div class="answer"><ul>
<li><b>How many bets: about two, and they are far from equal.</b> Four names rest on one thing. Verizon is the other. The four are 80% of the money and {pct(four_risk)} of the portfolio's swing over ten years (calc.). Verizon is 20% of the money and {pct(vz_risk)} of the swing (calc.).</li>
<li><b>Biggest shared exposure: AI data center spending.</b> It is not on our graph. Our graph shows only Corning at the middle, because we built it from Corning.</li>
<li><b>What it means for the limit: the 5% stays, and the counting changes.</b> With each at the limit, four theses counted apart let one event cost 20% of the portfolio. Counted as one, 5% (calc.). `sizing` said one thesis shares one limit, but gave no test for "one thesis". <b>The owner approved a test on Nov. 3, 2026,</b> shown below.</li>
<li><b>This count is Claude's reading.</b> Only Corning has a written thesis. The other four have no thesis, kill lines or base value yet, so the count comes from their filings and prices.</li>
</ul></div>

<h2>Names against real bets</h2>
<p>Same five stocks, three ways to count them.</p>
<div class="card">
<div class="legend"><span><i style="background:var(--s1)"></i>AI data center bet</span><span><i style="background:var(--s2)"></i>Verizon</span></div>
<div class="bars">
<b>Names<small>What rule 2 counts: 5</small></b><div class="bar">{names_bar}</div>
<b>Money by bet<small>80% and 20%</small></b><div class="bar">{bets_bar}</div>
<b>Swing by bet<small>{pct(four_risk)} and {pct(vz_risk)} (calc.)</small></b><div class="bar">{risk_bar}</div>
</div>
<figcaption>Swing is each block's share of the portfolio's daily variance, Nov. 2016 to Nov. 2026, reset to equal parts daily (calc., {HF}). With the market taken out, the four's share is {pct(res_four)} and Verizon's slightly below zero (calc.), so this is not just the market. In the last year the four are {pct(sum(R['risk']['last1'][t] for t in FOUR))}, since Verizon moved against them (calc.).</figcaption>
</div>
<p><b>Prices alone say 1.9 to 3.4.</b> Each measure below asks how many unrelated stocks these five act like. All eight fall well short of five (calc.). They disagree on the middle, because the eigenvalue count treats each stock's own noise as a bet.</p>
<div class="card"><figure><div class="wrap"><div style="min-width:620px">{bets_chart()}</div></div><figcaption>Where shown, bars give the 5th to 95th percentile of {2000:,} resamples of 21-day blocks (calc.). The same-swing measure is the average stock's variance ÷ the portfolio's variance. No measure here can see a thesis, so the count of two comes from the business. Prices only fit with it.</figcaption></figure></div>

<h2>The five on the graph</h2>
<p>Pick an exposure. The gray map is all of `graph.html`, and it stays gray.</p>
<div class="card"><div class="chips"></div><p id="mapnote" style="margin:0 0 6px;color:var(--ink-2);font-size:13.5px;min-height:40px"></p>
<div class="wrap"><svg class="g" id="map" viewBox="40 20 1120 740" role="img" aria-label="Map of our graph with the five companies and their shared links lit"></svg></div>
<figcaption><b>Read this with care.</b> In our graph, these five share only Corning, and Zayo for NVIDIA. That is mostly how we built it. The notes could not support Broadcom against NVIDIA or Amphenol selling to NVIDIA. The filings read here name none of the other four: not NVIDIA's, Broadcom's, Amphenol's, Verizon's or Corning's latest 10-Q (calc., word search). No link is not the same as no overlap.</figcaption></div>

<h2>Each company against each shared exposure</h2>
<p>Each bold word is Claude's reading of the source beside it. Darker cells mean more of the business.</p>
<div class="card"><div class="wrap"><table class="x"><thead><tr><th>Exposure</th>{head}<th>Shared by</th></tr></thead><tbody>{table_rows}</tbody></table></div>
<figcaption>No shared named customer can be shown. NVIDIA and Broadcom name no customers, and Amphenol's CEO would not ({AP_C}). A cut in AI spending is the event that would hit four of the five. At the owner's request it now has a catalyst note, and Corning's claim C1 has kill line K9 (`Research/2026-11-03 Corning kill criteria.md`, Nov. 3, 2026). The other three have no thesis, so no line of their own.</figcaption></div>

<h2>How the prices moved</h2>
<ul class="txt">
<li><b>The four move together, and Verizon does not.</b> The average pair among the four is {n2(P['daily']['four'])}. Verizon with them is {n2(P['daily']['vz'])} (calc., ten years, daily).</li>
<li><b>The bad days show it.</b> All four fell on all {R['worst25']['all4_down']} of their 25 worst days, by {sgn(R['worst25']['four'], 1)} on average. Verizon rose on {R['worst25']['vz_up']} of them (calc.).</li>
<li><b>They can fall on their own.</b> The four fell 5% or more in a day, with the other {R['others']} stocks within 1%, on {len(qd)} days. All {len(qd)} came on or after {day(qd[0]['date'])} (calc.). At a 4% cut, {qc['0.04']['all'] - qc['0.04']['before_2024']} of {qc['0.04']['all']} came after 2023. So the shared bet looks recent, in prices at least. The causes were not looked up.</li>
<li><b>Verizon is not a dependable hedge.</b> With the four it was {n2(P['last1']['vz'])} in the last year, but {n2([y for y in R['years'] if y['year'] == 2020][0]['vz'])} in 2020. It fell {sgn(abs(f22['names']['VZ'])).replace('+', '')} in the 2022 fall (calc.).</li>
<li><b>Corning is the loosest of the four.</b> Corning with NVIDIA is {n2(R['corr']['daily'][0][3])} daily and {n2(R['corr']['monthly'][0][3])} monthly (calc.). Its past was not AI, so this says little about a thesis that now is. See the case against, below.</li>
</ul>
<div class="card"><div class="hms">{heat('daily', 'Ten years, daily', f"{R['days']:,} days")}{heat('last1', 'Last year, daily', f"{R['counts']['last1']} days")}{heat('monthly', 'Ten years, monthly', f"{R['counts']['monthly']} months")}</div>
<figcaption>Correlation of returns (calc., {HF}). 1 means they move in step, 0 means no relation. Blue is positive, orange negative. A 5-year test of a 5-year rule has only two separate samples in this data, so none is shown.</figcaption></div>
<div class="card"><figure><figcaption class="top"><b>Average daily correlation by year</b></figcaption>{years_chart()}<figcaption>Calc., same data. It swings from {n2(min(y['four'] for y in R['years']))} to {n2(max(y['four'] for y in R['years']))} with no steady trend, so a reading from one year is weak evidence. Both lines, as numbers, are in the hover labels.</figcaption></figure></div>
<div class="card"><figure><figcaption class="top"><b>The four's four largest falls, and what each stock did</b></figcaption><div class="wrap"><table><thead><tr><th>Peak to trough</th><th class=n>The four</th>{''.join(f'<th class=n>{t}</th>' for t in T)}</tr></thead><tbody>{fall_rows}</tbody></table></div>
<figcaption>Calc., same data, the four reset to equal parts daily. On 80% of a portfolio, the worst fall is {pct(abs(f22['fall']) * .8)} of the whole (calc.). That is a past price fall, not "loss if wrong", and no causes are named.</figcaption></figure></div>

<h2>What it means for the sizing limit</h2>
<ul class="txt">
<li><b>The limit was not too high. It was being counted by name.</b> Five positions counted apart can lose 5 × 5% = 25% if every thesis fails. Counted as two bets, 2 × 5% = 10% (calc.).</li>
<li><b>Equal parts cannot pass.</b> Alone, a 20% position fits the limit only if its loss if wrong is 25% or less. Four sharing a limit at 80% fit only if it is 6.25% or less (calc.: 5 ÷ 20, 5 ÷ 80).</li>
<li><b>Only Corning has a loss to test.</b> It is 88.6% (calc.: the $123.20 close of Nov. 2, 2026, {YF}, against base low $14.06, `sensors/valuation/runs/2026-11-03-01.md`). At 20% it would lose 17.7% of the portfolio by itself (calc.). The other four have no base value, so the table below is a grid and not an estimate.</li>
<li><b>This paper portfolio could not be built anyway.</b> Corning fails all three gates. The others have no thesis on file, so they fail the first. 20% each leaves no cash, under the 5% floor in `cash`.</li>
</ul>
<div class="card"><div class="wrap"><table style="max-width:720px"><thead><tr><th class=n>If the loss if wrong is</th><th class=n>All four together may be</th><th class=n>Each, split evenly</th><th class=n>The paper 80% would lose</th><th class=n>Against the 5% limit</th></tr></thead><tbody>{grid_rows}</tbody></table></div>
<figcaption>Calc. Loss on the 10-point grid `sizing` uses, sizes rounded down to 0.1%. A grid, not a forecast. Even split is only for the sum: the rule does not force an even split.</figcaption></div>
<p><b>The cost of counting honestly is cash.</b> With both at a 90% loss, two bets hold only 11.0% of the portfolio (calc.: 2 × 5.5%). The rest stays in cash. If that lasted 24 months, the alert in `cash` would ask whether the search is wide enough. That is the right question here: more real bets, not more names.</p>

<h2>The change to Rules/sizing.md</h2>
<p><b>Approved by the owner, Nov. 3, 2026, counting whole positions, and made.</b> The 5%, the caps, the gates, the five tests and alert-only all stay. So do `rules.md` and `my-rules.md`.</p>
<p class="tag">Before, under "The hard limit"</p>
<div class="quote was"><p>- Positions that rest on one thesis share one limit, because they fail together.</p></div>
<p class="tag">Now, in its place</p>
<div class="quote">
<p>- <b>Positions that rest on one thesis share one limit, because they fail together.</b> Add position × unrounded loss across them. The sum may not pass 5%.</p>
<p>- <b>The test for one thesis.</b> For each position, name the single event that would most surely break its thesis. If that event would also cross a kill line or break a load-bearing claim in another position's note, those positions rest on one thesis for that event. A position can sit in more than one such group, and each group has its own limit.</p>
<p>- <b>Count the whole position.</b> No discount for the share of sales that is exposed.</p>
<p>- <b>Same direction only.</b> An event that helps one and hurts the other does not join them. A market fall does not join them either, since this limit does not cover one.</p>
<p>- <b>Claude proposes the groups, with the event and its evidence, and I rule.</b> A group changes only on a dated event, never on a price move. Prices moving together can raise the question. They cannot answer it.</p>
<p>- <b>Each refresh shows names against bets:</b> the number of positions and the number of groups. It is a display. Rule 2 still counts positions.</p>
</div>
<p><b>Why this and not a correlation limit:</b> a rule set by prices moving together would break rule 6, and these numbers are not steady enough. Corning with NVIDIA gives {n2(R['corr']['daily'][0][3])} daily and {n2(R['corr']['monthly'][0][3])} monthly on the same ten years (calc.). Every group would change with the window.</p>
<p><b>Why the whole position and not a share:</b> it is simple, it fits "It counts the whole position", and the share can't be measured. Broadcom and Amphenol give no current AI share of sales. The cost is that it is strict on a business like Amphenol, with its other markets. The base low in the loss already keeps the proven part of a business, so the loss itself is not overstated by this.</p>
<p><b>Also changed:</b> the status line in `sizing`, `sizing.html`, `sensors/README.md`, `monitor.html` and the kill note.</p>

<h2>The strongest case against "two"</h2>
<ul class="txt">
<li><b>It could be three.</b> A thesis on Amphenol's industrial and defense connectors might survive a cut in AI spending. In 2025 IT datacom was only about 36% of sales ({AP_K}). Corning has glass, automotive and solar. A thesis written on those would stand apart. But Corning's draft thesis rests on data center fiber demand (`Research/2026-11-03 Corning thesis note.md`, Nov. 3, 2026).</li>
<li><b>Past prices say less for Corning.</b> Its link to NVIDIA is the weakest pair, and its Optical line, at 49.0% of Q3 sales (calc.), includes carrier work too.</li>
<li><b>It could be one.</b> Verizon carries {pct(vz_risk)} of the swing, and fell with the rest in 2020 and 2022. By risk this portfolio is close to one bet, and it counts as two only because Verizon's thesis would fail for different reasons.</li>
<li><b>The theses do not exist yet.</b> The test needs written kill lines, and four of the five have none. What was counted is what would likely fail together, not what a skeptic has tested.</li>
</ul>

<h2>What this does not say</h2>
<ul class="txt">
<li>That AI spending will fall, that any of these is cheap or dear, or that any should be bought or sold.</li>
<li>That the future will look like these ten years. All five survived it, and NVIDIA rose {R['multiple']['NVDA']:.0f} times (calc.), so these are winners picked afterward.</li>
<li>Why any price moved. No cause is sourced here.</li>
</ul>
<p style="font-size:13px;color:var(--muted)"><b>Data and checks.</b> Daily returns from a {HF}, already on this computer from `concentration.html`. Under the owner's Nov. 3 ruling, this page stays local. "The market" is the equal-weight average of the other {R['others']} stocks on the Nov. 2016 S&amp;P 500 list, not an index. Corning matches our own file ({YF}) within 0.11% over ten years (calc.). Against a {HF2}, through {R['check']['last']}, no day differs by over 2 points and no correlation by over {R['check']['corr_gap']:.3f}. Broadcom ends {pct(R['check']['ratio']['AVGO'] - 1, 0)} apart in total return, not traced, and it does not move these results (calc.). Filings are from SEC through `sensors/edgar`. Built by `sensors/overlap/`, checked by `test_overlap.py`.</p>
</main><div id="tip"></div><script>{JS.replace('/*G*/', GD)}</script></body></html>"""
PAGE = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", PAGE.split("<script>")[0]) + "<script>" + PAGE.split("<script>", 1)[1]
(ROOT / "overlap.html").write_text(PAGE)
print("written", len(PAGE))
