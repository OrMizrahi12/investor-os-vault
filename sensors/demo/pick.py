"""Pick the hunt's batch: the rule the owner set on Nov. 3, 2026, read as the Triage report reads it.

Rise on one line / latest full year's revenue, from SEC data, no price. Skip our map, the rejection log,
the watchlist and unit-slip rows. Top five. Count any lead with no revenue figure.
Revenue comes from SEC's annual frames (one number per company, CY2025), so three or four requests cover all leads.
A lead missing from them goes to the company's own facts in the next step. Writes sensors/demo/cache/pick.json.
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sensors/edgar"))
import edgar

RUN = ROOT / "sensors/radar/runs/2026-11-03-03.json"
TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"]
OUT = Path(__file__).resolve().parent / "cache"

s = edgar.load_settings()
client = edgar.SecClient(s["user_agent"], s["rate"])
rev = {}
for tag in TAGS:
    p = OUT / f"{tag}-CY2025.json"
    if not p.exists():
        try:
            p.write_bytes(client.get(f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/CY2025.json"))
        except edgar.EdgarError as e:
            print("no frame", tag, e); continue
    for row in json.loads(p.read_text())["data"]:
        if row["cik"] not in rev or row["val"] > rev[row["cik"]]["val"]:
            rev[row["cik"]] = {"val": row["val"], "tag": tag, "end": row["end"], "accn": row["accn"]}

run = json.loads(RUN.read_text())
log = (ROOT / "Research/Rejection log.md").read_text()
rejected = set(re.findall(r"\(([A-Z.]+)\) \|", log))
watch = {"MU"}
leads, skips = {}, {"on map": [], "rejection log": [], "watchlist": [], "unit slip": []}
for step in run["screen"]["steps"]:
    for lead in step["unit_check"]:
        skips["unit slip"].append(f"{lead['name']} ({lead.get('ticker')})")
    for lead in step["leads"]:
        best = max(lead["lines"], key=lambda l: l["rise_usd"])
        t = lead.get("ticker")
        if lead.get("on_map"): skips["on map"].append(lead["name"]); continue
        if t in rejected: skips["rejection log"].append(lead["name"]); continue
        if t in watch: skips["watchlist"].append(lead["name"]); continue
        cur = leads.get(lead["cik"])
        if not cur or best["rise_usd"] > cur["line"]["rise_usd"]:
            leads[lead["cik"]] = {"cik": lead["cik"], "name": lead["name"], "ticker": t, "line": best,
                                  "step": step["later"], "revenue": rev.get(lead["cik"])}
rows = list(leads.values())
for r in rows:
    r["ratio"] = r["line"]["rise_usd"] / r["revenue"]["val"] if r["revenue"] and r["revenue"]["val"] > 0 else None
have = sorted([r for r in rows if r["ratio"] is not None], key=lambda r: -r["ratio"])
miss = [r for r in rows if r["ratio"] is None]
json.dump({"skips": skips, "have": have, "miss": miss}, open(OUT / "pick.json", "w"), indent=1)
print("requests", len(client.sent), "| skips", {k: len(v) for k, v in skips.items()}, "| ranked", len(have), "| no frame revenue", len(miss))
print("skipped:", skips)
for r in have[:25]:
    l = r["line"]; print(f"{r['ratio']:8.2f} {r['ticker']} {r['name']} cik{r['cik']} | {l['label']} {l['earlier']/1e6:.1f}M->{l['later']/1e6:.1f}M {l['end_later']} | rev {r['revenue']['val']/1e6:.1f}M ({r['revenue']['end']})")
print("MISSING:")
for r in miss: print(r["ticker"], r["name"], r["cik"], r["line"]["rise_usd"]/1e6)
