"""Builds reviews.html from the two prompts in Playbooks/ and the dry run saved in samples/. No network.
Run: .venv/bin/python -I sensors/reviews/draw.py   Keep the page on this computer: it holds a Yahoo price."""
import calendar
import datetime as dt
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SAMPLE = HERE / "samples" / "dry-run"
R = json.loads((SAMPLE / "check.json").read_text())
META = json.loads((SAMPLE / "meta.json").read_text())
REPLAY = json.loads((SAMPLE / "replay.json").read_text())
e = html.escape


def prompt(name):
    return re.search(r"```text\n(.*?)\n```", (ROOT / "Playbooks" / name).read_text(), re.S).group(1)


# The year. Every date after today is an estimate.
START, END = dt.date(2026, 11, 3), dt.date(2027, 11, 2)
TEN_Q = {dt.date(2027, 4, 30): "Q1 2027 10-Q", dt.date(2027, 7, 29): "Q2 2027 10-Q", dt.date(2027, 10, 28): "Q3 2027 10-Q"}
TEN_K = {dt.date(2027, 2, 12): "FY2026 10-K"}
RESULTS = {dt.date(2027, 1, 28): "Q4 2026 results", dt.date(2027, 4, 27): "Q1 2027 results", dt.date(2027, 7, 27): "Q2 2027 results", dt.date(2027, 10, 26): "Q3 2027 results"}
CHECK_MONTHS = {2, 4, 5, 7, 8, 10, 11}


def days():
    d = START
    while d <= END:
        yield d
        d += dt.timedelta(days=1)


WEEKLY = [d for d in days() if d.weekday() == 0]
CHECKS = [d for d in days() if d.month in CHECK_MONTHS and d.weekday() in (1, 4)]
REAL = {}
for filed, name in {**TEN_K, **TEN_Q}.items():
    REAL[next(d for d in CHECKS if d > filed)] = name
QUIET = [d for d in CHECKS if d not in REAL]


def cell(d):
    if not START <= d <= END:
        return f'<td class="off">{d.day}</td>'
    cls, marks, tip = [], "", []
    if d in REAL:
        cls.append("real")
        tip.append(f"Quarterly refresh runs, on the {REAL[d]}")
    elif d in QUIET:
        marks += '<i class="tick"></i>'
        tip.append("Quarterly check: no new 10-Q, stops")
    if d in WEEKLY:
        marks += '<i class="dot"></i>'
        tip.append("Weekly thesis check")
    if d in TEN_Q:
        cls.append("q")
        tip.append(f"{TEN_Q[d]} filed, my estimate")
    if d in TEN_K:
        cls.append("k")
        tip.append(f"{TEN_K[d]} filed, my estimate")
    if d in RESULTS:
        cls.append("res")
        tip.append(f"{RESULTS[d]}, my estimate. The daily run reads it")
    t = f' title="{e("; ".join(tip))}"' if tip else ""
    return f'<td class="{" ".join(cls)}"{t}><span>{d.day}</span>{marks}</td>'


def month(y, m):
    rows = "".join("<tr>" + "".join(cell(d) if d.month == m else "<td></td>" for d in wk) + "</tr>" for wk in calendar.Calendar(0).monthdatescalendar(y, m))
    return f'<div class="mon"><h4>{calendar.month_name[m]} {y}</h4><table class="cal"><thead><tr><th>M</th><th>T</th><th>W</th><th>T</th><th>F</th><th>S</th><th>S</th></tr></thead><tbody>{rows}</tbody></table></div>'


MONTHS = "".join(month(y, m) for y, m in [(2026, 11), (2026, 12)] + [(2027, m) for m in range(1, 12)])


def num(v):
    if isinstance(v, float) and abs(v) < 10:
        return f"{v:.4f}"
    if v is None:
        return "not read"
    return f"{v:,.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else f"{v:,}"


LINKS = {role: d for role, d in json.loads((SAMPLE / "order.json").read_text())["documents"].items()}


def nice(text):
    d = dt.date.fromisoformat(text)
    name = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."][d.month - 1]
    return f"{name} {d.day}, {d.year}"


def src(role):
    d = LINKS.get(role)
    return f'<a href="{e(d["url"])}">{e(role)}, filed {nice(d["filed"])}</a>' if d else e(role)


def pill(status):
    cls = {"same": "ok", "changed": "chg", "RESTATED": "bad"}.get(status, "bad")
    return f'<span class="pill {cls}">{e(status)}</span>'


READ_ROWS = "".join(f'<tr><td>{e(r["what"])}<div class="muted">{e(r["rests_on"])}</div></td><td class="n">{num(r["on_file"])}</td><td class="n">{num(r["read"])}</td><td>{src(r["doc"])}</td><td>{pill(r["status"])}</td></tr>' for r in R["reads"])
CALC_ROWS = "".join(f'<tr><td>{e(r["what"])}<div class="muted">{e(r["rests_on"])}</div></td><td class="n">{num(r["on_file"])}</td><td class="n">{num(r["worked"])}</td><td>calc.</td><td>{pill(r["status"])}</td></tr>' for r in R["calcs"])
YEAR_ROWS = "".join(f'<tr><td>FY{y["year"]}</td><td class="n">{y["normal"]:,}</td><td>{e(", ".join(y["docs"]))}</td><td>{pill("same") if y["status"] == "all found" else "<span class=pill-bad>" + e(y["status"]) + ": " + e("; ".join(y["not_found"])) + "</span>"}</td></tr>' for y in R["years"])
KILL_ROWS = "".join(f'<tr><td><strong>{e(k["line"])}</strong></td><td>{e(k["threshold"])}</td><td>{e(k["reading"])}</td><td>{e(k["state"])}</td></tr>' for k in R["kill"])
B, A, S = R["before"], R["after"], R["after_at_old_price"]
close_day = R["close"][0]


def row(name, key, fmt="${:.2f}"):
    return f'<tr><th scope="row">{name}</th><td class="n">{fmt.format(B[key])}</td><td class="n">{fmt.format(S[key])}</td><td class="n">{fmt.format(A[key])}</td></tr>'


BA = (row("Base value, low", "base_low") + row("Base value, middle", "base_mid") + row("Base value, high", "base_high") + row("Buy-below", "buy_below") +
      row("Strategic value", "strategic") + row("Trim-above", "trim_above") + row("Price", "price") + row("Coverage", "coverage", "{:.1f}%"))
C = R["counts"]
SNIPPET = """{
  "permissions": {
    "allow": [
      "Bash(.venv/bin/python sensors/reviews/quarterly.py *)",
      "Bash(.venv/bin/python sensors/reviews/weekly.py *)",
      "Bash(agent-reach web search *)",
      "WebSearch",
""" + ",\n".join(f'      "WebFetch(domain:{x})"' for x in __import__("tomllib").loads((HERE / "theses.toml").read_text())["open_domains"]) + """
    ]
  }
}"""

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Slower Reviews</title>
<style>
:root{{--page:#f9f9f7;--surface:#fcfcfb;--panel:#f0efea;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--blue:#2a78d6;--green:#12795f;--orange:#c94f1e;--red:#b3261e;--real-ink:#fff}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--blue:#6aa6ee;--green:#4cc3a0;--orange:#ee7f50;--red:#f0776c;--real-ink:#0d0d0d}}}}
:root[data-theme="dark"]{{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--blue:#6aa6ee;--green:#4cc3a0;--orange:#ee7f50;--red:#f0776c;--real-ink:#0d0d0d}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:30px;line-height:1.2;margin:0 0 10px;text-wrap:balance}}
h2{{font-size:20px;margin:44px 0 10px}}
h3{{font-size:15px;margin:20px 0 6px}}
p{{margin:0 0 10px;max-width:74ch}}
.lead{{font-size:18px;color:var(--ink-2)}}
.muted{{color:var(--muted);font-size:13px}}
a{{color:var(--blue);overflow-wrap:anywhere}}
code{{font:13px ui-monospace,Menlo,Consolas,monospace;background:var(--panel);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}}
.tw{{overflow-x:auto}}
table.d{{border-collapse:collapse;font-size:14.5px;width:100%}}
table.d th,table.d td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}}
table.d thead th{{color:var(--muted);font-weight:600}}
table.d tbody th{{font-weight:500}}
table.d td.n,table.d thead th.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}}
.tile{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px}}
.tile b{{display:block;font-size:24px;font-variant-numeric:tabular-nums;line-height:1.2}}
.tile span{{font-size:13.5px;color:var(--ink-2)}}
.pill{{font-size:12px;font-weight:600;padding:1px 7px;border-radius:9px;white-space:nowrap}}
.pill.ok{{color:var(--green);border:1px solid var(--green)}}
.pill.chg{{color:var(--orange);border:1px solid var(--orange)}}
.pill.bad,.pill-bad{{color:var(--red);font-size:13px}}
.pill.bad{{border:1px solid var(--red)}}
.months{{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:18px 20px}}
.mon h4{{margin:0 0 4px;font-size:13.5px;font-weight:600}}
.cal{{border-collapse:separate;border-spacing:2px;width:100%;table-layout:fixed;font-size:12px}}
.cal th{{color:var(--muted);font-weight:400;padding:0}}
.cal td{{height:27px;text-align:center;position:relative;border-radius:4px;color:var(--ink-2);padding:0;font-variant-numeric:tabular-nums}}
.cal td.off{{color:var(--axis)}}
.cal td.real{{background:var(--orange);color:var(--real-ink);font-weight:700}}
.cal td.q{{box-shadow:inset 0 0 0 2px var(--orange)}}
.cal td.k{{box-shadow:inset 0 0 0 2px var(--red);color:var(--red);font-weight:700}}
.cal td.res{{background:var(--panel);font-weight:600}}
.dot,.tick{{position:absolute;display:block;left:50%;transform:translateX(-50%)}}
.dot{{width:5px;height:5px;border-radius:50%;background:var(--blue);bottom:1px}}
.tick{{width:9px;height:2px;background:var(--axis);top:1px}}
.key{{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:13.5px;color:var(--ink-2);list-style:none;padding:0;margin:0 0 14px}}
.key li{{display:flex;align-items:center;gap:7px}}
.sw{{display:inline-block;width:18px;height:18px;border-radius:4px;position:relative;flex:none}}
.box{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin:10px 0}}
ol.do{{padding-left:22px;max-width:78ch}}ol.do li{{margin-bottom:9px}}
pre{{background:var(--panel);border-radius:8px;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:8px 0 0}}
button{{font:inherit;font-size:14px;padding:6px 12px;border:1px solid var(--axis);border-radius:6px;background:var(--surface);color:var(--ink);cursor:pointer}}
details{{margin:10px 0}}details summary{{cursor:pointer;font-weight:600}}
@media (max-width:640px){{h1{{font-size:25px}}table.d{{font-size:13.5px}}table.d th,table.d td{{padding:6px 7px}}}}
</style></head><body><main>
<h1>Two slower reviews</h1>
<p class="lead"><strong>{e(META["lead"])}</strong></p>
<p class="muted">Stays on this computer: it holds a Yahoo price. Built by <code>sensors/reviews/draw.py</code>. It recommends nothing. Corning stays no buy, and no note changed.</p>

<div class="tiles">
<div class="tile"><b>{len(WEEKLY)}</b><span>weekly thesis checks in a year (calc.)</span></div>
<div class="tile"><b>{len(QUIET)}</b><span>quarterly checks that find nothing and stop (calc.)</span></div>
<div class="tile"><b>{len(REAL)}</b><span>real refreshes, one per 10-Q or 10-K (my estimate)</span></div>
<div class="tile"><b>{C["same"]} of {C["reads"]}</b><span>numbers re-read in the dry run matched what is on file</span></div>
</div>

<h2>A year of runs</h2>
<p>Nov. 3, 2026 to Nov. 2, 2027. <strong>Every date here is an estimate,</strong> set from Corning's last two years of filing dates (<a href="https://data.sec.gov/submissions/CIK0000024741.json">EDGAR filing list, fetched Nov. 3, 2026</a>). The task runs on the first Tuesday or Friday after a 10-Q or 10-K lands. Nothing has run on this schedule yet.</p>
<ul class="key">
<li><span class="sw" style="background:var(--panel)"><i class="dot"></i></span>Monday: weekly thesis check</li>
<li><span class="sw" style="background:var(--panel)"><i class="tick"></i></span>Tue. or Fri. in seven months: check for a filing, stops</li>
<li><span class="sw" style="box-shadow:inset 0 0 0 2px var(--orange)"></span>10-Q filed</li>
<li><span class="sw" style="background:var(--orange)"></span>Quarterly refresh really runs</li>
<li><span class="sw" style="box-shadow:inset 0 0 0 2px var(--red)"></span>10-K filed</li>
<li><span class="sw" style="background:var(--panel);outline:1px solid var(--axis)"></span>Results day: the daily run reads it</li>
</ul>
<div class="months">{MONTHS}</div>
<p class="muted" style="margin-top:12px">Hover a marked day for what it is. K3, K8 and K9 can first fire on the Q1 2027 report, about late April 2027, and K5's test reads about late October 2027 (my estimates, <code>Research/2026-11-03 Corning kill criteria.md</code>). A computer asleep skips a run. The next wake starts one catch-up, and both tasks work from what is new, so a skipped run loses nothing (<a href="https://code.claude.com/docs/en/desktop-scheduled-tasks">Desktop scheduled tasks docs, undated, retrieved Nov. 3, 2026</a>).</p>

<h2>The dry run: before and after</h2>
<p>{e(META["ba_lead"])}</p>
<div class="tw"><table class="d"><thead><tr><th></th><th class="n">Before</th><th class="n">After, same price</th><th class="n">After, newest close</th></tr></thead><tbody>{BA}</tbody></table></div>
<p class="muted" style="margin-top:8px">All calc. through the valuation skill's <code>value.py</code>. Before: the approved run, <code>sensors/valuation/runs/2026-11-03-01.md</code>, on the close of Nov. 2, 2026. Newest close: Nov. 3, 2026. Closes: <a href="https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&amp;interval=1d">Yahoo through yfinance, fetched Nov. 2 and Nov. 3, 2026</a>. The filing: {src("10-Q")}. Full proposal: <code>sensors/reviews/samples/dry-run/proposal.md</code>.</p>

<h3>What a filing that moves things looks like</h3>
<p>{e(REPLAY["words"])}</p>
<div class="tw"><table class="d"><thead><tr><th></th><th class="n">Q2 10-Q basis (replay)</th><th class="n">Q3 10-Q, on file</th><th class="n">Move (calc.)</th></tr></thead><tbody>
{"".join(f'<tr><th scope="row">{e(x["name"])}</th><td class="n">{e(x["q2"])}</td><td class="n">{e(x["q3"])}</td><td class="n">{e(x["move"])}</td></tr>' for x in REPLAY["rows"])}
</tbody></table></div>
<p class="muted" style="margin-top:8px">A replay I worked by hand from {' '.join(REPLAY["sources"])}, with Aaa and the rest held at today's inputs. A labeled what-if through <code>value.py</code>, not a past approved figure. It did not go through the task.</p>

<h2>The re-verify checklist</h2>
<p>Claude reads each number from the filing and quotes it. A script refuses a read if the quote is not in the saved filing or the number is not in the quote, so Claude cannot pass a number on from the note. Rows are in <code>sensors/reviews/checklist-GLW.toml</code>.</p>
<div class="tiles">
<div class="tile"><b>{C["reads"]}</b><span>read from a filing by quote</span></div>
<div class="tile"><b>{C["calcs"]}</b><span>sums worked by the script from those reads</span></div>
<div class="tile"><b>{C["years_found"]} of {C["years"]}</b><span>ten-year rows found by a weak label match</span></div>
<div class="tile"><b>{C["restated"]}</b><span>restated numbers found</span></div>
</div>
<h3>Kill lines, read from the filing</h3>
<div class="tw"><table class="d"><thead><tr><th>Line</th><th>Threshold</th><th>Reading</th><th>State</th></tr></thead><tbody>{KILL_ROWS}</tbody></table></div>
<details><summary>All {C["reads"]} numbers read from a filing</summary><div class="tw"><table class="d"><thead><tr><th>Number, and what rests on it</th><th class="n">On file</th><th class="n">Read</th><th>From</th><th>Result</th></tr></thead><tbody>{READ_ROWS}</tbody></table></div></details>
<details><summary>All {C["calcs"]} sums</summary><div class="tw"><table class="d"><thead><tr><th>Sum, and what rests on it</th><th class="n">On file</th><th class="n">Worked</th><th>From</th><th>Result</th></tr></thead><tbody>{CALC_ROWS}</tbody></table></div></details>
<details><summary>The ten years behind the low</summary><p class="muted">A filed number on or within eight lines under its label, in a saved 10-K. It does not prove the column. Normal earnings, $M, sum {R["ten_year_sum"]:,}, so the average is $1,028.4M (calc.).</p><div class="tw"><table class="d"><thead><tr><th>Year</th><th class="n">Normal, $M</th><th>10-K searched</th><th>Result</th></tr></thead><tbody>{YEAR_ROWS}</tbody></table></div></details>
<h3>What this checklist cannot re-verify</h3>
<ul>{"".join(f"<li>{x}</li>" for x in META["cannot"])}</ul>

<h2>The dry run itself</h2>
<ul>{"".join(f"<li>{x}</li>" for x in META["how"])}</ul>

<h2>What you ruled, Nov. 4, 2026</h2>
<ul>{"".join(f"<li>{x}</li>" for x in META["rule"])}</ul>

<h2>How to set them up in Desktop</h2>
<ol class="do">
<li><strong>Allow rules: done, Nov. 4, 2026.</strong> The rules below are in <code>~/.claude/settings.json</code>. The docs say those apply to scheduled runs. Without them, an approval a run has not seen makes it wait for you.</li>
<li>In the <strong>Code</strong> tab, click <strong>Scheduled</strong>, then <strong>New task</strong>. If it asks, choose <strong>Set up manually</strong>.</li>
<li><strong>Weekly:</strong> name <code>weekly-thesis-check</code>. Paste the weekly prompt below. Under <strong>Advanced settings</strong>, turn on <strong>Only on this computer</strong>, and pick this folder (<code>/home/superposition/investor-os</code>) as the local folder. Trigger: <strong>Weekly</strong>, Monday, 10:00. In the box's toolbar pick <strong>Accept edits</strong> and <strong>Opus</strong>. Click <strong>Create</strong>.</li>
<li><strong>Quarterly:</strong> <strong>New task</strong> again. Name <code>quarterly-refresh</code>. Paste the quarterly prompt. Same switch, folder, mode and model. Pick <strong>Weekly</strong> for now and click <strong>Create</strong>. Then click the pencil icon, set the schedule to <strong>Custom</strong>, and enter <code>30 10 * 2,4,5,7,8,10,11 2,5</code>. That is 10:30 on Tuesdays and Fridays in the seven months a 10-Q or 10-K can land. Desktop has no trigger for a filing, so this is how "only when a new filing lands" works: each run asks the script and stops if nothing is new. <strong>Do not use an hourly or daily schedule:</strong> each check starts a session.</li>
<li><strong>Keep them off each other.</strong> A task can be skipped if another is running, so these sit after your 8 a.m. daily run. If the daily runs long on a busy day, check <strong>History</strong>.</li>
<li><strong>Run each once with Run now, and watch.</strong> Answer any prompt with "always allow". Quarterly: its first run treats Corning's Q3 10-Q as new, because nothing is marked done yet, so it writes a real proposal like the dry run (about the same cost) and marks that filing done. After that it is quiet until the next 10-Q. Weekly: this is its first run ever.</li>
<li><strong>Read the result in the files.</strong> Weekly: end of today's Journal. Quarterly: <code>Research/&lt;date&gt; Corning refresh proposal.md</code>. Nothing notifies you of a Red or an Orange: you see it when you open the Journal or the run's session.</li>
</ol>
<details><summary>The allow rules</summary><pre>{e(SNIPPET)}</pre></details>
<p class="muted">Sources: <a href="https://code.claude.com/docs/en/desktop-scheduled-tasks">Desktop scheduled tasks docs, undated, retrieved Nov. 3, 2026</a>; <a href="https://code.claude.com/docs/en/permissions">permissions docs, undated, retrieved Nov. 3, 2026</a>. Not tried in Desktop yet, so these steps are from the docs and your daily run's setup.</p>

<h2>The prompts</h2>
<details><summary>Weekly thesis check. Not run yet.</summary><p style="margin-top:8px"><button data-copy="wk">Copy the prompt</button></p><pre id="wk">{e(prompt("Weekly thesis check.md"))}</pre></details>
<details><summary>Quarterly refresh. Run once, on the copy.</summary><p style="margin-top:8px"><button data-copy="qt">Copy the prompt</button></p><pre id="qt">{e(prompt("Quarterly refresh.md"))}</pre></details>
</main>
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){{b.addEventListener('click',function(){{var t=document.getElementById(b.dataset.copy).textContent;var l=b.textContent;var done=function(){{b.textContent='Copied';setTimeout(function(){{b.textContent=l}},1500)}};if(navigator.clipboard&&window.isSecureContext){{navigator.clipboard.writeText(t).then(done)}}else{{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{{document.execCommand('copy');done()}}finally{{a.remove()}}}}}})}});
</script>
</body></html>
"""
(ROOT / "reviews.html").write_text(PAGE)
print(f"reviews.html: {len(WEEKLY)} weekly, {len(QUIET)} quiet checks, {len(REAL)} real refreshes")
