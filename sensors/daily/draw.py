"""Builds daily.html from the prompt in Playbooks/ and the two samples saved from test runs. No network.
Run: .venv/bin/python -I sensors/daily/draw.py   Keep the page on this computer: it holds a Yahoo price."""
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
playbook = (ROOT / "Playbooks" / "Daily run.md").read_text()
PROMPT = re.search(r"```text\n(.*?)\n```", playbook, re.S).group(1)
QUIET = (HERE / "samples" / "quiet.md").read_text().strip()
BUSY = (HERE / "samples" / "busy.md").read_text().strip()


def inline(text):
    out = html.escape(text, quote=False)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', out)
    out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r"\1 (<code>\2</code>)", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def brief(text):
    rows, in_list = [], False
    for line in text.splitlines():
        if line.startswith("- ") and not in_list:
            rows.append("<ul>")
            in_list = True
        if not line.startswith("- ") and in_list and line.strip():
            rows.append("</ul>")
            in_list = False
        m = re.match(r"###\s*(Red|Orange|Info)", line)
        if m:
            rows.append(f'<h4 class="lv {m.group(1).lower()}">{m.group(1)}</h4>')
        elif line.startswith("- "):
            rows.append(f"<li>{inline(line[2:])}</li>")
        elif line.strip():
            rows.append(f"<p>{inline(line)}</p>")
    if in_list:
        rows.append("</ul>")
    return "\n".join(rows)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Daily Run</title>
<style>
:root{--page:#f9f9f7;--surface:#fcfcfb;--panel:#f0efea;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--script:#2a78d6;--claude:#12795f;--red:#b3261e;--orange:#c94f1e;--info:#52514e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--script:#6aa6ee;--claude:#4cc3a0;--red:#f0857d;--orange:#ee7f50;--info:#c3c2b7}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--script:#6aa6ee;--claude:#4cc3a0;--red:#f0857d;--orange:#ee7f50;--info:#c3c2b7}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:940px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:30px;line-height:1.2;margin:0 0 10px}
h2{font-size:20px;margin:44px 0 10px}
h3{font-size:15px;margin:0 0 6px}
p{margin:0 0 10px}
.lead{font-size:18px;color:var(--ink-2)}
.muted{color:var(--muted);font-size:14px}
a{color:var(--script);overflow-wrap:anywhere}
code{font:13px ui-monospace,Menlo,Consolas,monospace;background:var(--panel);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}
.flow{display:grid;gap:0}
.step{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--script);border-radius:8px;padding:12px 14px}
.step.c{border-left-color:var(--claude)}
.step ul{margin:4px 0 0;padding-left:18px;font-size:14.5px;color:var(--ink-2)}
.step p{font-size:14.5px;color:var(--ink-2);margin:0}
.who{font-size:12px;font-weight:600;letter-spacing:.02em;color:var(--script);margin-bottom:2px}
.step.c .who{color:var(--claude)}
.arrow{height:26px;position:relative}
.arrow:before{content:"";position:absolute;left:24px;top:0;bottom:7px;border-left:2px solid var(--axis)}
.arrow:after{content:"";position:absolute;left:19px;bottom:0;border:6px solid transparent;border-top:8px solid var(--axis);border-bottom:0}
.fork{display:grid;grid-template-columns:1fr 2fr;gap:12px;align-items:stretch}
.lane>.tag{font-size:13px;font-weight:600;margin-bottom:6px}
.lane{display:flex;flex-direction:column}
.lane>.step{flex:1}
.key{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--ink-2);margin:0 0 12px}
.key i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.sample{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px;margin:8px 0 18px}
.sample ul{margin:0 0 8px;padding-left:18px}
.sample li{margin-bottom:8px}
.lv{margin:14px 0 6px;font-size:14px}
.lv.red{color:var(--red)}.lv.orange{color:var(--orange)}.lv.info{color:var(--info)}
ol.do{padding-left:22px}ol.do li{margin-bottom:8px}
.tw{overflow-x:auto}
table{border-collapse:collapse;font-size:14.5px;width:100%}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted);font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
pre{background:var(--panel);border-radius:8px;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:8px 0 0}
button{font:inherit;font-size:14px;padding:6px 12px;border:1px solid var(--axis);border-radius:6px;background:var(--surface);color:var(--ink);cursor:pointer}
details summary{cursor:pointer;font-weight:600}
@media (max-width:640px){.fork{grid-template-columns:1fr}h1{font-size:25px}}
</style></head><body><main>
<h1>The daily run</h1>
<p class="lead"><strong>Built, and tested on copies of this vault. Nothing is live until you paste the prompt into Desktop.</strong> Until then, <code>daily-test</code> keeps writing its one test line.</p>

<h2>The pipeline</h2>
<div class="key"><span><i style="background:var(--script)"></i>A plain script: same result every time</span><span><i style="background:var(--claude)"></i>Claude: reads and judges</span></div>
<div class="flow">
<div class="step"><div class="who">1. SENSORS, <code>sensors/daily/collect.py</code></div><h3>Run two sensors, one at a time. Never Yahoo</h3>
<ul><li><strong>8-K watcher:</strong> a fresh SEC list. It writes its own Inbox note for each new 8-K, so those notes land here, before the brief.</li><li><strong>Radar:</strong> events, catalyst dates, the screen. It also adds a report in <code>Research/</code> and updates the catalyst notes.</li></ul></div>
<div class="arrow"></div>
<div class="step"><div class="who">2. WHAT IS NEW, same script</div><h3>Keep only what changed since the last brief, each with a first-pass level</h3>
<p>The first pass uses the item and form levels in <code>Rules/alerts.md</code>. It reads the closes you saved by hand, and one counts only if it crosses a line. A digest that was never briefed carries into the next run, so nothing is lost if a run dies.</p></div>
<div class="arrow"></div>
<div class="fork">
<div class="lane"><div class="tag">Nothing new</div><div class="step"><div class="who">3. NO TRIAGE NEEDED</div><p>Claude reads nothing. The next script writes the one line.</p></div></div>
<div class="lane"><div class="tag">Something new</div><div class="step c"><div class="who">3. TRIAGE, Claude</div><p>Reads each filing that needs it, against the kill lines and the company note. Keeps or lowers the level where the map allows, and writes the brief. A presumed Red stays Red until you rule.</p></div></div>
</div>
<div class="arrow"></div>
<div class="step"><div class="who">4. CHECK AND WRITE, <code>sensors/daily/publish.py</code></div><h3>Refuse a bad brief, then put it at the top of today's Journal</h3>
<p>It refuses advice words, a price move, a line with no source or date, a Red or Orange item left out, or a presumed Red moved out of Red. Earlier Journal text stays as it was. The session record goes at the end.</p></div>
<div class="arrow"></div>
<div class="step"><div class="who">5. INBOX, same script</div><h3>File what is new and has no note yet</h3>
<p>One dated note for each other filing. Forms 3, 4 and 144 share one note per run, as I4 rolls them into one line. A close, a date or a lead gets no note, since none is a filing.</p></div>
</div>

<h2>A quiet day</h2>
<p class="muted">Word for word from running the two scripts on a copy, with no fetch from Yahoo.</p>
<div class="sample">__QUIET__</div>
<p class="muted">A close you save by hand does not break the quiet, on purpose. It appears as I9 only when something else is new, or as an Orange if it crosses a line.</p>

<h2>A busy day</h2>
<p class="muted"><strong>A replay, not a real day.</strong> Real past filings on a copy, made to look new: the Q3 8-K, the 10-Q, two Forms 4, an SEC letter and one catalyst date. Word for word from the run, including its Info line on the 10-Q. It ran before prices came out of the run, which changes where its close came from and not the form of the brief. Claude's reading, for you to correct. I checked the release's segment figures against the filing.</p>
<div class="sample">__BUSY__</div>
<p class="muted"><strong>No real Red in that window</strong>, as the two-year test in <code>Rules/alerts.md</code> also found, so the replay has none. A Red line has the same form. <strong>Made up, to show the form only:</strong> "8-K 0000000000-00-000000, item 4.02: the company says its past accounts cannot be relied on. Presumed Red until I rule (R3). [8-K, filed date]." A unit test checks that such an item cannot leave Red.</p>

<h2>What to change in Desktop</h2>
<ol class="do">
<li>In the <strong>Code</strong> tab, click <strong>Scheduled</strong>, then <strong>daily-test</strong>, then the pencil icon.</li>
<li><strong>Instructions:</strong> delete everything and paste the prompt below.</li>
<li><strong>Description:</strong> replace it with <code>Daily run: sensors, triage, brief at the top of the Journal, then Inbox.</code></li>
<li><strong>Leave as they are:</strong> Accept edits, Opus, Daily at 8 a.m., this folder. Leave the name too: the docs do not say what renaming does to a task's history and saved approvals.</li>
<li>Save, then click <strong>Run now</strong> and open the run's session from <strong>History</strong>.</li>
<li><strong>Do not skip this.</strong> Accept edits does not cover running scripts. Choose <strong>always allow</strong> when it asks about each of these, and allow nothing else:<br><code>.venv/bin/python sensors/daily/collect.py</code><br><code>.venv/bin/python sensors/daily/publish.py</code></li>
<li>Check that the <strong>Always allowed</strong> panel shows those two, and that the Journal has the brief. That Run now is a real run, and it writes to your real Journal.</li>
</ol>
<p class="muted">Sources: <a href="https://code.claude.com/docs/en/desktop-scheduled-tasks">Desktop scheduled tasks docs, undated, retrieved Nov. 3, 2026</a>; <a href="https://code.claude.com/docs/en/permissions">permissions docs, undated, retrieved Nov. 3, 2026</a>. <strong>Not tested in Desktop.</strong> My test passed the same two approvals on the command line, so step 6 is the first true check.</p>

<h2>What the tests showed</h2>
<div class="tw"><table><tr><th>Run, on a copy, Accept edits, Opus</th><th>Result</th><th>Denied</th><th>Time</th><th>List price</th></tr>
<tr><td>Quiet: tonight's real sensors</td><td>Passed. It could not quote its own line, since fixed.</td><td class="n">0</td><td class="n">17 s</td><td class="n">$0.29</td></tr>
<tr><td>Busy, first replay</td><td><strong>Failed the key step.</strong> The Q3 release is one huge line, too long to read. The run kept Orange and said "not read".</td><td class="n">0</td><td class="n">85 s</td><td class="n">$1.00</td></tr>
<tr><td>Busy, second replay, after the fix</td><td>Passed. Read the release and the SEC letter, and dropped the closing letter to Info.</td><td class="n">0</td><td class="n">89 s</td><td class="n">$1.36</td></tr></table></div>
<p class="muted">You asked for one test. The two replays are extra, and they drew on your plan. A plan does not bill list price, so these figures only show size. These three ran with prices still in the run. <strong>After they ran, prices came out and the prompt changed: the Yahoo paragraph was replaced, and a sentence on naming vault files was added. No Claude run has used that prompt.</strong> I then ran the two scripts directly on a fresh copy: both finished and Yahoo's fetch log did not change. Your real Journal's checksum was the same before and after the three runs.</p>

<h2>Where this differs from what is on file</h2>
<div class="tw"><table><tr><th>On file</th><th>This run</th><th>Status</th></tr>
<tr><td><code>Rules/alerts.md</code>, decision 7: no schedule for the Yahoo close, by hand.</td><td>Fetches nothing from Yahoo. Checks the lines on the first run after you save a close by hand.</td><td><strong>Your decision stands, reconfirmed Nov. 3, 2026.</strong> A crossing between saves shows up late. The check covers every day since the last close it saw.</td></tr>
<tr><td><code>Rules/memory.md</code>: add to the end of today's file.</td><td>The brief goes at the top, under the date. The session record goes at the end.</td><td>An exception you approved, Nov. 3, 2026. Only adds lines.</td></tr>
<tr><td><code>Rules/alerts.md</code>: Red and Orange go out at once.</td><td>A brief in the Journal. Nothing notifies you.</td><td>Open. A Red waits until you look.</td></tr>
<tr><td><code>Rules/alerts.md</code>: 15 of 27 Oranges came from news and calls.</td><td>Reads neither. The quiet line says so.</td><td>Open. "Nothing needs me" means nothing in filings, dates or the closes you saved.</td></tr></table></div>

<h2>The prompt</h2>
<p><button id="copy" type="button">Copy the prompt</button></p>
<details open><summary>Show the prompt</summary><pre id="prompt">__PROMPT__</pre></details>
<p class="muted" style="margin-top:24px">Stays on this computer: it holds a Yahoo price. Built by <code>sensors/daily/draw.py</code>. It recommends nothing. Corning stays no buy.</p>
</main>
<script>
document.getElementById('copy').addEventListener('click',function(){var b=this;var t=document.getElementById('prompt').textContent;
var done=function(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy the prompt'},1500)};
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(done)}else{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');done()}finally{a.remove()}}});
</script></body></html>
"""
out = PAGE.replace("__QUIET__", brief(QUIET)).replace("__BUSY__", brief(BUSY)).replace("__PROMPT__", html.escape(PROMPT, quote=False))
assert "$126.14" in out and "nothing needs me" in out
(ROOT / "daily.html").write_text(out)
print("Wrote daily.html")
