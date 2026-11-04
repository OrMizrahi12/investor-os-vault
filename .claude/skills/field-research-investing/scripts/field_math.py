#!/usr/bin/env python3
"""Field-research calculators.

Subcommands:
  unitcount  Estimate period revenue from counted shipments and reconcile it with reported revenue.
  runway     Net cash per share, price versus net cash, and quarters of cash runway.
  capacity   Volume thresholds at which extra resources (shifts, people, vendors) must appear.
  costshare  How much an input price change raises a user's total cost (demand sensitivity).

Standard-library Python 3 only. Run any subcommand with --help.
"""
import argparse
import csv
import json
import math
import statistics
import sys

# Two-sided t critical values for 90% and 95% confidence, by degrees of freedom.
T_TABLE = {
    0.90: {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860,
           9: 1.833, 10: 1.812, 12: 1.782, 15: 1.753, 20: 1.725, 25: 1.708, 30: 1.697,
           40: 1.684, 60: 1.671, 120: 1.658},
    0.95: {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
           9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042,
           40: 2.021, 60: 2.000, 120: 1.980},
}
Z_VALUES = {0.90: 1.645, 0.95: 1.960}


def t_critical(df, confidence):
    table = T_TABLE[confidence]
    if df <= 0:
        return float("nan")
    if df in table:
        return table[df]
    keys = sorted(table)
    if df > keys[-1]:
        return Z_VALUES[confidence]
    # Use the next lower tabulated df (slightly conservative).
    lower = max(k for k in keys if k < df)
    return table[lower]


def money(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e9:
        return f"{sign}{x / 1e9:,.2f}B"
    if x >= 1e6:
        return f"{sign}{x / 1e6:,.2f}M"
    return f"{sign}{x:,.0f}"


def read_counts(args):
    counts = []
    if args.counts:
        counts.extend(float(c) for c in args.counts.split(",") if c.strip())
    if args.counts_file:
        with open(args.counts_file, newline="") as fh:
            reader = csv.DictReader(fh)
            col = args.count_column
            if col not in (reader.fieldnames or []):
                sys.exit(f"Column '{col}' not found in {args.counts_file}; columns: {reader.fieldnames}")
            for row in reader:
                value = (row.get(col) or "").strip()
                if value:
                    counts.append(float(value))
    if not counts:
        sys.exit("No counts given: use --counts 31,28,35 or --counts-file log.csv")
    return counts


def cmd_unitcount(args):
    counts = read_counts(args)
    n = len(counts)
    mean = statistics.mean(counts)
    sd = statistics.stdev(counts) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 1 else float("nan")
    tcrit = t_critical(n - 1, args.confidence) if n > 1 else float("nan")
    lo_day = max(mean - tcrit * se, 0.0) if n > 1 else mean
    hi_day = mean + tcrit * se if n > 1 else mean

    per_load_rev_assumed = args.units_per_load * args.load_factor * args.price
    per_load_rev_full = args.units_per_load * args.price

    est_loads = mean * args.period_days
    est = est_loads * per_load_rev_assumed + args.other_revenue
    est_lo = lo_day * args.period_days * per_load_rev_assumed + args.other_revenue
    est_hi = hi_day * args.period_days * per_load_rev_assumed + args.other_revenue
    upper_bound = hi_day * args.period_days * per_load_rev_full + args.other_revenue

    result = {
        "observed_days": n,
        "loads_per_day_mean": round(mean, 3),
        "loads_per_day_sd": round(sd, 3),
        "confidence": args.confidence,
        "loads_per_day_range": [round(lo_day, 3), round(hi_day, 3)],
        "period_days": args.period_days,
        "units_per_load_max": args.units_per_load,
        "load_factor_assumed": args.load_factor,
        "price_per_unit": args.price,
        "other_revenue": args.other_revenue,
        "estimated_period_revenue": round(est, 2),
        "estimated_range": [round(est_lo, 2), round(est_hi, 2)],
        "upper_bound_full_loads": round(upper_bound, 2),
    }
    if args.reported is not None:
        gap = args.reported - est
        result["reported_revenue"] = args.reported
        result["gap_reported_minus_estimate"] = round(gap, 2)
        result["gap_pct_of_reported"] = round(100 * gap / args.reported, 1) if args.reported else None
        result["reported_exceeds_upper_bound"] = args.reported > upper_bound
        result["implied_loads_per_day_for_reported"] = round(
            (args.reported - args.other_revenue) / (per_load_rev_assumed * args.period_days), 2)
        result["implied_loads_per_day_for_reported_at_full_load"] = round(
            (args.reported - args.other_revenue) / (per_load_rev_full * args.period_days), 2)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    pct = int(args.confidence * 100)
    print("Unit-count revenue reconciliation")
    print(f"  Observed days: {n}   loads/day mean {mean:.2f} (sd {sd:.2f}); {pct}% range {lo_day:.2f}-{hi_day:.2f}")
    print(f"  Conversion: {args.units_per_load:g} units/full load x load factor {args.load_factor:g} x price {args.price:g}"
          f" = {money(per_load_rev_assumed)} per load (full load {money(per_load_rev_full)})")
    print(f"  Period: {args.period_days:g} operating days; other revenue added: {money(args.other_revenue)}")
    print(f"  Estimated period revenue: {money(est)}  ({pct}% range {money(est_lo)} - {money(est_hi)})")
    print(f"  Upper bound (full loads, high end of range): {money(upper_bound)}")
    if args.reported is not None:
        print(f"  Reported revenue: {money(args.reported)}")
        print(f"  Gap (reported - estimate): {money(result['gap_reported_minus_estimate'])}"
              f" = {result['gap_pct_of_reported']}% of reported")
        print(f"  Loads/day needed to produce reported revenue: {result['implied_loads_per_day_for_reported']}"
              f" at assumed load factor; {result['implied_loads_per_day_for_reported_at_full_load']} at full load")
        if result["reported_exceeds_upper_bound"]:
            print("  FLAG: reported revenue exceeds the full-load upper bound for the observed volume.")
            print("        Before concluding, rule out other sites, other channels, non-shipment revenue,")
            print("        timing of recognition, and unobserved shipping hours.")
        elif result["gap_pct_of_reported"] is not None and abs(result["gap_pct_of_reported"]) > 15:
            print("  NOTE: gap above 15%; widen the sample and test assumptions before drawing conclusions.")
        else:
            print("  Reported revenue is within the plausible range of the observed volume.")
    print("  Assumptions drive the answer: state them and test sensitivity (load factor, price, days).")


def cmd_runway(args):
    net_cash = args.cash - args.debt - args.other_liabilities
    ncps = net_cash / args.shares
    mcap = args.price * args.shares
    ev = mcap - net_cash
    gross_runway = args.cash / args.quarterly_burn if args.quarterly_burn > 0 else float("inf")
    net_runway = net_cash / args.quarterly_burn if args.quarterly_burn > 0 else float("inf")
    out = {
        "net_cash": net_cash,
        "net_cash_per_share": round(ncps, 4),
        "price": args.price,
        "price_to_net_cash_per_share": round(args.price / ncps, 3) if ncps > 0 else None,
        "market_cap": mcap,
        "enterprise_value": ev,
        "quarters_runway_on_cash": round(gross_runway, 2),
        "quarters_runway_on_net_cash": round(net_runway, 2),
    }
    if args.burn_cut is not None:
        new_burn = args.quarterly_burn * (1 - args.burn_cut)
        out["burn_after_cut"] = new_burn
        out["quarters_runway_on_net_cash_after_cut"] = (round(net_cash / new_burn, 2) if new_burn > 0 else "no burn")
    horizon = args.horizon_quarters
    burn_for_horizon = out.get("burn_after_cut", args.quarterly_burn)
    ncps_h = (net_cash - burn_for_horizon * horizon) / args.shares
    out["horizon_quarters"] = horizon
    out["net_cash_per_share_after_horizon"] = round(ncps_h, 4)
    out["reference_prices_at_multiples_of_current_net_cash"] = {
        "1.0x": round(ncps, 4), "1.5x": round(1.5 * ncps, 4), "2.0x": round(2.0 * ncps, 4)}

    if args.json:
        print(json.dumps(out, indent=2, default=str))
        return
    print("Net cash and runway")
    print(f"  Net cash: {money(net_cash)}  = {ncps:,.4f} per share   price {args.price:g}")
    if ncps > 0:
        print(f"  Price / net cash per share: {args.price / ncps:.2f}x   enterprise value {money(ev)}"
              f" ({'market values the business below zero' if ev < 0 else 'positive'})")
    else:
        print("  Net cash is negative: this is not a below-net-cash situation.")
    print(f"  Runway at current burn: {gross_runway:.1f} quarters on gross cash; {net_runway:.1f} on net cash")
    if args.burn_cut is not None:
        nb = out["burn_after_cut"]
        if nb > 0:
            print(f"  After a {args.burn_cut:.0%} burn cut: burn {money(nb)}/quarter;"
                  f" {out['quarters_runway_on_net_cash_after_cut']} quarters on net cash")
        else:
            print("  After the burn cut the company no longer burns cash.")
    print(f"  Net cash per share after {horizon} quarters at {'cut' if args.burn_cut is not None else 'current'} burn:"
          f" {ncps_h:,.4f}")
    print(f"  Reference prices at 1.0x / 1.5x / 2.0x current net cash per share:"
          f" {ncps:,.3f} / {1.5 * ncps:,.3f} / {2 * ncps:,.3f}")
    print("  Verify the burn cut and management integrity first, then the customers.")


def cmd_capacity(args):
    steps = [float(s) for s in args.steps.split(",") if s.strip()]
    labels = [s.strip() for s in args.labels.split(",")] if args.labels else []
    rows = []
    for i, threshold in enumerate(steps):
        label = labels[i] if i < len(labels) else f"step {i + 1}"
        rows.append({
            "resource": label,
            "triggered_above_volume": threshold,
            "pct_above_current": round(100 * (threshold / args.current - 1), 1),
            "pct_above_guidance": round(100 * (threshold / args.guidance - 1), 1) if args.guidance else None,
            "guidance_reaches_it": bool(args.guidance and args.guidance >= threshold),
        })
    if args.json:
        print(json.dumps({"current": args.current, "guidance": args.guidance, "steps": rows}, indent=2))
        return
    print(f"Capacity triggers (current {args.current:g}, guidance {args.guidance:g} per {args.unit})")
    for r in rows:
        tag = "within guidance" if r["guidance_reaches_it"] else "BEYOND guidance"
        print(f"  {r['resource']}: appears above {r['triggered_above_volume']:g}"
              f" ({r['pct_above_current']:+.1f}% vs current, {r['pct_above_guidance']:+.1f}% vs guidance) -> {tag}")
    print("  If a resource marked BEYOND guidance is observed in use (from public places or voluntary conversation),")
    print("  volume has likely exceeded guidance. Confirm with a second independent signal before acting.")


def cmd_costshare(args):
    total_change = args.share * args.price_change
    out = {"input_cost_share": args.share, "input_price_change": args.price_change,
           "total_cost_change": round(total_change, 4)}
    if args.margin is not None:
        cost_ratio = 1 - args.margin
        margin_hit = args.share * cost_ratio * args.price_change
        out["operating_margin_before"] = args.margin
        out["operating_margin_after_no_passthrough"] = round(args.margin - margin_hit, 4)
    if args.json:
        print(json.dumps(out, indent=2))
        return
    print(f"An input that is {args.share:.1%} of operating cost rising {args.price_change:+.0%}"
          f" raises total operating cost by {total_change:+.1%}.")
    if args.margin is not None:
        print(f"  Operating margin {args.margin:.1%} -> {out['operating_margin_after_no_passthrough']:.1%}"
              " if none of it is passed on.")
    if total_change < 0.15:
        print("  Small effect: demand for the input is likely insensitive to price (room for prices to rise).")
    else:
        print("  Material effect: users have reason to economize or substitute; demand is more price-sensitive.")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    u = sub.add_parser("unitcount", help="revenue from counted shipments vs reported revenue")
    u.add_argument("--counts", help="comma-separated loads counted per observed day, e.g. 31,28,35")
    u.add_argument("--counts-file", help="CSV log with one row per observed day")
    u.add_argument("--count-column", default="outbound_loaded", help="column in the CSV holding the daily count")
    u.add_argument("--units-per-load", type=float, required=True, help="maximum units on a full load")
    u.add_argument("--load-factor", type=float, default=1.0, help="assumed average fill (0-1); default 1.0")
    u.add_argument("--price", type=float, required=True, help="net price per unit")
    u.add_argument("--period-days", type=float, required=True, help="operating days in the reporting period")
    u.add_argument("--reported", type=float, help="reported revenue for the period")
    u.add_argument("--other-revenue", type=float, default=0.0, help="known revenue not carried by these loads")
    u.add_argument("--confidence", type=float, choices=[0.90, 0.95], default=0.90)
    u.add_argument("--json", action="store_true")
    u.set_defaults(func=cmd_unitcount)

    r = sub.add_parser("runway", help="net cash per share and cash runway")
    r.add_argument("--cash", type=float, required=True, help="cash and short-term investments")
    r.add_argument("--debt", type=float, default=0.0)
    r.add_argument("--other-liabilities", type=float, default=0.0, help="all other liabilities to deduct")
    r.add_argument("--shares", type=float, required=True)
    r.add_argument("--price", type=float, required=True)
    r.add_argument("--quarterly-burn", type=float, required=True, help="cash consumed per quarter (positive)")
    r.add_argument("--burn-cut", type=float, help="fractional reduction in burn to test, e.g. 0.5")
    r.add_argument("--horizon-quarters", type=int, default=4)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_runway)

    c = sub.add_parser("capacity", help="volume thresholds that trigger extra resources")
    c.add_argument("--current", type=float, required=True)
    c.add_argument("--guidance", type=float, required=True)
    c.add_argument("--steps", required=True, help="comma-separated volume thresholds, e.g. 1000,1500")
    c.add_argument("--labels", help="comma-separated resource names for each step")
    c.add_argument("--unit", default="day")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_capacity)

    s = sub.add_parser("costshare", help="effect of an input price change on users' total cost")
    s.add_argument("--share", type=float, required=True, help="input cost as a fraction of operating cost")
    s.add_argument("--price-change", type=float, required=True, help="fractional price change, e.g. 1.0 for +100%%")
    s.add_argument("--margin", type=float, help="user's operating margin as a fraction of revenue")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_costshare)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
