#!/usr/bin/env python3
"""Checks value.py against the approved model in sensors/. The two share no code. Run from the project root."""
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
INPUTS = HERE.parent / "assets/corning-2026-11-03.json"
spec = importlib.util.spec_from_file_location("value", HERE / "value.py"); v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
s2 = importlib.util.spec_from_file_location("m", ROOT / "sensors/strategic/model.py"); m = importlib.util.module_from_spec(s2); s2.loader.exec_module(m)


def run(*a, data=None):
    path = str(INPUTS)
    if data is not None:
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(data, f); f.close(); path = f.name
    return subprocess.run([sys.executable, str(HERE / "value.py"), path, *a], capture_output=True, text=True)


d = json.load(open(INPUTS, encoding="utf8"))
inp = v.Inputs(); b = v.base(d, inp)
rows, mult = v.strategic(d, b, inp, {})
assert not inp.problems, inp.problems
want = m.compare()
for k in ("low", "mid", "high"):
    assert abs(b["combined"][k] - want["base"][k]) < 0.005, k
s = sum(r["value"] for r in rows)
assert abs(s - want["strategic"]) < 0.005, s
assert abs(mult - m.multiple()) < 1e-4
for r, x in zip(rows, m.scenarios()):
    assert r["key"] == x["key"] and abs(r["full"] - x["full"]) < 0.005, r["key"]
rows2, _ = v.strategic(d, b, v.Inputs(), {"plan": 0.6})
assert abs(b["combined"]["mid"] + sum(r["value"] for r in rows2) - m.trim_above(prob=dict(plan=.6))) < 0.005
assert abs(v.growth_needed(123.20, 1505 / 871) - m.base_model.need(123.20, 1505 / 871, .09)) < 1e-4

out = run().stdout
for text in ("17.6%", "$14.06", "$21.73", "$30.03", "$28.97", "$14.33", "$36.06"):
    assert text in out, text
# Moving the price moves neither line.
out30 = run("--price", "30").stdout
assert "$28.97" in out30 and "$36.06" in out30 and "WHAT-IF" in out30 and "not met" in out30
assert "Bar 75%: met" in run("--price", "28").stdout
# It stops on what the rules bar.
bad = json.loads(json.dumps(d)); bad["inputs"]["growth"]["high"]["v"] = 0.05
assert run(data=bad).returncode == 2
bad = json.loads(json.dumps(d)); bad["inputs"]["shares_diluted_m"]["src"] = "memory"
assert run(data=bad).returncode == 2
bad = json.loads(json.dumps(d)); bad["inputs"]["earnings_m"]["mid"]["v"] = None
assert run(data=bad).returncode == 2
assert run("--help").returncode == 2
# No scenarios means not worked out, never zero.
none = json.loads(json.dumps(d)); none["scenarios"] = []
o = run(data=none).stdout
assert "not worked out" in o and "Trim-above: unknown" in o
# An unapproved chance is flagged.
pro = json.loads(json.dumps(d)); pro["scenarios"][0]["chance"]["status"] = "proposed"
assert "proposals until" in run(data=pro).stdout
# Aaa a point away reopens the 9%.
aaa = json.loads(json.dumps(d)); aaa["inputs"]["aaa"]["v"] = 0.0712
assert "reopens" in run(data=aaa).stdout
# The loss line, a what-if label on changed inputs, a broken shape, and open items.
o = run().stdout
assert "82% to the base middle, 89% to the low" in o and "Open item" not in o
wi = json.loads(json.dumps(d)); wi["what_if"] = True; wi["inputs"]["earnings_m"]["mid"]["v"] = 2524
o = run(data=wi).stdout
assert "WHAT-IF" in o and "out of order" in o
print("all passed")
