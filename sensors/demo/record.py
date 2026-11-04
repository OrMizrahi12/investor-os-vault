"""Print one company's Gate 1 record from the saved SEC facts: annual lines by period end, and year-to-date lines."""
import json, sys, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TAGS = {"ni":["NetIncomeLoss","ProfitLoss"],"rev":["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax","RevenueFromContractWithCustomerIncludingAssessedTax"],
"opinc":["OperatingIncomeLoss"],"int":["InterestExpense","InterestExpenseNonoperating","InterestExpenseDebt","InterestIncomeExpenseNet","InterestPaidNet"],
"ocf":["NetCashProvidedByUsedInOperatingActivities"],"capex":["PaymentsToAcquirePropertyPlantAndEquipment","PaymentsToAcquireProductiveAssets","PaymentsToAcquireOilAndGasPropertyAndEquipment"],
"acq":["PaymentsToAcquireBusinessesNetOfCashAcquired"],"dil":["WeightedAverageNumberOfDilutedSharesOutstanding"],
"eps":["EarningsPerShareDiluted"]}
BAL={"cl":["ContractWithCustomerLiability","ContractWithCustomerLiabilityCurrent","ContractWithCustomerLiabilityNoncurrent"],
"debt":["LongTermDebt","LongTermDebtNoncurrent","LongTermDebtCurrent","DebtInstrumentCarryingAmount","LongTermDebtAndCapitalLeaseObligations","SeniorNotes","LineOfCredit"],
"cash":["CashAndCashEquivalentsAtCarryingValue","ShortTermInvestments"],"eq":["StockholdersEquity"]}
for cik in sys.argv[1:]:
    f=json.loads((ROOT/f"sensors/edgar/cache/CIK{int(cik):010d}/companyfacts.json").read_text())["facts"]["us-gaap"]
    print("=====",cik)
    for key,tags in TAGS.items():
        for t in tags:
            u=f.get(t,{}).get("units",{}); u=u.get("USD") or u.get("shares") or u.get("USD/shares") or []
            if not u: continue
            ann={};ytd={}
            for x in u:
                if "start" not in x: continue
                d=(dt.date.fromisoformat(x["end"])-dt.date.fromisoformat(x["start"])).days
                if 340<d<380 and x["form"].startswith("10-K"): ann[x["end"]]=x["val"]
                elif x["form"].startswith("10-Q") and x["end"]>="2025-01-01" and x["start"]>="2024-09-01": ytd[(x["start"],x["end"])]=x["val"]
            sc=1e6 if key!="eps" else 1
            print(f"{key} {t}: ANN",[(k[:7],round(v/sc,2)) for k,v in sorted(ann.items())][-11:])
            print("    YTD",[(a[:7],b[:7],round(v/sc,2)) for (a,b),v in sorted(ytd.items(),key=lambda z:(z[0][1],z[0][0]))][-8:])
    for key,tags in BAL.items():
        for t in tags:
            u=f.get(t,{}).get("units",{}).get("USD",[])
            if not u: continue
            pts={x["end"]:x["val"] for x in u if x["end"]>="2024-06-01"}
            print(f"{key} {t}:",[(k,round(v/1e6,1)) for k,v in sorted(pts.items())][-8:])
