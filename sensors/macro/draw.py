"""Draw economy.html from local files. This script makes no network requests.

Run from the project root, after prices.py and any new FRED downloads:
    uv run python sensors/macro/draw.py

A FRED file not downloaded yet leaves its line off the page, and the page says so.
A file that fails its checks stops the script. Yahoo and Moody's data are for my personal use,
so keep this page on this computer.
"""

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE), str(HERE.parent / "prices")]
import earnings  # noqa: E402
import macro  # noqa: E402
import prices  # noqa: E402

FACTS = HERE.parent / "edgar" / "cache" / "CIK0000024741"
OUT = ROOT / "economy.html"
LEGAL = "https://fred.stlouisfed.org/legal/"
K_FY17 = "https://www.sec.gov/Archives/edgar/data/24741/000002474118000010/glw-20171231x10k.htm"
Q3_RELEASE = "https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm"
MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
NAMES = {"DGS10": "10-year Treasury", "AAA": "Moody's Aaa bonds", "CPI": "CPI, change over 12 months", "EY": "Corning earnings yield"}
COLORS = {"DGS10": "--s1", "AAA": "--s2", "CPI": "--s3", "EY": "--s4"}
e = html.escape


def nice_date(value):
    day = dt.date.fromisoformat(value[:10]) if isinstance(value, str) else value
    return f"{MONTHS[day.month - 1]} {day.day}, {day.year}"


def nice_month(day):
    return f"{MONTHS[day.month - 1]} {day.year}"


def pct(value, places=1):
    return "no data" if value is None else f"{'−' if value < 0 else ''}{abs(value):.{places}f}%"


def eps_text(value):
    return f"{'−' if value < 0 else ''}${abs(value):.2f}"


def link(url, text):
    return f'<a href="{e(url, quote=True)}">{e(text)}</a>'


# ---- Data ----

def month_key(day):
    return (day.year, day.month)


def build_months(start, end, lines, ey):
    """One row per month for the tooltips and tables. Daily series use the month's last value."""
    months = {}
    cursor = dt.date(start.year, start.month, 1)
    while month_key(cursor) <= month_key(end):
        months[month_key(cursor)] = {"day": cursor}
        cursor = (cursor + dt.timedelta(days=32)).replace(day=1)
    for key, rows in lines.items():
        for day, value in rows:
            if value is not None and month_key(day) in months:
                months[month_key(day)][key] = value
    for row in ey:
        day = dt.date.fromisoformat(row["date"])
        if month_key(day) in months:
            months[month_key(day)].update(EY=row["yield"], close=row["close"], eps=row["eps"], close_date=row["date"])
    return list(months.values())


def beat_count(months):
    """Months where the month-end earnings yield is above that month's average Aaa yield (calc.)."""
    both = [m for m in months if "EY" in m and "AAA" in m]
    return sum(m["EY"] > m["AAA"] for m in both), len(both)


def since_above(months):
    """The last month the earnings yield was above Aaa, and how many months it has been at or below (calc.)."""
    both = [m for m in months if "EY" in m and "AAA" in m]
    above = [i for i, m in enumerate(both) if m["EY"] > m["AAA"]]
    return (both[above[-1]]["day"], len(both) - 1 - above[-1]) if above else (None, len(both))


# ---- Drawing ----

W, H = 960, 420
LEFT, RIGHT, TOP, BOTTOM = 44, 196, 14, 30


def ticks(low, high):
    step = 2 if high - low <= 14 else 5
    first = int(low // step) * step
    last = -int(-high // step) * step
    return list(range(first, last + 1, step))


def chart(chart_id, label, start, end, series, months, notes=()):
    """series: [(key, [(date, value)])]. A missing value breaks the line. Nothing is filled in."""
    values = [v for _, rows in series for d, v in rows if v is not None and start <= d <= end]
    grid = ticks(min(0, min(values)), max(values))
    low, high = grid[0], grid[-1]
    span = (end - start).days

    def x(day):
        return LEFT + (W - LEFT - RIGHT) * (day - start).days / span

    def y(value):
        return TOP + (H - TOP - BOTTOM) * (high - value) / (high - low)

    parts = [f'<svg class="chart" id="{chart_id}" viewBox="0 0 {W} {H}" role="img" aria-label="{e(label, quote=True)}">']
    for tick in grid:
        cls = "zero" if tick == 0 else "grid"
        parts.append(f'<line class="{cls}" x1="{LEFT}" x2="{W - RIGHT}" y1="{y(tick):.1f}" y2="{y(tick):.1f}"/>')
        parts.append(f'<text class="tick" x="{LEFT - 8}" y="{y(tick) + 4:.1f}" text-anchor="end">{"−" if tick < 0 else ""}{abs(tick)}%</text>')
    for year in range(start.year + 1, end.year + 1):
        if (year - start.year) % 2 == 1:
            tick_x = x(dt.date(year, 1, 1))
            parts.append(f'<text class="tick" x="{tick_x:.1f}" y="{H - 10}" text-anchor="middle">{year}</text>')
    parts.append(f'<line class="cross" x1="0" x2="0" y1="{TOP}" y2="{H - BOTTOM}" visibility="hidden"/>')

    ends = []
    for key, rows in series:
        segment = []
        inside = [(d, v) for d, v in rows if start <= d <= end]
        for day, value in inside + [(None, None)]:
            if value is None:
                if len(segment) == 1:
                    parts.append(f'<circle style="fill:var({COLORS[key]})" cx="{segment[0].split(",")[0]}" cy="{segment[0].split(",")[1]}" r="2"/>')
                elif segment:
                    parts.append(f'<polyline class="line" style="stroke:var({COLORS[key]})" points="{" ".join(segment)}"/>')
                segment = []
            else:
                segment.append(f"{x(day):.1f},{y(value):.1f}")
        last = next((v for _, v in reversed(inside) if v is not None), None)
        ends.append({"y": y(last), "name": NAMES[key], "value": pct(last)})
    ends.sort(key=lambda item: item["y"])
    for i in range(1, len(ends)):
        ends[i]["y"] = max(ends[i]["y"], ends[i - 1]["y"] + 34)
    for item in ends:
        words = item["name"].split(",")[0]
        parts.append(f'<text class="end" x="{W - RIGHT + 10}" y="{item["y"]:.1f}">{e(words)}</text>'
                     f'<text class="endv" x="{W - RIGHT + 10}" y="{item["y"] + 15:.1f}">{item["value"]}</text>')
    for day, value, text, dx, dy, anchor in notes:
        parts.append(f'<text class="val" x="{x(day) + dx:.1f}" y="{y(value) + dy:.1f}" text-anchor="{anchor}">{e(text)}</text>')
    parts.append(f'<rect class="hit" tabindex="0" x="{LEFT}" y="{TOP}" width="{W - LEFT - RIGHT}" height="{H - TOP - BOTTOM}" '
                 f'aria-label="{e(label, quote=True)} Use the arrow keys to move by month."/>')
    parts.append("</svg>")
    keys = [key for key, _ in series]
    data = [{"x": round(x(max(m["day"], start).replace(day=15) if m["day"].replace(day=15) >= start else start), 1),
             "t": nice_month(m["day"]),
             "r": [[COLORS[k], pct(m.get(k)), NAMES[k]] for k in keys]} for m in months]
    return "".join(parts), data


def legend(keys):
    items = "".join(f'<li><i class="key" style="background:var({COLORS[k]})"></i>{e(NAMES[k])}</li>' for k in keys)
    return f'<ul class="legend">{items}</ul>'


def plot(svg_markup):
    return f'<div class="plot"><div class="scroll">{svg_markup}</div><div class="tip" hidden></div></div>'


def fred_source(s):
    day = dt.date.fromisoformat(s["last_value_date"])
    latest = nice_date(day) if s["frequency"] == "daily" else nice_month(day)
    return (f'{e(s["owner"])}, {e(s["title"])} [{e(s["id"])}], retrieved from FRED, Federal Reserve Bank of St. Louis, '
            f'{link(macro.page_url(s["id"]), "series page")}, downloaded {nice_date(s["downloaded_utc"])}, '
            f'latest value {latest}.')


def waiting_list(missing):
    items = "".join(f'<li>{link(macro.page_url(i), i)}: choose the longest range, then Download, CSV (data). '
                    f'Save as <code>sensors/macro/downloads/{i}.csv</code>.</li>' for i in missing)
    return (f'<ol class="notes">{items}</ol><p>Then run <code>uv run python sensors/macro/draw.py</code>. '
            f'I download by hand because of <a href="{LEGAL}">FRED\'s terms, undated, retrieved Nov. 2, 2026</a>.</p>')


def steps_table(steps, first_day):
    rows = []
    for s in reversed(steps):
        if s["form"] == "10-K":
            how = f'{eps_text(s["eps"])} for the full year'
        else:
            how = (f'{eps_text(s["full_year"])} + {eps_text(s["ytd"])} − {eps_text(s["ytd_prior"])} '
                   f'(<a href="{e(s["full_year_filing"]["url"], quote=True)}">10-K, filed {nice_date(s["full_year_filing"]["filed"])}</a>)')
        close = f'${s["first_close"]:.2f}' if s.get("first_close") else "—"
        yld = pct(s["first_yield"]) if s.get("first_yield") is not None else "—"
        rows.append(f'<tr><th scope="row">{nice_date(s["period_end"])}</th>'
                    f'<td><a href="{e(s["url"], quote=True)}">{s["form"]}, filed {nice_date(s["filed"])}</a><br><code>{e(s["accession"])}</code></td>'
                    f'<td class="num">{eps_text(s["eps"])}</td><td>{how}</td><td class="num">{close}</td><td class="num">{yld}</td></tr>')
    return ('<table><thead><tr><th scope="col">Period ended</th><th scope="col">Filing</th><th scope="col" class="num">Trailing EPS (calc.)</th>'
            '<th scope="col">How (last full year + this year to date − last year to date)</th>'
            '<th scope="col" class="num">Close, first day on file</th><th scope="col" class="num">Yield then (calc.)</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def year_table(months):
    picks = [m for m in months if m["day"].month == 12] + [m for m in months[-1:] if m["day"].month != 12]
    rows = []
    for m in reversed(picks):
        cells = "".join(f'<td class="num">{pct(m.get(k))}</td>' for k in ("DGS10", "AAA", "CPI", "EY"))
        rows.append(f'<tr><th scope="row">{nice_month(m["day"])}</th>{cells}</tr>')
    heads = "".join(f'<th scope="col" class="num">{e(NAMES[k])}</th>' for k in ("DGS10", "AAA", "CPI", "EY"))
    return f'<table><thead><tr><th scope="col">Month</th>{heads}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#6250d6}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#9085e9}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#9085e9}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:24px;line-height:1.25;margin:0 0 8px;font-weight:650}
h2{font-size:17px;margin:32px 0 6px;font-weight:650}
p{margin:0 0 10px;max-width:75ch}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink-2);overflow-wrap:anywhere}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:16px 0}
.card h2{margin-top:0}
figure{margin:0}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:18px;height:2px;margin-right:7px;vertical-align:4px;border-radius:2px}
.plot{position:relative}.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:640px;height:auto;font:12px system-ui,-apple-system,"Segoe UI",sans-serif}
.grid{stroke:var(--grid)}.zero{stroke:var(--axis)}.cross{stroke:var(--axis)}
.tick{fill:var(--muted);font-size:12px}.val{fill:var(--ink-2);font-size:12px}
.end{fill:var(--ink);font-size:12.5px}.endv{fill:var(--ink-2);font-size:12.5px;font-variant-numeric:tabular-nums}
.line{fill:none;stroke-width:1.5;stroke-linejoin:round;stroke-linecap:round}
.hit{fill:transparent;outline:none;cursor:crosshair}.hit:focus-visible{stroke:var(--axis)}
.tip{position:absolute;z-index:2;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;min-width:210px;box-shadow:0 2px 10px rgba(0,0,0,.14)}
.tip[hidden]{display:none}.tip .h{font-weight:650;margin-bottom:4px}
.tip .r{display:flex;align-items:center;gap:7px}.tip .r b{font-weight:650;font-variant-numeric:tabular-nums}.tip .r span{color:var(--muted)}
figcaption{margin-top:10px;color:var(--muted);font-size:13px;max-width:85ch}figcaption p{margin:0 0 6px;max-width:none}
.wrap{overflow-x:auto;margin-top:8px}
table{border-collapse:collapse;width:100%;min-width:720px;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:8px 14px 8px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650}tbody th{font-weight:600;white-space:nowrap}
td{color:var(--ink-2)}.num{text-align:right;font-variant-numeric:tabular-nums}
ul.notes,ol.notes{margin:0 0 10px;padding-left:20px;max-width:75ch}.notes li{margin-bottom:6px}
details{margin-top:8px}summary{cursor:pointer;font-weight:600}
.foot{color:var(--muted);font-size:13px}
"""

SCRIPT = """
(function(){
  var D=JSON.parse(document.getElementById('data').textContent);
  function div(text,cls,tag){var n=document.createElement(tag||'div');if(cls)n.className=cls;n.textContent=text;return n;}
  document.querySelectorAll('svg.chart').forEach(function(svg){
    var months=D[svg.id],cross=svg.querySelector('.cross'),hit=svg.querySelector('.hit'),plot=svg.closest('.plot'),tip=plot.querySelector('.tip'),now=months.length-1;
    function show(i){
      now=Math.max(0,Math.min(months.length-1,i));var m=months[now];
      cross.setAttribute('x1',m.x);cross.setAttribute('x2',m.x);cross.setAttribute('visibility','visible');
      tip.textContent='';tip.appendChild(div(m.t,'h'));
      m.r.forEach(function(r){var row=div('','r'),k=div('','key','i');k.style.margin='0';k.style.background='var('+r[0]+')';row.appendChild(k);row.appendChild(div(r[1],'','b'));row.appendChild(div(r[2],'','span'));tip.appendChild(row);});
      tip.hidden=false;
      var scale=svg.getBoundingClientRect().width/D.width,px=m.x*scale-plot.querySelector('.scroll').scrollLeft,w=tip.offsetWidth;
      tip.style.left=Math.max(0,px+14+w>plot.clientWidth?px-14-w:px+14)+'px';tip.style.top='10px';
    }
    function hide(){tip.hidden=true;cross.setAttribute('visibility','hidden');}
    function nearest(x){var best=0;months.forEach(function(m,i){if(Math.abs(m.x-x)<Math.abs(months[best].x-x))best=i;});return best;}
    hit.addEventListener('pointermove',function(ev){var b=svg.getBoundingClientRect();show(nearest((ev.clientX-b.left)*D.width/b.width));});
    hit.addEventListener('pointerleave',hide);hit.addEventListener('focus',function(){show(now);});hit.addEventListener('blur',hide);
    hit.addEventListener('keydown',function(ev){if(ev.key==='ArrowLeft'){show(now-1);ev.preventDefault();}if(ev.key==='ArrowRight'){show(now+1);ev.preventDefault();}});
  });
})();
"""


def page(start, end, found, price_entry, facts_date, steps, ey, months):
    latest = ey[-1]
    step = steps[-1]
    aaa, dgs, cpi = found["AAA"], found["DGS10"], found["CPIAUCSL"]
    missing = [i for i, s in found.items() if s is None]
    aaa_rows = aaa["rows"] if aaa else None
    last_aaa = next(((d, v) for d, v in reversed(aaa_rows) if v is not None), None) if aaa else None
    daily_ey = [(dt.date.fromisoformat(r["date"]), r["yield"]) for r in ey]
    mid = lambda rows: [(d.replace(day=15), v) for d, v in rows]  # a monthly value belongs to the whole month

    # Second chart.
    series2 = [("EY", daily_ey)] + ([("AAA", mid(aaa_rows))] if aaa else [])
    low_row = min(ey, key=lambda r: r["yield"])
    gain = max((r for r in ey if "2017-02-06" <= r["date"] <= "2017-10-25"), key=lambda r: r["yield"])
    notes = [(dt.date.fromisoformat(gain["date"]), gain["yield"], "Includes the FY2016 gain", 0, -8, "middle"),
             (dt.date.fromisoformat(low_row["date"]), low_row["yield"], "Trailing loss, after the 2017 Tax Act", 0, 16, "middle")]
    svg2, data2 = chart("yieldchart", "Line chart of Corning's earnings yield against Moody's Aaa yield. Values are in the tables below.",
                        start, end, series2, months, notes)

    # Lede.
    close = latest["close"]
    calc = f'{eps_text(latest["eps"])} ÷ ${close:.2f}'
    lede = (f'On {nice_date(latest["date"])}, Corning\'s earnings yield was <b>{pct(latest["yield"])}</b> (calc.: {calc}), '
            f'using diluted GAAP EPS for the 12 months to {nice_date(step["period_end"])}. ')
    if last_aaa:
        wins, total = beat_count(months)
        lede += (f'Moody\'s Aaa yield was <b>{pct(last_aaa[1], 2)}</b> for {nice_month(last_aaa[0])}. '
                 f'The earnings yield was above it at {wins} of {total} month-ends (calc.). ')
        when, since = since_above(months)
        if when and since:
            lede += f'The last was {nice_month(when)}, and the {since} month-ends since have been at or below it (calc.). '
    else:
        lede += "The Aaa line is waiting for your FRED download. "
    lede += "Base value is not defined yet, so this page makes no buy or trim recommendation."

    # First chart, or what it is waiting for.
    lines1 = []
    if dgs:
        lines1.append(("DGS10", dgs["rows"]))
    if aaa:
        lines1.append(("AAA", mid(aaa_rows)))
    cpi_change = earnings.cpi_yearly_change(cpi["rows"]) if cpi else None
    if cpi:
        lines1.append(("CPI", mid(cpi_change)))
    data = {"width": W, "yieldchart": data2}
    if lines1:
        svg1, data1 = chart("rateschart", "Line chart of the 10-year Treasury yield, Moody's Aaa yield and the 12-month change in CPI. Values are in the table below.",
                            start, end, lines1, months)
        data["rateschart"] = data1
        body1 = legend([k for k, _ in lines1]) + plot(svg1)
    else:
        body1 = ""
    wait1 = f'<p><b>Waiting for your download:</b> {", ".join(missing)}.</p>{waiting_list(missing)}' if missing else ""
    sources1 = "".join(f"<p>{fred_source(s)}</p>" for s in (dgs, aaa, cpi) if s)
    if cpi:
        sources1 += ('<p>Inflation is calc.: this month\'s CPI index ÷ the same month a year earlier − 1. '
                     'CPI is seasonally adjusted. A blank day or month in a FRED file stays a gap in the line.</p>')
    gaps = [nice_month(d) for d, v in cpi_change if v is None and d >= start] if cpi else []
    gap_note = f'<li><b>Inflation gaps:</b> {e(", ".join(gaps))}: no change can be computed, because CPI or its month a year earlier is blank in the FRED file. Nothing is filled in.</li>' if gaps else ""
    cap1 = sources1 or "<p>No FRED file has been downloaded yet.</p>"

    moodys = ('<p>Moody\'s Aaa data © Moody\'s Corporation, Moody\'s Investors Service, Inc., and Moody\'s Analytics, Inc. '
              'Moody\'s proprietary information, not to be copied or redistributed without its consent '
              f'({link(macro.page_url("AAA"), "FRED series notes, retrieved Nov. 2, 2026")}).</p>') if aaa else ""
    yahoo = (f'Close: Yahoo Finance through yfinance, not adjusted for dividends, fetched {nice_date(price_entry["started_utc"])}, '
             f'latest close {nice_date(price_entry["last"])}, for personal use only.')
    edgar = f'EPS: {link("https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json", f"SEC company facts, retrieved {nice_date(facts_date)}")}, with each filing listed below.'
    aaa_source = f"<p>{fred_source(aaa)}</p>" if aaa else '<p>Aaa line: not downloaded yet.</p>'
    table1 = f'<h2>The numbers behind the charts</h2><p>Each December, plus the latest month. Treasury and earnings yield are the month\'s last value. Aaa and CPI are monthly.</p><div class="wrap">{year_table(months)}</div>'

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rates and Corning</title><style>{CSS}</style></head><body><main>
<h1>Rates, inflation and Corning's earnings yield</h1>
<p class="lede">{lede}</p>

<div class="card"><figure>
<h2>Rates and inflation, {nice_month(start)} to {nice_month(end)}</h2>
{body1}{wait1}
<figcaption>{cap1}</figcaption>
</figure></div>

<div class="card"><figure>
<h2>Corning's earnings yield against the Aaa yield</h2>
{legend([k for k, _ in series2])}{plot(svg2)}
<figcaption><p>Earnings yield is calc.: trailing diluted GAAP EPS ÷ the day's close. {edgar}</p><p>{yahoo}</p>{aaa_source}{moodys}</figcaption>
</figure></div>

{table1}

<h2>How to read the comparison</h2>
<ul class="notes">
<li><b>This is not a valuation method.</b> A comparison of two yields does not define base value or value. <a href="Rules/when-to-buy.md">The buy rule</a> and <a href="Rules/when-to-trim.md">the trim rule</a> wait for the method we build together.</li>
<li><b>The two yields are different things.</b> Aaa is a yield on bonds with maturities of 20 years and above (<a href="{macro.page_url("AAA")}">FRED series notes, retrieved Nov. 2, 2026</a>). Earnings yield is not a payment: it is one year's reported profit per share against the price.</li>
<li><b>EPS is GAAP, with one-offs left in.</b> FY2016 includes a $2.7 billion non-taxable gain. FY2017 includes a provisional $1.1 billion toll charge and a provisional $347 million re-measurement of deferred tax balances from the 2017 Tax Act (<a href="{K_FY17}">10-K, filed Feb. 15, 2018</a>). Corning's core EPS is higher: $0.91 in Q3 2026 against $0.78 GAAP (<a href="{Q3_RELEASE}">Q3 release, Oct. 27, 2026</a>; <a href="{step["url"]}">10-Q, filed {nice_date(step["filed"])}</a>). Core is not used here.</li>
<li><b>Each day uses the EPS on file that day.</b> It changes on the 10-K or 10-Q filing date, using figures as first filed. Earnings releases often come a few days earlier.</li>
<li><b>Trailing EPS is approximate between 10-Ks.</b> EPS amounts from different periods do not add exactly, because share counts change.</li>
<li><b>The close is not adjusted for dividends.</b> Adjusted prices would lower old prices and overstate old yields. No split falls in this window.</li>
{gap_note}
</ul>

<h2>Every EPS step and its filing</h2>
<details><summary>{len(steps)} filings, newest first</summary><div class="wrap">{steps_table(steps, start)}</div></details>

<p class="foot" style="margin-top:24px">Keep this page on this computer. It holds Yahoo and Moody's data. FRED's rule: <a href="{LEGAL}">FRED terms, undated, retrieved Nov. 2, 2026</a>. Yahoo's rule: <a href="https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html">Yahoo terms, updated Nov. 1, 2026</a>, which bar automated collection without permission. The price fetch is my decision of Nov. 3, 2026.</p>
</main>
<script type="application/json" id="data">{json.dumps(data).replace("</", "<\\/")}</script>
<script>{SCRIPT}</script></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description="Draw economy.html from local files.")
    parser.add_argument("--downloads", default=macro.DOWNLOADS, help="folder with the FRED files")
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()
    try:
        rows, price_entry = prices.read_latest()
        end = dt.date.fromisoformat(price_entry["last"])
        start = macro.window_start(end)
        found = macro.read_all(args.downloads, end)
        if Path(args.downloads) == macro.DOWNLOADS:
            macro.update_manifest(found)
        facts = [json.loads(line) for line in (FACTS / "facts.jsonl").read_text().splitlines()]
        steps = earnings.steps_in_window(earnings.eps_steps(facts), start)
        ey = earnings.yield_series(rows, steps, start)
    except (macro.MacroError, prices.PriceError, earnings.EarningsError, OSError) as err:
        sys.exit(f"Stopped: {err}")
    for s in steps:
        first = next((r for r in ey if r["accession"] == s["accession"]), None)
        s["first_close"], s["first_yield"] = (first["close"], first["yield"]) if first else (None, None)
    lines = {}
    if found["DGS10"]:
        lines["DGS10"] = found["DGS10"]["rows"]
    if found["AAA"]:
        lines["AAA"] = found["AAA"]["rows"]
    if found["CPIAUCSL"]:
        lines["CPI"] = earnings.cpi_yearly_change(found["CPIAUCSL"]["rows"])
    months = build_months(start, end, lines, ey)
    facts_date = json.loads((FACTS / "manifest.json").read_text())["companyfacts.json"]["retrieved_utc"]
    Path(args.out).write_text(page(start, end, found, price_entry, facts_date, steps, ey, months))
    missing = [i for i, s in found.items() if s is None]
    print(f"Wrote {Path(args.out).name}: {start} to {end}. {len(steps)} EPS steps. "
          f"Latest yield {ey[-1]['yield']:.2f}% (calc.). FRED files missing: {missing or 'none'}.")


if __name__ == "__main__":
    main()
