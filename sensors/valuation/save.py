"""Save one valuation run for the dashboard. It works no sums of its own: every figure comes from the valuation skill's value.py.

Run from the project root, by hand:
    .venv/bin/python sensors/valuation/save.py

It writes two new files and changes nothing else. A second run the same day gets its own files:
    sensors/valuation/runs/YYYY-MM-DD-NN.md     value.py's output, word for word
    sensors/valuation/runs/YYYY-MM-DD-NN.json   the same figures, the prices, and the what-ifs. The dashboard reads this.

No network. It reads the newest saved prices and never fetches any. It holds a Yahoo price, so keep it on this computer.
It stops, as the skill says, if the inputs disagree with the Corning note, if a newer 10-Q or 10-K is on file, or if Aaa changed.

The what-ifs change one assumption at a time. They are not the method's answer, and they go nowhere but this run.
Each reading rests on a filed figure, the method's own range, a line in the rules, or what the owner asked on Nov. 3, 2026.
"""

import contextlib
import copy
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RUNS = HERE / "runs"
SKILL = ROOT / ".claude/skills/valuation"
VALUE_PY = SKILL / "scripts/value.py"
NOTE = ROOT / "Companies/Corning.md"
AAA_CSV = ROOT / "sensors/macro/downloads/AAA.csv"
FILINGS = ROOT / "sensors/edgar/cache/CIK0000024741/filings.jsonl"
SCHEMA = 1

sys.path.insert(0, str(ROOT / "sensors/prices"))
import prices  # noqa: E402

_spec = importlib.util.spec_from_file_location("valuation_value", VALUE_PY)
value = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(value)

Stop = value.Stop
METHOD_RATE, METHOD_VOTES = value.RATE, dict(value.VOTES)
OUTPUTS = ("base", "buy", "trim")
Q10 = "[10-Q, filed Oct. 29, 2026](https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm)"
K8_WARRANT = "[8-K, May 6, 2026](https://www.sec.gov/Archives/edgar/data/24741/000120677426000273/glw4631061-8k.htm)"
Q1 = "[Q1 release, Apr. 28, 2026](https://www.sec.gov/Archives/edgar/data/24741/000002474126000198/glw-20260328xex991xq12026.htm)"


# ---- The sums, always value.py's ----

@contextlib.contextmanager
def _method(rate=None, votes=None):
    """value.py fixes the 9% and the votes as constants, and cash_sum holds its 9% as a default. A what-if on either sets all of them, then puts them back."""
    saved = value.RATE, value.VOTES, value.cash_sum
    rate = METHOD_RATE if rate is None else rate
    value.RATE, value.VOTES = rate, dict(METHOD_VOTES if votes is None else votes)
    value.cash_sum = lambda cash, g, r=rate: saved[2](cash, g, r)
    try:
        yield
    finally:
        value.RATE, value.VOTES, value.cash_sum = saved


def zone(mid, price, buy, trim):
    """Where a price sits against the two lines. Compares unrounded figures, as the rule does: 74.9% is not 75%."""
    under, above = mid / price >= value.COVER_BAR, price > trim
    if under and above:  # possible only if strategic value is under a third of the middle
        return "under_and_above"
    return "under" if under else "above" if above else "between"


def work(d, price, rate=None, votes=None):
    inp = value.Inputs()
    with _method(rate, votes):
        b = value.base(d, inp)
        if b is None:
            raise Stop("\n".join(inp.problems))
        rows, mult = value.strategic(d, b, inp, {})
    if inp.problems:
        raise Stop("\n".join(inp.problems))
    c = b["combined"]
    s = sum(r["value"] for r in rows)
    out = dict(low=c["low"], base=c["mid"], high=c["high"], strategic=s, buy=c["mid"] / value.COVER_BAR, trim=c["mid"] + s,
               multiple=mult, b=b, rows=rows, used=inp.used)
    return out


def _flags(result, d, price):
    c = {s["key"]: s["chance"]["v"] for s in d["scenarios"]}
    flags = []
    if not result["low"] <= result["base"] <= result["high"]:
        flags.append("breaks the base's order: low, middle, high")
    if not c["signed"] >= c["plan"] >= c["scaleup"]:
        flags.append("breaks the ladder: a higher step beats the one under it")
    if result["trim"] < result["buy"]:
        flags.append("the trim-above falls under the buy-below")
    return flags


# ---- One assumption at a time ----

def _scenario(d, key):
    return next(s for s in d["scenarios"] if s["key"] == key)


def _set(node, v):
    node["v"] = v


def _reading(text, change=None, rate=None, votes=None, after=None):
    return dict(text=text, change=change, rate=rate, votes=votes, after=after)


def _base_input(group, point="mid"):
    return lambda v: (lambda d: _set(d["inputs"][group][point], v))


def _chance(key):
    return lambda v: (lambda d: _set(_scenario(d, key)["chance"], v))


OPTICAL = ("signed", "plan", "scaleup")


def _margin(m):
    """The Optical margin, and the rival cut measured from it, as sensors/strategic/model.py does."""
    def change(d):
        first = _scenario(d, "signed")["margin"]["v"]
        floor = first - _scenario(d, "rival")["margin_cut"]["v"]
        for key in OPTICAL:
            _set(_scenario(d, key)["margin"], m)
        _set(_scenario(d, "rival")["margin_cut"], max(m - floor, 0))
    return change


def _ladder_step(key, new_sales):
    """The plan is what is left on the ladder to the $35 billion target, so a change to another step comes back out of it."""
    def change(d):
        node = _scenario(d, key)["new_sales_m"]
        gap = new_sales - node["v"]
        _set(node, new_sales)
        plan = _scenario(d, "plan")["new_sales_m"]
        _set(plan, plan["v"] - gap)
    return change


def _no_capital(d):
    for s in d["scenarios"]:
        if "capital_per_sale" in s:
            _set(s["capital_per_sale"], 0)
        if "extra_capital_m" in s:
            _set(s["extra_capital_m"], 0)


def _capital_lost(result, d):
    """If the plants get built and a fiber scenario fails, the capital is lost. Same sum as model.failed_capital()."""
    lost = sum((1 - r["chance"]) * r["kpv"] / result["b"]["shares"] for r in result["rows"] if r["key"] in OPTICAL)
    return {**result, "strategic": result["strategic"] - lost, "trim": result["trim"] - lost}


def _from_high(result, d):
    return {**result, "trim": result["high"] + result["strategic"]}


def assumptions(d):
    """Each row: an assumption, its method's reading, and the other readings. Sizes come from the sources named, never made up."""
    x = d["inputs"]
    pct = lambda v, n=0: f"{v * 100:.{n}f}%"  # noqa: E731
    chance_basis = ("Half to double the owner's chance, capped at 100%. Doubling is the what-if the owner asked for on Nov. 3, 2026 (Journal). "
                    "Halving is Claude's mirror of it.")
    rows = [
        dict(key="earnings", label="Normal earnings, middle", method=f'${x["earnings_m"]["mid"]["v"]:,.0f}M', scope="base",
             readings=[_reading(f'${x["earnings_m"][k]["v"]:,.0f}M', _base_input("earnings_m")(x["earnings_m"][k]["v"])) for k in ("low", "high")],
             basis="The method's own low (ten-year average) and high (last twelve months) in place of the last audited year. " + x["earnings_m"]["high"]["src"]),
        dict(key="cash", label="Cash with deposits out, middle", method=f'${x["cash_m"]["mid"]["v"]:,.0f}M', scope="base",
             readings=[_reading(f'${x["cash_m"][k]["v"]:,.0f}M', _base_input("cash_m")(x["cash_m"][k]["v"])) for k in ("low", "high")],
             basis="The method's other two cash readings. " + x["cash_m"]["high"]["src"]),
        dict(key="growth", label="Cash growth, middle", method=pct(x["growth"]["mid"]["v"], 2), scope="base",
             readings=[_reading(pct(x["growth"][k]["v"]), _base_input("growth")(x["growth"][k]["v"])) for k in ("low", "high")],
             basis="The method's low (no growth) and its 3% cap. `base.html`, Nov. 3, 2026."),
        dict(key="rate", label="The 9% rate", method="9%", scope="base",
             readings=[_reading("8%", rate=.08), _reading("10%", rate=.10)],
             basis="A point either way, the step at which the rule reopens the 9%, and the two rates `strategic.html` shows, Nov. 3, 2026. Changes every vote that uses it and every scenario."),
        dict(key="aaa", label="Aaa yield", method=pct(x["aaa"]["v"], 2), scope="base",
             readings=[_reading(pct(x["aaa"]["v"] + s, 2), lambda d, s=s: _set(d["inputs"]["aaa"], d["inputs"]["aaa"]["v"] + s)) for s in (-.01, .01)],
             basis="A point either way, the step named in the rule. " + x["aaa"]["src"]),
        dict(key="shares", label="Diluted shares", method=f'{x["shares_diluted_m"]["v"]:,.0f}M', scope="base",
             readings=[_reading("861.4M", lambda d: _set(d["inputs"]["shares_diluted_m"], 861.4)),
                       _reading("889M", lambda d: _set(d["inputs"]["shares_diluted_m"], 889))],
             basis=f"861.4M is shares out, {Q10}. 889M adds all 18M NVIDIA warrant shares to the 871M, {K8_WARRANT}, ignoring the cash they would bring. Whether any are already in the 871M was not checked."),
        dict(key="votes", label="The votes, all on one", method="40, 40, 20", scope="base", ends=True,
             readings=[_reading("all on earnings ÷ 9%", votes=dict(earn=1, cash=0, bond=0)),
                       _reading("all on the cash sum", votes=dict(earn=0, cash=1, bond=0)),
                       _reading("all on earnings ÷ Aaa", votes=dict(earn=0, cash=0, bond=1))],
             basis="The ends of the approved votes, with no weight chosen in between. In both the base and the multiple on new profit. `strategic.html` shows the earnings vote alone, Nov. 3, 2026."),
    ]
    names = dict(signed="Chance: signed fiber deals ship", plan="Chance: rest of the high-confidence plan", scaleup="Chance: optical scale-up",
                 solar="Chance: Solar reaches its goal", display="Chance: display price rises last", rival="Chance: rival capacity cuts the margin")
    for key, label in names.items():
        now = _scenario(d, key)["chance"]["v"]
        rows.append(dict(key=f"chance_{key}", label=label, method=pct(now), scope="trim",
                         readings=[_reading(pct(now / 2, 1 if key == "solar" else 0), _chance(key)(now / 2)), _reading(pct(min(now * 2, 1)), _chance(key)(min(now * 2, 1)))],
                         basis=chance_basis))
    first = _scenario(d, "signed")
    m0 = first["margin"]["v"]
    floor = m0 - _scenario(d, "rival")["margin_cut"]["v"]
    added = (532 - 295) / (2379 - 1652)  # Optical Q3 2026 against Q3 2025, 10-Q, as model.OPT_INCREMENTAL
    ceiling = first["new_sales_m"]["v"] / .75
    disp = _scenario(d, "display")["new_sales_m"]["v"] / .05
    rows += [
        dict(key="margin", label="Optical margin on new sales", method=pct(m0, 1), scope="trim",
             readings=[_reading(pct(floor, 1), _margin(floor)), _reading(pct(added, 1), _margin(added))],
             basis=f"17.9% is Q4 2025. 32.6% is what the last year's added sales earned (calc.). Both on `strategic.html`, Nov. 3, 2026; {Q10}; {Q1}. The rival cut is measured from it, so it shrinks as well."),
        dict(key="new_share", label="Share of signed deals that is new sales", method="75%", scope="trim",
             readings=[_reading("50%", _ladder_step("signed", ceiling * .5)), _reading("100%", _ladder_step("signed", ceiling))],
             basis="The 75% is an assumption with no source. 50% is on `strategic.html`, Nov. 3, 2026. 100% is the end of the range. What leaves this step goes to the plan's step, so the ladder still adds up."),
        dict(key="display_rise", label="Display price rise", method="5%", scope="trim",
             readings=[_reading("0%", _ladder_step("display", 0)), _reading("10%", _ladder_step("display", disp * .10))],
             basis="The 5% is an assumption: the amount is undisclosed. 10% is on `strategic.html`, Nov. 3, 2026. 0% is no rise. The plan's step takes the difference."),
        dict(key="capital", label="Capital charge on new sales", method="charged, none lost", scope="trim", ends=True,
             readings=[_reading("lost when a fiber scenario fails", after=_capital_lost), _reading("none: customers fund every plant", _no_capital)],
             basis="The two ends on `strategic.html`, Nov. 3, 2026."),
        dict(key="from_high", label="Trim-above starts from the base high", method="base middle", scope="trim",
             readings=[_reading("base high", after=_from_high)],
             basis="The owner chose the middle on Nov. 3, 2026. The high is the known gap in `references/strategic.md`: profit since the last audited year is in neither the middle nor a scenario."),
    ]
    return rows


NOT_RUN = ("The 75% bar: fixed by the rule, with no other reading on file.",
           "Years away, the capital ratio alone, Solar's profit and the sizes of the plan and scale-up steps: no sourced other reading, so no size was made up. Their slopes are in the table.")


def _apply(d, price, reading):
    trial = copy.deepcopy(d)
    if reading["change"]:
        reading["change"](trial)
    result = work(trial, price, reading["rate"], reading["votes"])
    if reading["after"]:
        result = reading["after"](result, trial)
    return result, _flags(result, trial, price)


def what_ifs(d, price, method):
    rows, zones = [], zone(method["base"], price, method["buy"], method["trim"])
    for a in assumptions(d):
        readings = []
        for r in a["readings"]:
            result, flags = _apply(d, price, r)
            readings.append(dict(text=r["text"], base=result["base"], buy=result["buy"], trim=result["trim"], coverage=result["base"] / price,
                                 zone=zone(result["base"], price, result["buy"], result["trim"]), flags=flags))
        row = dict(key=a["key"], label=a["label"], method=a["method"], scope=a["scope"], basis=a["basis"], ends=bool(a.get("ends")), readings=readings, swing={})
        for out in OUTPUTS:
            values = [method[out]] + [r[out] for r in readings]
            row["swing"][out] = max(values) - min(values)
        rows.append(row)
    ranked = {out: [r["key"] for r in sorted(rows, key=lambda r: -r["swing"][out]) if r["swing"][out] > 1e-9] for out in OUTPUTS}
    changed = [r["key"] for r in rows for x in r["readings"] if x["zone"] != zones]
    # "Most" leaves out far ends of a method choice, and any reading that breaks the method's own shape. Both stay on the chart, marked.
    clean = [r for r in rows if not r["ends"] and not any(x["flags"] for x in r["readings"])]
    most = {out: max(clean, key=lambda r: r["swing"][out])["key"] for out in OUTPUTS}
    return dict(rows=rows, ranked=ranked, most=most, zone_changes=sorted(set(changed)), not_run=list(NOT_RUN),
                highest_coverage=max(x["coverage"] for r in rows for x in r["readings"]))


# ---- The slope: no size chosen ----

def _nudge(path_fn):
    def change(d):
        for node in path_fn(d):
            _set(node, node["v"] * 1.01)
    return change


def slopes(d, price, method):
    """A 1% rise in each input, and the % it changes each output. A local slope, for comparing without choosing a range."""
    scen = lambda *keys: lambda d: [_scenario(d, k) for k in keys]  # noqa: E731
    items = [
        ("The 9% rate", None, METHOD_RATE * 1.01),
        ("Aaa yield", lambda d: [d["inputs"]["aaa"]], None),
        ("Normal earnings, middle", lambda d: [d["inputs"]["earnings_m"]["mid"]], None),
        ("Cash with deposits out, middle", lambda d: [d["inputs"]["cash_m"]["mid"]], None),
        ("Cash growth, middle", lambda d: [d["inputs"]["growth"]["mid"]], None),
        ("Diluted shares", lambda d: [d["inputs"]["shares_diluted_m"]], None),
        ("Optical margin on new sales", "margin", None),
        ("Capital per dollar of sales", lambda d: [s["capital_per_sale"] for s in d["scenarios"] if "capital_per_sale" in s], None),
        ("Years away, every scenario", lambda d: [s["years"] for s in d["scenarios"]], None),
        ("Size of the plan's step", lambda d: [_scenario(d, "plan")["new_sales_m"]], None),
        ("Size of the scale-up step", lambda d: [_scenario(d, "scaleup")["new_sales_m"]], None),
        ("Solar's new profit", lambda d: [_scenario(d, "solar")["new_profit_m"]], None),
    ]
    for s in d["scenarios"]:
        items.append((f'Chance: {s["key"]}', lambda d, k=s["key"]: [_scenario(d, k)["chance"]], None))
    out = []
    m0 = _scenario(d, "signed")["margin"]["v"]
    for label, path, rate in items:
        change = _margin(m0 * 1.01) if path == "margin" else _nudge(path) if path else None
        result, _ = _apply(d, price, _reading("", change, rate=rate))
        out.append(dict(label=label, base=result["base"] / method["base"] - 1, trim=result["trim"] / method["trim"] - 1))
    return sorted(out, key=lambda r: -abs(r["trim"]))


# ---- What the skill says to check first ----

def _note_figures(path=NOTE):
    head = Path(path).read_text().split("\n---", 1)[0]
    grab = lambda key: re.search(rf'^{key}: "(.*)"$', head, re.M)[1]  # noqa: E731
    base, strat, trim = grab("base value"), grab("strategic value"), grab("trim above")
    money = lambda text: [float(x.replace(",", "")) for x in re.findall(r"\$([\d,.]*\d)", text)]  # noqa: E731
    low, high, mid, buy = money(base)[:4]
    return dict(low=low, high=high, base=mid, buy=buy, strategic=money(strat)[0], trim=money(trim)[0])


def check_note(method, path=NOTE):
    note = _note_figures(path)
    wrong = [f"{k}: note ${note[k]:.2f}, inputs ${method[k]:.2f}" for k in note if round(method[k], 2) != note[k]]
    if wrong:
        raise Stop("The inputs and the Corning note disagree. The skill says stop and tell the owner.\n" + "\n".join(wrong))
    return "Base, strategic value and trim-above match the Corning note's properties."


def check_aaa(d, path=AAA_CSV):
    month, level = Path(path).read_text().strip().splitlines()[-1].split(",")
    latest, used = float(level) / 100, d["inputs"]["aaa"]["v"]
    if abs(latest - used) > 1e-9:
        raise Stop(f"Aaa for {month[:7]} is {latest:.2%}, and the inputs use {used:.2%}. The figures need a refresh.")
    if abs(latest - value.AAA_ANCHOR) >= .01 - 1e-9:
        raise Stop(f"Aaa is {latest:.2%}, a point or more from 6.12%. The 9% reopens: ask the owner.")
    return f"Aaa {latest:.2%} for {month[:7]}, as used."


MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def _filed_in(src):
    found = re.search(r"filed (\w{3})\w*\.? (\d+), (\d{4})", src)
    if not found:
        raise Stop(f"No filing date in the shares source: {src}")
    return dt.date(int(found[3]), MONTHS[found[1]], int(found[2]))


def check_filing(d, path=FILINGS):
    used = _filed_in(d["inputs"]["shares_diluted_m"]["src"])
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    newest = max(dt.date.fromisoformat(r["filed"]) for r in rows if r["form"] in ("10-Q", "10-K", "10-Q/A", "10-K/A"))
    if newest > used:
        raise Stop(f"A 10-Q or 10-K filed {newest} is newer than the inputs' {used}. The figures need a refresh.")
    return f"Newest 10-Q or 10-K on the saved SEC list is filed {newest}, as used."


# ---- The run ----

def newest_inputs(folder=SKILL / "assets"):
    return max(Path(folder).glob("corning-*.json"))


def read_prices(d):
    rows, entry = prices.read_latest(ticker=d["ticker"])
    series = [[r["date"], round(r["close"], 2)] for r in rows]
    day = dt.date.fromisoformat(entry["last"])
    label = f"{day:%b}. {day.day}, {day.year}"
    fetched = dt.date.fromisoformat(entry["started_utc"][:10])
    src = f"close of {label}, [Yahoo through yfinance, fetched {fetched:%b}. {fetched.day}, {fetched.year}](https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d)"
    return series, entry, src


def build(inputs_path, now):
    d = json.loads(Path(inputs_path).read_text())
    series, entry, src = read_prices(d)
    close = series[-1][1]
    if d["inputs"]["price"]["v"] != close:  # the skill: use the approved inputs if only the price differs
        d["inputs"]["price"] = dict(v=close, src=src)
    method = work(d, close)
    b = method["b"]
    checks = [check_note(method), check_aaa(d), check_filing(d)]
    with tempfile.TemporaryDirectory() as folder:
        merged = Path(folder) / "inputs.json"
        merged.write_text(json.dumps(d))
        done = subprocess.run([sys.executable, str(VALUE_PY), str(merged)], capture_output=True, text=True)
    if done.returncode:
        raise Stop(done.stderr)
    inp = value.Inputs()
    no_vote, need = value.no_vote(d, b, inp, close)
    used = [dict(label=label, v=v, src=src, status=status) for label, v, src, status in method["used"]]
    used.append(dict(label="Price", v=close, src=d["inputs"]["price"]["src"], status=""))
    run = dict(
        schema=SCHEMA, company=d["company"], ticker=d["ticker"], worked_out=d["as_of"], run_utc=now.isoformat(timespec="seconds"),
        inputs_file=str(Path(inputs_path).relative_to(ROOT)),
        method="Rules/when-to-buy.md and Rules/when-to-trim.md, through .claude/skills/valuation/scripts/value.py",
        price=dict(close=close, date=series[-1][0], src=d["inputs"]["price"]["src"], file=f'sensors/prices/cache/{d["ticker"]}/{entry["file"]}', source=entry["source"]),
        series=series,
        base=dict(low=method["low"], mid=method["base"], high=method["high"], votes={k: b["votes"][k] for k in b["votes"]}),
        coverage=dict(mid=method["base"] / close, low=method["low"] / close, high=method["high"] / close, bar=value.COVER_BAR, met=method["base"] / close >= value.COVER_BAR),
        buy_below=method["buy"], strategic=method["strategic"], trim_above=method["trim"],
        zone=zone(method["base"], close, method["buy"], method["trim"]),
        scenarios=[{k: r[k] for k in ("key", "name", "full", "chance", "value", "status")} for r in method["rows"]],
        no_vote=[dict(name=n, low=lo, mid=mi, high=hi) for n, lo, mi, hi in no_vote], growth_needed=dict(from_high=need[0], from_mid=need[1]),
        inputs=used, checks=checks, open=d.get("open") or [],
        what_if=dict(label="What-if, one assumption at a time. Not the method's answer.", **what_ifs(d, close, method), slopes=slopes(d, close, method)),
    )
    return run, done.stdout


def next_stem(day, folder=RUNS):
    taken = [int(p.stem[-2:]) for p in Path(folder).glob(f"{day}-*.json")]
    return f"{day}-{max(taken, default=0) + 1:02d}"


def main():
    now = dt.datetime.now(dt.timezone.utc)
    inputs = newest_inputs()
    run, report = build(inputs, now)
    RUNS.mkdir(parents=True, exist_ok=True)
    stem = next_stem(now.date().isoformat())
    run["run_file"] = f"sensors/valuation/runs/{stem}.json"
    run["report_file"] = f"sensors/valuation/runs/{stem}.md"
    (RUNS / f"{stem}.md").write_text(report)
    (RUNS / f"{stem}.json").write_text(json.dumps(run, indent=1))
    print(f"Saved {run['run_file']} and {run['report_file']}.")


if __name__ == "__main__":
    try:
        main()
    except Stop as err:
        print("STOPPED. Nothing was saved.\n" + str(err), file=sys.stderr)
        sys.exit(2)
