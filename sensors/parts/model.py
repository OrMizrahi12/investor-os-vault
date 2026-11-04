"""The sum of Corning's parts. Inputs are typed from the printed filings. No network, and it writes nothing.
It is a picture I asked for, not our valuation method. All amounts are $M."""

import statistics
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SEGS = ["Optical", "Glass", "Auto", "Solar", "Life"]
NAME = {"Optical": "Optical Communications", "Glass": "Glass Innovations", "Auto": "Automotive", "Solar": "Solar",
        "Life": "Life Sciences and Emerging Growth"}

# 10-Q filed Oct. 29, 2026, note 14. Nine months of 2026.
SALES_9M26 = dict(Optical=6297, Glass=4389, Auto=1378, Solar=1244, Life=856)
NI_9M26 = dict(Optical=1357, Glass=1006, Auto=219, Solar=-7, Life=-73)
TAX_9M26 = dict(Optical=392, Glass=265, Auto=58, Solar=10, Life=-21)
ASSETS = dict(Optical=5039, Glass=9865, Auto=2384, Solar=3166, Life=1408)
# Q1 2026 release, Apr. 28, 2026: the Q4 2025 column, on the new segments.
SALES_Q425 = dict(Optical=1701, Glass=1499, Auto=440, Solar=475, Life=297)
NI_Q425 = dict(Optical=305, Glass=356, Auto=63, Solar=30, Life=-15)
# Q4 2025 segment tax = FY2025 tax (10-K, old segments) less nine months of 2025 (10-Q, new segments). Calc.
TAX_Q425 = dict(Optical=304 - 215, Glass=259 + 98 - 264, Auto=74 - 57)
_rest = 7 + 16 - (28 - 13)  # Solar and Life together. The filings do not split them.
TAX_Q425["Solar"] = round(30 * 21 / 79)  # 21%, the rate the filing states
TAX_Q425["Life"] = _rest - TAX_Q425["Solar"]

# Reconciliation lines: FY2025 (10-K), nine months 2025 and nine months 2026 (10-Q). TTM = FY - 9M25 + 9M26.
LINES = {
    "fx": (-665, -496, -180 - 424),
    "tec": (150, 63, 212),
    "debt_fx": (-52, -66, 1),
    "legal": (-63, -57, 1),
    "rd": (-159, -124, -124),
    "amort": (-110, -83, -68),
    "interest": (-260, -197, -172),
    "tax": (448, 332, 321),
    "charges": (-33 - 26 - 23 - 11, -10, -123),  # 10-K: pension mark-to-market, severance, capacity, loss on sale
    "other": (-175, -189, -183),
}
def ttm(t):
    return t[0] - t[1] + t[2]
L = {k: ttm(v) for k, v in LINES.items()}

GAAP = dict(sales=ttm((15629, 11414, 13504)), oi=ttm((2279, 1607, 2248)), pretax=ttm((2052, 1374, 2146)),
            ni=ttm((1742, 1155, 1763)), nci=ttm((146, 99, 153)))
FX_SALES = ttm((-779, -582, -201 - 459))

# Market: same inputs as multiples.html, close of Nov. 2, 2026, the latest saved.
PRICE = 123.20
SHARES = 861.4
MKT = 106125  # 861.4M x $123.20, rounded as on multiples.html
DEBT = 8200
CASH = 2537
NCI_BOOK = 617
EV = MKT + DEBT + NCI_BOOK - CASH

# Q3 2026 Optical, 10-Q note 14.
OPTICAL_Q3_PRETAX = 532 + 155
# FY2025 old Life Sciences segment, 10-K: net income 61, tax 16.
OLD_LIFE_PRETAX = 61 + 16


def peers():
    out = {}
    for p in tomllib.loads((ROOT / "sensors/multiples/peers.toml").read_text())["peer"]:
        out[p["name"]] = dict(name=p["name"], url=p["base"], quoted="Nov. 3, 2026 read", ev_ebit=p["ev_ebit"], ev_sales=None)
    for p in tomllib.loads((HERE / "peers.toml").read_text())["peer"]:
        out[p["name"]] = dict(ev_ebit=None, **p) if "ev_ebit" not in p else dict(p)
    return out


OPTICAL_SET = ["YOFC (Hong Kong shares)", "Amphenol", "Furukawa Electric", "Prysmian", "Fujikura", "STL"]
OPTICAL_OUT = ["Sumitomo Electric", "Hengtong"]
GLASS_SET = ["AGC", "Nippon Electric Glass", "Jenoptik"]
AUTO_SET = ["NGK", "AGC", "Fuyao Glass"]
AUTO_OUT = ["Ibiden"]
SOLAR_SET = ["Wacker Chemie", "Tokuyama", "T1 Energy", "OCI Holdings", "First Solar"]
LIFE_SET = ["Avantor", "Thermo Fisher", "Danaher"]


def span(names, key, P):
    vals = sorted(P[n][key] for n in names)
    return vals[0], statistics.median(vals), vals[-1]


def build():
    P = peers()
    sales = {s: SALES_9M26[s] + SALES_Q425[s] for s in SEGS}
    ni = {s: NI_9M26[s] + NI_Q425[s] for s in SEGS}
    tax = {s: TAX_9M26[s] + TAX_Q425[s] for s in SEGS}
    pre = {s: ni[s] + tax[s] for s in SEGS}
    mult = {"Optical": span(OPTICAL_SET, "ev_ebit", P), "Glass": span(GLASS_SET, "ev_ebit", P),
            "Auto": span(AUTO_SET, "ev_ebit", P), "Solar": span(SOLAR_SET, "ev_sales", P)}
    avantor, tmo = P["Avantor"], P["Thermo Fisher"]
    life = (avantor["ev_ebit"] * OLD_LIFE_PRETAX, avantor["ev_sales"] * sales["Life"], tmo["ev_sales"] * sales["Life"])
    val = {}
    for s in ("Optical", "Glass", "Auto"):
        val[s] = [pre[s] * m for m in mult[s]]
    val["Solar"] = [sales["Solar"] * m for m in mult["Solar"]]
    val["Life"] = list(life)
    earners = pre["Optical"] + pre["Glass"] + pre["Auto"]
    blended = [sum(val[s][i] for s in ("Optical", "Glass", "Auto")) / earners for i in range(3)]
    corp_all = -(L["rd"] + L["amort"] + L["other"] + L["charges"] + L["legal"])
    corp_rec = -(L["rd"] + L["amort"] + L["other"])
    corp_base = [corp_all, corp_rec, corp_rec]
    yen = -(L["fx"] + L["tec"])
    cases = []
    for i, nm in enumerate(("Low", "Middle", "High")):
        gross = sum(val[s][i] for s in SEGS)
        corp = corp_base[i] * blended[i]
        yen_v = yen * mult["Glass"][i]
        biz = gross - corp - yen_v
        nci = GAAP["nci"] * blended[i]
        eq = biz - DEBT + CASH - nci
        cases.append(dict(name=nm, gross=gross, corp=corp, yen=yen_v, biz=biz, nci=nci, eq=eq, blended=blended[i],
                          parts={s: val[s][i] for s in SEGS}, corp_base=corp_base[i]))
    low, mid, high = cases
    rest_mid = mid["biz"] - val["Optical"][1]
    need_ev = (EV - rest_mid) / pre["Optical"]
    q3x4 = OPTICAL_Q3_PRETAX * 4
    extra = q3x4 - pre["Optical"]
    sens = [
        ("Middle case as built", mid["eq"]),
        ("High case as built", high["eq"]),
        ("Middle, with Optical on Q3 2026 × 4", mid["eq"] + extra * mult["Optical"][1]),
        ("High, with Optical on Q3 2026 × 4", high["eq"] + extra * mult["Optical"][2]),
        ("High, with Ibiden's multiple on Automotive", high["eq"] + pre["Auto"] * (P["Ibiden"]["ev_ebit"] - mult["Auto"][2])),
        ("High, with no yen gap taken off", high["eq"] + high["yen"]),
        ("High, with no costs outside the segments taken off", high["eq"] + high["corp"]),
        ("High, with outside owners at book", high["eq"] + high["nci"] - NCI_BOOK),
        ("Middle, with Sumitomo and Hengtong added to the Optical set", None),
    ]
    alt = sorted([P[n]["ev_ebit"] for n in OPTICAL_SET + OPTICAL_OUT])
    sens[-1] = (sens[-1][0], mid["eq"] + pre["Optical"] * (statistics.median(alt) - mult["Optical"][1]))
    return dict(P=P, sales=sales, ni=ni, tax=tax, pre=pre, mult=mult, val=val, cases=cases, corp_all=corp_all, corp_rec=corp_rec,
                yen=yen, need_ev=need_ev, q3x4=q3x4, sens=sens, alt_med=statistics.median(alt), blended=blended)


# Segment net income by year, each from the latest 10-K that reports it on that year's segments.
YEARS = list(range(2016, 2026))
HIST = {
    "Optical": [351, 469, 592, 489, 366, 553, 661, 478, 612, 1048],
    "Display": [953, 888, 835, 786, 717, 960, 769, 842, 1006, 993],
    "Specialty": [228, 301, 313, 302, 423, 371, 340, 202, 260, 367],
    "EnvAuto": [159, 165, 208, 263, 197, 269, 292, 290, 261, 278],
    "OldLife": [90, 95, 117, 150, 139, 194, 153, 50, 63, 61],
    "Hemlock": [None, None, None, None, -214, -51, 39, 111, 42, -26],
}
# New segments, by quarter. Q1, Q2 and Q3 releases of 2026, and 10-Q for nine-month ties.
QUARTERS = ["Q1 25", "Q2 25", "Q3 25", "Q4 25", "Q1 26", "Q2 26", "Q3 26"]
QNI = dict(Optical=[201, 247, 295, 305, 387, 438, 532], Glass=[317, 324, 363, 356, 324, 354, 328],
           Auto=[68, 79, 68, 63, 70, 82, 67], Solar=[27, 2, 30, 30, 7, -7, -7], Life=[-30, 6, -15, -15, -24, -21, -28])
QSALES = dict(Optical=[1355, 1566, 1652, 1701, 1846, 2072, 2379], Glass=[1406, 1443, 1560, 1499, 1420, 1463, 1506],
              Auto=[440, 460, 454, 440, 437, 471, 470], Solar=[206, 231, 319, 475, 370, 438, 436], Life=[272, 345, 287, 297, 272, 294, 290])
