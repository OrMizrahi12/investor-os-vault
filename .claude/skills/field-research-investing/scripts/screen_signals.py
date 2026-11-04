#!/usr/bin/env python3
"""Idea-generation screens.

Subcommands:
  text      Flag warning phrases (possible trouble) and quiet-improvement phrases in news or filings text.
  capacity  Flag capacity starvation (capex below depreciation, shrinking net PP&E) and turning demand
            (accelerating sales, sales outrunning inventory, rising gross margin) from a CSV.

Screens are radar only: every hit is a lead to read in context and then research firsthand.
Standard-library Python 3 only. Run any subcommand with --help.
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict

WARNING_PATTERNS = [
    ("denial", r"\b(management|company)\s+(categorically\s+)?denie[sd]\b"),
    ("denial", r"\brumou?rs?\b[^.]{0,60}\b(no basis|unfounded|baseless|without merit)\b"),
    ("departure", r"\b(left|resign\w*|step\w*\s+down|depart\w*)\b[^.]{0,80}\b(health reasons|personal reasons|pursue other (interests|opportunities)|spend more time with (his|her|their) family)\b"),
    ("sales_leadership", r"\b(vice president|vp|head|chief)\s+(of\s+)?(sales|marketing|revenue)\b[^.]{0,60}\b(left|resign\w*|depart\w*|replaced|appointed|hired|named)\b"),
    ("sales_leadership", r"\b(hired|appointed|named)\b[^.]{0,40}\bnew\s+(vice president|vp|head|chief)\s+(of\s+)?(sales|marketing)\b"),
    ("guidance_cut", r"\b(lower\w*|reduc\w*|cut\w*|withdr\w*)\b[^.]{0,30}\b(guidance|outlook|forecast)\b"),
    ("attack_on_critics", r"\b(lawsuit|sue[sd]?|suing)\b[^.]{0,40}\bshort[- ]sellers?\b"),
    ("attack_on_critics", r"\b(took issue with|disput\w*|reject\w*)\b[^.]{0,60}\banalyst'?s?\b"),
    ("attack_on_critics", r"\banalyst\b[^.]{0,60}\b(bias\w*|inaccura\w*|misleading|speculative)\b"),
    ("coverage", r"\b(drop\w*|discontinu\w*|suspend\w*|terminat\w*)\b[^.]{0,20}\bcoverage\b"),
    ("accounting", r"\b(restat\w*|non-?reliance|material weakness|late filing|nt 10-?[kq]|notification of late)\b"),
    ("accounting", r"\b(change\w* in|dismiss\w*|resign\w*)\b[^.]{0,30}\b(auditor|accounting firm)\b"),
    ("accounting", r"\bforensic (accountant|accounting|audit)\b"),
    ("distress", r"\b(covenant (breach|violation|waiver)|waiver from (its )?lenders|going concern|forbearance)\b"),
    ("distress", r"\b(restructuring (adviser|advisor|firm)|bankruptcy counsel|chapter 11|creditor protection)\b"),
    ("regulatory", r"\b(subpoena|wells notice|formal investigation|informal inquiry)\b"),
]

IMPROVEMENT_PATTERNS = [
    ("debt_reduction", r"\bdebt (reduction|repayment)\b[^.]{0,40}\b(ahead of|exceed\w*|surpass\w*|faster than)\b"),
    ("debt_reduction", r"\b(repaid|prepaid|retired)\b[^.]{0,40}\b(debt|loan|notes|debentures)\b[^.]{0,30}\b(early|ahead of schedule)\b"),
    ("cash_build", r"\bcash\b[^.]{0,30}\b(grew|rose|increased)\b[^.]{0,30}\b(faster than|ahead of|more than expected)\b"),
    ("settlement", r"\bsettle[sd]?\b[^.]{0,40}\b(lawsuit|litigation|dispute|claims?)\b"),
    ("asset_sale", r"\b(sold|divest\w*|completed the sale of)\b[^.]{0,40}\b(plant|real estate|property|division|unit|business)\b"),
    ("cost_cuts", r"\b(cost (reduction|cuts?)|cash burn)\b[^.]{0,50}\b(ahead of|exceed\w*|reduc\w*|lower)\b"),
    ("new_leadership", r"\b(appoint\w*|named|hired)\b[^.]{0,30}\b(new\s+)?(chief executive|ceo|president)\b"),
    ("insider_buying", r"\b(director|officer|ceo|cfo|insider)s?\b[^.]{0,40}\b(bought|purchased|acquired)\b[^.]{0,30}\bshares\b"),
    ("control_change", r"\b(13d|activist|acquired a stake|controlling (stake|interest))\b"),
    ("buyback", r"\b(share|stock) (buyback|repurchase)\b"),
]


def compile_patterns(pairs):
    return [(cat, re.compile(rx, re.IGNORECASE)) for cat, rx in pairs]


def scan_text(name, text, warn, improve, width):
    hits = []
    seen = set()
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, patterns in (("warning", warn), ("improvement", improve)):
            for cat, rx in patterns:
                for m in rx.finditer(line):
                    if (lineno, kind, cat) in seen:
                        continue
                    seen.add((lineno, kind, cat))
                    start = max(m.start() - width, 0)
                    end = min(m.end() + width, len(line))
                    hits.append({"source": name, "line": lineno, "kind": kind, "category": cat,
                                 "match": m.group(0), "context": line[start:end].strip()})
    return hits


def cmd_text(args):
    warn = compile_patterns(WARNING_PATTERNS)
    improve = compile_patterns(IMPROVEMENT_PATTERNS)
    if args.extra_warning:
        warn += [("custom", re.compile(rx, re.IGNORECASE)) for rx in args.extra_warning]
    if args.extra_improvement:
        improve += [("custom", re.compile(rx, re.IGNORECASE)) for rx in args.extra_improvement]
    hits = []
    sources = args.files or ["-"]
    for path in sources:
        if path == "-":
            hits += scan_text("stdin", sys.stdin.read(), warn, improve, args.context)
        else:
            with open(path, encoding="utf-8", errors="replace") as fh:
                hits += scan_text(path, fh.read(), warn, improve, args.context)
    if args.json:
        print(json.dumps(hits, indent=2))
        return
    if not hits:
        print("No flagged phrases found.")
        return
    summary = defaultdict(int)
    for h in hits:
        summary[(h["source"], h["kind"])] += 1
    print("Summary (source, kind: hits)")
    for (src, kind), n in sorted(summary.items()):
        print(f"  {src}, {kind}: {n}")
    print()
    for h in hits:
        print(f"[{h['kind'].upper()}:{h['category']}] {h['source']}:{h['line']}: ...{h['context']}...")
    print("\nRead each hit in context; a phrase is a lead, not a conclusion.")


def num(row, key):
    v = (row.get(key) or "").strip().replace(",", "")
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def cmd_capacity(args):
    with open(args.csv, newline="") as fh:
        rows = list(csv.DictReader(fh))
    by_entity = defaultdict(list)
    for r in rows:
        ent = (r.get(args.entity_column) or "").strip()
        yr = num(r, args.year_column)
        if ent and yr is not None:
            by_entity[ent].append((yr, r))
    results = []
    for ent, items in by_entity.items():
        items.sort(key=lambda t: t[0])
        series = {k: [num(r, k) for _, r in items] for k in
                  ("capex", "depreciation", "net_ppe", "sales", "inventory", "gross_profit")}
        years = [y for y, _ in items]
        flags = {}
        notes = []

        cx, dp = series["capex"], series["depreciation"]
        if len(cx) >= 3 and all(v is not None for v in cx[-3:] + dp[-3:]):
            c3, d3 = sum(cx[-3:]), sum(dp[-3:])
            flags["capex_below_depreciation_3y"] = c3 < d3
            notes.append(f"capex/depr 3y {c3 / d3:.2f}" if d3 else "depr 0")
        ppe = series["net_ppe"]
        declines = 0
        for a, b in zip(ppe[:-1][::-1], ppe[1:][::-1]):
            if a is None or b is None or b >= a:
                break
            declines += 1
        if any(v is not None for v in ppe):
            flags["net_ppe_falling_2y_plus"] = declines >= 2
            notes.append(f"net PP&E down {declines} yr(s) in a row")

        s = series["sales"]
        if len(s) >= 3 and all(v not in (None, 0) for v in s[-3:]):
            g1 = s[-1] / s[-2] - 1
            g0 = s[-2] / s[-3] - 1
            flags["sales_growth_accelerating"] = g1 > g0 and g1 > 0
            notes.append(f"sales growth {g0:+.1%} -> {g1:+.1%}")
        inv = series["inventory"]
        if len(s) >= 2 and len(inv) >= 2 and all(v not in (None, 0) for v in (s[-1], s[-2], inv[-1], inv[-2])):
            r1, r0 = s[-1] / inv[-1], s[-2] / inv[-2]
            flags["sales_to_inventory_rising"] = r1 > r0
            notes.append(f"sales/inventory {r0:.2f} -> {r1:.2f}")
        gp = series["gross_profit"]
        if len(s) >= 2 and len(gp) >= 2 and all(v not in (None, 0) for v in (s[-1], s[-2])) \
                and gp[-1] is not None and gp[-2] is not None:
            m1, m0 = gp[-1] / s[-1], gp[-2] / s[-2]
            flags["gross_margin_rising"] = m1 > m0
            notes.append(f"gross margin {m0:.1%} -> {m1:.1%}")

        starve = sum(1 for k in ("capex_below_depreciation_3y", "net_ppe_falling_2y_plus") if flags.get(k))
        demand = sum(1 for k in ("sales_growth_accelerating", "sales_to_inventory_rising", "gross_margin_rising")
                     if flags.get(k))
        verdict = ("starved capacity + turning demand: research" if starve >= 1 and demand >= 2 else
                   "starved capacity, demand not yet turning: watch" if starve >= 1 else
                   "demand turning, capacity not starved" if demand >= 2 else "no signal")
        results.append({"entity": ent, "latest_year": years[-1], "starvation_flags": starve,
                        "demand_flags": demand, "verdict": verdict, "flags": flags, "notes": notes})
    results.sort(key=lambda r: (r["starvation_flags"] >= 1 and r["demand_flags"] >= 2,
                                r["starvation_flags"] + r["demand_flags"]), reverse=True)
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for r in results:
        print(f"{r['entity']} ({int(r['latest_year'])}): starvation {r['starvation_flags']}/2,"
              f" demand {r['demand_flags']}/3 -> {r['verdict']}")
        print("   " + "; ".join(r["notes"]))
    print("\nScreens point the way only: call the industry's customers, suppliers and staff before concluding.")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("text", help="flag warning and improvement phrases in text files (or stdin)")
    t.add_argument("files", nargs="*", help="text files; '-' or nothing for stdin")
    t.add_argument("--context", type=int, default=80, help="characters of context around each hit")
    t.add_argument("--extra-warning", action="append", help="additional warning regex (repeatable)")
    t.add_argument("--extra-improvement", action="append", help="additional improvement regex (repeatable)")
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_text)

    c = sub.add_parser("capacity", help="capacity starvation and demand flags from a CSV")
    c.add_argument("csv", help="columns: entity,year,capex,depreciation,net_ppe,sales,inventory,gross_profit")
    c.add_argument("--entity-column", default="entity")
    c.add_argument("--year-column", default="year")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_capacity)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
