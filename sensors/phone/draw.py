"""Builds phone.html: the path of a Red, where the token lives, and how many alerts a month. No network.
Run: .venv/bin/python -I sensors/phone/draw.py   The counts come from the saved samples and the figures in Rules/alerts.md."""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SAMPLE = ROOT / "sensors/hunt/samples"
MONTHS = 24

rule = (ROOT / "Rules/alerts.md").read_text()
m = re.search(r"gives 0 Reds that count, (\d+) Oranges and (\d+) Info items", rule)
ORANGE, INFO = int(m.group(1)), int(m.group(2))
Y102 = [r for r in json.loads((SAMPLE / "two-years-102.json").read_text()) if r["company"] != "Corning" and r["alone"]]
Y101 = [r for r in json.loads((SAMPLE / "two-years.json").read_text()) if r["company"] not in ("Corning", "Linde")]
RED, EVENT = len(Y102), len(Y101)
ALL = ORANGE + INFO + RED + EVENT
RED_M, ALL_M = RED / MONTHS, ALL / MONTHS


def dots(total, red):
    cols, step, r = 40, 14, 5
    rows = (total + cols - 1) // cols
    out = []
    for i in range(total):
        x, y = i % cols * step + r + 1, i // cols * step + r + 1
        is_red = i < red
        label = "A Red: a 1.02 with no 1.01, none ended a deal with Corning" if is_red else "An Orange or an Info"
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="var(--{"red" if is_red else "dot"})"><title>{label}</title></circle>')
    h = rows * step + 2
    return f'<svg viewBox="0 0 {cols * step + 2} {h}" role="img" aria-label="{total} dots, {red} of them red" style="width:100%;max-width:560px;display:block">{"".join(out)}</svg>'


def nice(day):
    y, mo, d = day.split("-")
    return f'{"Jan. Feb. Mar. Apr. May June July Aug. Sept. Oct. Nov. Dec.".split()[int(mo) - 1]} {int(d)}, {y}'


filings = "; ".join(f'<a href="{html.escape(r["url"])}">{"T1 Energy, filed as FREYR" if r["company"] == "T1 Energy" else r["company"]}, 8-K, filed {nice(r["day"])}</a>' for r in sorted(Y102, key=lambda r: r["day"]))
TEST_MSG = """RED ALERT

TEST, made up, R1. TEST ONLY. NOT A REAL ALERT. No kill line was crossed and no such filing exists. Made-up 8-K, filed 2026-11-04: https://www.sec.gov/, 0000000000-00-000000.

Daily run, Journal/2026-11-04.md. An alert states a condition. It gives no advice."""

CSS = """
:root{--page:#f9f9f7;--surface:#fcfcfb;--panel:#f0efea;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--script:#2a78d6;--claude:#12795f;--red:#b3261e;--dot:#a9a79c;--key:#8a5a00}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--script:#6aa6ee;--claude:#4cc3a0;--red:#f0857d;--dot:#5c5b55;--key:#e0b050}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--axis:#4a4a46;--border:rgba(255,255,255,.10);--script:#6aa6ee;--claude:#4cc3a0;--red:#f0857d;--dot:#5c5b55;--key:#e0b050}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:940px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:30px;line-height:1.2;margin:0 0 10px}
h2{font-size:20px;margin:44px 0 10px}
p{margin:0 0 10px}
.lead{font-size:18px;color:var(--ink-2)}
.muted{color:var(--muted);font-size:14px}
a{color:var(--script);overflow-wrap:anywhere}
code{font:13px ui-monospace,Menlo,Consolas,monospace;background:var(--panel);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}
.status{border:1px solid var(--border);border-left:4px solid var(--key);background:var(--surface);border-radius:8px;padding:12px 14px;margin:16px 0}
.key{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--ink-2);margin:0 0 12px}
.key i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.path{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,320px);gap:20px;align-items:start}
.step{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--script);border-radius:8px;padding:10px 14px}
.step.c{border-left-color:var(--claude)}
.step.t{border-left-color:var(--muted)}
.step b{display:block}
.step span{font-size:14px;color:var(--ink-2)}
.who{font-size:12px;font-weight:600;color:var(--script)}
.step.c .who{color:var(--claude)}
.step.t .who{color:var(--muted)}
.arrow{height:24px;position:relative}
.arrow:before{content:"";position:absolute;left:24px;top:0;bottom:7px;border-left:2px solid var(--axis)}
.arrow:after{content:"";position:absolute;left:19px;bottom:0;border:6px solid transparent;border-top:8px solid var(--axis);border-bottom:0}
.vault{border:2px solid var(--key);border-radius:10px;padding:14px;background:var(--surface)}
.vault h3{font-size:15px;margin:0 0 6px}
.vault ul{margin:6px 0 0;padding-left:18px;font-size:14.5px;color:var(--ink-2)}
.vault li{margin-bottom:6px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0 20px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.tile b{display:block;font-size:30px;line-height:1.15}
.tile span{font-size:14px;color:var(--ink-2)}
.chart h3{font-size:15px;margin:18px 0 8px}
.tw{overflow-x:auto}
table{border-collapse:collapse;font-size:14.5px;width:100%;margin:14px 0}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted);font-weight:600}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.sum td{font-weight:600}
td:last-child{min-width:170px}
pre{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px;white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.45 ui-monospace,Menlo,Consolas,monospace}
ol li,ul.plain li{margin-bottom:8px}
@media (max-width:760px){.path{grid-template-columns:minmax(0,1fr)}}
"""

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Phone Alerts</title>
<style>{CSS}</style></head><body><main>

<h1>Red on my phone, and nothing else</h1>
<p class="lead"><strong>Red only is about one alert every {1 / RED_M:.0f} months. Everything would be about {ALL_M:.0f} a month (calc.).</strong> The sending needs no AI. A Red that rests on reading a filing still needs a run to write it.</p>
<div class="status"><strong>Live since Nov. 4, 2026.</strong> My TEST message arrived on my phone and <code>phone.py check</code> passed, my report. No real Red has gone out yet, and none has gone from a Desktop task. <code>Rules/alerts.md</code> records this.</div>

<h2>The path of a Red</h2>
<div class="key"><span><i style="background:var(--script)"></i>Plain script, no AI</span><span><i style="background:var(--claude)"></i>Claude, in a Desktop task</span><span><i style="background:var(--muted)"></i>Outside this computer</span><span><i style="background:var(--key)"></i>The token</span></div>
<div class="path">
<div>
<div class="step t"><div class="who">SEC</div><b>A company files an 8-K</b></div>
<div class="arrow"></div>
<div class="step"><div class="who">Script, started by the task</div><b>Sensors find it</b><span><code>collect.py</code> in the daily run, <code>events.py start</code> in the event run. An item number alone can presume a Red (R3).</span></div>
<div class="arrow"></div>
<div class="step c"><div class="who">Claude, in the task</div><b>Reads the filing and writes the level</b><span>R1 and R2 can only come from this reading. Desktop must be running and the computer on.</span></div>
<div class="arrow"></div>
<div class="step"><div class="who">Script</div><b>The run's last script checks it and writes it down</b><span><code>publish.py</code> or <code>events.py finish</code>. The Journal gets every level, as before.</span></div>
<div class="arrow"></div>
<div class="step"><div class="who">Script, no model</div><b><code>sensors/phone/phone.py</code> takes the Red lines only</b><span>Orange and Info stop here. It skips a filing already in <code>sensors/phone/sent.json</code>. A replay or a scratch copy never goes out.</span></div>
<div class="arrow"></div>
<div class="step t"><div class="who">Telegram</div><b>The bot's servers pass it on</b><span>Telegram sees the message. It holds only what the Red line says, drawn from public filings.</span></div>
<div class="arrow"></div>
<div class="step t"><div class="who">My phone</div><b>The alert: condition, source, date</b><span>No advice. It goes one way: the script never reads messages sent to the bot after setup.</span></div>
</div>
<div class="vault">
<h3>Where the token lives</h3>
<p><code>~/.config/investor-os/telegram.env</code></p>
<ul>
<li>Outside the vault, in one file only.</li>
<li>Only my user can read it (mode 600, folder 700). The script stops if the file loosens.</li>
<li>I paste it into <code>phone.py setup</code>. The paste does not show and stays out of shell history. Setup refuses to run without a real terminal.</li>
<li>Only <code>phone.py</code> uses it: to send when a Red is waiting, and to search for leaks.</li>
<li>Errors are scrubbed before they print or reach the Journal.</li>
<li>Deny rules in <code>.claude/settings.json</code> stop Claude opening that folder or naming it in a shell command. They are not a wall: any script running as me could still read the file.</li>
<li><strong>Never in a chat with Claude.</strong> That would save it in a transcript.</li>
</ul>
<h3 style="margin-top:14px">How it is checked</h3>
<ul>
<li><code>phone.py check</code> searches the vault, Claude's transcripts, the task files and shell history. It names files, never what it found.</li>
<li>Each run's end repeats the vault part. A hit writes a line in the Journal.</li>
</ul>
</div>
</div>

<h2>What works with no session</h2>
<div class="tw"><table>
<tr><th>Case</th><th>Does the Red reach me?</th></tr>
<tr><td>Nobody has a session open. The scheduled run finishes.</td><td><strong>Yes.</strong> The run's own script sends it.</td></tr>
<tr><td>Telegram or the network is down at that moment.</td><td>It stays waiting. The next run or pass retries it, and the Journal gets one line a day.</td></tr>
<tr><td>The run dies after the sensors, with a presumed Red.</td><td><strong>Only with the retry loop on.</strong> After 2 hours it goes out marked "not read". Without the loop, it waits for the next finished run.</td></tr>
<tr><td>Desktop is closed, the computer is off, or Claude hits a usage limit.</td><td><strong>No.</strong> No run, so no Red exists. This computer has no cron, and systemd is not running, so nothing else starts a run.</td></tr>
<tr><td>A kill line or claim is hit in news, a call or a customer's release.</td><td><strong>No.</strong> No sensor reads those (<code>Rules/alerts.md</code>, Nov. 3, 2026).</td></tr>
</table></div>
<p><strong>A quiet phone proves nothing.</strong> At this rate, months of silence are normal, and a dead system looks the same. I asked for nothing else on the phone, so there is no "still alive" message. A failed run still shows only in the Journal.</p>

<h2>How many alerts a month</h2>
<div class="tiles">
<div class="tile"><b>{RED_M:.3f}</b><span>a month, Red only: {RED} in {MONTHS} months (calc.)</span></div>
<div class="tile"><b>{ALL_M:.1f}</b><span>a month, everything: {ALL} in {MONTHS} months (calc.)</span></div>
<div class="tile"><b>0 of {RED}</b><span>of those Reds ended a deal with Corning (<code>Rules/alerts.md</code>, Nov. 4, 2026)</span></div>
</div>
<div class="chart">
<h3>Red only: {RED} alerts in two years. Each dot is one alert.</h3>
{dots(RED, RED)}
<h3>Everything: {ALL} alerts in two years, on the same scale</h3>
{dots(ALL, RED)}
</div>
<div class="tw"><table>
<tr><th>What</th><th class="n">Two years</th><th class="n">A month (calc.)</th><th>On the phone</th><th>Source</th></tr>
<tr><td>Corning's Reds that count</td><td class="n">0</td><td class="n">0</td><td>Yes</td><td><code>Rules/alerts.md</code>, test of Nov. 3, 2026</td></tr>
<tr><td>Item 1.02 with no 1.01, other graph filers (R3)</td><td class="n">{RED}</td><td class="n">{RED_M:.3f}</td><td>Yes</td><td>{filings}</td></tr>
<tr><td>Corning's Oranges</td><td class="n">{ORANGE}</td><td class="n">{ORANGE / MONTHS:.1f}</td><td>No</td><td><code>Rules/alerts.md</code>, test of Nov. 3, 2026</td></tr>
<tr><td>Corning's Info items</td><td class="n">{INFO}</td><td class="n">{INFO / MONTHS:.1f}</td><td>No</td><td><code>Rules/alerts.md</code>, test of Nov. 3, 2026</td></tr>
<tr><td>Item 1.01s from other graph filers, each Orange or Info once read</td><td class="n">{EVENT}</td><td class="n">{EVENT / MONTHS:.1f}</td><td>No</td><td><code>sensors/hunt/samples/two-years.json</code>, SEC filing lists, retrieved Nov. 4, 2026</td></tr>
<tr class="sum"><td>Everything</td><td class="n">{ALL}</td><td class="n">{ALL_M:.1f}</td><td></td><td>calc.</td></tr>
</table></div>
<p class="muted"><strong>Read this first: it is a test with hindsight, on one thesis.</strong> The kill lines did not exist during these two years, and the levels are Claude's reading. "Everything" counts each line as one ping, which is the worst case, and a few lines across the lists may be one event. More theses mean more alerts. K3 run back gives one more Red, a false one, left out here because it cannot first fire until Q1 2027 (<code>Rules/alerts.md</code>, Nov. 3, 2026).</p>

<h2>Setting it up</h2>
<ol>
<li>In Telegram, open <strong>@BotFather</strong> and send <code>/newbot</code>. Give it a name, then a username that ends in "bot" (<a href="https://core.telegram.org/bots/features">Telegram bot features, undated, retrieved Nov. 4, 2026</a>). Bots message their users at no cost by default (<a href="https://core.telegram.org/bots/faq">Telegram bot FAQ, undated, retrieved Nov. 4, 2026</a>).</li>
<li>BotFather shows the token. Copy it and paste it only in step 3. If it ever leaks, <code>/token</code> in BotFather makes a new one (same features page).</li>
<li>In my own terminal, not with <code>!</code> in Claude: <code>cd ~/investor-os &amp;&amp; .venv/bin/python sensors/phone/phone.py setup</code>. Paste the token, open the bot on the phone, tap Start, press Enter, and confirm the name.</li>
<li><code>.venv/bin/python sensors/phone/phone.py test</code> sends the one TEST message below.</li>
<li><code>.venv/bin/python sensors/phone/phone.py check</code> checks that the token stayed out.</li>
<li>Optional, for retries and dead runs: <code>nohup .venv/bin/python sensors/phone/phone.py send --every 900 &gt;/dev/null 2&gt;&amp;1 &amp;</code>. It stops when the computer restarts, and nothing restarts it.</li>
</ol>
<h3 style="font-size:15px">The made-up Red</h3>
<pre>{TEST_MSG}</pre>
<p class="muted">The test builds this in a throwaway folder with that day's date, sends it through the same code twice and expects 1 and then 0. It never touches the Journal or the real sent list.</p>

<h2>What was checked, and what was not</h2>
<ul class="plain">
<li><strong>Checked, Nov. 4, 2026, against a fake Telegram:</strong> <code>sensors/phone/test_phone.py</code>. On a throwaway copy, the real <code>publish.py</code> sent one made-up TEST Red, and the real <code>events.py finish</code> sent the three saved replays. A second pass sent nothing, no Orange or Info went out, and the fake token appeared nowhere.</li>
<li><strong>Checked by me, Nov. 4, 2026:</strong> <code>phone.py setup</code>, one TEST message to my phone, and <code>phone.py check</code> with the real token.</li>
<li><strong>Not checked:</strong> a real Red, or a send from inside a Desktop task.</li>
<li><strong>"Once" has one gap.</strong> If Telegram takes a message and its answer is lost, the message goes again. Claude chose twice over never, for me to correct.</li>
</ul>

</main></body></html>
"""
(ROOT / "phone.html").write_text(PAGE)
print(f"phone.html: Red {RED}, everything {ALL}, {RED_M:.3f} and {ALL_M:.1f} a month")
