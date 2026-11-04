"""Builds guardrails.html from the saved runs: what each routine may touch, what is walled off, and what caught each test. No network.
Run: python3 sensors/guardrails/draw.py
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNS = HERE / "runs"


def newest(prefix):
    files = sorted(RUNS.glob(f"{prefix}-*.json"))
    return json.loads(files[-1].read_text()) if files else None


ATT, ROUT, REPLAY = newest("attempts"), newest("routines"), newest("replay")
e = html.escape
NICE = "Nov. 4, 2026"


def caught(att):
    return bool(att["stopped_by"]) and att["stopped_by"] != "broken test: no allow rule" and att["file_unchanged"] is not False


def passed(att):
    return att["attempted"] and not att["error"] and not att["stopped_by"]


ROWS = ATT["rows"]
GAPS = [r for r in ROWS if r["id"].startswith("G")]
TESTS = [r for r in ROWS if not r["id"].startswith("G")]
N_CAUGHT = sum(caught(r["blocked"]) for r in TESTS)
N_PASSED = sum(passed(r["works"]) for r in TESTS)
COST = sum(r["blocked"]["cost"] + r.get("works", {}).get("cost", 0) for r in ROWS)
REAL = ATT.get("real") or []


def asked(att):
    given = att["asked"]
    return given.get("command") or given.get("file_path") or given.get("url") or given.get("query") or given.get("prompt", "")


def who(att):
    by = att["stopped_by"]
    if not by:
        return '<span class="chip none">Nothing</span>'
    rules = ", ".join(att["rules"])
    if by == "deny rule":
        return '<span class="chip deny">Deny rule</span>'
    if by == "hook: after-check":
        return f'<span class="chip after">After-check</span> <span class="rule">{e(rules)}</span>'
    return f'<span class="chip hook">Hook</span> <span class="rule">{e(rules)}</span>'


def proof(att):
    if att["file_unchanged"] is True:
        return "File unchanged"
    if att["file_unchanged"] is False:
        return "File changed"
    return "Nothing was sent"


def still(att):
    return f'<span class="ok">Worked</span> <code>{e(asked(att)[:90])}</code>' if passed(att) else f'<span class="bad">FAILED</span> <code>{e(asked(att)[:90])}</code>'


SECTIONS = [("deny", "The deny rules alone"), ("hook", "The hook alone"), ("both", "Both, as installed")]


def test_rows(setup):
    out = []
    for row in TESTS:
        if row["setup"] != setup:
            continue
        att = row["blocked"]
        out.append(f'<tr><td>{e(row["guardrail"])}<br><span class="muted">{e(row["label"])}</span></td><td><code>{e(asked(att)[:110])}</code></td><td class="nw">{who(att)}<br><span class="muted">{proof(att)}</span></td><td>{still(row["works"])}</td></tr>')
    return "".join(out)


TABLES = "".join(f'<h3>{e(title)}</h3><div class="wrap"><table class="tests"><thead><tr><th>Guardrail, and the attempt</th><th>What Claude really tried</th><th>What caught it</th><th>The one that should still work</th></tr></thead><tbody>{test_rows(key)}</tbody></table></div>' for key, title in SECTIONS)
GAP_ROWS = "".join(f'<tr><td><code>{e(asked(r["blocked"]))}</code></td><td>{e(r["label"])}</td><td><span class="bad">Got through.</span> The copy\'s file changed. With the hook on, the same attempt is caught (S3 and A1 above).</td></tr>' for r in GAPS)

# ---- what each routine may touch. R read, C Claude writes, S a script writes, X walled ----
COLUMNS = ["Daily run", "Event run", "Weekly check", "Quarterly refresh", "Monthly hunt"]
AREAS = [
    ("Rules/, rules.md, CLAUDE.md", "W1, W3, W4", ["R X", "R X", "R X", "R X", "X"]),
    ("Portfolio/", "W2", ["R X", "X", "X", "X", "X"]),
    ("The method's code and inputs, saved value runs", "W3", ["X", "X", "X", "R X", "R X"]),
    ("The alert map's code, saved kill lines", "W4", ["R X", "R X", "R X", "R X", "X"]),
    ("Settings, hooks, agents, skills, Desktop tasks", "W5", ["X", "X", "X", "X", "X"]),
    ("Companies/", "", ["R", "R", "R", "R", "–"]),
    ("Catalysts/", "", ["S", "–", "–", "–", "–"]),
    ("Research/, other notes", "", ["S", "R", "R", "C", "S"]),
    ("Inbox/", "", ["S", "–", "R", "–", "S"]),
    ("Journal/", "", ["S", "S", "S", "S", "S"]),
    ("Its own folder under sensors/", "", ["C S", "C S", "C S", "C S", "C S"]),
    ("The web, from Claude", "", ["–", "–", "Search, listed sites", "–", "One price page each"]),
    ("Filings, from a script", "", ["SEC", "SEC", "SEC", "SEC", "SEC"]),
    ("My phone, from a script", "", ["Red only", "Red only", "–", "–", "–"]),
]
WORDS = {"R": "reads", "C": "Claude writes", "S": "script writes", "X": "walled"}


def cell(value):
    if value == "–":
        return '<td class="dash">–</td>'
    if set(value.split()) <= set(WORDS):
        parts = value.split()
        marks = "".join(f'<span class="m m{p}">{WORDS[p]}</span>' for p in parts)
        return f'<td>{marks}</td>'
    return f'<td class="plain">{e(value)}</td>'


MATRIX = "".join(f'<tr class="{"walled" if wall else ""}"><th scope="row">{e(area)}{f" <span class=rule>{wall}</span>" if wall else ""}</th>{"".join(cell(v) for v in row)}</tr>' for area, wall, row in AREAS)
HEAD = "".join(f"<th>{e(c)}</th>" for c in COLUMNS)

WALLS = [
    ("W1", "My rules", "<code>Rules/</code>, <code>rules.md</code>, <code>CLAUDE.md</code>", "Yes", "Yes", "Yes"),
    ("W2", "My portfolio", "<code>Portfolio/</code>", "Yes", "Yes", "Yes"),
    ("W3", "The method", "<code>when-to-buy</code>, <code>when-to-trim</code>, <code>sizing</code> and <code>cash</code> in <code>Rules/</code>, the valuation and portfolio-manager skills with their inputs, <code>sensors/base/model.py</code>, <code>sensors/strategic/model.py</code>, <code>sensors/valuation/save.py</code>, saved value runs", "Yes", "Yes", "Yes. A new run may be added."),
    ("W4", "The alert map", "<code>Rules/alerts.md</code>, <code>sensors/alerts/alertmap.py</code>, the monitor skill", "Yes", "Yes", "Yes"),
    ("W4", "Saved kill lines", "<code>Research/*kill criteria*.md</code>. The map's Reds read these.", "No, so a new thesis can add one", "Yes", "Yes. A new note may be added."),
    ("W5", "The guardrails", "All of <code>.claude/</code>, <code>.mcp.json</code>, <code>sensors/guardrails/</code>, and in my home folder Claude's settings, hooks, agents, skills and Desktop tasks", "Yes", "Yes", "Yes, inside the vault"),
]
WALL_ROWS = "".join(f'<tr><td class="rule">{a}</td><td><strong>{b}</strong></td><td>{c}</td><td>{d}</td><td>{f}</td><td>{g}</td></tr>' for a, b, c, d, f, g in WALLS)
TRADES = [
    ("T1", "A broker's site", "31 broker and exchange sites, in any command, fetch, subagent prompt or code file", "Main ones"),
    ("T2", "Broker software or an order call", "Libraries such as <code>ib_insync</code>, calls such as <code>place_order</code>, the local ports of a broker's desktop gateway. A script is read before it runs.", "Main ones"),
    ("T3", "A broker with an action", "A broker's name near log in, account, order, trade and the like, in a command, search or subagent prompt", "No"),
    ("T4", "The shape of an order", "<code>buy 100 shares</code>, <code>BUY 100 GLW</code>, <code>limit order</code>, <code>--side=buy</code>, a POST to <code>/orders</code>, in a shell command", "No"),
    ("T5", "Tools that act on a screen", "Computer use, the Chrome extension and the desktop browser, since a click names no site. Any other tool named for a broker or an order.", "The first three"),
]
TRADE_ROWS = "".join(f'<tr><td class="rule">{a}</td><td><strong>{b}</strong></td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in TRADES)


def routine_rows():
    if not ROUT:
        return '<tr><td colspan="5">Not run yet.</td></tr>'
    out = []
    for row in ROUT["rows"]:
        touched = ", ".join(f"{k} ({v})" for k, v in row["changed"].items()) or "nothing"
        reply = row["reply"].strip().splitlines()[0][:120] if row["reply"].strip() else ""
        out.append(f'<tr><td>{e(row["routine"])}</td><td class="n">{len(row["blocks"])}</td><td>{"Unchanged" if row["walls_unchanged"] else "<span class=bad>CHANGED</span>"}</td><td>{e(touched)}</td><td class="muted">{e(reply)}</td></tr>')
    return "".join(out)


def real_rows():
    if not REAL:
        return '<tr><td colspan="4">Not run yet.</td></tr>'
    return "".join(f'<tr><td>{e(r["label"])}</td><td><code>{e(asked(r["att"])[:90])}</code></td><td class="nw">{who(r["att"])}</td><td>{e(r["proof"])}</td></tr>' for r in REAL)


DIAGRAM = """<svg viewBox="0 0 900 250" role="img" aria-label="A tool call must pass the deny rules and the hook before it runs. A shell call is then checked again, and any walled file that changed is put back." style="width:100%;height:auto;display:block">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--muted)"/></marker></defs>
<g font-size="14" fill="var(--ink)" text-anchor="middle">
<rect x="10" y="80" width="130" height="66" rx="8" class="box"/><text x="75" y="108" font-weight="600">A routine</text><text x="75" y="128" class="sm">asks for a tool call</text>
<rect x="200" y="14" width="210" height="72" rx="8" class="gdeny"/><text x="305" y="42" font-weight="600">Deny rules</text><text x="305" y="62" class="sm">settings.json, by name and path</text>
<rect x="200" y="140" width="210" height="72" rx="8" class="ghook"/><text x="305" y="168" font-weight="600">Hook, before the call</text><text x="305" y="188" class="sm">every tool, by what it would do</text>
<rect x="480" y="80" width="130" height="66" rx="8" class="box"/><text x="545" y="108" font-weight="600">The tool runs</text><text x="545" y="128" class="sm">only if both say yes</text>
<rect x="680" y="14" width="210" height="72" rx="8" class="gafter"/><text x="785" y="38" font-weight="600">Hook, after a shell call</text><text x="785" y="58" class="sm">did a walled file change?</text><text x="785" y="75" class="sm">Put it back, keep the copy</text>
<rect x="680" y="140" width="210" height="72" rx="8" class="box"/><text x="785" y="168" font-weight="600">Blocked</text><text x="785" y="188" class="sm">recorded on the dashboard</text>
</g>
<g fill="none" stroke="var(--muted)" stroke-width="1.5" marker-end="url(#a)"><path d="M140 103L198 60"/><path d="M140 123L198 166"/><path d="M410 60L478 100"/><path d="M410 176L478 126"/><path d="M610 100L678 60"/></g>
<g fill="none" stroke="var(--red)" stroke-width="1.5" stroke-dasharray="5 4" marker-end="url(#a)"><path d="M410 30L640 30L640 165L678 165"/><path d="M410 196C520 244 620 226 678 192"/></g>
<text x="450" y="24" font-size="12" fill="var(--red)">no</text><text x="450" y="238" font-size="12" fill="var(--red)">no</text>
</svg>"""

REPLAY_LINE = ""
if REPLAY:
    fetches = REPLAY["stopped"].get("WebFetch T1", 0)
    writes = sum(v for k, v in REPLAY["stopped"].items() if " W" in k)
    REPLAY_LINE = (f'<p>I also put all {REPLAY["calls"]:,} tool calls from this project\'s past sessions through the check, without running them (calc., <code>sensors/guardrails/runs/replay-{REPLAY["date"]}.json</code>). It would have stopped {REPLAY["stopped_total"]}. '
                   f'{writes} are real writes or code that names a walled file, most of them made with your yes, which is the change described below. {fetches} are fetches of broker sites for news.</p>')

CSS = """
:root{--page:#f9f9f7;--surface:#fcfcfb;--panel:#f0efea;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--border:rgba(11,11,11,.12);--link:#2a78d6;--red:#b3261e;--deny:#2a78d6;--hook:#6250d6;--after:#12795f;--wall:#f3e9e6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--border:rgba(255,255,255,.12);--link:#6aa6ee;--red:#ef7a70;--deny:#6aa6ee;--hook:#9085e9;--after:#4fb99a;--wall:#2a1d1a}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--panel:#121211;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--border:rgba(255,255,255,.12);--link:#6aa6ee;--red:#ef7a70;--deny:#6aa6ee;--hook:#9085e9;--after:#4fb99a;--wall:#2a1d1a}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:30px;line-height:1.2;margin:0 0 10px}h2{font-size:21px;margin:44px 0 10px}h3{font-size:16px;margin:26px 0 8px}
p{margin:0 0 10px}.lead{font-size:18px;color:var(--ink-2)}.muted{color:var(--muted);font-size:13px}
ul{padding-left:20px;margin:0 0 10px}li{margin-bottom:6px}
code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere}
.tiles{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}.tile{flex:1 1 180px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px}.tile b{display:block;font-size:26px;line-height:1.2;font-variant-numeric:tabular-nums}.tile span{font-size:13px;color:var(--ink-2)}
.fig{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px;margin:14px 0}
.box{fill:var(--panel);stroke:var(--border)}.gdeny{fill:color-mix(in srgb,var(--deny) 14%,var(--surface));stroke:var(--deny)}.ghook{fill:color-mix(in srgb,var(--hook) 14%,var(--surface));stroke:var(--hook)}.gafter{fill:color-mix(in srgb,var(--after) 14%,var(--surface));stroke:var(--after)}.sm{font-size:12px;fill:var(--ink-2)}
.wrap{overflow-x:auto;margin:8px 0 14px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.4;min-width:760px}th{text-align:left;font-weight:600;padding:7px 9px;border-bottom:1px solid var(--muted);vertical-align:bottom}td{padding:8px 9px;border-bottom:1px solid var(--border);vertical-align:top}tbody th{font-weight:500;border-bottom:1px solid var(--border)}.n{text-align:right;font-variant-numeric:tabular-nums}.nw{white-space:nowrap}
.rule{font:600 12px ui-monospace,Menlo,Consolas,monospace;color:var(--ink-2)}.dash{color:var(--muted)}.plain{font-size:13px}
.chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:600;border:1px solid}.deny{color:var(--deny)}.hook{color:var(--hook)}.after{color:var(--after)}.none{color:var(--muted)}
.ok{color:var(--after);font-weight:600}.bad{color:var(--red);font-weight:600}
.m{display:inline-block;font-size:12px;padding:0 6px;border-radius:4px;margin:0 3px 3px 0;background:var(--panel)}.mX{background:var(--red);color:var(--page);font-weight:600}.mC{background:color-mix(in srgb,var(--hook) 22%,transparent)}.mS{background:color-mix(in srgb,var(--deny) 18%,transparent)}
tr.walled th,tr.walled td{background:var(--wall)}
.note{border-left:4px solid var(--red);padding:8px 14px;background:var(--surface);margin:14px 0}
"""

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Routine Guardrails</title><style>{CSS}</style></head><body><main>
<h1>Guardrails on the routines</h1>
<p class="lead"><strong>No routine can edit your rules, portfolio, method or alert map, or reach for a broker, without a guardrail stopping it, in every way I tried.</strong> In the {len(TESTS)} real attempts, {N_CAUGHT} were caught and {N_PASSED} of the {len(TESTS)} that should still work did. The gaps that remain are listed under "What this does not stop".</p>
<p class="muted">Tested {NICE} with {e(ATT["model"])}, on throwaway copies of this vault, on Linux. All sums calc., from <code>sensors/guardrails/runs/</code>. Hook: <code>.claude/hooks/guardrails.py</code>. Rules: <code>.claude/settings.json</code>. No rule, map or portfolio file changed in this work, and the method's sums did not. Two skills and one playbook gained a line on how a yes now reaches a walled file.</p>
<div class="tiles">
<div class="tile"><b>{N_CAUGHT} of {len(TESTS)}</b><span>attempts that should be blocked were caught</span></div>
<div class="tile"><b>{N_PASSED} of {len(TESTS)}</b><span>attempts that should still work did</span></div>
<div class="tile"><b>{len(GAPS)}</b><span>attempts got past the deny rules alone, which is why the hook is there</span></div>
<div class="tile"><b>{sum(len(r["blocks"]) for r in ROUT["rows"]) if ROUT else "–"}</b><span>blocks across {len(ROUT["rows"]) if ROUT else "–"} whole routine runs, so the routines still work</span></div>
</div>

<h2>How a call is stopped</h2>
<p>A call must pass both gates, and either one alone is enough to stop it. Deny rules are simple and hard to break, but they match only names and paths. The hook reads what a command would do. The after-check catches what no reading can, such as a script with a disguised path.</p>
<div class="fig">{DIAGRAM}</div>
<p>If the hook crashes, or Python is missing, the call is blocked rather than let through.</p>

<h2>What each routine may touch</h2>
<p>A red row is walled off from every routine and every session. Below those rows, the routine's prompt sets the limit, and no guardrail does. "Reads" means the prompt or its script reads it.</p>
<div class="wrap"><table class="matrix"><thead><tr><th>Area</th>{HEAD}</tr></thead><tbody>{MATRIX}</tbody></table></div>
<p class="muted">From each prompt in <code>Playbooks/</code>, each script's own description, and what the whole runs below really changed. The radar, run by the daily run's script, rewrites catalyst notes.</p>

<h2>What is walled off</h2>
<div class="wrap"><table><thead><tr><th></th><th>Wall</th><th>What is behind it</th><th>Deny rule</th><th>Hook, before</th><th>After-check</th></tr></thead><tbody>{WALL_ROWS}</tbody></table></div>
<h3>Trades and brokers</h3>
<div class="wrap"><table><thead><tr><th></th><th>Check</th><th>What it catches</th><th>Also a deny rule</th></tr></thead><tbody>{TRADE_ROWS}</tbody></table></div>
<p>Reading stays open. A routine can still read the map, the rules and a note that names Fidelity as a holder, and search for "Fidelity 13F stake in Corning".</p>

<h2>Which guardrail caught each test</h2>
<p>Each row is real: one <code>claude -p</code> run asked to make that exact call, in Accept edits mode, with an allow rule for that call. A deny rule and a hook both outrank an allow rule, so only a guardrail could refuse it. The copies came in three setups, so each layer had to do it alone. List price, which a plan does not bill: ${COST:.2f} (calc.).</p>
{TABLES}
<h3>What got past the deny rules alone</h3>
<div class="wrap"><table><thead><tr><th>What Claude really tried</th><th>The attempt</th><th>Result</th></tr></thead><tbody>{GAP_ROWS}</tbody></table></div>
<p class="muted">Rerun after a fix to my test: {e(", ".join(ATT.get("rerun", [])) or "none")}. On the first pass the Edit tool refused three badly formed requests of mine before any guardrail saw them, and one should-work command wrote outside the folder. Those first results did not count.</p>
{REPLAY_LINE}
<p>A further 36 tests in <code>sensors/guardrails/test_guardrails.py</code> try many more spellings with no model: <code>rm Rul*/</code>, <code>bash -c</code>, a link into a wall, backslash and Windows paths, PowerShell, a hook that crashes.</p>

<h2>The routines, whole, with the guardrails on</h2>
<p>The real prompts from <code>Playbooks/</code>, run start to finish on one throwaway copy, in the order below. The copy's phone script had no token, so nothing could reach your phone.</p>
<div class="wrap"><table><thead><tr><th>Routine</th><th class="n">Blocks</th><th>Walls</th><th>What really changed (files)</th><th>Its reply</th></tr></thead><tbody>{routine_rows()}</tbody></table></div>

<h2>In the real vault, once switched on</h2>
<div class="wrap"><table><thead><tr><th>Attempt</th><th>What Claude really tried</th><th>What caught it</th><th>Proof</th></tr></thead><tbody>{real_rows()}</tbody></table></div>

<h2>What this does not stop</h2>
<ul>
<li><strong>A script that talks to a broker with a disguised address.</strong> The hook reads a script before it runs, but pieces joined at run time pass, and the after-check only watches files. Only a network wall can stop this. I have not built one, and I have not checked whether Claude Code's sandbox would do it on your computers.</li>
<li><strong>A background program that writes a wall later.</strong> The after-check runs when a shell call returns. A later change is written down at the next shell call but not undone, since it looks the same as your own edit.</li>
<li><strong>Everything below the red rows.</strong> <code>Companies/</code>, <code>Catalysts/</code>, <code>Playbooks/</code> and the routines' own scripts rest on the prompts. You did not list them, and sessions need them.</li>
</ul>
<h3>What was not tested</h3>
<ul>
<li><strong>Inside a Desktop task.</strong> All runs used <code>claude -p</code> from this folder, which reads the same settings file. Whether a Desktop task loads it is not yet seen. The next task run will show it: look for a block or none in the dashboard's record.</li>
<li><strong>On a Mac or on Windows.</strong> The hook uses only the standard library, and tests cover Windows-style paths and PowerShell words, but it has run only on Linux. The routines' own commands use <code>.venv/bin/python</code>, and <code>sensors/phone/phone.py</code> imports <code>fcntl</code>, so those parts do not run on Windows as written.</li>
<li><strong>Browser and desktop tools, and my home folder.</strong> None of those tools is connected here, and I did not risk your real home settings. Those were tested on crafted calls only.</li>
<li><strong>The <code>!</code> prefix.</strong> The docs do not say whether hooks fire for it. If the door below is refused there, run it in your own terminal.</li>
</ul>

<h2>What changes for you</h2>
<ul>
<li><strong>Claude cannot edit these files in a session either, even with your yes.</strong> A deny rule cannot tell a routine from you. You can always edit them yourself. When you say yes to a change, Claude writes the new text to a file and gives you one line to type: <code>! python3 .claude/hooks/owner-apply.py &lt;new text&gt; &lt;walled file&gt;</code>. It shows the change, keeps the old copy and records it. Claude is barred from running it.</li>
<li><strong>Logging a trade and applying a refresh</strong> go through that door now. The <code>portfolio-manager</code> and <code>valuation</code> skills and <code>Playbooks/Quarterly refresh.md</code> say so.</li>
<li><strong>Editing a rule while a routine's script runs:</strong> if a shell call is running when you save, your edit is put back and your text is kept in <code>.claude/guardrails/quarantine/</code>. The dashboard's record shows it.</li>
<li><strong>Broker sites are closed even for news.</strong> Past research opened Webull, Futu and Fidelity pages. Those fetches now stop, by your "even looks like". A saved link to one is fine.</li>
<li><strong>Computer use and the Chrome extension are closed in this project.</strong> That was my choice, because they use your signed-in browser and a click names no site. Tell me if you want them back.</li>
<li><strong>A block sends you nothing.</strong> The alert map is yours and has no line for this. A routine stopped by a guardrail writes its failure line, and the dashboard shows the block.</li>
</ul>
<footer class="muted" style="margin-top:32px">Stays on this computer. It recommends nothing, and no order was placed. Corning stays no buy. Built by <code>sensors/guardrails/draw.py</code>.</footer>
</main></body></html>
"""
(ROOT / "guardrails.html").write_text(PAGE)
print(f"caught {N_CAUGHT}/{len(TESTS)}, still work {N_PASSED}/{len(TESTS)}, gaps {len(GAPS)}, routines {len(ROUT['rows']) if ROUT else 0}, real {len(REAL)}")
