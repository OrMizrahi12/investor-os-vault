"""Strategic value for Corning, as approved Nov. 3, 2026 and saved in Rules/when-to-trim.md. No network, and it writes nothing.
Each scenario is valued only on what is not in the base value or the reported numbers. Nothing here reads the price,
except the page's comparison, so value cannot rise because the price did. Amounts are $M unless marked."""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
_s = importlib.util.spec_from_file_location("base_model", ROOT / "sensors/base/model.py")
base_model = importlib.util.module_from_spec(_s)
_s.loader.exec_module(base_model)

SHARES, RATE, AAA = base_model.SHARES, base_model.RATE, base_model.AAA
PRICE = base_model.PRICE  # used only for comparisons in compare(), never inside a scenario

# Q3 2026, 10-Q filed Oct. 29, 2026, note 14. Segment sales add to core sales.
Q3_SALES = dict(Optical=2379, Glass=1506, Auto=470, Solar=436, Life=290)
Q3_NI = dict(Optical=532, Glass=328, Auto=67, Solar=-7, Life=-28)
Q3_TAX_GLASS = 87
Q3_OPT_LAST_YEAR = (1652, 295)  # Q3 2025 sales and net income
Q3_GAAP = (4855, 680)  # GAAP sales and net income
Q425_OPT = (1701, 305)  # Q4 2025, Q1 2026 release
ASSETS = dict(Optical=5039, Solar=3166)  # segment assets, Sept. 30, 2026
TTM_SALES = dict(Optical=6297 + 1701, Solar=1244 + 475)
DISPLAY_FY25 = 3697  # 10-K filed Feb. 12, 2026
EARN_OUT = 132  # contingent liability, Sept. 30, 2026
RUN_RATE = 4 * sum(Q3_SALES.values())
INTERNAL_2030, HIGH_CONF_2030 = 40000, 35000
SOLAR_GOAL = 3000

OPT_MARGIN = Q3_NI["Optical"] / Q3_SALES["Optical"]
OPT_MARGIN_LOW = Q425_OPT[1] / Q425_OPT[0]
OPT_INCREMENTAL = (Q3_NI["Optical"] - Q3_OPT_LAST_YEAR[1]) / (Q3_SALES["Optical"] - Q3_OPT_LAST_YEAR[0])
GROUP_MARGIN = Q3_GAAP[1] / Q3_GAAP[0]
GLASS_TAX = Q3_TAX_GLASS / (Q3_NI["Glass"] + Q3_TAX_GLASS)
OPT_CAPITAL = ASSETS["Optical"] / TTM_SALES["Optical"]
SOLAR_CAPITAL = ASSETS["Solar"] / TTM_SALES["Solar"]

# Years from Nov. 3, 2026.
T2027, T2028, T2029, T2030 = 1.16, 2.16, 3.16, 4.16

# Signed deals: annual sales at the stated ceiling. Term and minimums are my assumptions where marked.
TERM = 6  # the only full term stated is Verizon's, 2027 through 2032
MULTI_MIN = 2000  # "multibillion" read as at least $2 billion
DEALS = [
    ("Meta", 6000, "up to $6 billion, stated"),
    ("Two unnamed hyperscalers", 12000, "each similar to Meta, so up to $6 billion each"),
    ("Verizon", MULTI_MIN, "multibillion, no figure"),
    ("AT&T", 3000 - 1000, "more than $3 billion, less the 2024 deal of more than $1 billion it may include"),
    ("Two other Q3 deals", 2 * MULTI_MIN, "multibillion, no figure; Zayo may be one"),
]
DEALS_CEILING = sum(d[1] for d in DEALS) / TERM
NEW_SHARE = .75  # my assumption: the rest replaces sales already in the Q3 run rate
DISPLAY_RISE = .05  # my assumption: the amount is not disclosed


def multiple(g=None, r=RATE, aaa=AAA):
    """The base vote applied to a dollar of new earnings: 40% ÷ 9%, 40% cash sum at record growth, 20% ÷ Aaa."""
    g = base_model.growth()["ni"] if g is None else g
    return .4 / r + .4 * (1 + g) / (r - g) + .2 / aaa


def sized(key, sales, margin, t, capital_ratio, p, extra=0, ni=None, mult=None, capital=True, r=RATE):
    mult = multiple(r=r) if mult is None else mult
    ni = sales * margin if ni is None else ni
    gross = ni * mult
    pv = gross / (1 + r) ** t
    kapital = (sales * capital_ratio + extra) if capital else 0
    kpv = kapital / (1 + r) ** (t / 2)
    dollars = pv - kpv
    return dict(key=key, sales=sales, margin=margin, ni=ni, t=t, gross=gross, pv=pv, capital=kapital, kpv=kpv, dollars=dollars,
                full=dollars / SHARES, p=p, ev=p * dollars / SHARES)


PROB = dict(signed=.70, plan=.40, scaleup=.20, solar=.35, display=.50, rival=.40)


def ladder(new_share=NEW_SHARE, display_rise=DISPLAY_RISE):
    signed = DEALS_CEILING * new_share
    solar = SOLAR_GOAL - 4 * Q3_SALES["Solar"]
    display = DISPLAY_FY25 * display_rise
    plan = HIGH_CONF_2030 - RUN_RATE - signed - solar - display
    top = INTERNAL_2030 - HIGH_CONF_2030
    return dict(signed=signed, plan=plan, scaleup=top, solar=solar, display=display)


def scenarios(prob=None, margin=None, mult=None, capital=True, new_share=NEW_SHARE, display_rise=DISPLAY_RISE, r=RATE, rival_low=None):
    prob = {**PROB, **(prob or {})}
    m = OPT_MARGIN if margin is None else margin
    lad = ladder(new_share, display_rise)
    kw = dict(mult=mult, capital=capital, r=r)
    out = [
        sized("signed", lad["signed"], m, T2028, OPT_CAPITAL, prob["signed"], **kw),
        sized("plan", lad["plan"], m, T2030, OPT_CAPITAL, prob["plan"], **kw),
        sized("scaleup", lad["scaleup"], m, T2030, OPT_CAPITAL, prob["scaleup"], **kw),
        sized("solar", lad["solar"], GROUP_MARGIN, T2029, SOLAR_CAPITAL, prob["solar"], extra=EARN_OUT,
              ni=SOLAR_GOAL * GROUP_MARGIN - 4 * Q3_NI["Solar"], **kw),
        sized("display", lad["display"], 1 - GLASS_TAX, T2027, 0, prob["display"], **kw),
    ]
    # The downside: rival capacity cuts the margin on the Optical sales the scenarios above add. Base value is not touched.
    exp_sales = sum(x["p"] * x["sales"] for x in out[:3])
    low = OPT_MARGIN_LOW if rival_low is None else rival_low
    cut = max(m - low, 0) * exp_sales
    gross = cut * (multiple(r=r) if mult is None else mult)
    pv = gross / (1 + r) ** T2029
    out.append(dict(key="rival", sales=exp_sales, margin=m - low, ni=-cut, t=T2029, gross=-gross, pv=-pv, capital=0, kpv=0, dollars=-pv,
                    full=-pv / SHARES, p=prob["rival"], ev=-prob["rival"] * pv / SHARES))
    return out


def base_value():
    return base_model.combine(base_model.methods())


def strategic(**kw):
    return sum(x["ev"] for x in scenarios(**kw))


def trim_above(**kw):
    return base_value()["mid"] + strategic(**kw)


def all_true():
    """All five come true, with no rival cut. Not a forecast."""
    return base_value()["mid"] + sum(x["full"] for x in scenarios() if x["key"] != "rival")


def failed_capital():
    """If the plants get built and a scenario fails, the capital is lost. Not in the middle case, because agreements share that risk."""
    return sum((1 - x["p"]) * x["kpv"] / SHARES for x in scenarios() if x["key"] in ("signed", "plan", "scaleup"))


def sensitivities():
    t0 = trim_above()
    p_up = {k: min(v + .1, 1) for k, v in PROB.items() if k != "rival"}
    p_dn = {k: max(v - .1, 0) for k, v in PROB.items() if k != "rival"}
    g3 = multiple(g=.03)
    rows = [
        ("Each chance 10 points lower", trim_above(prob=p_dn)),
        ("Each chance 10 points higher", trim_above(prob=p_up)),
        ("New profit ÷ 9%, the earnings vote only", trim_above(mult=1 / RATE)),
        ("Cash vote at the 3% cap, not the record", trim_above(mult=g3)),
        (f"Optical margin {OPT_INCREMENTAL * 100:.1f}%, the last year's added", trim_above(margin=OPT_INCREMENTAL)),
        ("No capital charge: customers fund every plant", trim_above(capital=False)),
        ("Capital lost when a fiber scenario fails", t0 - failed_capital()),
        ("No rival price cut", trim_above(prob=dict(rival=0))),
        ("Only half of signed deals are new sales", trim_above(new_share=.5)),
        ("Display rise of 10%, not 5%", trim_above(display_rise=.10)),
        ("Base high in place of base middle", base_value()["high"] + strategic()),
        ("Discount rate 8%", base_mid_at(.08) + strategic(r=.08)),
        ("Discount rate 10%", base_mid_at(.10) + strategic(r=.10)),
    ]
    return t0, rows


def base_mid_at(r):
    return base_model.combine(base_model.methods(r))["mid"]


def stretch():
    """Every favorable reading at once: all five true, the added margin, no capital, the 3% cap, no rival cut."""
    xs = scenarios(margin=OPT_INCREMENTAL, capital=False, mult=multiple(g=.03))
    return base_value()["high"] + sum(x["full"] for x in xs if x["key"] != "rival")


def multiple_needed():
    """What multiple of new earnings the price needs if all five come true, with capital charged. Arithmetic only."""
    lo, hi = 1, 400
    for _ in range(80):
        x = (lo + hi) / 2
        v = base_value()["mid"] + sum(s["full"] for s in scenarios(mult=x) if s["key"] != "rival")
        lo, hi = (x, hi) if v < PRICE else (lo, x)
    return lo


def compare():
    b = base_value()
    s = strategic()
    t = b["mid"] + s
    return dict(base=b, strategic=s, trim=t, price=PRICE, gap=PRICE - t, cover=t / PRICE, times=PRICE / t,
                implied=PRICE - b["mid"], share=s / (PRICE - b["mid"]), buy=base_model.buy_below(b["mid"]))


# Where each of the 38 catalyst notes went. Each note is in exactly one place. Tested against the folder.
SIGNED, PLAN, SCALE, SOLAR, DISPLAY, RIVAL = "Scenario 1", "Scenario 2", "Scenario 3", "Scenario 4", "Scenario 5", "Downside"
OUT_NUM, OUT_PRICE, OUT_NOSIZE, OUT_EMPTY, OUT_COST = "Out: in the numbers", "Out: turns on the price", "Out: cannot be sized", "Out: no event", "Cost, not value"
MAP = {
    "$20 billion run rate by end of 2026": (OUT_NUM, "Q3 times four already reaches it."),
    "$30 billion run rate by end of 2028": (PLAN, "A checkpoint on the ladder. It adds no dollars of its own."),
    "$40 billion run rate by end of 2030": (SCALE, "Sets the top of the ladder. Adding it to the deals would count them twice."),
    "AT&T fiber deal": (SIGNED, "Net of the 2024 deal it may include."),
    "Activist Schedule 13D watch": (OUT_EMPTY, "No filing exists."),
    "Amazon fiber deal": (SIGNED, "Not added. It may be one of the two unnamed deals."),
    "Apple cover glass move to Kentucky": (OUT_NUM, "Apple glass is already sold. The $2.5 billion is not split out."),
    "At-the-market share program": (OUT_PRICE, "Selling shares changes value only by how the price compares with it. Plant money is charged instead."),
    "BEAD Buy America priority": (PLAN, "Not sized. Sits inside Carrier sales."),
    "Capex plan for 2027": (OUT_COST, "The capital charge in each scenario covers this."),
    "Carrier data center interconnect goal": (PLAN, "No new target. Sits inside Optical sales."),
    "China duty on US fiber": (OUT_NOSIZE, "Corning's China fiber sales are unknown."),
    "China germanium export suspension": (OUT_NOSIZE, "A risk with no link to Corning proved. Held in the fiber chances."),
    "Display glass price rises": (DISPLAY, "Amount undisclosed, so sized on my assumption."),
    "EU cover glass commitments": (OUT_NOSIZE, "Sales effect not stated."),
    "Hickory expansion": (SIGNED, "How the Meta deal ships. A plant is not extra sales."),
    "Hollow-core fiber with Microsoft": (OUT_NOSIZE, "Size unknown. Any sales fall inside the Optical plan."),
    "India plants": (PLAN, "Capacity, not extra sales."),
    "Lumen capacity reservation": (OUT_NUM, "Shipments may be in Optical since 2024. Terms unknown."),
    "Meta fiber deal": (SIGNED, "At its ceiling, then cut for sales it replaces."),
    "NVIDIA partnership and warrants": (PLAN, "Contract value unknown. The deposit is not value, and the $500M is already received."),
    "Operating margin goal": (OUT_NUM, "Reached on core. No new target."),
    "Optical scale-up and Photonics": (SCALE, "Capped at the $5 billion between the two 2030 plans."),
    "Poland plant opening": (PLAN, "Capacity, not extra sales."),
    "Rival fiber capacity from 2028": (RIVAL, "Taken off the added Optical margin."),
    "Samsung Display share sale": (OUT_PRICE, "A buyback adds value only below value. At this price it would take value away."),
    "Section 232 polysilicon tariff": (SOLAR, "Helps reach the Solar goal. Not extra dollars."),
    "Solar module plant earn-out": (SOLAR, "Its $132M liability is charged to the scenario."),
    "Solar revenue goal": (SOLAR, "The size of the scenario."),
    "Solar supply deals": (SOLAR, "How Solar sells. Not extra dollars."),
    "Solar wafer ramp": (SOLAR, "How Solar produces. Not extra dollars."),
    "Spin-off or sale": (OUT_EMPTY, "No report or bid. A split adds no profit by itself."),
    "Three new plants with NVIDIA": (PLAN, "Capacity, not extra sales."),
    "Two unnamed hyperscaler deals": (SIGNED, "Size rests on Corning's comparison with Meta."),
    "US manufacturing tax credits": (OUT_NUM, "45X credits are already in margins. Losing them is held in Solar's chance."),
    "Verizon fiber deal": (SIGNED, "Read as at least $2 billion."),
    "Wilmington fiber expansion": (PLAN, "$585M of capacity. The capital charge covers it."),
    "Zayo and the fourth Q3 deal": (SIGNED, "Inside the two other Q3 deals. No source says Zayo is one of them."),
}


if __name__ == "__main__":
    for x in scenarios():
        print({k: round(v, 3) if isinstance(v, float) else v for k, v in x.items()})
    print("multiple", multiple(), "run rate", RUN_RATE, "ladder", ladder(), "sum", sum(ladder().values()), INTERNAL_2030 - RUN_RATE)
    print({k: round(v, 4) if isinstance(v, float) else v for k, v in compare().items()})
    print("margins", OPT_MARGIN, OPT_MARGIN_LOW, OPT_INCREMENTAL, GROUP_MARGIN, GLASS_TAX, OPT_CAPITAL, SOLAR_CAPITAL, "ceiling", DEALS_CEILING)
    print("all true", all_true(), "stretch", stretch(), "multiple needed", multiple_needed())
    t0, rows = sensitivities()
    for n, v in rows:
        print(round(v, 2), n)
    print(len(MAP))
