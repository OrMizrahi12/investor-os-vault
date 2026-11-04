#!/usr/bin/env python3
"""Portfolio and security arithmetic for classic value investing.

Standard library only. Each subcommand prints a short, labeled result.

  rebalance   the 25-75% band / 50-50 rule and calendar rebalancing
  expected    Expected stock return: dividend yield + growth (+/- valuation change)
  breakeven   Gain needed to recover a loss, and years to recover at a given return
  convertible Conversion value, premium, payback period, stock price needed
  taxequiv    Taxable-equivalent yield of a tax-exempt bond
  realreturn  Return after inflation (and optionally tax)
  premium     Closed-end fund: discount/premium to NAV
  dca         Dollar-cost averaging vs lump sum on a supplied price path

Examples:
  python3 portfolio_math.py rebalance --stocks 62000 --bonds 38000 --target 0.5
  python3 portfolio_math.py expected --dividend-yield 0.015 --real-growth 0.02 --inflation 0.025
  python3 portfolio_math.py breakeven --loss 0.95 --return 0.10
  python3 portfolio_math.py convertible --bond-price 881.30 --ratio 24.24 --stock 5.66 --coupon 47.50 --stock-dividend 0
  python3 portfolio_math.py taxequiv --muni-yield 0.035 --tax-rate 0.32
  python3 portfolio_math.py dca --monthly 100 --prices 100 90 80 70 80 90 100
"""

import argparse
import math


def pct(x):
    return f"{x * 100:.2f}%"


def cmd_rebalance(a):
    total = a.stocks + a.bonds
    if total <= 0:
        raise SystemExit("total must be positive")
    target = a.target
    if not 0.25 <= target <= 0.75:
        print(f"WARNING: target stock share {pct(target)} is outside the classic 25%-75% band.")
    cur = a.stocks / total
    drift = cur - target
    print(f"Current: stocks {pct(cur)}, bonds {pct(1 - cur)} of {total:,.2f}")
    print(f"Target:  stocks {pct(target)}; drift {drift * 100:+.2f} percentage points")
    trade = target * total - a.stocks
    if abs(drift) < a.band:
        print(f"Within the +/-{a.band * 100:.0f}-point band: no trade needed (the classic rule rebalances at ~5 points, e.g. 55/45 -> sell 1/11 of stocks).")
    else:
        side = "BUY stocks / SELL bonds" if trade > 0 else "SELL stocks / BUY bonds"
        print(f"Rebalance: {side} for {abs(trade):,.2f}")
    print("Alternative: rebalance on a fixed calendar (every 6 months), asking only 'Do I own more of this asset than my plan calls for?'")


def cmd_expected(a):
    base = a.dividend_yield + a.real_growth + a.inflation
    print(f"Dividend yield {pct(a.dividend_yield)} + real growth {pct(a.real_growth)} + inflation {pct(a.inflation)} = {pct(base)} nominal ({pct(base - a.inflation)} real)")
    if a.start_pe and a.end_pe and a.years:
        val = (a.end_pe / a.start_pe) ** (1 / a.years) - 1
        print(f"Valuation change P/E {a.start_pe:g} -> {a.end_pe:g} over {a.years:g} yrs adds {val * 100:+.2f}% a year -> {pct((1 + base) * (1 + val) - 1)} nominal")
    print("Basis: classic (dividend + reinvestment growth); modern (real growth + inflation + yield +/- speculative change). Present as a range.")


def cmd_breakeven(a):
    loss = a.loss
    if not 0 < loss < 1:
        raise SystemExit("--loss must be between 0 and 1 (0.5 = 50% loss)")
    need = 1 / (1 - loss) - 1
    print(f"A {pct(loss)} loss needs a {pct(need)} gain to break even.")
    if a.ret and a.ret > 0:
        yrs = math.log(1 / (1 - loss)) / math.log(1 + a.ret)
        print(f"At {pct(a.ret)} a year that takes {yrs:.1f} years.")
    if a.benchmark and a.ret:
        # Example: lose X in year one then earn ret; how long to catch a benchmark?
        v, b, y = 1 - loss, 1.0, 0
        while v < b * (1 + a.benchmark) and y < 200:
            v *= 1 + a.ret
            b *= 1 + a.benchmark
            y += 1
        print(f"Catching a portfolio compounding at {pct(a.benchmark)} from the same start takes about {y + 1} years in total.")


def cmd_convertible(a):
    conv_value = a.ratio * a.stock
    premium = a.bond_price / conv_value - 1 if conv_value else float("inf")
    print(f"Conversion value = {a.ratio:g} shares x {a.stock:g} = {conv_value:,.2f}")
    print(f"Conversion premium = {pct(premium)} over conversion value (bond at {a.bond_price:,.2f})")
    income_adv = a.coupon - a.ratio * (a.stock_dividend or 0)
    if income_adv > 0:
        payback = (a.bond_price - conv_value) / income_adv
        print(f"Income advantage {income_adv:,.2f} a year -> payback of the premium ~{payback:.1f} years")
    else:
        print("No income advantage over the shares: the premium is never earned back by income.")
    print(f"Stock price at which conversion value equals today's bond price: {a.bond_price / a.ratio:,.2f} "
          f"({a.bond_price / a.ratio / a.stock - 1:+.0%} from {a.stock:g})")
    if a.par:
        print(f"Stock price at which conversion value equals par ({a.par:g}): {a.par / a.ratio:,.2f}")
    print("Rule: buy only a strongly secured issue convertible into a stock you'd want anyway, at a conversion price near the market; 'never convert' needlessly.")


def cmd_taxequiv(a):
    te = a.muni_yield / (1 - a.tax_rate)
    print(f"Taxable-equivalent yield = {pct(a.muni_yield)} / (1 - {pct(a.tax_rate)}) = {pct(te)}")
    if a.taxable_yield:
        better = "tax-exempt" if te > a.taxable_yield else "taxable"
        print(f"Compared with a {pct(a.taxable_yield)} taxable bond, the {better} bond pays more after tax (also check state tax and AMT).")


def cmd_realreturn(a):
    after_tax = a.nominal * (1 - (a.tax_rate or 0))
    real = (1 + after_tax) / (1 + a.inflation) - 1
    print(f"Nominal {pct(a.nominal)}; after tax {pct(after_tax)}; after inflation {pct(real)} (judge results by what you keep).")


def cmd_premium(a):
    p = a.price / a.nav - 1
    word = "premium" if p > 0 else "discount"
    print(f"Price {a.price:g} vs NAV {a.nav:g}: {pct(abs(p))} {word}.")
    print("Rule: prefer closed-end funds at a 10-15% discount to open-end funds at a premium; never pay a premium to NAV for 'superior management'.")


def cmd_dca(a):
    prices = a.prices
    shares = sum(a.monthly / p for p in prices)
    invested = a.monthly * len(prices)
    avg_cost = invested / shares
    avg_price = sum(prices) / len(prices)
    final = shares * prices[-1]
    lump_shares = invested / prices[0]
    print(f"Invested {invested:,.2f} over {len(prices)} periods; average cost {avg_cost:,.4f} vs average price {avg_price:,.4f}")
    print(f"Final value {final:,.2f} ({pct(final / invested - 1)}) vs lump sum at the first price {lump_shares * prices[-1]:,.2f}")
    print("DCA buys more shares when prices are low; its real value is behavioral: no forecasting, no freezing after a crash.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("rebalance")
    r.add_argument("--stocks", type=float, required=True)
    r.add_argument("--bonds", type=float, required=True, help="bonds + cash equivalents")
    r.add_argument("--target", type=float, default=0.5, help="target stock share (default 0.5)")
    r.add_argument("--band", type=float, default=0.05, help="tolerance in percentage points as decimal (default 0.05)")
    r.set_defaults(f=cmd_rebalance)

    e = sub.add_parser("expected")
    e.add_argument("--dividend-yield", type=float, required=True)
    e.add_argument("--real-growth", type=float, default=0.02)
    e.add_argument("--inflation", type=float, required=True)
    e.add_argument("--start-pe", type=float)
    e.add_argument("--end-pe", type=float)
    e.add_argument("--years", type=float)
    e.set_defaults(f=cmd_expected)

    b = sub.add_parser("breakeven")
    b.add_argument("--loss", type=float, required=True, help="fractional loss, e.g. 0.5")
    b.add_argument("--return", dest="ret", type=float, help="annual return afterwards")
    b.add_argument("--benchmark", type=float, help="annual return of a portfolio that avoided the loss")
    b.set_defaults(f=cmd_breakeven)

    c = sub.add_parser("convertible")
    c.add_argument("--bond-price", type=float, required=True, help="price of one bond in currency (e.g. 881.30)")
    c.add_argument("--ratio", type=float, required=True, help="shares received per bond")
    c.add_argument("--stock", type=float, required=True, help="stock price")
    c.add_argument("--coupon", type=float, required=True, help="annual interest per bond in currency")
    c.add_argument("--stock-dividend", type=float, default=0.0, help="annual dividend per share")
    c.add_argument("--par", type=float, default=1000.0)
    c.set_defaults(f=cmd_convertible)

    t = sub.add_parser("taxequiv")
    t.add_argument("--muni-yield", type=float, required=True)
    t.add_argument("--tax-rate", type=float, required=True)
    t.add_argument("--taxable-yield", type=float)
    t.set_defaults(f=cmd_taxequiv)

    rr = sub.add_parser("realreturn")
    rr.add_argument("--nominal", type=float, required=True)
    rr.add_argument("--inflation", type=float, required=True)
    rr.add_argument("--tax-rate", type=float)
    rr.set_defaults(f=cmd_realreturn)

    p = sub.add_parser("premium")
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--nav", type=float, required=True)
    p.set_defaults(f=cmd_premium)

    d = sub.add_parser("dca")
    d.add_argument("--monthly", type=float, required=True)
    d.add_argument("--prices", type=float, nargs="+", required=True)
    d.set_defaults(f=cmd_dca)

    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
