#!/usr/bin/env python3
"""The sums for the approved valuation method. Reads one inputs file, prints a Markdown table, writes nothing, uses no network.

    python3 value.py INPUTS.json [--price 30] [--what-if-chance plan=0.6]

Method: Rules/when-to-buy.md and Rules/when-to-trim.md. Those rules win over this file.
It stops, and prints why, if an input has no dated source or breaks a limit in the rules.
The fixed numbers below can change only with the owner's approval.
"""
import json
import re
import sys

RATE = 0.09          # the 9%
AAA_ANCHOR = 0.0612  # the 9% reopens if Aaa moves a point from here
VOTES = dict(earn=0.40, cash=0.40, bond=0.20)
GROWTH_CAP = 0.03
COVER_BAR = 0.75
DATED = re.compile(r"(19|20)\d\d|undated, retrieved")


class Stop(Exception):
    pass


def usage():
    raise Stop("Usage: value.py INPUTS.json [--price N] [--what-if-chance KEY=CHANCE]. No other flags.")


def parse(argv):
    path, price, whatif = None, None, {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--price" and i + 1 < len(argv):
            price = float(argv[i + 1]); i += 2
        elif a == "--what-if-chance" and i + 1 < len(argv) and "=" in argv[i + 1]:
            k, v = argv[i + 1].split("=", 1); whatif[k] = float(v); i += 2
        elif a.startswith("-") or path:
            usage()
        else:
            path = a; i += 1
    if not path:
        usage()
    return path, price, whatif


class Inputs:
    """Reads sourced values and collects every one that fails, so the owner sees the whole list at once."""

    def __init__(self):
        self.problems, self.used = [], []

    def get(self, node, label, required=True):
        if node is None or node.get("v") is None:
            if required:
                self.problems.append(f"{label}: no value. Call it unknown, do not fill it in.")
            return None
        src = str(node.get("src", ""))
        if not DATED.search(src):
            self.problems.append(f"{label}: no dated source.")
        self.used.append((label, node["v"], src, node.get("status", "")))
        return float(node["v"])


def cash_sum(cash, g, r=RATE):
    return cash * (1 + g) / (r - g)


def worth(cash, g, r=RATE, t=GROWTH_CAP):
    ten = sum(cash * (1 + g) ** i / (1 + r) ** i for i in range(1, 11))
    return ten + cash * (1 + g) ** 10 * (1 + t) / (r - t) / (1 + r) ** 10


def growth_needed(price, cash):
    if cash <= 0:
        return None
    lo, hi = -0.5, 1.0
    for _ in range(80):
        x = (lo + hi) / 2
        lo, hi = (x, hi) if worth(cash, x) < price else (lo, x)
    return lo


def base(d, inp):
    x = d["inputs"]
    shares = inp.get(x.get("shares_diluted_m"), "Diluted shares, M")
    aaa = inp.get(x.get("aaa"), "Aaa yield")
    rec = inp.get(x.get("record_growth"), "Record growth, the ceiling")
    pts = ("low", "mid", "high")
    e = {k: inp.get(x.get("earnings_m", {}).get(k), f"Normal earnings {k}, $M") for k in pts}
    c = {k: inp.get(x.get("cash_m", {}).get(k), f"Cash, deposits out, {k}, $M") for k in pts}
    g = {k: inp.get(x.get("growth", {}).get(k), f"Cash growth {k}") for k in pts}
    if inp.problems and None in (shares, aaa, rec, *e.values(), *c.values(), *g.values()):
        return None
    ceiling = min(GROWTH_CAP, rec)
    for k in pts:
        if g[k] > ceiling + 1e-9:
            inp.problems.append(f"Cash growth {k} {g[k]:.2%} is above the ceiling of {ceiling:.2%}: the record, and never above 3%.")
    votes = {
        "earn": {k: e[k] / shares / RATE for k in pts},
        "cash": {k: cash_sum(c[k] / shares, g[k]) for k in pts},
        "bond": {k: e[k] / shares / aaa for k in pts},
    }
    combined = {k: sum(VOTES[v] * votes[v][k] for v in VOTES) for k in pts}
    return dict(shares=shares, aaa=aaa, e=e, c=c, g=g, votes=votes, combined=combined)


def multiple(b):
    g = b["g"]["mid"]
    return VOTES["earn"] / RATE + VOTES["cash"] * (1 + g) / (RATE - g) + VOTES["bond"] / b["aaa"]


def strategic(d, b, inp, whatif):
    rows, by_key = [], {}
    mult = multiple(b)
    for s in d.get("scenarios") or []:
        k, name = s["key"], s["name"]
        chance = whatif.get(k, inp.get(s.get("chance"), f"{name}: chance"))
        if chance is not None and not 0 <= chance <= 1:
            inp.problems.append(f"{name}: chance {chance} is not between 0 and 1.")
        years = inp.get(s.get("years"), f"{name}: years away")
        if "margin_cut" in s:  # a downside on the sales other scenarios add, weighted by their chances
            cut = inp.get(s["margin_cut"], f"{name}: margin cut")
            if None in (chance, years, cut):
                continue
            missing = [a for a in s["applies_to"] if a not in by_key]
            if missing:
                inp.problems.append(f"{name}: applies to {missing}, which come later or do not exist. List it after them.")
                continue
            sales = sum(by_key[a]["chance"] * by_key[a]["sales"] for a in s["applies_to"])
            profit, capital = -cut * sales, 0.0
        else:
            sales = inp.get(s.get("new_sales_m"), f"{name}: new sales, $M")
            if "new_profit_m" in s:
                profit = inp.get(s["new_profit_m"], f"{name}: new profit, $M")
            else:
                margin = inp.get(s.get("margin"), f"{name}: margin")
                profit = None if None in (sales, margin) else sales * margin
            ratio = inp.get(s.get("capital_per_sale"), f"{name}: capital per dollar of sales")
            extra = inp.get(s["extra_capital_m"], f"{name}: other capital, $M") if "extra_capital_m" in s else 0.0
            if None in (chance, years, sales, profit, ratio):
                continue
            capital = sales * ratio + extra
        pv = profit * mult / (1 + RATE) ** years
        kpv = capital / (1 + RATE) ** (years / 2)
        full = (pv - kpv) / b["shares"]
        row = dict(key=k, name=name, sales=sales, profit=profit, years=years, pv=pv, kpv=kpv, full=full, chance=chance,
                   status=(s.get("chance") or {}).get("status", ""), value=full * chance)
        rows.append(row); by_key[k] = row
    return rows, mult


def no_vote(d, b, inp, price):
    x, out = d["inputs"], []
    e = b["e"]; sh = b["shares"]
    if x.get("past_tags"):
        low = inp.get(x["past_tags"].get("low"), "Past tag, lowest")
        med = inp.get(x["past_tags"].get("median"), "Past tag, median")
        if None not in (low, med):
            out.append(("Own past multiples", low * e["low"] / sh, med * e["mid"] / sh, med * e["high"] / sh))
    else:
        out.append(("Own past multiples", None, None, None))
    if x.get("rival_per_share"):
        out.append(("Rival multiples", *[inp.get(x["rival_per_share"].get(k), f"Rival multiples {k}") for k in ("low", "mid", "high")]))
    else:
        out.append(("Rival multiples", None, None, None))
    need = None
    if price:
        need = (growth_needed(price, b["c"]["high"] / sh), growth_needed(price, b["c"]["mid"] / sh))
    return out, need


def money(v):
    return "unknown" if v is None else ("−" if v < 0 else "") + f"${abs(v):,.2f}"


def report(d, b, rows, mult, nv, need, price, price_src, price_whatif, whatif):
    c = b["combined"]
    p = print
    p(f"# {d['company']}: valuation sums, as of {d['as_of']}\n")
    if price_whatif or whatif or d.get("what_if"):
        p("**WHAT-IF. Not the method's result. Do not save or act on it.**\n")
    proposed = [r["name"] for r in rows if r["status"] != "approved"]
    p("All figures below are calc. from the inputs listed at the end.\n")
    p("| Measure | Low | Middle | High | Vote |\n|---|---|---|---|---|")
    names = dict(earn="Normal earnings ÷ 9%", cash="Cash sum at 9%", bond="Normal earnings ÷ Aaa")
    for k, n in names.items():
        v = b["votes"][k]
        p(f"| {n} | {money(v['low'])} | {money(v['mid'])} | {money(v['high'])} | {VOTES[k]:.0%} |")
    if not c["low"] <= c["mid"] <= c["high"]:
        p("\n**The base's low, middle and high are out of order. The inputs have broken the method's shape: say so.**\n")
        p("| Measure | Low | Middle | High | Vote |\n|---|---|---|---|---|")
    p(f"| **Base value** | **{money(c['low'])}** | **{money(c['mid'])}** | **{money(c['high'])}** | 100% |")
    for n, lo, mi, hi in nv:
        p(f"| {n} | {money(lo)} | {money(mi)} | {money(hi)} | none |")
    p("")
    buy = c["mid"] / COVER_BAR
    p(f"- Buy-below: {money(buy)} (calc., {money(c['mid'])} ÷ 0.75)")
    if price:
        tag = " (a what-if price)" if price_whatif else f" ({price_src})"
        p(f"- Price: {money(price)}{tag}")
        p(f"- Coverage: {c['mid'] / price:.1%} (calc., middle ÷ price). Range {c['low'] / price:.1%} to {c['high'] / price:.1%}. Bar 75%: {'met' if c['mid'] / price >= COVER_BAR else 'not met'}.")
        p(f"- If the thesis is wrong, the fall from this price: {1 - c['mid'] / price:.0%} to the base middle, {1 - c['low'] / price:.0%} to the low (calc.). A distance, not a forecast.")
        if need:
            a, m = need
            p(f"- Growth the price needs, ten years then 3%, at 9%, no vote: {'unknown' if a is None else f'{a:.1%}'} from the high cash reading, {'unknown' if m is None else f'{m:.1%}'} from the middle (calc.)")
    else:
        p("- Price: unknown. Coverage: unknown.")
    if abs(b["aaa"] - AAA_ANCHOR) >= 0.01 - 1e-9:
        p(f"- **Aaa is {b['aaa']:.2%}, a point or more from 6.12%. The 9% reopens: ask the owner before relying on these.**")
    p("")
    if not rows:
        p("Strategic value: **not worked out.** No scenarios in the inputs. This does not mean zero. Trim-above: unknown.")
    else:
        p(f"New profit × {mult:.2f} (calc., the base's votes), brought back at 9%, less capital, per diluted share.\n")
        p("| Scenario | New sales, $M | New profit, $M | Years | Worth today, $M | Capital today, $M | If it happens, a share | Chance | Value, a share | Chance status |\n|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            p(f"| {r['name']} | {r['sales']:,.0f} | {r['profit']:,.0f} | {r['years']:.2f} | {r['pv']:,.0f} | {r['kpv']:,.0f} | {money(r['full'])} | {r['chance']:.0%} | {money(r['value'])} | {'what-if' if r['key'] in whatif else r['status'] or 'not stated'} |")
        s = sum(r["value"] for r in rows)
        trim = c["mid"] + s
        p(f"\n- Strategic value: {money(s)} (calc.). Never counts toward coverage.")
        p(f"- Trim-above: {money(trim)} (calc., {money(c['mid'])} + {money(s)}).")
        if price:
            p(f"- Price ÷ trim-above: {price / trim:.2f} times (calc.). Being above is not the test: a rise must take the price through the line.")
        if proposed:
            p(f"- **Chances not approved by the owner: {', '.join(proposed)}. Strategic value and trim-above are proposals until they are.**")
    unapproved = [l for l, _, _, st in INP.used if st == "unconfirmed"]
    if unapproved:
        p(f"- **Inputs the owner has not confirmed: {', '.join(unapproved)}. Base value is a proposal until they are.**")
    p("\n## Inputs\n\n| Input | Value | Source | Status |\n|---|---|---|---|")
    for label, v, src, st in INP.used:
        p(f"| {label} | {v} | {src} | {st} |")
    for item in d.get("open") or []:
        p(f"\n**Open item:** {item}")
    p("\nOwner's rules decide what any of this means. These sums make no recommendation.")


INP = Inputs()


def main():
    path, price_arg, whatif = parse(sys.argv[1:])
    d = json.load(open(path, encoding="utf8"))
    b = base(d, INP)
    if b is None:
        raise Stop("\n".join(INP.problems))
    rows, mult = strategic(d, b, INP, whatif)
    node = d["inputs"].get("price")
    saved = INP.get(node, "Price", required=False)
    price = price_arg if price_arg is not None else saved
    nv, need = no_vote(d, b, INP, price)
    unknown = [k for k in whatif if k not in {r["key"] for r in rows}]
    if unknown:
        INP.problems.append(f"--what-if-chance: no scenario called {unknown}.")
    if INP.problems:
        raise Stop("\n".join(INP.problems))
    report(d, b, rows, mult, nv, need, price, (node or {}).get("src", ""), price_arg is not None, whatif)


if __name__ == "__main__":
    try:
        main()
    except Stop as e:
        print("STOPPED. Nothing was worked out.\n" + str(e), file=sys.stderr)
        sys.exit(2)
