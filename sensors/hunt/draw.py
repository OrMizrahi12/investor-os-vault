"""Builds hunt-events.html from the two prompts in Playbooks/ and the runs saved in samples/. No network.
Run: .venv/bin/python -I sensors/hunt/draw.py   Keep the page on this computer: it holds a StockAnalysis price."""
import html
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SAMPLE = HERE / "samples"
e = html.escape
HUNT = json.loads((SAMPLE / "hunt-order.json").read_text())
HUNT_META = json.loads((SAMPLE / "hunt-meta.json").read_text())
R1, R2, R3 = ({k: json.loads((SAMPLE / r / f"{k}.json").read_text()) for k in ("order", "readings", "meta")} for r in ("replay-1", "replay-2", "replay-3"))
Y102 = [r for r in json.loads((SAMPLE / "two-years-102.json").read_text()) if r["company"] != "Corning"]
YEARS = json.loads((SAMPLE / "two-years.json").read_text())
SCOPE = [r for r in YEARS if r["company"] not in ("Corning", "Linde")]


def prompt(name):
    return re.search(r"```text\n(.*?)\n```", (ROOT / "Playbooks" / name).read_text(), re.S).group(1)


def nice(day):
    y, m, d = day.split("-")
    return f'{"Jan. Feb. Mar. Apr. May June July Aug. Sept. Oct. Nov. Dec.".split()[int(m) - 1]} {int(d)}, {y}'


def squeeze(text):
    return re.sub(r"\s+", " ", text).strip()


# ---- the funnel: every count comes from the saved run
sk, rk = HUNT["skipped"], HUNT["ranked"]
past1 = [t for t in HUNT["tested"] if t["gate1"]["state"] != "fail"]
ideas = HUNT["ideas"]
FUNNEL = [
    ("Rows on the screen", HUNT["rows"], f'{HUNT["hidden"]} more were hidden first by the radar, as possibly not new growth. {len(sk["unit slip"])} unit-slip row is apart.'),
    ("Companies", HUNT["companies"], "Some have rows on both quarter steps."),
    ("After the rejection log", HUNT["pool"], f'Off: {len(sk["rejection log"])} on the log, {len(sk["watchlist"])} on the watchlist, {len(sk["on our map"])} on our map.'),
    ("With a revenue figure", rk["ranked"], f'Off: {", ".join(squeeze(x) for x in rk["no_revenue"])}'.rstrip(".") + "."),
    ("Tested, top by rise ÷ revenue", len(HUNT["tested"]), f'{rk["looked_up"]} looked up to find them. Off: {len(rk["not_us"])} not US, and Powell, whose look-again month came but whose 10-K has not.'),
    ("Past Gate 1, the record", len(past1), "Akamai, CytomX, C4 Therapeutics and CoreWeave fell here."),
    ("Past Gate 2, base value against price", len(ideas), past1[0]["name"] + ": " + past1[0]["gate2"]["read"]),
    ("Ideas written to Inbox", len(ideas), "None this month. Gate 3 never runs here: it is yours."),
]
top = FUNNEL[0][1]
bars = "".join(
    f'<div class="fn"><div class="fl">{e(a)}</div><div class="ft"><span class="fb{" zero" if not n else ""}" style="width:{max(n / top * 100, 0.6):.1f}%"></span><b>{n}</b></div><div class="fd">{e(d)}</div></div>'
    for a, n, d in FUNNEL)

# ---- the walk: the real graph, one spoke per US filer
counts = {}
for r in SCOPE:
    counts[r["company"]] = counts.get(r["company"], 0) + 1
SPOKES = [("T1 Energy", "supplies, solar", True, "orange"), ("Lumen", "supplies, fiber", False, "blue"), ("AT&T", "supplies, fiber", False, "blue"), ("Verizon", "supplies, fiber", False, ""),
          ("Meta", "supplies, fiber", False, "seen"), ("Amazon", "supplies, fiber", False, ""), ("Microsoft", "partners, fiber", False, ""), ("NVIDIA", "supplies, partners, fiber", False, "seen"),
          ("Broadcom", "supplies, fiber", False, ""), ("Amphenol", "supplies, competes, fiber", True, "seen"), ("Apple", "supplies, cover glass", False, "")]
SPOKES[4] = ("Meta", "supplies, fiber", False, "")
W, H, CX, CY = 980, 560, 490, 280
parts = []
for i, (name, label, weak, mark) in enumerate(SPOKES):
    a = -math.pi / 2 + 2 * math.pi * i / len(SPOKES)
    x, y = CX + 395 * math.cos(a), CY + 225 * math.sin(a)
    ax, ay = CX + 72 * math.cos(a), CY + 46 * math.sin(a)
    cls = {"orange": "e-or", "blue": "e-bl"}.get(mark, "e-mute")
    dash = ' stroke-dasharray="6 5"' if weak else ""
    parts.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{ax:.0f}" y2="{ay:.0f}" class="{cls}"{dash} marker-end="url(#a-{mark if mark in ("orange", "blue") else "mute"})"/>')
    lx, ly = x + (CX - x) * 0.42, y + (CY - y) * 0.42
    tw = len(label) * 6.1 + 8
    parts.append(f'<rect x="{lx - tw / 2:.0f}" y="{ly - 9:.0f}" width="{tw:.0f}" height="17" class="lbg"/><text x="{lx:.0f}" y="{ly + 4:.0f}" text-anchor="middle" class="sm">{e(label)}</text>')
for i, (name, label, weak, mark) in enumerate(SPOKES):
    a = -math.pi / 2 + 2 * math.pi * i / len(SPOKES)
    x, y = CX + 395 * math.cos(a), CY + 225 * math.sin(a)
    cls = {"orange": "n-or", "blue": "n-bl"}.get(mark, "n")
    n = counts.get(name, 0)
    parts.append(f'<rect x="{x - 66:.0f}" y="{y - 23:.0f}" width="132" height="46" rx="7" class="{cls}"/><text x="{x:.0f}" y="{y - 4:.0f}" text-anchor="middle" class="nm">{e(name)}</text>'
                 f'<text x="{x:.0f}" y="{y + 13:.0f}" text-anchor="middle" class="sm">{n} Item 1.01{"" if n == 1 else "s"}</text>')
parts.append(f'<ellipse cx="{CX}" cy="{CY}" rx="70" ry="44" class="n-t"/><text x="{CX}" y="{CY - 3}" text-anchor="middle" class="nm">Corning</text><text x="{CX}" y="{CY + 14}" text-anchor="middle" class="sm">the only target</text>')
defs = "".join(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="m-{k}"/></marker>' for k in ("orange", "blue", "mute"))
claim = "The walk from each of the 12 US filers in the graph. All 11 others reach Corning, the only target, in one step."
GRAPH = f'<figure><div class="tw"><svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(claim)}" class="graph"><defs>{defs}</defs>{"".join(parts)}</svg></div><figcaption><strong>Every arrow is one walk the event run takes when that company files an Item 1.01 or 1.02.</strong> On a narrow screen, scroll the picture sideways. Orange: T1\'s filing of July 30, 2026, which came back Orange. Blue: Lumen and AT&T on May 21, 2025, one deal and one alert, Info. Dashed: the graph marks that link weak. The count is each filer\'s Item 1.01s in two years, calc. Links: Typed links in <code>Companies/Corning.md</code>, written Nov. 3, 2026.</figcaption></figure>'

# ---- the replay
LEVEL = {"Orange": "chg", "Info": "info", "Red": "bad"}
rows = []
for run in (R2, R1):
    ev = {x["accession"]: x for x in run["order"]["events"]}
    for r in sorted(run["readings"], key=lambda x: {"Red": 0, "Orange": 1, "Info": 2}[x["level"]]):
        v = ev[r["accession"]]
        tie = " One alert with Lumen's." if r.get("same_event_as") and v["company"] != "Lumen" else (" One alert with AT&T's." if r.get("same_event_as") else "")
        rows.append(f'<tr><td class="nw">{nice(v["filed"])}</td><th scope="row">{e(v["company"])}</th><td>{", ".join(e(i) for i in v["items"])}</td><td><span class="pill {LEVEL[r["level"]]}">{r["level"]}, {r["rule"]}</span></td>'
                    f'<td>"{e(squeeze(r["quote"]))}" <a href="{e(v["url"])}">8-K, filed {nice(v["filed"])}</a>, {v["accession"]}.{e(tie)}</td></tr>')
T1 = next(x for x in R2["readings"] if x["level"] == "Orange")
T1E = next(x for x in R2["order"]["events"] if x["accession"] == T1["accession"])
items_2 = sum("2.03" in r["items"] for r in SCOPE)
days_n = len({r["day"] for r in SCOPE})
corning_named = sum("Corning" in r["hits"] for r in SCOPE)
cost = lambda m: f'${m["total_cost_usd"]:.2f}'
PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hunt and Events</title>
<style>
:root{{--page:#f9f9f7;--surface:#fcfcfb;--panel:#f0efea;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--blue:#2a78d6;--green:#12795f;--orange:#c94f1e;--red:#b3261e;--bar:#8a8880}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--blue:#6aa6ee;--green:#4fbb9a;--orange:#ee8a5c;--red:#ef8079;--bar:#77756e}}}}
:root[data-theme="dark"]{{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--blue:#6aa6ee;--green:#4fbb9a;--orange:#ee8a5c;--red:#ef8079;--bar:#77756e}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:30px;line-height:1.2;margin:0 0 10px;text-wrap:balance}}h2{{font-size:20px;margin:44px 0 10px}}h3{{font-size:15px;margin:20px 0 6px}}
p{{margin:0 0 10px;max-width:74ch}}.lead{{font-size:18px;color:var(--ink-2)}}.muted{{color:var(--muted);font-size:13px}}
a{{color:var(--blue);overflow-wrap:anywhere}}code{{font:13px ui-monospace,Menlo,Consolas,monospace;background:var(--panel);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}}
.tw{{overflow-x:auto}}table.d{{border-collapse:collapse;font-size:14.5px;width:100%}}table.d th,table.d td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}}table.d thead th{{color:var(--muted);font-weight:600}}table.d tbody th{{font-weight:500}}.nw{{white-space:nowrap}}td.n,th.n{{text-align:right!important;font-variant-numeric:tabular-nums}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}}.tile{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px}}.tile b{{display:block;font-size:24px;font-variant-numeric:tabular-nums;line-height:1.2}}.tile span{{font-size:13.5px;color:var(--ink-2)}}
.pill{{font-size:12px;font-weight:600;padding:1px 7px;border-radius:9px;white-space:nowrap}}.pill.chg{{color:var(--orange);border:1px solid var(--orange)}}.pill.info{{color:var(--muted);border:1px solid var(--axis)}}.pill.bad{{color:var(--red);border:1px solid var(--red)}}
.box{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin:10px 0}}.box.hot{{border-left:4px solid var(--orange)}}
ol.do{{padding-left:22px;max-width:78ch}}ol.do li{{margin-bottom:9px}}pre{{background:var(--panel);border-radius:8px;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:8px 0 0}}
button{{font:inherit;font-size:14px;padding:6px 12px;border:1px solid var(--axis);border-radius:6px;background:var(--surface);color:var(--ink);cursor:pointer}}details{{margin:10px 0}}details summary{{cursor:pointer;font-weight:600}}
.fn{{display:grid;grid-template-columns:230px 1fr;gap:2px 14px;padding:7px 0;border-bottom:1px solid var(--border)}}.fl{{font-size:14.5px;font-weight:500}}.ft{{display:flex;align-items:center;gap:8px}}.ft b{{font-variant-numeric:tabular-nums}}.fb{{display:block;height:16px;background:var(--bar);border-radius:0 4px 4px 0}}.fb.zero{{background:var(--axis)}}.fd{{grid-column:2;font-size:13px;color:var(--muted)}}
table.wide{{min-width:720px}}figure{{margin:14px 0}}figcaption{{font-size:13.5px;color:var(--ink-2);margin-top:8px;max-width:78ch}}svg.graph{{display:block;width:100%;min-width:760px;height:auto;color:var(--ink)}}
.sm{{font-size:12px;fill:var(--muted)}}.nm{{font-size:14px;font-weight:600;fill:currentColor}}.n,.n-or,.n-bl,.n-t{{fill:var(--surface);stroke:var(--axis);stroke-width:1.2}}.n-or{{stroke:var(--orange);stroke-width:2.4}}.n-bl{{stroke:var(--blue);stroke-width:2.4}}.n-t{{stroke:currentColor;stroke-width:2;fill:var(--panel)}}
.lbg{{fill:var(--page)}}.e-mute{{stroke:var(--axis);stroke-width:1.2}}.e-or{{stroke:var(--orange);stroke-width:2.4}}.e-bl{{stroke:var(--blue);stroke-width:2.4}}.m-mute{{fill:var(--axis)}}.m-orange{{fill:var(--orange)}}.m-blue{{fill:var(--blue)}}
@media (max-width:640px){{h1{{font-size:25px}}table.d{{font-size:13.5px}}table.d th,table.d td{{padding:6px 7px}}.fn{{grid-template-columns:1fr}}.fd{{grid-column:1}}}}
</style></head><body><main>
<h1>The hunt and the event run</h1>
<p class="lead"><strong>Both tasks are live in Desktop, on your report of Nov. 4, 2026. Their tests ran on scratch copies, not in Desktop. The event run watches items 1.01 and 1.02. On 11 real past filings it reaches one company, Corning: 1 Orange, 3 Reds that name no Corning deal, and the rest Info. This month's hunt writes no idea, because every lead tested fell at Gate 1 or Gate 2.</strong></p>
<p class="muted">Stays on this computer: it holds a StockAnalysis price. Built by <code>sensors/hunt/draw.py</code>. It recommends nothing. Corning stays no buy, and no note changed.</p>
<div class="tiles">
<div class="tile"><b>{len(HUNT["tested"])} of {rk["ranked"]}</b><span>ranked leads tested in the trial, as your pick rule says (calc.)</span></div>
<div class="tile"><b>{len(ideas)}</b><span>ideas the trial would have written to Inbox</span></div>
<div class="tile"><b>{len(SCOPE) + sum(r["alone"] for r in Y102)}</b><span>Item 1.01 or 1.02 8-Ks from the graph's other US filers in two years (calc.)</span></div>
<div class="tile"><b>{corning_named} of {len(SCOPE)}</b><span>Item 1.01s name Corning in the 8-K itself (calc.)</span></div>
</div>

<h2>The hunt funnel</h2>
<p><strong>{HUNT["rows"]} rows come down to {len(ideas)} ideas.</strong> A real run of the prompt on a copy, Nov. 4, 2026, on SEC data retrieved that day. It would test the next five next month, because a lead tested on this quarter's figures is not tested again.</p>
<div>{bars}</div>
<p class="muted" style="margin-top:8px">All counts calc., from <code>sensors/hunt/samples/hunt-order.json</code> and its report, <code>hunt-report.md</code> beside it. Screen: <a href="https://data.sec.gov/api/xbrl/frames/us-gaap/RevenueRemainingPerformanceObligation/USD/CY2026Q3I.json">SEC frames, retrieved Nov. 4, 2026</a>. Archrock's price: {e(past1[0]["gate2"]["price_source"]).replace("[", "").replace("](", " at ").replace(")", "")}. Its base is a proposal on reported earnings.</p>
<h3>Against what you sorted by hand</h3>
<p>Gate 1 gives the same fail or no-fail on all 15 companies triaged on Nov. 3, 2026. Two of the passes, Corning and Powell, come back open, because a figure could not be read, and an open test does not stop a lead. Gate 2's middle matches to the cent on Micron, GE Vernova, Quanta and Powell. It reads higher on Lockheed, $344.99 against $282.26, and Huntington Ingalls, $194.12 against $171.09. Lockheed's gap is growth: with no growth at the middle, the script's inputs give the hand figure, and the script takes the record, capped at 3%. Huntington's gap is only partly that, and I did not trace the rest. Both still fail (calc., <code>sensors/hunt/test_hunt.py</code>).</p>

<h2>The walk on the graph</h2>
<p><strong>Today the walk has one place to go.</strong> Only Corning has a thesis with kill lines, and the paper portfolio is empty. So who gets alerted is always Corning. What the walk adds is the path, and the reading decides the level. Every filer is one step away, so two-step walks have not run on real data, only in a test.</p>
{GRAPH}
<p class="muted"><strong>Left out:</strong> {e("; ".join(R2["order"]["left_out"]))}. Linde files 8-Ks but has no typed link and is incorporated in Ireland. Corning's own 8-Ks stay with the daily run, so one event gets one alert.</p>

<h2>The replay: who would have been alerted</h2>
<div class="box hot">
<p><span class="pill chg">Orange, O2</span> <strong>Corning, reached from T1 Energy in one step.</strong> {e(T1["says"])}</p>
<p>"{e(squeeze(T1["quote"]))}" <a href="{e(T1E["url"])}">8-K, filed {nice(T1E["filed"])}</a>, {T1E["accession"]}, items {", ".join(T1E["items"])}.</p>
<p class="muted">The line as the run wrote it. Claude's reading through the run, for you to correct. The filing names neither Corning nor wafers. Only the graph's Conditional link ties Phase 1 to Corning, so you may well drop this one.</p>
</div>
<p><strong>Read this first: it is a test with hindsight.</strong> This table is the eight Item 1.01 filings. The three Item 1.02 filings are in the next section. I marked these filings as new on a copy, and the unchanged prompt read them. The thesis and kill lines date from Nov. 3, 2026, after all of them. Nothing was held. With a draft thesis and no holding, even a Red would only reopen the draft. I chose the three in the second batch because they looked most likely to bear on a claim, so one Orange in eight is not a rate.</p>
<div class="tw"><table class="d wide"><thead><tr><th>Filed</th><th>Filer</th><th>Items</th><th>Level for Corning</th><th>Quote</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="muted">The script checked each quote against the saved filing, and <code>test_hunt.py</code> checks them again. The Lumen and AT&T filings make one alert, so eight readings gave seven alerts. No Red fired on these eight. A Red on a kill line or a claim, R1 or R2, has passed only on a made-up case in a test.</p>

<h2>Item 1.02: what it adds</h2>
<p><strong>You added it because a customer ending a deal is K2. Rules/alerts.md presumes a 1.02 with no 1.01 Red, and only you can drop it, so I kept that.</strong> In two years it adds {sum(r["alone"] for r in Y102)} filings, and all three would have been false Reds (calc., <code>samples/two-years-102.json</code>). None was a customer ending a deal. {len(Y102) - sum(r["alone"] for r in Y102)} more carry both items, so the run already saw them, and they stay Orange until read.</p>
<div class="tw"><table class="d wide"><thead><tr><th>Filed</th><th>Filer</th><th>Level for Corning</th><th>What ended</th></tr></thead><tbody>{"".join(f'<tr><td class="nw">{nice(next(v for v in R3["order"]["events"] if v["accession"] == r["accession"])["filed"])}</td><th scope="row">{e(next(v for v in R3["order"]["events"] if v["accession"] == r["accession"])["company"])}</th><td><span class="pill bad">Red, R3</span></td><td>{e(r["says"])} "{e(squeeze(r["quote"]))}" <a href="{e(next(v for v in R3["order"]["events"] if v["accession"] == r["accession"])["url"])}">8-K</a>, {r["accession"]}.</td></tr>' for r in R3["readings"])}</tbody></table></div>
<p>A real K2 has not fired: it passed only on a made-up case in a test. K2 also cannot fire from Zayo's filings, because Zayo is private. <strong>Your ruling, Nov. 4, 2026:</strong> R3's Red holds for these filers. That means about 1.5 Reds a year on filings that end no Corning deal, each asking for a same-day read (calc.).</p>

<h2>What this trigger still misses</h2>
<p><strong>The filings that really moved Corning's deals were neither item.</strong> You left 7.01 and 8.01 out, so this run alone misses these.</p>
<ul>
<li>T1 Energy announced its wafer deal with Corning under Item 8.01 (<a href="https://www.sec.gov/Archives/edgar/data/1992243/000121390025077036/ea0253426-8k_t1energy.htm">8-K, filed Aug. 15, 2025</a>).</li>
<li>Corning filed its NVIDIA deal under items 3.02 and 7.01 (<a href="https://www.sec.gov/Archives/edgar/data/24741/000120677426000273/glw4631061-8k.htm">8-K, filed May 6, 2026</a>). The daily run does catch that one.</li>
<li>Of the {len(SCOPE)} Item 1.01s, {items_2} also carry item 2.03, new debt, and they fell on {days_n} days in two years (calc., <a href="https://data.sec.gov/submissions/CIK0001992243.json">SEC filing lists, retrieved Nov. 4, 2026</a>, and the others in <code>samples/two-years.json</code>). T1 Energy has {counts["T1 Energy"]} and Lumen {counts["Lumen"]}. I read 8 in full through the run and searched the rest for words, so most of the {len(SCOPE)} have no level.</li>
<li>Corning's Meta deal first appeared in a filing under items 2.02 and 9.01 (<a href="https://www.sec.gov/Archives/edgar/data/24741/000002474126000034/glw-20251231xex99xq42025.htm">Q4 release, Jan. 28, 2026</a>). The daily run reads that one too.</li>
</ul>

<h2>How they were set up in Desktop</h2>
<p class="muted">Sources: <a href="https://code.claude.com/docs/en/desktop-scheduled-tasks">Desktop scheduled tasks docs, undated, retrieved Nov. 4, 2026</a>, and your own setup of the daily run. <strong>Not tried in Desktop.</strong></p>
<ol class="do">
<li><strong>The allow rules first.</strong> Open <code>~/.claude/settings.json</code> and add the two lines below to <code>permissions.allow</code>. I did not add them, because you asked me to merge only the last set. The StockAnalysis fetch rule is already there. Or skip this and answer "always allow" in step 5.<pre id="al">"Bash(.venv/bin/python sensors/hunt/hunt.py *)",
"Bash(.venv/bin/python sensors/hunt/events.py *)"</pre></li>
<li><strong>Event run.</strong> In the Code tab, click <strong>Scheduled</strong>, then <strong>New task</strong>. If it asks, choose <strong>Set up manually</strong>. Name: <code>event-run</code>. Paste the event prompt below. Under <strong>Advanced settings</strong>, turn on <strong>Only on this computer</strong>, and pick <code>/home/superposition/investor-os</code> as the local folder. Trigger: <strong>Weekdays</strong>, 8:30. In the box's toolbar, pick <strong>Accept edits</strong> and <strong>Opus</strong>. Click <strong>Create</strong>.</li>
<li><strong>Monthly hunt.</strong> <strong>New task</strong> again. Name: <code>monthly-hunt</code>. Paste the hunt prompt. Same switch, folder, mode and model. The form has no monthly choice, so pick <strong>Weekly</strong> for now and click <strong>Create</strong>.</li>
<li>On its detail page, click the pencil icon, set the schedule to <strong>Custom</strong>, and enter <code>30 11 15 * *</code>. That is 11:30 on the 15th of each month, so most 10-Qs are in. It sits clear of your 8:00, 10:00 and 10:30 tasks.</li>
<li><strong>Click Run now on each and watch.</strong> Answer any prompt with "always allow", and allow nothing else. <strong>These are real runs.</strong> The event run's first run sets today as its start and writes one line to the Journal. The hunt's first run writes a real report in <code>Research/</code>, may write ideas to <code>Inbox/</code>, and marks five leads as tested. To keep the five for the 15th, skip Run now on the hunt and read its first run on the day.</li>
<li><strong>Read the result in the files.</strong> Event run: the end of that day's Journal. Hunt: <code>Research/&lt;date&gt; Monthly hunt.md</code> and any <code>Inbox/&lt;date&gt; &lt;ticker&gt; idea.md</code>. Nothing notifies you of a Red or an Orange.</li>
</ol>
<p><strong>What Desktop's limits mean here.</strong> It has no filing trigger, so "when a company files" means the next weekday's 8:30 check. An 8-K can wait up to a day, longer over a weekend. A run skipped because the daily is still going loses nothing, since the next run takes everything new. A sleeping computer gets a catch-up only for a miss in the last seven days. A hunt missed for longer simply waits for the next 15th.</p>
<h3>The prompts</h3>
<details><summary>Event run. Replayed three times on a copy.</summary><p style="margin-top:8px"><button data-copy="ev">Copy the prompt</button></p><pre id="ev">{e(prompt("Event run.md"))}</pre></details>
<details><summary>Monthly hunt. Run twice on a copy.</summary><p style="margin-top:8px"><button data-copy="hn">Copy the prompt</button></p><pre id="hn">{e(prompt("Monthly hunt.md"))}</pre></details>

<h2>How they were tested</h2>
<div class="tw"><table class="d"><thead><tr><th>Run, on a scratch copy, Accept edits, Opus</th><th>Result</th><th class="n">Denied</th><th class="n">Time</th><th class="n">List price</th></tr></thead><tbody>
<tr><td>Event replay, 5 filings</td><td>Passed: 4 alerts, all Info. It ran <code>wc</code> and <code>ls</code> against the prompt's wording, and read most of a huge Journal, so I tightened the prompt and made the script do that search.</td><td class="n">0</td><td class="n">{R1["meta"]["duration_ms"] / 1000:.0f} s</td><td class="n">{cost(R1["meta"])}</td></tr>
<tr><td>Event replay, 3 filings, tighter prompt</td><td>Passed: 1 Orange, 2 Info. It ran one no-op <code>echo</code> against the prompt's wording and said so.</td><td class="n">0</td><td class="n">{R2["meta"]["duration_ms"] / 1000:.0f} s</td><td class="n">{cost(R2["meta"])}</td></tr>
<tr><td>Event run, quiet day</td><td>Passed: one Journal line, right after other runs, so the cache was warm. A cold start would cost more, and the daily's quiet test was $0.29.</td><td class="n">0</td><td class="n">8 s</td><td class="n">$0.02</td></tr>
<tr><td>Event replay, 3 Item 1.02 filings, on a fresh copy</td><td>Passed: 3 Red under R3, each saying what ended. It ran one read-only <code>grep</code> against the prompt's wording and said so. That makes three of three busy runs with a stray read-only command, so the wording does not stop it.</td><td class="n">0</td><td class="n">{R3["meta"]["duration_ms"] / 1000:.0f} s</td><td class="n">{cost(R3["meta"])}</td></tr>
<tr><td>Hunt, first run</td><td><strong>Exposed my bug.</strong> Archrock's falling record made the value script refuse, Gate 2 stayed open, and it reached Inbox as an idea. Fixed.</td><td class="n">0</td><td class="n">24 s</td><td class="n">$0.40</td></tr>
<tr><td>Hunt, on the fixed code</td><td>Passed: 0 ideas. <code>Companies/</code>, <code>Rules/</code>, <code>Portfolio/</code>, <code>Catalysts/</code> and the Rejection log had the same hash before and after the first hunt run.</td><td class="n">0</td><td class="n">{HUNT_META["duration_ms"] / 1000:.0f} s</td><td class="n">{cost(HUNT_META)}</td></tr>
</tbody></table></div>
<p class="muted">A plan does not bill list price, so these only show size, and all drew on your plan. <code>claude -p</code>, not Desktop. The hunt's write of a real idea ran only before the fix, and in a unit test after it. On a real month with an idea, no run has been seen on the final code.</p>

<h2>What waits on you</h2>
<ul>
<li><strong>Rejection log:</strong> your ruling: the hunt proposes lines, and you add them. A line you skip means that company is tested again when a new quarter puts it back on the screen.</li>
<li><strong><code>Rules/</code>:</strong> <code>Rules/alerts.md</code> and <code>Rules/memory.md</code> were updated on your yes, Nov. 4, 2026.</li>
<li><strong>Prices:</strong> Gate 2 opens one StockAnalysis page per lead that passes Gate 1. Its terms exempt AI agents that follow its robots.txt, and they allow short unchanged excerpts with the source named (<a href="https://stockanalysis.com/terms-of-use/">terms, updated Oct. 29, 2026, retrieved Nov. 4, 2026</a>). That is my reading of a tool's short quotes. Your Yahoo decision is untouched: neither run asks Yahoo.</li>
<li><strong>Claude's choices:</strong> a level rests on what the filing says, not on the link's distance. "US" means incorporated in the US. Micron's look-again month is typed in <code>sensors/hunt/settings.toml</code>, because the watchlist has no file. Aaa is typed there too, at 6.12%, and needs updating by hand.</li>
</ul>
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){{b.addEventListener('click',function(){{var t=document.getElementById(b.dataset.copy).textContent;var l=b.textContent;var done=function(){{b.textContent='Copied';setTimeout(function(){{b.textContent=l}},1500)}};if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done,function(){{b.textContent='Select the text below'}})}}else{{b.textContent='Select the text below'}}}})}});
</script>
</main></body></html>
"""
(ROOT / "hunt-events.html").write_text(PAGE)
print("hunt-events.html", len(PAGE))
