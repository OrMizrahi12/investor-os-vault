"""Run the proposed alert map over Corning's saved record, Nov. 3, 2024 to Nov. 2, 2026.

    .venv/bin/python -I sensors/alerts/analyze.py

No network. Reads the EDGAR sensor's saved lists, company facts and Forms 4, the saved Yahoo close and
the FRED Aaa download. Writes cache/results.json. Holds a Yahoo price and Moody's data, so it stays on this computer.
"""
import collections
import csv
import datetime as dt
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from alertmap import ITEMS, MOVE_READ, OTHER, QUARTERS, READ_8K, REPORTED  # noqa: E402

ROOT = HERE.parents[1]
EDGAR = ROOT / "sensors/edgar/cache"
GLW = EDGAR / "CIK0000024741"
START, END = "2024-11-03", "2026-11-03"
LEVEL = {"Info": 0, "Orange": 1, "Red": 2}
K3_LINE, K5_LINE = 17.9, 1505
BUY, TRIM, BASE_LOW = 28.97, 36.06, 14.06


def first_pass(items):
    """Highest level across a filing's items, before anyone reads it."""
    its = [i for i in items if i != "9.01"] or items
    levels = [ITEMS[i][0] for i in its]
    if "1.02" in its and "1.01" not in its:
        levels.append("Red")
    return max(levels, key=LEVEL.get)


rows = [json.loads(line) for line in open(GLW / "filings.jsonl")]
window = [r for r in rows if START <= r["filed"] < END]
kinds = collections.Counter(r["form"] for r in window)

# ---- 8-Ks ----
eights = sorted((r for r in window if r["form"] == "8-K"), key=lambda r: r["filed"])
flag_items = {"1.01", "2.01", "2.02", "5.02", "3.02", "7.01", "8.01"}
events = []
for r in eights:
    items = r["items"].split(",")
    final, mid, claim, said = READ_8K[r["accession"]]
    events.append({"date": r["filed"], "what": said, "map": mid, "first": first_pass(items), "final": final, "claim": claim,
                   "seen": "8-K watcher", "kind": "8-K", "items": r["items"], "label": f'8-K, filed {r["filed"]}', "url": r["url"], "flagged": bool(set(items) & flag_items)})
for date, what, mid, level, claim, seen, label, url in OTHER:
    events.append({"date": date, "what": what, "map": mid, "first": level if level != "Info" else "Orange", "final": level, "claim": claim,
                   "seen": seen, "kind": "other", "items": "", "label": label, "url": url, "flagged": False})
events.sort(key=lambda e: e["date"])

# ---- Insider forms ----
insider_forms = [r for r in window if r["form"] in ("4", "4/A", "144", "3", "3/A")]
folder = GLW / "documents/insider"
names = os.listdir(folder)
sales = buys = grants = read = 0
for r in insider_forms:
    if r["form"] not in ("4", "4/A"):
        continue
    hit = [n for n in names if n.startswith(r["accession"])]
    root = ET.parse(folder / hit[0]).getroot()
    read += 1
    codes = [x.findtext("transactionCoding/transactionCode", "").strip()
             for t in ("nonDerivativeTable/nonDerivativeTransaction", "derivativeTable/derivativeTransaction") for x in root.findall(t)]
    relation = root.find("reportingOwner/reportingOwnerRelationship")
    director_only = relation.findtext("isDirector", "").strip() in ("1", "true") and not relation.findtext("officerTitle", "").strip()
    sales += "S" in codes
    buys += "P" in codes
    grants += bool(codes) and director_only and set(codes) == {"A"}

# ---- Info tally: every filing is one item, except the two that merge or stay Orange ----
letters_orange = {e["url"].split("/")[-2] for e in events if e["map"] == "O10"}
other_forms = collections.Counter()
info_filings = []
for r in window:
    if r["form"] == "8-K" or r["form"] == "424B5":
        continue
    if r["form"] == "UPLOAD" and r["accession"].replace("-", "") in letters_orange:
        continue
    other_forms[r["form"]] += 1
    info_filings.append(r["filed"])
info_8k = [e for e in events if e["kind"] == "8-K" and e["final"] == "Info"]
info_news = [e for e in events if e["kind"] == "other" and e["final"] == "Info"]
brief_days = sorted(set(info_filings) | {e["date"] for e in info_8k} | {e["date"] for e in info_news})

# ---- Kill lines run back ----
quarters, prev = [], None
for i, q in enumerate(QUARTERS):
    name, sales_q, income, core, ocf, capex, dep, src = q
    row = {"q": name, "sales": sales_q, "income": income, "core": core, "x4": core * 4, "src": src, "reported": REPORTED.get(name)}
    row["margin"] = round(income / sales_q * 100, 1) if sales_q else None
    if i >= 3:
        last4 = QUARTERS[i - 3:i + 1]
        row["k5"] = sum(x[4] for x in last4) - sum(x[5] for x in last4) - sum(x[6] for x in last4)
    quarters.append(row)
for i, row in enumerate(quarters):
    before = quarters[i - 1] if i else None
    row["fall"] = bool(before and before["sales"] and row["sales"] and row["sales"] < before["sales"])
    row["k3_low"] = row["margin"] is not None and row["margin"] <= K3_LINE
    row["k3_cross"] = bool(row["k3_low"] and before and before.get("k3_low"))

# K9, from the three buyers' saved facts: the same measure as the catalyst note
P = dt.date.fromisoformat
CIKS = {"Meta": "0001326801", "Amazon": "0001018724", "Microsoft": "0000789019"}
TAGS = {"Meta": ["PaymentsToAcquirePropertyPlantAndEquipment"], "Amazon": ["PaymentsToAcquireProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"],
        "Microsoft": ["PaymentsToAcquirePropertyPlantAndEquipment"]}
spend = {}
for name, cik in CIKS.items():
    facts = json.load(open(EDGAR / f"CIK{cik}/companyfacts.json"))["facts"]["us-gaap"]
    points = {}
    for tag in TAGS[name]:
        for u in facts.get(tag, {}).get("units", {}).get("USD", []):
            if "start" in u:
                key = (u["start"], u["end"])
                if key not in points or u["filed"] > points[key][1]:
                    points[key] = (u["val"], u["filed"])
    per = {}
    for (s, e), (v, _) in points.items():
        if 80 < (P(e) - P(s)).days < 100:
            per[e] = v
    for (s, e), (v, _) in points.items():
        if (P(e) - P(s)).days > 100 and e not in per:
            for (s2, e2), (v2, _) in points.items():
                if s2 == s and 80 < (P(e) - P(e2)).days < 100:
                    per[e] = v - v2
    spend[name] = per
ends = sorted(e for e in spend["Meta"] if e >= "2017-06-30" and all(e in spend[n] for n in CIKS))
k9 = [{"end": e, "total": round(sum(spend[n][e] for n in CIKS) / 1e6)} for e in ends]
for i, row in enumerate(k9):
    row["fall"] = bool(i and row["total"] < k9[i - 1]["total"])
    row["fired"] = bool(i and row["fall"] and k9[i - 1]["fall"])

# ---- Prices ----
prices = [(r["date"], float(r["close"])) for r in csv.DictReader(open(ROOT / "sensors/prices/cache/GLW/2026-11-02.csv"))]
win = [p for p in prices if p[0] >= START]
low, high = min(win, key=lambda p: p[1]), max(win, key=lambda p: p[1])
moves = []
for (d0, c0), (d1, c1) in zip(prices, prices[1:]):
    if d1 >= START:
        moves.append({"date": d1, "from": round(c0, 2), "to": round(c1, 2), "pct": round((c1 / c0 - 1) * 100, 1)})
top = sorted(moves, key=lambda m: -abs(m["pct"]))[:16]
for m in top:
    how, note, label, url = MOVE_READ.get(m["date"], ("unknown", "Nothing on file. Not searched.", "", ""))
    m.update(how=how, note=note, label=label, url=url)
last_under = {str(L): [p for p in prices if p[1] < L][-1] for L in (BUY, TRIM)}

# ---- Aaa ----
aaa_rows = list(csv.DictReader(open(ROOT / "sensors/macro/downloads/AAA.csv")))
key = list(aaa_rows[0])
aaa = [(r[key[0]], float(r[key[1]])) for r in aaa_rows if r[key[0]] >= "2024-11-01" and r[key[1]] not in ("", ".")]
aaa_far = max(abs(v - 6.12) for _, v in aaa)

# ---- Sizing drill on a made-up position: the gates would have barred this buy ----
start_price = win[0][1]
shares = 5000 / start_price
refresh_days = sorted(r["filed"] for r in window if r["form"] in ("10-Q", "10-K"))
drill = []
closes = dict(win)
for day in refresh_days:
    close = closes.get(day) or [c for d, c in win if d <= day][-1]
    book = 95000 + shares * close
    raw = shares * (close - BASE_LOW) / book * 100
    drill.append({"day": day, "close": round(close, 2), "loss_pct": round(raw, 2), "over": raw > 5})
drill_first = next(d for d in drill if d["over"])

# ---- 8-K items over the whole dotted record ----
dotted = [r for r in rows if r["form"] in ("8-K", "8-K/A") and r["filed"] >= "2004-10-01" and "." in r["items"]]
item_all = collections.Counter(i for r in dotted for i in r["items"].split(","))
item_win = collections.Counter(i for r in eights for i in r["items"].split(","))
red_set = {"1.03", "2.04", "2.06", "3.01", "4.02", "5.01"}
red_all = [{"filed": r["filed"], "items": r["items"], "url": r["url"]} for r in sorted(dotted, key=lambda r: r["filed"])
           if set(r["items"].split(",")) & red_set or ("1.02" in r["items"] and "1.01" not in r["items"])]

run = json.load(open(ROOT / "sensors/radar/runs/2026-11-03-03.json"))
tally = {
    "red": 0, "red_runback": 1,
    "orange": sum(e["final"] == "Orange" for e in events),
    "orange_watcher": sum(e["final"] == "Orange" and e["seen"] == "8-K watcher" for e in events),
    "orange_radar": sum(e["final"] == "Orange" and e["seen"] == "radar" for e in events),
    "orange_person": sum(e["final"] == "Orange" and e["seen"] == "person" for e in events),
    "orange_news": sum(e["final"] == "Orange" and e["seen"] == "person" and e["map"] == "O2" for e in events),
    "orange_letters": sum(e["final"] == "Orange" and e["map"] == "O10" for e in events),
    "first_8k": dict(collections.Counter(e["first"] for e in events if e["kind"] == "8-K")),
    "final_8k": dict(collections.Counter(e["final"] for e in events if e["kind"] == "8-K")),
    "flagged_8k": sum(e["flagged"] for e in events if e["kind"] == "8-K"),
    "info": len(info_filings) + len(info_8k) + len(info_news),
    "info_filings": len(info_filings), "info_8k": len(info_8k), "info_news": len(info_news),
    "brief_days": len(brief_days), "trading_days": len(win),
    "insider": len(insider_forms), "insider_sales": sales, "insider_buys": buys, "insider_grants": grants, "insider_read": read,
    "filings": len(window),
    "price_alerts": 0, "aaa_alerts": 0, "aaa_far": round(aaa_far, 2),
    "moves_filing": sum(m["how"] == "filing" for m in top), "moves_news": sum(m["how"] == "news" for m in top),
    "moves_none": sum(m["how"] == "none" for m in top), "moves_unknown": sum(m["how"] == "unknown" for m in top),
    "radar_leads": run["screen"]["lead_count"], "radar_hidden": run["hidden"]["lead_count"],
    "radar_dates": sum(len(run["dates"][k]) for k in ("soon", "passed", "wide")),
    "radar_soon": len(run["dates"]["soon"]), "radar_passed": len(run["dates"]["passed"]), "radar_wide": len(run["dates"]["wide"]),
}

out = {"window": [START, END], "tally": tally, "events": events, "quarters": quarters, "k9": k9,
       "k9_falls": [r["end"] for r in k9 if r["fall"]], "k9_fired": [r["end"] for r in k9 if r["fired"]],
       "prices": [(d, round(c, 2)) for d, c in win], "low": low, "high": high, "last": win[-1], "top": top,
       "last_under": last_under, "aaa": aaa, "drill": drill, "drill_first": drill_first, "drill_shares": shares,
       "item_all": item_all, "item_win": item_win, "dotted": len(dotted), "red_all": red_all,
       "other_forms": other_forms, "kinds": kinds, "brief_days": brief_days}
(HERE / "cache").mkdir(exist_ok=True)
(HERE / "cache/results.json").write_text(json.dumps(out, indent=1))
print(json.dumps(tally, indent=1))
print("K3 crossed:", [q["q"] for q in quarters if q["k3_cross"]], "K8 falls:", [q["q"] for q in quarters if q["fall"]])
print("K5:", [(q["q"], q.get("k5")) for q in quarters if q.get("k5")])
print("K9 falls:", out["k9_falls"], "fired:", out["k9_fired"], k9[-3:])
print("drill:", drill, "first:", drill_first)
print("other:", other_forms, "red_all:", red_all, "dotted", len(dotted))
print("low/high", low, high, "under", last_under)
for m in top:
    print(m["date"], m["pct"], m["how"])
