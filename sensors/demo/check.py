"""Pull SEC data for the top of the ranking, one at a time, and print each company's own annual record."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sensors/edgar"))
import edgar
REV = ["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax","RevenueFromContractWithCustomerIncludingAssessedTax","SalesRevenueNet","SalesRevenueGoodsNet"]
def annual(facts, tags):
    out = {}
    for t in tags:
        u = facts.get("facts", {}).get("us-gaap", {}).get(t, {}).get("units", {}).get("USD", [])
        for f in u:
            if f.get("form") not in ("10-K","10-K/A","20-F","40-F") or "start" not in f: continue
            import datetime as dt
            d=(dt.date.fromisoformat(f["end"])-dt.date.fromisoformat(f["start"])).days
            if 340<d<380:
                k=f["end"]
                if k not in out or f["filed"]>out[k][1] : out[k]=(f["val"],f["filed"],t)
    return dict(sorted(out.items()))
for cik in sys.argv[1:]:
    folder = edgar.CACHE / f"CIK{int(cik):010d}"
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        edgar.pull(cik)
    sub = json.loads((folder/"submissions.json").read_text()); facts = json.loads((folder/"companyfacts.json").read_text())
    print(f"== {sub['name']} cik{cik} tickers {sub.get('tickers')} ex {sub.get('exchanges')} inc {sub.get('stateOfIncorporationDescription') or sub.get('stateOfIncorporation')} addr {sub.get('addresses',{}).get('business',{}).get('stateOrCountryDescription')} sic {sub.get('sicDescription')} cat {sub.get('category')}")
    forms = sub["filings"]["recent"]
    seen = {}
    for f,d in zip(forms["form"],forms["filingDate"]):
        if f in ("10-K","10-Q","20-F","40-F","6-K") and f not in seen: seen[f]=d
    print("   newest", seen)
    r = annual(facts,REV); print("   rev", [(k[:7],round(v[0]/1e6,1)) for k,v in list(r.items())[-4:]])
    n = annual(facts,["NetIncomeLoss","ProfitLoss"]); print("   ni ", [(k[:7],round(v[0]/1e6,1)) for k,v in list(n.items())[-11:]])
