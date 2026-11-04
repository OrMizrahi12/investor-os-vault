---
name: value-investing
description: Apply the classic value-investing framework, updated for modern markets, to real decisions. Use it to value a stock against defensive and enterprising investor criteria, screen for net-nets and bargains, test margin of safety, and check bond or preferred safety. It also covers stock/bond allocation and rebalancing, judging the market's level, IPOs, convertibles, funds and advisers, accounting red flags, dividends and management, and the investor's own behavior. Use it whenever the user asks if a stock, bond, fund or market is cheap or expensive, wants a value-investing analysis or screen, mentions value investing, intrinsic value, margin of safety, Mr. Market, net-net or net current asset value, earnings yield, P/E or P/B, defensive or enterprising investor, or Buffett-style investing, or is tempted by a hot stock, IPO, tip, crash sale or timing call, even if value investing is not named.
---

# Value Investing — the Classic Framework, Operational

This skill turns the classic value-investing framework into procedures, tests and checklists. It analyzes facts against stated standards; it does not forecast prices. Present findings as analysis against stated criteria and leave the decision with the user (each investor must make the decision and take responsibility for it). Do not present the output as personalized financial advice, and say so briefly when the user asks "should I buy?".

## Operating rules (apply to every task)

1. **Always ask "how much?"** Every conclusion relates the price paid to the value received. A wonderful company can be a poor investment at a high price, and a mediocre one can be sound at a low enough price. No stock is good or bad in itself, only cheap or dear.
2. **Use current, sourced data.** Never rely on memory for prices, financials, yields or index levels. Get them from filings (annual and quarterly reports, e.g. SEC EDGAR 10-K/10-Q), the company's investor-relations pages, or data the user supplies. Get market rates from official series (e.g. FRED: `AAA` Moody's Aaa corporate yield, `DGS10` 10-year Treasury, `CPIAUCSL` CPI). State the as-of date and source of every number. If data cannot be obtained, say which tests could not be run; do not guess.
3. **Classify the investor before advising.** Defensive (wants safety and freedom from effort) or enterprising (will give investing the time and skill of a business). Their rules differ. If unknown, default to defensive and say so.
4. **Label every operation: investment or speculation.** An investment, on thorough analysis, promises safety of principal and an adequate return; anything else is speculation. Margin purchases, hot issues, market-direction bets and price-momentum plays are speculation by definition. Speculation is allowed only knowingly and in a separate account (classic rule: the smaller the better; modern update: never more than 10% of total wealth).
5. **Insist on a margin of safety.** Quantify it (see the tests below). With no margin, say so plainly, even for a great company.
6. **Normalize earnings.** Use multi-year averages (3, 5, 7 or 10 years as each test specifies) and adjust reported figures for special charges, dilution and accounting choices before applying any multiplier (references/security-analysis.md).
7. **Diversify.** Defensive: 10-30 issues, or index funds. Bargain methods work only as diversified groups.
8. **Translate dated numbers.** The classic figures are early-1970s levels; the modern update's are 2003 levels. Inflation-adjust dollar floors with current CPI (1971 dollars ×≈7.8-8.0 in the mid-2020s). Read P/E cut-offs against current high-grade bond yields, as the classic method does. Say when you translate.
9. **No forecasts, behavior first.** Never predict short-term market moves. Help the user act on prices (pricing), not predictions (timing), and protect them from their own impulses.
10. **Keep attribution clean.** Distinguish the classic rule, the 2003 modern update, and your own extension or modern judgment.

## Route the request

| The user wants... | Do this | Read |
|---|---|---|
| An opinion on one stock ("is X cheap?", "analyze X the value way") | Workflow A | security-analysis.md, defensive-selection.md or enterprising-selection.md, red-flags.md |
| To screen many stocks, find net-nets or value bargains | Workflow B | enterprising-selection.md, defensive-selection.md |
| An asset-allocation plan, rebalancing, cash/bond choices, inflation hedges | Workflow C | portfolio-policy.md |
| To know whether the overall market is cheap or expensive | Workflow D | market-level.md |
| A bond, preferred, junk bond, convertible or warrant judged | Workflow E | security-analysis.md, convertibles-warrants.md, margin-of-safety.md |
| A mutual fund, ETF, closed-end fund, adviser or broker evaluated | Workflow F | funds-and-advisers.md |
| Help with fear, greed, a hot tip, an IPO, a crash, or market timing | Workflow G | market-fluctuations.md, core-principles.md |
| Dividend policy, buybacks, options, governance, shareholder action | Workflow A step 6 | management-and-dividends.md |
| A lesson from history or a case study | Pick the matching case | case-studies.md, superinvestors-and-speculation.md |
| The philosophy itself (definitions, risk, margin of safety) | Answer from the reference | core-principles.md, margin-of-safety.md |

All paths are relative to this skill's folder: `references/`, `scripts/`, `assets/`.

---

## Workflow A — Analyze one stock

1. **Frame it.** Which investor (defensive or enterprising)? Which business, industry, and type (industrial, utility, railroad/transport, retail, financial)? Is the user asking about investment or a short-term trade? If a trade, say it is speculation and continue only with the business analysis. Trading on market moves and on next year's earnings are crowded games already reflected in prices; short selling is out for individuals because the possible loss is unlimited.
2. **Gather data (10 years where possible):** price and shares (basic and diluted); EPS and dividends per share for 10 years (dividend record back 20 years); revenue; current assets and liabilities; total liabilities; long-term and short-term debt; preferred stock; equity; goodwill and intangibles; operating and financing cash flow; interest/fixed charges and pre-tax earnings (7-year average and poorest year); options, warrants and convertibles outstanding; current high-grade (AAA) bond yield; CPI ratio. Use `assets/company_input_template.json` as the checklist. Then reconcile the figures before testing: EPS × diluted shares ≈ net income, dividends per share × shares ≈ cash dividends paid, and current assets − current liabilities = working capital. If something does not tie out (e.g. a "diluted" EPS that equals net income ÷ basic shares), restate it and say so.
3. **Adjust the earnings** before testing. Count special charges and "nonrecurring" items against earnings, averaging them over the years they relate to. Use fully diluted shares, adding the market value of warrants and options. Strip pension-return and other non-operating gains. Check tax payments against reported profit, depreciation and inventory policy changes, and acquisition accounting. Note the adjustments explicitly.
4. **Run the numbers:** `python3 scripts/value_screen.py <company>.json [--cpi-multiplier X --aaa-yield Y]`. It applies the seven defensive criteria, the 2003 recalibration, the general defensive rules, the enterprising screen, net current asset value, the defensive price ceiling, the 8.5+2g formula with implied growth, earnings yield vs bond yield, the coverage-table test, debt/capital and cash-flow quality checks, each with its basis (classic rule or modern update). Treat the output as raw material, not the verdict.
5. **Judge value and margin of safety.**
   - Defensive: must pass the seven defensive criteria, be bought within the price ceiling, and be held as part of 10-30 issues. Allow at most one small near-miss, and only when a strength elsewhere offsets it. This limit is the skill's own, stricter than the classic practice: the classic application to the Dow 30 at end-1970 accepted Woolworth's 1.8 current ratio against ample room for more debt financing, and Swift with two shortfalls (a 3-year P/E of 18.1 and 25% growth) after its good showing in the poor year 1970. A modest current-ratio shortfall is the most forgivable miss when earnings are strong and steady, since long-term financing can repair it. Explain any waiver.
   - Enterprising: enterprising criteria applied flexibly (a big plus can offset a small minus). Or a bargain: appraised value at least 50% above price, i.e. price no more than two-thirds of value. Or a net-net: price below net current assets, bought as part of a group. Or a relatively unpopular large company at a low multiple of normal earnings and below its past average price and P/E.
   - Growth stories: value only on conservative growth (estimates that depart from the record must err on the low side). Growth above about 8% a year cannot be capitalized reliably. Show the growth rate the price implies, and judge whether it is plausible (the bigger the company, the slower it grows). Base rates are harsh: very few large companies sustain 15-20% earnings growth for a decade or more, and at P/Es much above 25-30 even great businesses usually make poor investments.
   - Value each company on its own earnings, assets and cash flow. Never call a stock cheap because a peer is even dearer.
   - If the company owns a listed stake, value the stake per share. A price below that (after net debt) means the market prices the rest of the business below zero: a possible bargain or a mispriced subsidiary (enterprising-selection.md).
   - Margin of safety: normalized earnings yield vs high-grade bond yield (the classic sound case: earnings yield well above the bond rate, building over 10 years an excess near half the price), plus balance-sheet cushion. See references/margin-of-safety.md.
6. **Quality, management and red flags.** Run the red-flags.md checklist. Review the five capitalization factors (long-term prospects, management, financial strength and capital structure, dividend record, current dividend rate), counting management only once. Check dividend policy and buybacks (management-and-dividends.md). Compare with one or two peers on the standard comparison grid (security-analysis.md, case-studies.md).
7. **Write the verdict** using the output template below. Give the price at which the stock would qualify (e.g. the defensive price ceiling, or two-thirds of appraised value) instead of a price forecast.

## Workflow B — Screen a list

1. Define the universe and the investor type. Get data in bulk from a screener or filings; record dates.
2. Apply the screen in order of cheapness, then quality:
   - Defensive: seven defensive criteria, keeping the 22.5 combined test.
   - Enterprising Stock Guide method: start with low P/E (classic: 9 or less when AA bonds yielded about 7.5%; scale to today's yields), then current ratio ≥1.5, debt ≤110% of net current assets, no deficit in 5 years, some current dividend, earnings above 5 years earlier, price <120% of net tangible assets. Optionally require an earnings-and-dividend quality rank of average or better (S&P B+).
   - Net-nets: price < (current assets − all liabilities − preferred) per share, ideally ≤ two-thirds of it; drop names with losses in the last 12 months if enough remain; hold a couple dozen or more.
   - Unpopular large companies: lowest multiples of normal earnings among the largest firms, also low against their own past average earnings and prices (screens out cyclicals at peak earnings).
3. Run `scripts/value_screen.py` on a JSON list of candidates. Rank the survivors and flag the red-flag hits. Expect few passes: at end-1970 only 5 of the 30 Dow stocks met all seven defensive criteria, two of them (Swift, Woolworth) only with small deficiencies waived, and only about 100 issues in the whole Stock Guide were estimated to qualify. Passing the screen ensures value for money, not market-beating results.
4. For a list of current holdings (with `position_value`), the script adds the defensive portfolio test: the portfolio's overall earnings/price ratio should be at least the high-grade (AA) bond yield (`--aa-yield`).
5. Present the survivors as a diversified group, not a single pick, with the data date and what each failed or nearly failed.

## Workflow C — Portfolio policy

1. Classify the investor; ask (or infer) their life circumstances, using the checklist in portfolio-policy.md §9.
2. Set stocks between 25% and 75% (default 50-50). Go above 50% only with true confidence and proven ability to sit through a drop of about a third. Allow 100% stocks only if every one of the modern tests for it is met. Consider putting up to about a third of the stock money in low-cost funds of foreign and emerging-market stocks, since the investor's job and home already bet on the home economy.
3. Choose the bond side: taxable vs tax-exempt by arithmetic (`python3 scripts/portfolio_math.py taxequiv ...`), short or intermediate maturities unless the user accepts price swings, high grade only, funds unless at least about $100k goes into individual bonds. Add inflation-indexed bonds for inflation insurance.
4. Set the rebalancing rule: 5-point band or a fixed six-month calendar (`portfolio_math.py rebalance`). Automate dollar-cost averaging into index funds for defensive savers.
5. List exclusions for this investor (foreign bonds, preferreds, junk, new issues, high-cost annuities, margin) and any speculative sleeve (classic rule: separate and as small as possible; modern update: at most 10% of total wealth).
6. Offer a written investment policy using `assets/investment_policy_template.md`, including the investment owner's contract.

## Workflow D — Market level

Follow references/market-level.md §2. Compute P/E on multi-year (ideally 10-year inflation-adjusted) earnings, earnings yield vs AAA and 10-year yields, and dividend yield vs bond yield. Check the five classic signs of a bull-market top and the new-issue boom. Estimate a 10-year expected-return range (`portfolio_math.py expected`). Conclude attractive, fair or unattractive for conservative purchase, translate that into a position within the 25-75% band, and add no timing forecast.

## Workflow E — Bonds, preferreds, convertibles, warrants

- Safety comes from earning power, not ratings or collateral alone. Apply the minimum coverage of fixed charges (7-year average or poorest year): utilities 4x/3x pre-tax, railroads 5x/4x, industrials 7x/5x, retailers 5x/4x. For preferreds use fixed charges plus twice the preferred dividends. Alternative when rates are high: pre-tax earnings at least 33% of debt principal (industrials), 20% (utilities) or 25% (railroads). Industrial bonds only from companies of major size that have come through a serious depression.
- Second-grade bonds and preferreds: never at full price for a little extra yield. Buy only at bargain levels (ordinarily at least 30% below par for high-coupon issues) with real recovery potential, diversified.
- Straight preferreds: an inherently weak form; bargain basis or not at all; investment-grade ones suit corporate buyers.
- Convertibles: compute conversion value, premium and payback (`portfolio_math.py convertible`). Buy only a strongly secured issue, convertible into a stock you would want anyway, near conversion parity. Be wary of new issues late in bull markets. Do not convert needlessly.
- Warrants and options: add their market value to the common's market capitalization before computing P/E.
- Details and evidence: security-analysis.md, convertibles-warrants.md, margin-of-safety.md.

## Workflow F — Funds and advisers

- Funds: default to low-cost, broadly diversified index funds for defensive investors. Judge active funds over at least five years that are not one big bull market, and look at costs first (expenses are certain; outperformance is not). Avoid hot "performance" funds and star managers proven only in bull markets. Prefer closed-end funds at a discount to NAV; never pay a premium for "superior management".
- Advisers and brokers: apply the second business principle. Delegate only to someone whose work you can supervise, or whose integrity and ability you have unusually strong reasons to trust. Verify credentials, fees and conflicts. Expect conservative, not dazzling, advice.
- Details and selection checklists: funds-and-advisers.md.

## Workflow G — Behavior and temptation

Recognize the pattern, name it kindly, and redirect to price and value:
- **Panic in a decline:** Mr. Market is offering a lower price, not new information. Ask whether the business value changed. If not, hold or, with spare cash and courage, buy more. If yes, re-analyze. The investor's advantage is never being forced to sell.
- **Euphoria or FOMO:** the higher the price, the riskier the stock. Never buy just because it went up. Check the price against value. Put any irresistible bet in the capped speculative account.
- **Hot IPO or new issue:** sold when conditions favor the seller, with extra commissions and salesmanship. Apply the private-owner test (would you buy the whole business at this valuation?). Most new issues later fall far below their offering price.
- **Timing calls and forecasts:** experts' forecasts are unreliable. Replace them with rebalancing, dollar-cost averaging and written rules. "I don't know and I don't care" is a complete answer for a defensive investor.
- **Index-inclusion runs, squeezes, "forced buyers":** buying because others will have to buy is a bet on other buyers, not on the business. Treat it as speculation.
- **Formulas and backtests:** popular formulas self-destruct. Ask for a causal business reason, a long sample, and net-of-cost results.
- Use the calibration and regret checklists in core-principles.md §10, and the investment owner's contract (assets/investment_policy_template.md §7; background in market-fluctuations.md §11).

---

## Quick reference: the core tests

**Defensive investor (all seven; size floors in 1971 dollars):**
1. Adequate size: annual sales ≥ $100M (industrial); total assets ≥ $50M (public utility).
2. Strong financial condition: industrials current assets ≥ 2× current liabilities, and long-term debt ≤ net current assets (working capital); utilities debt ≤ 2× common equity at book.
3. Earnings stability: positive earnings for the common in each of the past 10 years.
4. Dividend record: uninterrupted dividends for at least the past 20 years.
5. Earnings growth: at least +33% in per-share earnings over 10 years, using 3-year averages at each end.
6. Moderate P/E: price ≤ 15× average earnings of the past 3 years.
7. Moderate price-to-assets: price ≤ 1.5× book value; or P/E × P/B ≤ 22.5 (e.g. 9 × 2.5). Price ceiling = √(22.5 × 3-yr avg EPS × book value per share).
- Portfolio as a whole: earnings yield (on 3-year average EPS) ≥ the AA bond yield. With AA bonds at 7.5% that capped the portfolio P/E at 13.3.
- Utilities: skip the current-ratio test and require debt ≤ 2× equity. Financial companies: apply the same P/E and P/B standards, not the current ratio. Railroads: only when the value is overwhelming.
- **The 2003 recalibration (modern update):**
  - Size: market value of at least $2B in 2003 dollars (≈$3.5B today). Own small companies through a small-cap fund instead.
  - Growth: at least +50% over the decade (about 4% a year); +100% (about 7% a year) is the strict version.
  - P/E: compute it yourself on trailing 3-year average earnings. Never use a forward P/E.
  - Warning sign: institutional ownership above 60% suggests the stock is "overowned".
  - Homework: read five years of reports and the proxy statement first, or own an index fund.
  - Core and explore: an index fund as the core; picks limited to about 10% of the stock money.

**Defensive, general stock rules:** 10-30 issues; large and prominent companies (classic: at least about $50M of assets or sales at early-1970s prices, and in the top quarter or third of the industry by size; modern update: market value of at least $10B in 2003 dollars; apply with judgment); conservatively financed (common equity at book ≥ 50% of total capitalization for industrials, ≥ 30% for railroads and utilities); continuous dividends for about 20 years (modern minimum: 10); price ≤ 25× 7-year average EPS and ≤ 20× trailing EPS. Defensive buyers who want asset backing pay at most about 1.33× tangible book, and only with a satisfactory earnings yield, strong finances and earnings at least maintained.

**Enterprising screen:** low P/E start; current ratio ≥ 1.5; debt ≤ 110% of net current assets; no deficit in the last 5 years; some current dividend; latest earnings > 5 years earlier; price < 120% of net tangible assets.

**Bargain thresholds:** bargain = appraised value ≥ 1.5× price. Secondary common stocks only at two-thirds or less of appraised value. Second-grade bonds and preferreds only at a considerable discount, ordinarily at least 30% below par for high-coupon issues. Net-net = price below current assets minus all liabilities and preferred; the classic practice paid two-thirds or less of that.

**Valuation:** value ≈ current normal earnings × (8.5 + 2g), with g the expected annual growth over 7-10 years, in percent. Report it as a range: latest-year, 3-year and 7-year average EPS, the 7-year figure being the conservative end. Implied growth = (P/E − 8.5) / 2. Distrust g above about 8%.

**Margin of safety:** bonds, by coverage or enterprise value well above debt; stocks at normal prices, by an earnings yield well above the high-grade bond yield; bargains and growth stocks, by the gap between conservative value and price. Diversify so the odds work across many holdings.

**Allocation:** stocks 25-75% (default 50-50); rebalance at about ±5 points (sell 1/11 of stocks at 55/45) or every six months.

## Output template (single-stock analysis)

```
# <Company> (<ticker>) — value analysis, data as of <date>
Investor lens: defensive | enterprising   Operation type: investment | speculation (why)
Bottom line: <one or two sentences: qualifies / does not qualify, margin of safety yes/no, why>

## Business and normalized earnings
<what it does; earnings adjustments made; normal EPS used>

## Value tests
<table: test | result | figure | basis>  (from scripts/value_screen.py, after adjustments)

## Value and margin of safety
<8.5+2g value, implied growth vs plausible growth, earnings yield vs AAA yield, NCAV, price ceiling, peer comparison>

## Risks and red flags
<red-flags.md hits, management and dividend observations>

## What would change the verdict
<price at which it qualifies; data that would alter the conclusion>

Sources: <filings, data series, dates>.  This applies published value-investing criteria to the data above; it is not personalized financial advice.
```

Keep prose tight; put numbers in tables; label each rule as the classic rule, the modern update, or your own judgment.

## Reference files (load only what the task needs)

Each file opens with a Contents list. Read the sections the task needs rather than whole files.

- `references/core-principles.md`: definitions (investment vs speculation, risk), Mr. Market summary, margin of safety summary, the four business principles, the law of formulas, bias list, calibration and regret checklists.
- `references/portfolio-policy.md`: allocation, rebalancing, bonds and cash, preferreds and junk, inflation hedges, dollar-cost averaging, personal situations, taxes.
- `references/market-level.md`: tests of the market's level, signs of a bull-market top, expected-return arithmetic, history.
- `references/market-fluctuations.md`: Mr. Market in full, timing vs pricing, formula plans, bond price swings, behavioral finance, the investment owner's contract.
- `references/security-analysis.md`: bond analysis and coverage, stock valuation factors, the growth formula and its traps, per-share earnings adjustments, the four-company comparison.
- `references/defensive-selection.md`: defensive criteria in depth, with worked applications and modern translation.
- `references/enterprising-selection.md`: the don'ts, unpopular large companies, bargains, net-nets, secondary companies, special situations, the Stock Guide screen, modern value methods.
- `references/convertibles-warrants.md`: convertible math and rules, warrant dilution, structured products.
- `references/management-and-dividends.md`: dividend policy, splits and stock dividends, buybacks, options, governance, shareholder action.
- `references/margin-of-safety.md`: every margin-of-safety test, diversification logic, cost of loss.
- `references/funds-and-advisers.md`: fund types and selection, closed-end discounts, advisers, brokers, planners.
- `references/red-flags.md`: cross-cutting checklist of accounting, financing, management and market warning signs.
- `references/case-studies.md`: Penn Central, LTV, NVF, AAA Enterprises, the eight pairs, Lucent, Tyco, AOL, eToys and more, grouped by lesson.
- `references/superinvestors-and-speculation.md`: Buffett's superinvestors argument, old vs new speculation, and further cases.

Scripts: `scripts/value_screen.py` (company tests; `--help`) and `scripts/portfolio_math.py` (rebalance, expected, breakeven, convertible, taxequiv, realreturn, premium, dca; `--help`). Both are standard-library Python 3. Templates are in `assets/`.
