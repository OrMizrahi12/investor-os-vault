"""Draw edgar.html from the cache. This script makes no network requests.

Run from the project root, after edgar.py:
    uv run python sensors/edgar/draw.py

It stops if a fiscal year is missing or a number's form and date disagree with the filing list.
The check table is computed: it reads the printed statement tables in the cached 10-K,
not the XBRL tags, and compares them with the sensor's number.
"""

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FOLDER = HERE / "cache" / "CIK0000024741"
OUT = ROOT / "edgar.html"
CIK = 24741
YEARS = 10

MEASURES = [
    # Revenue changed tags in 2018, so it needs both. Later filings win.
    {"key": "revenue", "name": "Revenue", "concepts": ["Revenues", "SalesRevenueGoodsNet"], "color": "--s1"},
    {"key": "cash", "name": "Operating cash flow", "color": "--s3",
     "concepts": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]},
    {"key": "income", "name": "Net income", "concepts": ["NetIncomeLoss"], "color": "--s2"},
]

# Three numbers read from the printed statements, from three different 10-Ks.
CHECKS = [
    {"measure": "revenue", "year": 2025, "statement": "Consolidated Statements of Income", "row": r"Net sales",
     "why": "Newest year"},
    {"measure": "income", "year": 2017, "statement": "Consolidated Statements of Income", "row": r"Net income \(loss\) attributable to Corning Incorporated",
     "why": "The only loss, so it tests the sign"},
    {"measure": "cash", "year": 2016, "statement": "Consolidated Statements of Cash Flows", "row": r"Net cash provided by operating activities",
     "why": "Oldest year, and the one number that was restated"},
]

MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
e = html.escape


def stop(message):
    sys.exit(f"Stopped: {message}")


def nice_date(text):
    d = dt.date.fromisoformat(text[:10])
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def money(value):
    """$15,629M, or -$497M."""
    millions = value / 1_000_000
    if millions != int(millions):
        stop(f"{value} is not a whole number of millions.")
    return f"{'−' if millions < 0 else ''}${abs(int(millions)):,}M"


def billions(value):
    return f"{'−' if value < 0 else ''}${abs(value) / 1e9:.1f}B"


def read_jsonl(name):
    return [json.loads(line) for line in (FOLDER / name).read_text().splitlines()]


def full_year(row):
    if not row["start"]:
        return False
    days = (dt.date.fromisoformat(row["end"]) - dt.date.fromisoformat(row["start"])).days
    return 350 <= days <= 380


def build_series(facts, filings):
    """For each fiscal year and measure, take the number from the latest 10-K that reports it."""
    by_accession = {f["accession"]: f for f in filings}
    series = {}
    restated = []
    for m in MEASURES:
        # Period comes from the row's end date. SEC's "fy" field is the filing's year, not the period's.
        rows = [r for r in facts if r["taxonomy"] == "us-gaap" and r["concept"] in m["concepts"]
                and r["unit"] == "USD" and r["form"] == "10-K" and full_year(r)]
        years = {}
        for r in rows:
            years.setdefault(int(r["end"][:4]), []).append(r)
        series[m["key"]] = {}
        for year, group in years.items():
            group.sort(key=lambda r: (r["filed"], -m["concepts"].index(r["concept"])))
            chosen = group[-1]
            filing = by_accession.get(chosen["accession"])
            if not filing or (filing["form"], filing["filed"]) != (chosen["form"], chosen["filed"]):
                stop(f"{chosen['accession']} disagrees with the filing list.")
            series[m["key"]][year] = chosen
            if len({r["value"] for r in group}) > 1:
                restated.append((m, year, group))
    latest = min(max(values) for values in series.values())
    span = list(range(latest - YEARS + 1, latest + 1))
    for key, values in series.items():
        missing = [y for y in span if y not in values]
        if missing:
            stop(f"{key} has no 10-K number for {missing}.")
    restated = [r for r in restated if r[1] in span]
    return span, series, restated


# ---- Reading the printed statements ----

def clean(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    text = re.sub(r"[ ﻿‎​]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def table_rows(table_html):
    rows = []
    for tr in re.findall(r"<tr\b.*?</tr>", table_html, flags=re.S | re.I):
        cells = [clean(td) for td in re.findall(r"<td\b.*?</td>", tr, flags=re.S | re.I)]
        rows.append([c for c in cells if c and c not in ("$", ")", "%")])
    return [r for r in rows if r]


def parse_printed(cell):
    """'15,629' or '(497' or '(497)' to a number, with what was printed."""
    match = re.fullmatch(r"(\()?([\d,]+)\)?", cell.replace(" ", ""))
    if not match:
        return None
    number = int(match.group(2).replace(",", ""))
    return -number if match.group(1) else number


def read_statement(document, statement, row_pattern, year):
    """Find the statement's table, the row, and the column for that year. Returns what is printed."""
    source = (FOLDER / "documents" / document).read_text(errors="ignore")
    previous_start = 0
    for match in re.finditer(r"<table\b.*?</table>", source, flags=re.S | re.I):
        # Some filings put the title in a small table of its own, so look back through the last table too.
        before = clean(source[previous_start:match.start()])[-400:]
        previous_start = match.start()
        head = clean(match.group(0))[:300]
        # Filings can split a word across tags ("Statem ents"), so compare with the spaces removed.
        if statement.replace(" ", "").lower() not in (before + head).replace(" ", "").lower():
            continue
        rows = table_rows(match.group(0))
        for i, row in enumerate(rows):
            if not re.fullmatch(row_pattern, row[0], flags=re.I):
                continue
            header = next((rows[j] for j in range(i, -1, -1)
                           if sum(bool(re.fullmatch(r"20\d\d", c)) for c in rows[j]) >= 2), None)
            if not header:
                continue
            columns = [c for c in header if re.fullmatch(r"20\d\d", c)]
            values = [c for c in row[1:] if parse_printed(c) is not None]
            if str(year) not in columns or len(values) != len(columns):
                continue
            printed = values[columns.index(str(year))].replace(" ", "")
            unit = "millions" if re.search(r"in millions", clean(match.group(0))[:600] + before, flags=re.I) else None
            if not unit:
                stop(f"{document}: {statement} does not say it is in millions.")
            # Older filings end a page with a copyright line, newer ones with "57 Table of Contents".
            rest = clean(source[match.start():match.start() + 2_000_000])
            page = re.search(r"All Rights Reserved\.?\s*(\d+)|\b(\d+) Table of Contents", rest)
            return {"cell": printed if printed.count("(") == printed.count(")") else printed + ")",
                    "millions": parse_printed(printed), "columns": columns, "label": row[0],
                    "page": (page.group(1) or page.group(2)) if page else None}
    stop(f"{document}: could not find {row_pattern} for {year} in {statement}.")


def run_checks(series):
    measures = {m["key"]: m for m in MEASURES}
    results = []
    for check in CHECKS:
        fact = series[check["measure"]][check["year"]]
        document = fact["filing_url"].rsplit("/", 1)[-1]
        printed = read_statement(document, check["statement"], check["row"], check["year"])
        results.append({**check, "fact": fact, "printed": printed, "name": measures[check["measure"]]["name"],
                        "match": printed["millions"] * 1_000_000 == fact["value"]})
    return results


# ---- Drawing ----

W, H = 960, 440
LEFT, RIGHT, TOP, BOTTOM = 52, 214, 14, 34
Y_MIN, Y_MAX = -2e9, 18e9


def x_at(index):
    return LEFT + (W - LEFT - RIGHT) * index / (YEARS - 1)


def y_at(value):
    return TOP + (H - TOP - BOTTOM) * (Y_MAX - value) / (Y_MAX - Y_MIN)


def svg(span, series):
    parts = [f'<svg id="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Line chart of Corning revenue, '
             f'operating cash flow and net income, fiscal {span[0]} to {span[-1]}. All values are in the table below.">']
    for tick in range(0, 17, 4):
        y = y_at(tick * 1e9)
        parts.append(f'<line class="{"zero" if tick == 0 else "grid"}" x1="{LEFT}" x2="{W - RIGHT}" y1="{y:.1f}" y2="{y:.1f}"/>')
        parts.append(f'<text class="tick" x="{LEFT - 8}" y="{y + 4:.1f}" text-anchor="end">${tick}B</text>')
    for i, year in enumerate(span):
        parts.append(f'<text class="tick" x="{x_at(i):.1f}" y="{H - 12}" text-anchor="middle">{year}</text>')
    parts.append(f'<line id="cross" class="cross" x1="0" x2="0" y1="{TOP}" y2="{H - BOTTOM}" visibility="hidden"/>')

    for m in MEASURES:
        points = " ".join(f"{x_at(i):.1f},{y_at(series[m['key']][y]['value']):.1f}" for i, y in enumerate(span))
        parts.append(f'<polyline class="line" style="stroke:var({m["color"]})" points="{points}"/>')
        for i, y in enumerate(span):
            parts.append(f'<circle class="dot" style="fill:var({m["color"]})" cx="{x_at(i):.1f}" '
                         f'cy="{y_at(series[m["key"]][y]["value"]):.1f}" r="4"/>')
        last = series[m["key"]][span[-1]]["value"]
        parts.append(f'<text class="end" x="{W - RIGHT + 12}" y="{y_at(last) + 4:.1f}">{e(m["name"])}'
                     f'<tspan class="endv" dx="6">{billions(last)}</tspan></text>')

    def label(key, year, dy, anchor="middle", dx=0):
        value = series[key][year]["value"]
        x = x_at(span.index(year)) + dx
        parts.append(f'<text class="val" x="{x:.1f}" y="{y_at(value) + dy:.1f}" text-anchor="{anchor}">{billions(value)}</text>')

    label("revenue", span[0], -12)
    label("income", span[0], -7, "start", 9)
    label("income", 2017, 20)

    for i, year in enumerate(span):
        band = (W - LEFT - RIGHT) / (YEARS - 1)
        x = max(LEFT - 20, x_at(i) - band / 2)
        parts.append(f'<rect class="hit" data-i="{i}" tabindex="0" x="{x:.1f}" y="{TOP}" width="{band:.1f}" '
                     f'height="{H - TOP - BOTTOM}" aria-label="Fiscal {year} values"><title>Fiscal {year}</title></rect>')
    parts.append("</svg>")
    return "".join(parts)


def filing_link(fact, text=None):
    label = text or f"{fact['form']}, filed {nice_date(fact['filed'])}"
    return f'<a href="{e(fact["filing_url"], quote=True)}">{e(label)}</a>'


def data_table(span, series):
    rows = []
    for year in reversed(span):
        facts = {m["key"]: series[m["key"]][year] for m in MEASURES}
        accessions = {f["accession"]: f for f in facts.values()}
        sources = "<br>".join(f'{filing_link(f)}<br><code>{e(a)}</code>' for a, f in accessions.items())
        cells = "".join(f'<td class="num">{money(facts[m["key"]]["value"])}</td>' for m in MEASURES)
        rows.append(f'<tr><th scope="row">FY{year}</th>{cells}<td>{sources}</td></tr>')
    heads = "".join(f'<th scope="col" class="num">{e(m["name"])}</th>' for m in MEASURES)
    return f'<table><thead><tr><th scope="col">Year</th>{heads}<th scope="col">Form, filing date, accession</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'


def check_table(results):
    rows = []
    for r in results:
        f, p = r["fact"], r["printed"]
        where = f"{r['statement']}, row “{p['label']}”, {r['year']} column" + (f", page {p['page']}" if p["page"] else "")
        verdict = '<span class="ok">✓ Match</span>' if r["match"] else '<span class="bad">✗ No match</span>'
        rows.append(
            f'<tr><th scope="row">{e(r["name"])}, FY{r["year"]}<div class="why">{e(r["why"])}</div></th>'
            f'<td class="num">{money(f["value"])}<div class="why">Raw: {f["value"]:,}<br>Tag: {e(f["concept"])}</div></td>'
            f'<td class="num">{e(p["cell"])}<div class="why">in millions</div></td>'
            f'<td>{filing_link(f)}<br><code>{e(f["accession"])}</code><div class="why">{e(where)}</div></td>'
            f'<td>{verdict}</td></tr>')
    return ('<table><thead><tr><th scope="col">Number</th><th scope="col" class="num">Sensor, from XBRL</th>'
            '<th scope="col" class="num">Printed in the 10-K</th><th scope="col">Where to look</th><th scope="col">Result</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def restatement_notes(restated):
    notes = []
    for m, year, group in restated:
        seen = []
        for r in sorted(group, key=lambda r: r["filed"]):
            if not seen or seen[-1]["value"] != r["value"]:
                seen.append(r)
        path = "; then ".join(f'{money(r["value"])} in the {filing_link(r)}' for r in seen)
        notes.append(f'<li>{e(m["name"])}, FY{year}: {path}.</li>')
    return "".join(notes)


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--good:#0a7a52;--bad:#b3261e;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--good:#4fc99a;--bad:#f28b82;--s1:#3987e5;--s2:#d95926;--s3:#199e70}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--good:#4fc99a;--bad:#f28b82;--s1:#3987e5;--s2:#d95926;--s3:#199e70}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:24px;line-height:1.25;margin:0 0 8px;font-weight:650}
h2{font-size:17px;margin:32px 0 6px;font-weight:650}
p{margin:0 0 10px;max-width:75ch}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink-2);white-space:nowrap}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:16px 0}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:18px;height:2px;margin-right:7px;vertical-align:4px;border-radius:2px}
.plot{position:relative}.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:640px;height:auto;font:12px system-ui,-apple-system,"Segoe UI",sans-serif}
.grid{stroke:var(--grid)}.zero{stroke:var(--axis)}.cross{stroke:var(--axis)}
.tick{fill:var(--muted);font-size:12px}.val{fill:var(--ink-2);font-size:12px;font-variant-numeric:tabular-nums}
.end{fill:var(--ink);font-size:12.5px}.endv{fill:var(--ink-2);font-variant-numeric:tabular-nums}
.line{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.dot{stroke:var(--surface);stroke-width:2}
.hit{fill:transparent;outline:none;cursor:crosshair}.hit:focus-visible{fill:var(--border)}
#tip{position:absolute;z-index:2;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;min-width:210px;box-shadow:0 2px 10px rgba(0,0,0,.14)}
#tip[hidden]{display:none}#tip .h{font-weight:650;margin-bottom:4px}
#tip .r{display:flex;align-items:center;gap:7px}#tip .r b{font-weight:650;font-variant-numeric:tabular-nums}#tip .r span{color:var(--muted)}
#tip .s{margin-top:5px;color:var(--muted);font-size:11.5px}
figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:80ch}
.wrap{overflow-x:auto;margin-top:8px}
table{border-collapse:collapse;width:100%;min-width:820px;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:8px 14px 8px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650}tbody th{font-weight:600}
td{color:var(--ink-2)}.num{text-align:right;font-variant-numeric:tabular-nums}
.why{color:var(--muted);font-size:12.5px;font-weight:400;margin-top:2px;overflow-wrap:anywhere}
tbody th{min-width:150px}
.ok{color:var(--good);font-weight:650;white-space:nowrap}.bad{color:var(--bad);font-weight:650;white-space:nowrap}
ul.notes{margin:0 0 10px;padding-left:18px;max-width:75ch}ul.notes li{margin-bottom:6px}
.foot{color:var(--muted);font-size:13px}
"""

SCRIPT = """
(function(){
  var D=JSON.parse(document.getElementById('data').textContent);
  var svg=document.getElementById('chart'),cross=document.getElementById('cross'),tip=document.getElementById('tip'),plot=tip.parentNode;
  function line(text,cls,tag){var n=document.createElement(tag||'div');if(cls)n.className=cls;n.textContent=text;return n;}
  function show(i,rect){
    var y=D.years[i];cross.setAttribute('x1',y.x);cross.setAttribute('x2',y.x);cross.setAttribute('visibility','visible');
    tip.textContent='';tip.appendChild(line('FY'+y.year+', ended Dec. 31','h'));
    y.rows.forEach(function(r){var row=document.createElement('div');row.className='r';var k=document.createElement('i');k.className='key';k.style.margin='0';k.style.background='var('+r.color+')';row.appendChild(k);row.appendChild(line(r.value,'','b'));row.appendChild(line(r.name,'','span'));tip.appendChild(row);});
    y.sources.forEach(function(s){tip.appendChild(line(s,'s'));});
    tip.hidden=false;
    var scale=svg.getBoundingClientRect().width/D.width,sc=plot.querySelector('.scroll').scrollLeft;
    var px=y.x*scale-sc,w=tip.offsetWidth,room=plot.clientWidth;
    var left=px+14+w>room?px-14-w:px+14;
    tip.style.left=Math.max(0,left)+'px';tip.style.top='10px';
  }
  function hide(){tip.hidden=true;cross.setAttribute('visibility','hidden');}
  svg.querySelectorAll('.hit').forEach(function(r){
    var i=+r.getAttribute('data-i');
    r.addEventListener('pointerenter',function(){show(i);});
    r.addEventListener('pointermove',function(){show(i);});
    r.addEventListener('focus',function(){show(i);});
    r.addEventListener('blur',hide);
  });
  svg.addEventListener('pointerleave',hide);
})();
"""


def page(span, series, restated, results, manifest, profit):
    retrieved = nice_date(manifest["companyfacts.json"]["retrieved_utc"])
    get = lambda key, year: series[key][year]["value"]
    first, last = span[0], span[-1]
    growth = round((get("revenue", last) / get("revenue", first) - 1) * 100)
    beat = sum(get("cash", y) > get("income", y) for y in span)
    matches = sum(r["match"] for r in results)
    k25 = series["revenue"][2025]["filing_url"]
    original = "https://www.sec.gov/Archives/edgar/data/24741/000002474117000011/q4201610k.htm"
    fy17 = "https://www.sec.gov/Archives/edgar/data/24741/000002474118000010/glw-20171231x10k.htm"

    data = {"width": W, "years": [{
        "year": y, "x": round(x_at(i), 1),
        "rows": [{"name": m["name"], "color": m["color"], "value": money(series[m["key"]][y]["value"])} for m in MEASURES],
        "sources": sorted({f"{series[m['key']][y]['form']}, filed {nice_date(series[m['key']][y]['filed'])}" for m in MEASURES}
                          | {series[m["key"]][y]["accession"] for m in MEASURES}, reverse=True),
    } for i, y in enumerate(span)]}
    legend = "".join(f'<li><i class="key" style="background:var({m["color"]})"></i>{e(m["name"])}</li>' for m in MEASURES)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corning EDGAR History</title><style>{CSS}</style></head><body><main>
<h1>Corning: ten years from SEC data</h1>
<p class="lede">{matches} of {len(results)} checked numbers match the printed 10-K. Revenue grew {growth}% (calc.) from FY{first} to FY{last}. Operating cash flow beat net income in {beat} of {len(span)} years (calc.). The exception is FY2016, when net income included a $2.7 billion gain.</p>

<div class="card"><figure style="margin:0">
<ul class="legend">{legend}</ul>
<div class="plot"><div class="scroll">{svg(span, series)}</div><div id="tip" hidden></div></div>
<figcaption>Fiscal years ended Dec. 31, in billions of US dollars, GAAP. FY2026 is left out because it has not ended. Every number and its filing are in the table below.</figcaption>
</figure></div>

<h2>Three numbers checked against the 10-K</h2>
<p>The script read each number from the printed statement in the filing, not from its XBRL tag, and compared the two.</p>
<div class="wrap">{check_table(results)}</div>

<h2>Why the two big net income years stand out</h2>
<ul class="notes">
<li>FY2016 includes a $2.7 billion non-taxable gain on the realignment of Corning's stake in Dow Corning (<a href="{fy17}">10-K, filed Feb. 15, 2018</a>).</li>
<li>FY2017 is a loss. It includes the impact of the 2017 Tax Act: a provisional toll charge of $1.1 billion and a provisional re-measurement of deferred tax balances of $347 million (same 10-K, five-year table footnote).</li>
</ul>

<h2>One number was restated</h2>
<ul class="notes">{restatement_notes(restated)}</ul>
<p>The chart uses the later figure. In the FY2016 column, the later filing adds a financing line, “Payments of employee withholding tax on stock award”, of −$16M. “Accounts payable and other current liabilities” goes from $243M to $259M, and net cash used in financing goes from −$5,306M to −$5,322M (<a href="{original}">10-K, filed Feb. 6, 2017</a>; <a href="{fy17}">10-K, filed Feb. 15, 2018</a>). So $16M moved from financing to operating, and Corning's total cash did not change (calc.). That filing says only that “certain prior year amounts have been reclassified”.</p>

<h2>All {len(span) * 3} numbers and their filings</h2>
<div class="wrap">{data_table(span, series)}</div>

<h2>How to read these numbers</h2>
<ul class="notes">
<li><b>The source of each number is the latest 10-K that reports it.</b> So it may differ from the figure first filed for that year. Only the number above differs.</li>
<li><b>Net income</b> is the part attributable to Corning (tag <code>NetIncomeLoss</code>), as in the company note. It leaves out noncontrolling interests. Including them, FY2025 is {money(profit)}, from the same <a href="{k25}">10-K, filed Feb. 12, 2026</a>.</li>
<li><b>Revenue</b> is “Net sales”. SEC's data files it under <code>SalesRevenueGoodsNet</code> in filings through Feb. 15, 2018 and <code>Revenues</code> after that. The annual values agree where both exist.</li>
<li><b>This is history, not a measure of value.</b> Base value is not defined yet, so this page makes no buy recommendation.</li>
</ul>

<p class="foot">Sources: <a href="https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json">SEC company facts, retrieved {retrieved}</a>; <a href="https://data.sec.gov/submissions/CIK0000024741.json">EDGAR filing list, retrieved {retrieved}</a>; each filing linked above. Access rules: <a href="https://www.sec.gov/about/webmaster-frequently-asked-questions">SEC webmaster FAQ, reviewed Aug. 23, 2024</a>; <a href="https://www.sec.gov/about/developer-resources">SEC developer resources, reviewed March 10, 2025</a>. Calc.: {growth}% = {money(get("revenue", last))} ÷ {money(get("revenue", first))} − 1.</p>
</main>
<script type="application/json" id="data">{json.dumps(data).replace("</", "<\\/")}</script>
<script>{SCRIPT}</script></body></html>
"""


def main():
    facts = read_jsonl("facts.jsonl")
    filings = read_jsonl("filings.jsonl")
    manifest = json.loads((FOLDER / "manifest.json").read_text())
    span, series, restated = build_series(facts, filings)
    results = run_checks(series)
    profit = next(r["value"] for r in facts if r["concept"] == "ProfitLoss" and r["end"] == "2025-12-31"
                          and r["form"] == "10-K" and full_year(r))
    OUT.write_text(page(span, series, restated, results, manifest, profit))
    for r in results:
        print(f"{r['name']} FY{r['year']}: sensor {money(r['fact']['value'])}, 10-K prints {r['printed']['cell']} "
              f"(page {r['printed']['page']}), {'match' if r['match'] else 'NO MATCH'}")
    print(f"Wrote {OUT.name}: FY{span[0]} to FY{span[-1]}, {len(restated)} restated number(s).")


if __name__ == "__main__":
    main()
