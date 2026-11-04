"""Monthly opportunity hunt, the plain-script parts. No advice, no picks. The prompt is in Playbooks/Monthly hunt.md.

Run from the project root:
    .venv/bin/python sensors/hunt/hunt.py start       screen, rejection log, pick rule, Gate 1. Prints who needs a price
    .venv/bin/python sensors/hunt/hunt.py gate2       Gate 2 from the run's prices.json. Saves the filing lines behind each idea
    .venv/bin/python sensors/hunt/hunt.py finish      check, write Inbox ideas, the report in Research/, the end of today's Journal

It runs the radar's screen only, not the radar: a full run would mark new filings as reported and the daily run would lose them.
It never asks Yahoo. It writes no rejection line and changes no note: the report lists proposed lines, and the owner adds them (ruling, Nov. 4, 2026).
"""
import contextlib
import datetime as dt
import io
import json
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE), str(ROOT / "sensors/radar"), str(ROOT / "sensors/edgar"), str(ROOT / "sensors/prices"), str(ROOT / "sensors/daily")]
import edgar  # noqa: E402
import gates  # noqa: E402
import radar  # noqa: E402
from collect import plain_text  # noqa: E402
from publish import ADVICE  # noqa: E402

RUNS = HERE / "runs"
STATE = HERE / "hunt-state.json"
INBOX = ROOT / "Inbox"
RESEARCH = ROOT / "Research"
JOURNAL = ROOT / "Journal"
LOG = RESEARCH / "Rejection log.md"
US = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May June July Aug Sept Oct Nov Dec".split())}
REV_TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"]
KEYWORDS = re.compile(r"contract liabilit|remaining performance|deferred revenue|customer deposit|backlog|unearned", re.I)


class Refused(Exception):
    pass


def settings():
    return tomllib.loads((HERE / "settings.toml").read_text())


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"tested": {}}


def nice(day):
    d = dt.date.fromisoformat(day)
    month = "Jan. Feb. Mar. Apr. May June July Aug. Sept. Oct. Nov. Dec.".split()[d.month - 1]
    return f"{month} {d.day}, {d.year}"


def read_log(text):
    """Ticker to its look-again month, from Research/Rejection log.md. A row that cannot be read stops the run, so nothing slips through."""
    out, bad = {}, []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith(("| Date", "|---")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        tick = re.search(r"\(([A-Z.]+)\)", cells[1]) if len(cells) >= 5 else None
        if not tick:
            bad.append(line[:60])
            continue
        out[tick.group(1)] = {"look_again": look_month(cells[-1]), "words": cells[-1], "gate": cells[2], "date": cells[0]}
    if bad:
        raise Refused("Rejection log rows that could not be read: " + "; ".join(bad))
    return out


def look_month(words):
    m = re.search(r"about (?:early |mid |late )?(Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)\.? (\d{4})", words)
    if m:
        return f"{m.group(2)}-{MONTHS[m.group(1)]:02d}"
    y = re.search(r"about (?:early |mid |late )?(\d{4})", words)
    return f"{y.group(1)}-01" if y else None


def iso_day(words):
    m = re.match(r"(\w+)\.? (\d{1,2}), (\d{4})", words)
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def due(month, today):
    return bool(month) and month <= today[:7]


def sort_leads(steps, log, watch, tested, today):
    """Every lead, once per company at its largest rise, into a skip list or the ranking pool. Pure, so a test can run it."""
    pool, skipped, seen_any = {}, {"on our map": [], "rejection log": [], "watchlist": [], "unit slip": [], "tested before on this step": []}, set()
    for step in steps:
        for lead in step.get("unit_check", []):
            skipped["unit slip"].append(lead["name"])
        for lead in step["leads"]:
            seen_any.add(lead["cik"])
            cur = pool.get(lead["cik"])
            best = max(lead["lines"], key=lambda ln: ln["rise_usd"])
            if not cur or best["rise_usd"] > cur["line"]["rise_usd"]:
                pool[lead["cik"]] = {"cik": lead["cik"], "name": squeeze(lead["name"]), "ticker": lead.get("ticker"), "line": best, "step": step["later"],
                                     "on_map": lead.get("on_map"), "filling": step.get("filling", False), "not_new_growth": lead.get("not_new_growth")}
    keep = []
    for r in pool.values():
        t = r["ticker"]
        if r["on_map"]:
            skipped["on our map"].append(r["name"])
        elif t in log and not due(log[t]["look_again"], today):
            skipped["rejection log"].append(f'{r["name"]} ({t})')
        elif t in watch and not due(watch[t], today):
            skipped["watchlist"].append(f'{r["name"]} ({t})')
        elif str(r["cik"]) in tested and tested[str(r["cik"])] == r["step"]:
            skipped["tested before on this step"].append(f'{r["name"]} ({t})')
        else:
            r["look_again_due"] = (log.get(t) or {}).get("words") if t in log else (f"watchlist, look again {watch[t]}" if t in watch else None)
            if t in log:
                words = log[t]["words"]
                r["back"] = {"since": iso_day(log[t]["date"]), "forms": ["10-K"] if "10-K" in words else ["10-K", "10-Q"]}
            elif t in watch:
                r["back"] = {"since": "2026-11-03", "forms": ["10-K", "10-Q"]}
            keep.append(r)
    return keep, skipped, len(seen_any)


def revenue_frames(client, today):
    """The largest figure across the tags in SEC's annual frames. Before April the newest year is still filling, so use the one before."""
    day = dt.date.fromisoformat(today)
    year = day.year - 1 if day.month >= 4 else day.year - 2
    folder = HERE / "cache"
    folder.mkdir(exist_ok=True)
    out = {}
    for tag in REV_TAGS:
        p = folder / f"{tag}-CY{year}.json"
        if not p.exists():
            try:
                p.write_bytes(client.get(f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/CY{year}.json"))
            except edgar.EdgarError:
                continue
        for row in json.loads(p.read_text())["data"]:
            if row["val"] > out.get(row["cik"], 0):
                out[row["cik"]] = row["val"]
    return out, year


def is_us(sub):
    state_code = (sub.get("stateOfIncorporation") or "").strip()
    if state_code:
        return state_code in US, sub.get("stateOfIncorporationDescription") or state_code
    biz = (sub.get("addresses") or {}).get("business") or {}
    forms = set(sub.get("filings", {}).get("recent", {}).get("form", []))
    if biz.get("stateOrCountry") in US and forms & {"10-K", "10-Q"}:
        return True, "blank on SEC's list, US business address, files 10-K or 10-Q"
    return False, "blank on SEC's list, no 10-K or 10-Q in its recent filings"


def new_filing_since(sub, since, forms):
    """Is a filing of these forms newer than the rejection? A look-again month only says when to check. The filing is the reason to look."""
    r = sub.get("filings", {}).get("recent", {})
    return any(f in forms and d > since for f, d in zip(r.get("form", []), r.get("filingDate", [])))


def lookup(cik):
    with contextlib.redirect_stdout(io.StringIO()):
        edgar.pull(str(cik))
    folder = edgar.CACHE / f"CIK{int(cik):010d}"
    return json.loads((folder / "submissions.json").read_text()), gates.Facts.load(folder / "companyfacts.json")


def rank(pool, frames_rev, take, us_only, max_pulls, look=lookup):
    """Rank by rise / revenue, then check each from the top against the company's own facts, because a frame can hold a partial line.
    A too-small frame figure only pushes a company up, so stop once the top five's true ratios beat the next frame ratio."""
    have, no_rev = [], []
    for r in pool:
        val = frames_rev.get(r["cik"])
        if val and val > 0:
            r["ratio_frame"] = r["line"]["rise_usd"] / val
            have.append(r)
        else:
            no_rev.append(r)
    have.sort(key=lambda r: -r["ratio_frame"])
    checked, skipped_foreign, problems, pulls, not_yet = [], [], [], 0, []
    for i, r in enumerate(have):
        ready = sorted(checked, key=lambda x: -x["ratio"])
        if len(ready) >= take and ready[take - 1]["ratio"] >= r["ratio_frame"]:
            break
        if pulls >= max_pulls:
            problems.append(f"Stopped at {max_pulls} look-ups. {len(have) - i} ranked companies were not looked at.")
            break
        pulls += 1
        try:
            sub, facts = look(r["cik"])
        except edgar.EdgarError as err:
            problems.append(f'{r["name"]}: {err}')
            continue
        us, where = is_us(sub)
        r["incorporated"] = where
        back = r.get("back")
        if back and not new_filing_since(sub, back["since"], back["forms"]):
            not_yet.append(f'{r["name"]} ({r["ticker"]})')
            r["look_again_due"] = None
            continue
        if us_only and not us:
            skipped_foreign.append(f'{r["name"]} ({where})')
            continue
        year, val = facts.latest_year_revenue()
        if not val or val <= 0:
            no_rev.append(r)
            continue
        r.update(revenue=val, revenue_year=year, ratio=r["line"]["rise_usd"] / val, facts=facts)
        checked.append(r)
    top = sorted(checked, key=lambda x: -x["ratio"])[:take]
    return top, {"ranked": len(have), "no_revenue": [r["name"] for r in no_rev], "not_us": skipped_foreign, "not_yet": not_yet, "looked_up": pulls, "problems": problems}


def open_run():
    runs = sorted((p for p in RUNS.glob("hunt-*") if (p / "order.json").exists() and not (p / "closed.json").exists()), reverse=True)
    if not runs:
        raise Refused("No open run. Run start first.")
    return runs[0]


def start(today=None, steps=None, look=lookup, frames_rev=None):
    today = today or dt.date.today().isoformat()
    cfg = settings()["hunt"]
    log = read_log(LOG.read_text())
    watch = {w["ticker"]: w["look_again"] for w in settings().get("watch", [])}
    s = state()
    sec = edgar.load_settings()
    client = edgar.SecClient(sec["user_agent"], sec["rate"])
    screen_status, retrieved = "given", today
    if steps is None:
        paths = radar.Paths()
        rsettings = tomllib.loads(paths.settings.read_text())
        table = radar.ticker_table(paths)
        now = dt.date.fromisoformat(today)
        found = radar.run_screen(rsettings["screen"], paths, now, lambda: client, [client], radar.map_nodes(paths, table), table, {}, True)
        if found["status"] != "ok":
            raise Refused(f'The screen did not run: {found["status"]}')
        steps, screen_status, retrieved = found["steps"], "ok", found["retrieved"]
    hidden = sum(len(st.get("hidden_leads", [])) for st in steps)
    rows = sum(len(st["leads"]) for st in steps)
    pool, skipped, companies = sort_leads(steps, log, watch, s["tested"], today)
    if frames_rev is None:
        frames_rev, rev_year = revenue_frames(client, today)
    else:
        rev_year = "given"
    top, ranked = rank(pool, frames_rev, cfg["take"], cfg["us_only"], cfg["max_pulls"], look)
    tested = []
    for r in top:
        g1 = gates.gate1(r.pop("facts"))
        tested.append({**r, "gate1": g1, "rank": len(tested) + 1})
    run = RUNS / f"hunt-{today}"
    (run / "docs").mkdir(parents=True, exist_ok=True)
    need = [t for t in tested if t["gate1"]["state"] != "fail"]
    order = {"today": today, "retrieved": retrieved, "revenue_year": rev_year, "steps": [{"later": st["later"], "earlier": st["earlier"], "rows": len(st["leads"]), "filling": st.get("filling", False)} for st in steps],
             "rows": rows, "hidden": hidden, "companies": companies, "skipped": skipped, "pool": len(pool), "ranked": ranked, "tested": tested,
             "need_price": [{"ticker": t["ticker"], "name": t["name"], "url": f'https://{cfg["open_price_domain"]}/stocks/{(t["ticker"] or "").lower()}/'} for t in need],
             "prices_file": str((run / "prices.json").relative_to(ROOT)), "reasons_file": str((run / "reasons.json").relative_to(ROOT))}
    (run / "order.json").write_text(json.dumps(order, indent=1) + "\n")
    print(f'OPEN: {(run / "order.json").relative_to(ROOT)}')
    print(f'Leads: {rows} rows, {companies} companies. Skipped: ' + ", ".join(f"{k} {len(v)}" for k, v in skipped.items()) + f'. Tested: {len(tested)}. Past Gate 1: {len(need)}.')
    print("NEEDS A PRICE: " + (", ".join(t["ticker"] or t["name"] for t in need) or "nobody"))
    return run


def filing_lines(line, cik):
    """The later filing's lines that speak to the screen's rise, so a run reads a few lines and not a whole 10-Q."""
    folder = edgar.CACHE / f"CIK{int(cik):010d}"
    url = None
    for raw in (folder / "filings.jsonl").read_text().splitlines():
        row = json.loads(raw)
        if row["accession"] == line["accession_later"]:
            url = row["url"]
            break
    if not url:
        return None, None
    sec = edgar.load_settings()
    text = plain_text(edgar.SecClient(sec["user_agent"], sec["rate"]).get(url))
    lines = text.splitlines()
    picks = sorted({j for i, ln in enumerate(lines) if KEYWORDS.search(ln) for j in range(max(0, i - 1), min(len(lines), i + 2))})
    return url, "\n".join(lines[j] for j in picks)[:30000]


def gate2(fetch=filing_lines):
    run = open_run()
    order = json.loads((run / "order.json").read_text())
    cfg = settings()["hunt"]
    prices = json.loads((run / "prices.json").read_text()) if (run / "prices.json").exists() else {}
    ideas = []
    for t in order["tested"]:
        if t["gate1"]["state"] == "fail":
            t["gate2"] = {"state": "not run", "read": "Gate 1 failed."}
            continue
        url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{int(t["cik"]):010d}.json'
        facts = gates.Facts.load(edgar.CACHE / f'CIK{int(t["cik"]):010d}' / "companyfacts.json")
        b, why = gates.base(facts, cfg["aaa"], cfg["aaa_src"], url, nice(order["retrieved"]), cfg["peak_flag"])
        p = prices.get(t["ticker"]) or {}
        if b is None:
            t["gate2"] = {"state": "open", "read": f"Base value not worked out: {why}"}
        else:
            t["base"] = b
            if not p.get("price"):
                t["gate2"] = {"state": "open", "read": f'Base middle ${b["mid"]:,.2f}, buy-below ${b["buy_below"]:,.2f} (calc., a proposal). No price read: {p.get("problem", "none given")}.'}
            else:
                cover = b["mid"] / float(p["price"])
                t["gate2"] = {"state": "pass" if cover >= 0.75 else "fail", "coverage": cover, "price": p["price"], "price_source": p.get("source", ""),
                              "read": f'Base middle ${b["mid"]:,.2f} against ${float(p["price"]):,.2f}, {cover:.1%}. Buy-below ${b["buy_below"]:,.2f} (calc., a proposal on reported earnings).'}
        if t["gate2"]["state"] != "fail":
            ideas.append(t)
            doc_url, lines = fetch(t["line"], t["cik"])
            t["doc_url"] = doc_url
            path = run / "docs" / f'{t["ticker"] or t["cik"]}-lines.txt'
            path.write_text(lines or "")
            t["lines_file"] = str(path.relative_to(ROOT))
    order["ideas"] = [t["ticker"] or str(t["cik"]) for t in ideas]
    (run / "order.json").write_text(json.dumps(order, indent=1) + "\n")
    print("IDEAS: " + (", ".join(order["ideas"]) or "none"))
    for t in ideas:
        print(f'Read: {t["lines_file"]}')
    return order


def squeeze(text):
    table = str.maketrans({"“": '"', "”": '"', "’": "'", "‘": "'", " ": " "})
    return re.sub(r"\s+", " ", text.translate(table)).strip()


def check(order, reasons, run):
    problems = []
    if "ideas" not in order:
        return ["Run gate2 first."]
    for t in order["tested"]:
        key = t["ticker"] or str(t["cik"])
        if key not in order["ideas"]:
            continue
        r = reasons.get(key)
        if r is None:
            problems.append(f'{key} has no entry in reasons.json. Give "quote", or "quote": "" and "read": false.')
            continue
        if r.get("quote"):
            have = squeeze((ROOT / t["lines_file"]).read_text())
            if squeeze(r["quote"]) not in have:
                problems.append(f"{key}: the quote is not in {t['lines_file']}. Copy it word for word.")
        elif r.get("read", True):
            problems.append(f'{key}: no quote. If the lines say nothing about the rise, write "quote": "" and "read": false.')
        for field in ("says",):
            hit = ADVICE.search(r.get(field, "") or "")
            if hit:
                problems.append(f'{key}: reads as advice ("{hit.group(0)}"). State what the filing says.')
    return problems


def money(v):
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v) / 1e9:,.2f}B" if abs(v) >= 1e9 else f"{sign}${abs(v) / 1e6:,.1f}M"


def lead_source(t, retrieved):
    ln = t["line"]
    return (f'[filing with the later balance, {nice(ln["end_later"])}]({ln["filing_later"]}); [frame {ln["frame_later"]}, retrieved {nice(retrieved)}]({ln["frame_url_later"]}); '
            f'[frame {ln["frame_earlier"]}, retrieved {nice(retrieved)}]({ln["frame_url_earlier"]})')


def why_line(t, retrieved):
    ln = t["line"]
    return (f'{ln["label"]} went from {money(ln["earlier"])} at {nice(ln["end_earlier"])} to {money(ln["later"])} at {nice(ln["end_later"])} '
            f'(+{money(ln["rise_usd"])}, calc.). That rise is {t["ratio"]:.2f}× the latest full year\'s revenue of {money(t["revenue"])}, year to {nice(t["revenue_year"])} (calc.). '
            f'Sources: {lead_source(t, retrieved)}; [SEC company facts, retrieved {nice(retrieved)}](https://data.sec.gov/api/xbrl/companyfacts/CIK{int(t["cik"]):010d}.json).')


def idea_note(t, order, reason):
    key, today, retrieved = t["ticker"] or str(t["cik"]), order["today"], order["retrieved"]
    g1 = "\n".join(f'| {x["name"]} | {x["state"]} | {x["read"]} |' for x in t["gate1"]["tests"])
    fm = ["---", 'form: "idea"', f'company: {json.dumps(t["name"])}', f'ticker: {json.dumps(key)}', f'surfaced: "{today}"', f'filed: "{today}"', 'attention: "unknown"',
          'reason: "A lead to read, never a pick."', "sources:", f'  - {json.dumps(t["line"]["filing_later"])}', f'  - {json.dumps(t["line"]["frame_url_later"])}', "---", ""]
    body = [f'# Idea to read: {t["name"]} ({key}), {nice(today)}', "",
            "*A lead to read, never a pick. It says nothing on whether to own this stock. The hunt wrote this from SEC data, with no thesis and no skeptic's review.*", "",
            "## Why it surfaced", "", why_line(t, retrieved), ""]
    if t.get("look_again_due"):
        body += [f'It is back because its look-again date came: "{t["look_again_due"]}".', ""]
    if t.get("not_new_growth"):
        body += [f'Flag from the radar: {t["not_new_growth"]}.', ""]
    if t.get("filling"):
        body += ["The screen's quarter is still filling, so the figures may be restated.", ""]
    body += ["## What the filing says about the rise", ""]
    if reason.get("quote"):
        body += [f'"{squeeze(reason["quote"])}" ([filing, balance at {nice(t["line"]["end_later"])}]({t.get("doc_url") or t["line"]["filing_later"]}))', ""]
        if reason.get("says"):
            body += [reason["says"], ""]
    else:
        body += ["Not read: the lines the script saved say nothing on it, or could not be read. A rise can be a deal, a deposit, an acquisition, a reclassification, a season or a data slip.", ""]
    body += ["## How far it got", "", "| Test | State | What it read |", "|---|---|---|", g1, "", f'**Gate 2: {t["gate2"]["state"]}.** {t["gate2"]["read"]}']
    if t["gate2"].get("price_source"):
        body += ["", f'Price source: {t["gate2"]["price_source"]}.']
    if t.get("base", {}).get("peak_flag"):
        body += ["", f'**Peak flag:** the last audited year is {t["base"]["peak"]:.1f}× the best earlier year, so the base may rest on a peak (calc.). The owner ruled the method does not fit Micron on such a year. That ruling reaches no other company by itself.']
    body += ["", "**Gate 3, a real edge: not run.** A script and a quick reading of public filings cannot pass it.", "",
              f'Gate 1 figures come from [SEC company facts, retrieved {nice(retrieved)}](https://data.sec.gov/api/xbrl/companyfacts/CIK{int(t["cik"]):010d}.json), not read in print. Reported earnings stand in for normal earnings, so any base value here is a proposal, not the method in full. An open test means a figure could not be read. It is not a pass.', ""]
    return "\n".join(fm + body)


def log_line(t, order):
    for x in t["gate1"]["tests"]:
        if x["state"] == "fail":
            reason, gate = x["read"], "Gate 1"
            break
    else:
        reason, gate = t["gate2"]["read"], "Gate 2"
    return f'| {nice(order["today"])} | {t["name"]} ({t["ticker"]}) | {gate} | {reason} (calc., [SEC company facts, retrieved {nice(order["retrieved"])}](https://data.sec.gov/api/xbrl/companyfacts/CIK{int(t["cik"]):010d}.json)) | After the next 10-K. |'


def report(order, reasons):
    sk, rk = order["skipped"], order["ranked"]
    ideas = [t for t in order["tested"] if (t["ticker"] or str(t["cik"])) in order["ideas"]]
    out = ["---", "track: monthly hunt", f'written: {order["today"]}', "---", "", f'# Monthly hunt, {nice(order["today"])}', "",
           "*Leads, never picks. Waiting for me to read. No note changed. Log: [[Rejection log]].*", "",
           f'**{order["rows"]} rows, {len(order["tested"])} tested, {len(ideas)} written to Inbox (calc.).**', "", "## The funnel", "", "| Step | Count (calc.) | Who |", "|---|---|---|",
           f'| Rows on the screen, retrieved {nice(order["retrieved"])} | {order["rows"]} | {order["companies"]} companies. {order["hidden"]} more hidden by the radar as possibly not new growth |']
    for k, v in sk.items():
        out.append(f'| Skipped: {k} | {len(v)} | {", ".join(v) or "nobody"} |')
    out += [f'| Ranked by rise ÷ revenue | {rk["ranked"]} | |', f'| No revenue figure | {len(rk["no_revenue"])} | {", ".join(rk["no_revenue"]) or "nobody"} |',
            f'| Skipped as not US, while ranking | {len(rk["not_us"])} | {", ".join(rk["not_us"]) or "nobody"} |', f'| Look-again month came, no new filing yet | {len(rk["not_yet"])} | {", ".join(rk["not_yet"]) or "nobody"} |', f'| Tested | {len(order["tested"])} | Top {len(order["tested"])} after checking revenue against company facts |', "", "## The tested companies", "",
            "| Rank | Company | Rise ÷ revenue (calc.) | Gate 1 | Gate 2 | Sorted |", "|---|---|---|---|---|---|"]
    for t in order["tested"]:
        g1 = t["gate1"]["state"]
        fails = "; ".join(x["read"] for x in t["gate1"]["tests"] if x["state"] == "fail")
        sort = "Idea in Inbox" if t in ideas else ("Stopped at Gate 1" if g1 == "fail" else "Stopped at Gate 2")
        out.append(f'| {t["rank"]} | {t["name"]} ({t["ticker"]}) | {t["ratio"]:.2f} | {g1}. {fails} | {t["gate2"]["state"]}. {t["gate2"]["read"]} | {sort} |')
    out += ["", "Sources: " + "; ".join(f'{t["ticker"]}: {lead_source(t, order["retrieved"])}' for t in order["tested"]), ""]
    rej = [t for t in order["tested"] if t not in ideas]
    out += ["## Proposed lines for the Rejection log", "", "*Nothing was added. These are Claude's sort under the bars I accepted, on XBRL figures not read in print. I add them to the log myself.*", ""]
    out += [log_line(t, order) for t in rej] or ["None."]
    out += ["", "## Not done", "", "- Gate 3 ran on nobody. Normal earnings were not worked out. The fit check did not run.", "- Why a lead rose was read only for those written to Inbox, and only in the lines the script saved."]
    out += [f"- {p}" for p in rk["problems"]]
    return "\n".join(out) + "\n"


def finish():
    run = open_run()
    order = json.loads((run / "order.json").read_text())
    reasons = json.loads((run / "reasons.json").read_text()) if (run / "reasons.json").exists() else {}
    problems = check(order, reasons, run)
    if problems:
        print("REFUSED. Fix these and run finish again:")
        for p in problems:
            print("  " + p)
        return 1
    today, written = order["today"], []
    for t in order["tested"]:
        key = t["ticker"] or str(t["cik"])
        if key in order["ideas"]:
            path = INBOX / f"{today} {key} idea.md"
            path.write_text(idea_note(t, order, reasons[key]))
            written.append(path.name)
    rep = RESEARCH / f"{today} Monthly hunt.md"
    rep.write_text(report(order, reasons))
    journal = JOURNAL / f"{today}.md"
    old = journal.read_text() if journal.exists() else f"# {today}\n"
    ideas = ", ".join(f"`Inbox/{n}`" for n in written) or "none"
    block = (f"## Session: monthly hunt\n\n### What we did\n\n- Ran the radar's screen and the hunt triage: {order['rows']} rows, {len(order['tested'])} tested, {len(written)} written to Inbox (calc.). Ideas: {ideas}. Funnel and proposed rejection lines: `{rep.relative_to(ROOT)}`.\n\n"
             f"### What we decided\n\n- Nothing. The hunt picks nothing and recommends nothing. An idea is a lead to read.\n\n### What we left open\n\n- For me: add any proposed lines I want to `Research/Rejection log.md`. The hunt does not.\n")
    temp = journal.with_name(journal.name + ".tmp")
    temp.write_text(old.rstrip("\n") + "\n\n" + block)
    temp.replace(journal)
    s = state()
    for t in order["tested"]:
        s["tested"][str(t["cik"])] = t["step"]
    s["last"] = today
    STATE.write_text(json.dumps(s, indent=1) + "\n")
    (run / "closed.json").write_text(json.dumps({"closed": today}) + "\n")
    print(f"Done. {len(written)} idea(s). Report: {rep.relative_to(ROOT)}")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "start":
            start()
            return 0
        if cmd == "gate2":
            gate2()
            return 0
        if cmd == "finish":
            return finish()
        print(__doc__)
        return 2
    except (Refused, edgar.EdgarError) as err:
        print("STOPPED: " + str(err))
        return 1


if __name__ == "__main__":
    sys.exit(main())
