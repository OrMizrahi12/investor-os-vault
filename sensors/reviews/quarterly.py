"""Quarterly refresh, the plain-script parts. No advice and no change to any note. The prompt is in Playbooks/Quarterly refresh.md.

Run from the project root:
    .venv/bin/python sensors/reviews/quarterly.py start    is there a new 10-Q or 10-K? If so, save the documents and open a run
    .venv/bin/python sensors/reviews/quarterly.py check    check the reads against the filing, work the sums through value.py
    .venv/bin/python sensors/reviews/quarterly.py finish   refuse if a note changed, then add to the Journal and close the run

Reads come from Claude. A read counts only if its quote is really in the saved filing, with its number in it.
Writes only under sensors/reviews/ and at the end of today's Journal. Claude writes the proposal in Research/.
SEC requests go through the EDGAR client. It never asks Yahoo: it reads the newest saved close.
"""

import ast
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "sensors" / "edgar"))
sys.path.insert(0, str(ROOT / "sensors" / "prices"))
sys.path.insert(0, str(ROOT / "sensors" / "daily"))
import edgar  # noqa: E402
import prices  # noqa: E402
from collect import plain_text  # noqa: E402

RUNS = HERE / "runs"
STATE = HERE / "state.json"
ASSETS = ROOT / ".claude/skills/valuation/assets"
VALUE_PY = ROOT / ".claude/skills/valuation/scripts/value.py"
AAA_CSV = ROOT / "sensors/macro/downloads/AAA.csv"
JOURNAL = ROOT / "Journal"
RESEARCH = ROOT / "Research"
LOCKED = ["Companies", "Rules", "Portfolio", ".claude/skills/valuation/assets", "sensors/valuation/runs"]
CIK = 24741
FOLDER = edgar.CACHE / f"CIK{CIK:010d}"
METHOD_AAA, AAA_MOVE = 0.0612, 0.01
# Dates scenarios are measured to, from the approved inputs. "years" is days to here ÷ 365.25, to two places.
FORMS = ("10-Q", "10-K")
# At a 10-K the twelve months are the year just filed, so the year-to-date pieces fall away.
ZERO_AT_10K = {f"{n}_{k}" for n in ("ni", "trans", "unreal", "sales", "ocf", "capex", "line", "got", "used") for k in ("ytd", "prior")} | {"opt_rest", "solar_rest"}
TARGETS = {"signed": "2029-01-01", "plan": "2031-01-01", "scaleup": "2031-01-01", "solar": "2030-01-01", "display": "2028-01-01", "rival": "2030-01-01"}


class Stop(Exception):
    pass


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"reviewed": [], "told": []}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=1) + "\n")


def filings():
    return [json.loads(line) for line in (FOLDER / "filings.jsonl").open()]


def snapshot():
    """A hash of every file a refresh proposal must leave alone."""
    out = {}
    for name in LOCKED:
        for path in sorted((ROOT / name).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                out[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def changed(old, new):
    return sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))


def newest(rows, form):
    return next((r for r in rows if r["form"] == form), None)


def fetch_doc(client, cik, accession, name, saved):
    """Cached copy if we have one, else through the EDGAR client."""
    path = FOLDER / "documents" / saved
    if path.exists():
        return path.read_bytes()
    plain = accession.replace("-", "")
    cache = edgar.Cache(FOLDER, lambda: client(), edgar.MAX_AGE_HOURS)
    return cache.fetch(f"documents/{saved}", f"https://www.sec.gov/Archives/edgar/data/{cik}/{plain}/{name}")


def exhibit(r, client):
    """A results 8-K's Exhibit 99: (local name, remote name). From the cache if saved, else from the filing's index."""
    prefix = r["accession"]
    saved = [p.name for p in (FOLDER / "documents").glob(f"{prefix}-*ex*99*") if p.suffix == ".htm"]
    if saved:
        return saved[0], saved[0][len(prefix) + 1:]
    listing = json.loads(client().get(f'https://www.sec.gov/Archives/edgar/data/{CIK}/{prefix.replace("-", "")}/index.json'))
    names = [f["name"] for f in listing["directory"]["item"] if re.search(r"ex-?_?99.*\.htm", f["name"], re.I)]
    return (f"{prefix}-{names[0]}", names[0]) if names else (None, None)


def release_doc(r, client):
    local, remote = exhibit(r, client)
    if not local:
        raise Stop(f'No Exhibit 99 found on the results 8-K {r["accession"]}.')
    return r["accession"], remote, local, f'https://www.sec.gov/Archives/edgar/data/{CIK}/{r["accession"].replace("-", "")}/{remote}', r["filed"]


def start(pull=edgar.pull, today=None):
    """A new 10-Q or 10-K opens a run. Decision of Nov. 4, 2026: a 10-K starts the refresh too."""
    today = today or dt.date.today().isoformat()
    state = load_state()
    pull("GLW")  # 24-hour cache, so a run after the daily sensors asks SEC nothing
    rows = filings()
    filing = next(r for r in rows if r["form"] in FORMS)
    # A notice is told once. Only what came after the report before this one counts, so old amendments stay quiet.
    told = state.setdefault("told", [])
    earlier = [r["filed"] for r in rows if r["form"] in FORMS and r["accession"] != filing["accession"]]
    floor = max(earlier) if earlier else ""
    print_lines = []
    for r in rows:
        if r["form"] in ("10-Q/A", "10-K/A") and r["filed"] > floor and r["accession"] not in told:
            print_lines.append(f'AMENDED: {r["form"]}, filed {r["filed"]}, {r["url"]}. Method trigger O9.')
            told.append(r["accession"])
    if filing["accession"] in state["reviewed"]:
        save_state(state)
        print("NO NEW FILING." + (" " + " ".join(print_lines) if print_lines else ""))
        return None

    run = RUNS / f'{today}-GLW-{filing["accession"]}'
    (run / "docs").mkdir(parents=True, exist_ok=True)
    settings = edgar.load_settings()
    made = []

    def client():
        if not made:
            made.append(edgar.SecClient(settings["user_agent"], settings["rate"]))
        return made[0]

    results = [r for r in rows if r["form"] == "8-K" and "2.02" in r.get("items", "") and r["filed"] <= filing["filed"]]
    if not results:
        raise Stop("No results 8-K found before this filing.")
    k10 = newest(rows, "10-K")
    docs = {filing["form"]: (filing["accession"], filing["primary_document"], filing["primary_document"], filing["url"], filing["filed"]),
            "release": release_doc(results[0], client)}
    if filing["form"] == "10-Q":
        docs["10-K"] = (k10["accession"], k10["primary_document"], k10["primary_document"], k10["url"], k10["filed"])
    q1 = next((r for r in results if r["filed"][5:7] in ("04", "05")), None)
    if q1:
        docs["Q1 release"] = release_doc(q1, client)
    listed = {}
    for role, (acc, remote, local, url, filed) in docs.items():
        body = fetch_doc(client, CIK, acc, remote, local)
        path = run / "docs" / f'{role.replace(" ", "-")}.txt'
        path.write_text(plain_text(body))
        listed[role] = {"path": str(path.relative_to(ROOT)), "url": url, "filed": filed, "accession": acc, "lines": path.read_text().count("\n")}
    checklist = tomllib.loads((HERE / "checklist-GLW.toml").read_text())
    reads_path = run / "reads.json"
    if not reads_path.exists():
        shell = {}
        for i in checklist["reads"]:
            doc = "10-K" if filing["form"] == "10-K" and i["doc"] == "10-Q" else i["doc"]
            if filing["form"] == "10-K" and i["id"] in ZERO_AT_10K:
                shell[i["id"]] = {"value": 0, "doc": "not used at a 10-K", "quote": ""}
            else:
                shell[i["id"]] = {"value": None, "doc": doc, "quote": ""}
        reads_path.write_text(json.dumps(shell, indent=1) + "\n")
    order_path = run / "order.json"
    order_path.write_text(json.dumps({
        "company": "Corning", "ticker": "GLW", "today": today, "form": filing["form"], "filing": filing, "report_date": filing["report_date"],
        "same_filing_as_on_file": filing["accession"] == checklist["filing"], "documents": listed, "reads": str(reads_path.relative_to(ROOT)),
        "checklist": "sensors/reviews/checklist-GLW.toml", "proposal": f"Research/{today} Corning refresh proposal.md", "notices": print_lines,
        "locked": snapshot()}, indent=1) + "\n")
    save_state(state)
    print(f'NEW {filing["form"]}: {order_path.relative_to(ROOT)}' + (" " + " ".join(print_lines) if print_lines else ""))
    return order_path


def open_run():
    runs = sorted((p for p in RUNS.iterdir() if (p / "order.json").exists() and not (p / "closed.json").exists()), reverse=True)
    if not runs:
        raise Stop("No open run. Run start first.")
    return runs[0]


def forms(value):
    """The ways a filing can print this number."""
    a = abs(value)
    out = {f"{a:,.0f}"} if a == int(a) else {f"{a:,}"}
    if a >= 100:
        out |= {f"{a / 1000:.1f} billion", f"{a / 1000:.2f} billion"}
    return out


def norm(text):
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("“", '"').replace("”", '"')).strip()


def calc(formula, names):
    tree = ast.parse(formula, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Expression, ast.BinOp, ast.Name, ast.Load, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UnaryOp, ast.USub)):
            raise Stop(f"Bad formula: {formula}")
    return eval(compile(tree, "formula", "eval"), {"__builtins__": {}}, names)


def check_reads(checklist, reads, texts, form="10-Q"):
    """Each row: id, on file, read, status. same, changed, RESTATED, or a reason it does not count.
    A list of quotes is a sum over several lines, and each may sit in any saved document. The script does not add them up."""
    rows, values = [], {}
    for item in checklist["reads"]:
        got = reads.get(item["id"], {})
        value, quote, doc = got.get("value"), got.get("quote") or "", got.get("doc", item["doc"])
        row = {"id": item["id"], "what": item["what"], "rests_on": item["rests_on"], "on_file": item["on_file"], "read": value, "doc": doc, "quote": quote, "moves": item["moves"]}
        if form == "10-K" and item["id"] in ZERO_AT_10K:
            values[item["id"]] = 0
            row.update(read=0, status="not used at a 10-K")
            rows.append(row)
            continue
        many = isinstance(quote, list)
        pieces = [norm(p) for p in (quote if many else [quote])]
        if value is None or not any(pieces):
            row["status"] = "NOT READ"
        elif not many and doc not in texts:
            row["status"] = f"NO SUCH DOCUMENT: {doc}"
        elif missing := [p for p in pieces if not (any(p in t for t in texts.values()) if many else p in texts[doc])]:
            row["status"] = f"QUOTE NOT IN FILING: {missing[0][:70]}"
        elif not many and value != 0 and not any(f in pieces[0] for f in forms(value)):
            row["status"] = "NUMBER NOT IN QUOTE"
        else:
            values[item["id"]] = value
            if value == item["on_file"]:
                row["status"] = "same"
            else:
                row["status"] = "changed" if item["moves"] == "each" or form == "10-K" else "RESTATED"
        rows.append(row)
    return rows, values


def work_calcs(checklist, values):
    rows = []
    for item in checklist["calcs"]:
        try:
            value = calc(item["formula"], values)
        except NameError as err:
            rows.append({**item, "worked": None, "status": f"MISSING {err.name}"})
            continue
        values[item["id"]] = value
        rows.append({**item, "worked": value, "status": "same" if abs(value - item["on_file"]) < 1e-6 else "changed"})
    return rows


def check_years(checklist):
    """The ten years behind the low. A filed number on or within eight lines under its label in a named 10-K.
    A weak check: it does not prove the column, and old tables print labels and numbers apart. A person read these on Nov. 3, 2026."""
    out, total = [], 0
    for y in checklist["years"]:
        total += y["normal"]
        lines = []
        for name in y["docs"]:
            path = FOLDER / "documents" / name
            if path.exists():
                lines += plain_text(path.read_bytes()).splitlines()
        cells = []
        for label, number in y["items"] + [["attributable to Corning|net income", abs(y["ni"])]]:
            text = re.compile(rf"(?<![\d,.]){re.escape(f'{number:,}')}(?![\d,])")
            where = re.compile(label, re.I)
            hit = any(text.search(line) and any(where.search(x) for x in lines[max(i - 8, 0):i + 1]) for i, line in enumerate(lines))
            cells.append({"label": label, "number": number, "found": hit})
        out.append({"year": y["year"], "docs": y["docs"], "normal": y["normal"], "status": "all found" if lines and all(c["found"] for c in cells) else "SOME NOT FOUND",
                    "not_found": [f'{c["label"]} {c["number"]:,}' for c in cells if not c["found"]]})
    return out, total


def check_record(checklist):
    """The record behind the growth ceiling: free cash flow per share, first and last year. Same weak match as check_years."""
    rows = []
    for y in checklist["record"]:
        lines = []
        for name in y["docs"]:
            path = FOLDER / "documents" / name
            if path.exists():
                lines += plain_text(path.read_bytes()).splitlines()
        missing = []
        for label, number in (("operating activities", y["ocf"]), ("capital expenditures", y["capex"]), ("diluted", y["shares"])):
            text = re.compile(rf"(?<![\\d,.]){re.escape(f'{number:,}')}(?![\\d,])")
            where = re.compile(label, re.I)
            if not any(text.search(line) and any(where.search(x) for x in lines[max(i - 8, 0):i + 1]) for i, line in enumerate(lines)):
                missing.append(f"{label} {number:,}")
        rows.append({"year": y["year"], "fcf": y["ocf"] - y["capex"], "shares": y["shares"], "per_share": round((y["ocf"] - y["capex"]) / y["shares"], 2), "not_found": missing})
    first, last = rows[0], rows[-1]
    return {"rows": rows, "record_growth": round((last["per_share"] / first["per_share"]) ** (1 / (last["year"] - first["year"])) - 1, 6)}


def k9_reading(pull=edgar.pull):
    """K9: three buyers' capital spending by quarter, from SEC's facts. Which quarter is complete, and the falls."""
    tags = {"META": ["PaymentsToAcquirePropertyPlantAndEquipment"], "AMZN": ["PaymentsToAcquireProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"], "MSFT": ["PaymentsToAcquirePropertyPlantAndEquipment"]}
    spend = {}
    for ticker, names in tags.items():
        folder = pull(ticker)
        facts = json.loads((Path(folder) / "companyfacts.json").read_text())["facts"]["us-gaap"]
        points = {}
        for tag in names:
            for u in facts.get(tag, {}).get("units", {}).get("USD", []):
                if "start" in u and ((u["start"], u["end"]) not in points or u["filed"] > points[(u["start"], u["end"])][1]):
                    points[(u["start"], u["end"])] = (u["val"], u["filed"])
        day = dt.date.fromisoformat
        per = {e: v for (s, e), (v, _) in points.items() if 80 < (day(e) - day(s)).days < 100}
        for (s, e), (v, _) in points.items():
            if (day(e) - day(s)).days > 100 and e not in per:
                for (s2, e2), (v2, _) in points.items():
                    if s2 == s and 80 < (day(e) - day(e2)).days < 100:
                        per[e] = v - v2
        spend[ticker] = per
    newest_each = {t: max(p) for t, p in spend.items()}
    ends = sorted(e for e in spend["META"] if all(e in spend[t] for t in tags))
    rows = [{"end": e, "total": round(sum(spend[t][e] for t in tags) / 1e6)} for e in ends[-3:]]
    return {"complete_through": ends[-1], "newest_each": newest_each, "rows": rows,
            "fell_once": rows[-1]["total"] < rows[-2]["total"], "fell_twice": rows[-1]["total"] < rows[-2]["total"] < rows[-3]["total"]}


def years_to(target, today):
    return round((dt.date.fromisoformat(target) - dt.date.fromisoformat(today)).days / 365.25, 2)


def aaa_now():
    last = AAA_CSV.read_text().strip().splitlines()[-1].split(",")
    return last[0], float(last[1]) / 100


def latest_close():
    path = sorted((ROOT / "sensors/prices/cache/GLW").glob("*.csv"))[-1]
    last = path.read_text().strip().splitlines()[-1].split(",")
    return last[0], round(float(last[4]), 2), path.name


def checklist_years():
    return tomllib.loads((HERE / "checklist-GLW.toml").read_text())["years"]


def after_inputs(before, v, order, aaa, price):
    """A copy of the approved inputs with only what the new filing, Aaa and the close change. Sources say where each came from."""
    d = copy.deepcopy(before)
    today, docs = order["today"], order["documents"]
    form = order.get("form", "10-Q")
    q = f'[{form}, filed {docs[form]["filed"]}]({docs[form]["url"]})'
    rel = f'[results release, filed {docs["release"]["filed"]}]({docs["release"]["url"]})'
    k = f'[10-K, filed {docs["10-K"]["filed"]}]({docs["10-K"]["url"]})'
    d["as_of"], d["proposal"] = today, True
    d["note"] = f"PROPOSAL from the refresh on {today}. Not approved. Do not save to assets until the owner says yes."
    i = d["inputs"]
    i["shares_diluted_m"].update(v=v["shares"], src=q)
    i["price"].update(v=price[1], src=f"close of {price[0]}, saved file {price[2]}, [Yahoo through yfinance]({prices.__dict__.get('SOURCE_URL', 'https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d')})")
    i["aaa"].update(v=aaa[1], src=f"[FRED AAA, {aaa[0]}, owner's download](https://fred.stlouisfed.org/series/AAA)")
    i["earnings_m"]["high"].update(v=v["earn_high"], src=f"twelve months (calc., {k}; {q}; {rel})")
    if form == "10-K":
        # A new audited year moves the middle and the ten-year low. Its adjustments wait for the owner, so all three are unconfirmed.
        rows = checklist_years()
        i["earnings_m"]["high"]["status"] = "unconfirmed"
        i["earnings_m"]["mid"].update(v=v["earn_high"], status="unconfirmed", src=f"new audited year, normal, adjustments not yet confirmed by the owner (calc., {q}; {rel})")
        i["earnings_m"]["low"].update(v=(sum(y["normal"] for y in rows[1:]) + v["earn_high"]) / 10, status="unconfirmed", src=f"ten-year normal average, newest year not yet confirmed (calc., {q}; `normal.html`)")
        record = min(0.03, i["record_growth"]["v"])
        grown = (v["earn_high"] / rows[1]["normal"]) ** (1 / 9) - 1
        i["growth"]["mid"].update(v=min(grown, record), src=f"normal net income over nine years, capped by the record and 3% (calc., {q}; `normal.html`)")
    for key, name in (("low", "cash_low"), ("mid", "cash_mid"), ("high", "cash_high")):
        i["cash_m"][key].update(v=v[name], src=f"{i['cash_m'][key]['src'].split(' (')[0]} (calc., {k}; {q})")
    for s in d["scenarios"]:
        s["years"]["v"] = years_to(TARGETS[s["key"]], today)
        if s["key"] in ("signed", "plan", "scaleup"):
            s["margin"].update(v=v["opt_margin"], src=f"Optical, the quarter, calc., {q}")
            s["capital_per_sale"].update(v=v["opt_capital"], src=f"calc., {q}")
        if s["key"] == "plan":
            s["new_sales_m"]["v"] = v["plan_new_sales"]
        if s["key"] == "solar":
            s["new_sales_m"]["v"] = v["solar_new_sales"]
            s["new_profit_m"]["v"] = v["solar_new_profit"]
            s["capital_per_sale"]["v"] = v["solar_capital"]
            s["extra_capital_m"]["v"] = v["earnout"]
        if s["key"] == "display":
            s["margin"]["v"] = v["glass_after_tax"]
            s["new_sales_m"]["v"] = v["display_fy"] * 0.05
        if s["key"] == "rival":
            s["margin_cut"]["v"] = v["margin_cut"]
    return d


def value_out(path):
    done = subprocess.run([sys.executable, str(VALUE_PY), str(path)], cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        raise Stop(done.stderr.strip())
    return done.stdout


def pull_figures(text):
    def num(pattern):
        m = re.search(pattern, text)
        if not m:
            raise Stop(f"value.py's report changed shape: {pattern}")
        return m.groups() if len(m.groups()) > 1 else m.group(1)
    low, mid, high = num(r"\*\*Base value\*\* \| \*\*\$([\d.]+)\*\* \| \*\*\$([\d.]+)\*\* \| \*\*\$([\d.]+)\*\*")
    return {"base_low": float(low), "base_mid": float(mid), "base_high": float(high), "buy_below": float(num(r"Buy-below: \$([\d.]+)")),
            "price": float(num(r"Price: \$([\d.]+)")), "coverage": float(num(r"Coverage: ([\d.]+)%")),
            "strategic": float(num(r"Strategic value: \$([\d.]+)")), "trim_above": float(num(r"Trim-above: \$([\d.]+)"))}


def kill_rows(v, k9):
    """Readings only. Claude says what each one means, under its wording and test date."""
    m, m0 = round(v["opt_margin"] * 100, 1), round(v["opt_margin_last_q"] * 100, 1)
    return [
        {"line": "K1", "reading": f'Optical sales ${v["opt_sales"]:,}M', "threshold": "At or below $2,379M at Q4 2027", "state": "Test not due"},
        {"line": "K2", "reading": "A statement, not a number", "threshold": "A customer ends or says it reduced a deal", "state": "Not in a 10-Q. The weekly check reads this"},
        {"line": "K3", "reading": f"{m}%, the quarter before {m0}%", "threshold": "At or below 17.9% two quarters running", "state": "CROSSED" if m <= 17.9 and m0 <= 17.9 else ("One step short" if m <= 17.9 else "Not crossed")},
        {"line": "K4", "reading": f'Core × 4 ${v["run_rate"]:,}M', "threshold": "Under $27,000M at Q4 2028", "state": "Test not due"},
        {"line": "K5", "reading": f'Deposit-out cash ${v["cash_high"]:,}M', "threshold": "Under $1,505M, twelve months to Sept. 30, 2027", "state": "Test not due"},
        {"line": "K6", "reading": f'{v["atm_shares"]:,} shares', "threshold": "More than zero", "state": "CROSSED" if v["atm_shares"] > 0 else "Not crossed"},
        {"line": "K7", "reading": "A statement, not a number", "threshold": "Corning names a year after 2028 or drops 2028", "state": "Not in a 10-Q (kill note). The weekly check reads this"},
        {"line": "K8", "reading": f'${v["opt_sales"]:,}M against ${v["opt_sales_last_q"]:,}M', "threshold": "Lower than the quarter before, two quarters running", "state": "One step short" if v["opt_sales"] < v["opt_sales_last_q"] else "Not crossed"},
        {"line": "K9", "reading": f'${k9["rows"][-1]["total"]:,}M, {k9["rows"][-1]["end"]}, against ${k9["rows"][-2]["total"]:,}M', "threshold": "Lower than the quarter before, two quarters running", "state": "CROSSED" if k9["fell_twice"] else ("One step short" if k9["fell_once"] else "Not crossed"), "complete_through": k9["complete_through"]},
    ]


def check(pull=edgar.pull):
    run = open_run()
    order = json.loads((run / "order.json").read_text())
    checklist = tomllib.loads((HERE / "checklist-GLW.toml").read_text())
    reads = json.loads((run / "reads.json").read_text())
    texts = {role: norm(Path(ROOT / d["path"]).read_text()) for role, d in order["documents"].items()}
    read_rows, values = check_reads(checklist, reads, texts, order.get("form", "10-Q"))
    calc_rows = work_calcs(checklist, values)
    years, total = check_years(checklist)
    record = check_record(checklist)
    bad = [r for r in read_rows if r["status"] not in ("same", "changed", "RESTATED", "not used at a 10-K")] + [r for r in calc_rows if r["status"].startswith("MISSING")]
    result = {"today": order["today"], "filing": order["filing"], "reads": read_rows, "calcs": calc_rows, "years": years, "record": record,
              "ten_year_sum": total, "problems": [f'{r["id"]}: {r["status"]}' for r in bad]}
    if bad:
        (run / "check.json").write_text(json.dumps(result, indent=1) + "\n")
        print("REFUSED. These reads do not count yet. Fix them in reads.json and run check again:")
        for line in result["problems"]:
            print("  " + line)
        return 1
    before_path = sorted(ASSETS.glob("corning-*.json"))[-1]
    before = json.loads(before_path.read_text())
    aaa, close = aaa_now(), latest_close()
    after = after_inputs(before, values, order, aaa, close)
    # The same date and price as the approved run, so a change here can only come from the filing or a correction.
    same_price = copy.deepcopy(after)
    same_price["inputs"]["price"] = before["inputs"]["price"]
    for name, data in (("after-inputs.json", after), ("after-at-old-price-inputs.json", same_price)):
        (run / name).write_text(json.dumps(data, indent=1) + "\n")
    out_before = value_out(before_path)
    out_after = value_out(run / "after-inputs.json")
    out_same = value_out(run / "after-at-old-price-inputs.json")
    (run / "after-report.md").write_text(out_after)
    k9 = k9_reading(pull)
    fb, fa, fs = pull_figures(out_before), pull_figures(out_after), pull_figures(out_same)
    crossed = []
    for name, line in (("buy_below", "O6: a refresh moved the buy-below across the price"), ("trim_above", "O6: a refresh moved the trim-above across the price")):
        if (fb[name] - fa["price"]) * (fa[name] - fa["price"]) < 0:
            crossed.append(line)
    if abs(aaa[1] - METHOD_AAA) >= AAA_MOVE:
        crossed.append(f"O9: Aaa {aaa[1]:.2%} is a point from 6.12%, so the 9% reopens")
    result.update({"before": fb, "after": fa, "after_at_old_price": fs, "before_file": str(before_path.relative_to(ROOT)), "close": close, "aaa": aaa,
                   "kill": kill_rows(values, k9), "k9": k9, "alerts": crossed, "counts": {
                       "reads": len(read_rows), "same": sum(r["status"] == "same" for r in read_rows), "changed": sum(r["status"] == "changed" for r in read_rows),
                       "restated": sum(r["status"] == "RESTATED" for r in read_rows), "calcs_same": sum(r["status"] == "same" for r in calc_rows), "calcs": len(calc_rows),
                       "not_used": sum(r["status"] == "not used at a 10-K" for r in read_rows),
                       "years_found": sum(y["status"] == "all found" for y in years), "years": len(years)}})
    (run / "check.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("before", "after", "after_at_old_price", "counts", "alerts", "kill")}, indent=1))
    print(f"Saved: {(run / 'check.json').relative_to(ROOT)} and {(run / 'after-report.md').relative_to(ROOT)}")
    return 0


def add_to_journal(block, day):
    path = JOURNAL / f"{day}.md"
    old = path.read_text() if path.exists() else f"# {day}\n"
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(old.rstrip("\n") + "\n\n" + block.strip() + "\n")
    temp.replace(path)


def finish():
    run = open_run()
    order = json.loads((run / "order.json").read_text())
    result = json.loads((run / "check.json").read_text()) if (run / "check.json").exists() else None
    if not result or result["problems"]:
        raise Stop("check has not passed. Nothing written.")
    moved = changed(order["locked"], snapshot())
    if moved:
        raise Stop("A file this run must not change has changed: " + ", ".join(moved[:6]) + ". Nothing written. Tell the owner.")
    proposal = ROOT / order["proposal"]
    if not proposal.exists():
        raise Stop(f'No proposal at {order["proposal"]}. Write it first.')
    words = proposal.read_text()
    a, b = result["after"], result["before"]
    for figure in (f'${a["base_mid"]:.2f}', f'${a["buy_below"]:.2f}', f'${b["base_mid"]:.2f}', f'${b["buy_below"]:.2f}'):
        if figure not in words:
            raise Stop(f"The proposal does not show {figure}. Use the figures in check.json.")
    f = order["filing"]
    line = (f'Base middle ${b["base_mid"]:.2f} to ${a["base_mid"]:.2f} and buy-below ${b["buy_below"]:.2f} to ${a["buy_below"]:.2f}, proposed, not applied (calc., `{order["proposal"]}`, '
            f'[10-Q, filed {f["filed"]}]({f["url"]})).')
    c = result["counts"]
    alerts = "".join(f"- **Orange.** {x} (`{(run / 'check.json').relative_to(ROOT)}`, {order['today']}).\n" for x in result["alerts"])
    add_to_journal(f"""## Session: quarterly refresh, Corning

### What we did

- Ran the quarterly refresh on the {f["form"]} filed {f["filed"]}, accession {f["accession"]}. {line}
- Re-read {c["reads"]} numbers from the filings: {c["same"]} same, {c["changed"]} changed, {c["restated"]} restated. Ten-year rows found on labeled lines: {c["years_found"]} of {c["years"]}.
{alerts}
### What we decided

- Nothing. The run recommends nothing and changed no note. The proposal waits for my yes.

### What we left open

- **For me:** read `{order["proposal"]}` and say yes or no.
""", order["today"])
    state = load_state()
    state["reviewed"].append(f["accession"])
    save_state(state)
    (run / "closed.json").write_text(json.dumps({"closed": order["today"]}) + "\n")
    print(f'Done. Journal/{order["today"]}.md updated. The note, the inputs and the rules were not changed.')
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "start":
            start()
            return 0
        if cmd == "check":
            return check()
        if cmd == "finish":
            return finish()
        print(__doc__)
        return 2
    except Stop as err:
        print("STOPPED: " + str(err))
        return 1


if __name__ == "__main__":
    sys.exit(main())
