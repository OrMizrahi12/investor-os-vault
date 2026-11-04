# Defensive Selection: The Seven Criteria, the Portfolio Test, Sectors, Building a Portfolio Today

Use this file when a defensive (passive) investor wants to choose common stocks or check that the ones they own meet the classic defensive standards. It covers applying, waiving or interpreting the seven defensive criteria, testing a whole portfolio against the bond yield, handling utilities, financials and railroads, and building a defensive stock portfolio today, by the index route or the individual-stock route. The criteria in brief are in SKILL.md's Quick reference. Allocation between stocks and bonds is in portfolio-policy.md, how to read a company's numbers in security-analysis.md, the enterprising alternative in enterprising-selection.md, and margin-of-safety arithmetic in margin-of-safety.md.

## Contents
1. The defensive investor's job: two routes, and protection over prediction
2. The seven criteria in depth
3. The portfolio test: earnings yield vs the AA bond yield
4. Near-misses and waivers (the classic practice)
5. The classic application: the Dow 30 at end-1970
6. Sector rules: utilities, financial companies, railroads
7. When to change a defensive portfolio
8. The 2003 recalibration
9. Procedure: building a defensive portfolio today
10. Worked example: the portfolio test on a holdings list
11. Feeding and reading value_screen.py
12. Cases, grouped by lesson
13. Translating to today
14. The general defensive stock rules

---

## 1. The defensive investor's job: two routes, and protection over prediction

The classic prescription: high-grade bonds plus a diversified list of leading common stocks, bought at prices not unduly high by applicable standards. There are two ways to build the stock list:

| Route | Classic rule | Modern update (2003) |
|---|---|---|
| A. Cross-section of leading issues | Buy the same number of shares of all 30 Dow stocks (10 each cost about $16,000 with the Dow at 900; the actual average Dow share price was about $53 in early 1972), or buy several representative investment funds. | Buy a low-cost total-market index fund. Any attempt to improve on it takes more work, risk and cost than a truly defensive investor can justify. |
| B. Quantitatively tested list | Apply minimum standards of quality (past performance, current financial position) and quantity (earnings and assets per dollar of price) to each purchase: the seven criteria. | The seven criteria still work as an initial screen, after recalibration (§8). Limit picks to about 10% of stock money, with an index fund as the core. |

**Protection, not prediction.** There are two approaches to the future:
- Prediction (projection) is qualitative: prospects, management and other intangibles. It recommends stocks with unusually good long-term prospects almost regardless of price. Air-transport stocks were recommended for years after 1946 despite bad results.
- Protection is quantitative: insist on a margin of present, demonstrable value over price, large enough to absorb unfavorable developments. It extends the logic of bond and preferred selection to common stocks.
- The classic approach is committed to protection. Never accept future prospects as compensation for insufficient value in hand.
- Modern update: we invest in the present for an almost entirely uncertain future, and even expert forecasts do worse than a coin flip. The defense is to refuse to overpay and to resist overconfidence.

**Do not hunt for the "best" stocks.** Ask 100 analysts for the five best Dow stocks and you would get few identical lists and many entirely different ones. Current prices already reflect the record and the general opinion, so any preference expresses personal emphasis. If everyone agreed on one stock, its price would rise until its advantage disappeared. So the defensive investor should emphasize diversification over selection; diversification itself contradicts claims of selectivity.
- Don't spend effort choosing between broad representative lists either. Their relative results can differ a lot and can't be predicted: from December 1960 to December 1970 the DJIA rose 36% while the S&P 500 rose 58%, and nobody could have called that in 1960.
- Modern efficient-market summary: prices incorporate public information. The market is not perfectly efficient, but it is close most of the time. Pick up the occasional $20 bill only after thorough research, and keep trading costs and taxes low.
- Within the general defensive rules (10-30 issues; large, prominent, conservatively financed companies; long dividend records; reasonable price; §14) personal preference is harmless and may help. Seek a middle way between neglecting technology changes and overemphasizing them.

## 2. The seven criteria in depth

All seven are required. Run them on the latest annual figures. The classic floors are in 1971-72 dollars; translate them (§13).

**Criterion 1: Adequate size.**
- Rule: at least $100 million of annual sales for an industrial company; at least $50 million of total assets for a public utility.
- Why: it excludes small companies, which face more than average ups and downs, especially in industry. Small companies are not rejected as investments; they simply don't suit the defensive investor.
- Today: × CPI ratio. The script's default multiplier is 7.9, giving about $790 million of sales or $395 million of utility assets. The 2003 alternative is a market value of at least $2 billion in 2003 dollars, about $3.5 billion today (§8).

**Criterion 2: Sufficiently strong financial condition.**
- Industrials: current assets at least twice current liabilities (current ratio ≥ 2), and long-term debt no greater than net current assets (working capital).
- Public utilities: debt no more than twice the stock equity at book value. The current-ratio test does not apply, because utilities manage working capital by continually issuing bonds and stock.
- Why: in 1970-72 this was the most severe test. Many large, once-strong companies had weakened their current ratios or over-expanded their debt. In 1960 only 2 of the 29 Dow industrials failed the 2:1 ratio and only 2 failed the debt test; by December 1970, 12 failed each.
- Interpretation: "stock equity" is ambiguous (with or without preferred). The rule does not say whether short-term debt counts. The script judges common equity (equity minus preferred) against long-term debt, and reports the broader reading (total debt against total equity including preferred) in the same row. When a utility is close to the limit, report both.
- The rule excludes most heavily bonded gas pipelines, whose "guarantees" of bond payments through purchase contracts are too complicated for a defensive investor.

**Criterion 3: Earnings stability.**
- Rule: some earnings for the common stock in each of the past ten years.
- Why: it removes companies carrying a deficit stigma. Modern update (2003): 86% of S&P 500 companies had positive earnings every year from 1993 to 2002, so the test removes chronic losers without being too restrictive.
- Use earnings after special charges. A year rescued only by excluding a "nonrecurring" loss is a deficit year (security-analysis.md §6-7).

**Criterion 4: Dividend record.**
- Rule: uninterrupted payments for at least the past 20 years.
- Why: a long continuous dividend is among the most persuasive tests of quality. In 1970 every Dow company had paid some dividend since at least 1940, and five records went back to the 1800s.
- Interpretation: "uninterrupted" means some payment every year. A cut is not an interruption; an omitted year is. Do not substitute buybacks for dividends without saying so: that is a departure from the classic test, not a translation of it.
- Modern update (2003): 354 S&P 500 companies (71%) paid dividends; 255 had paid at least 20 years in a row; 57 had raised dividends for at least 25 consecutive years.

**Criterion 5: Earnings growth.**
- Rule: per-share earnings up at least one-third over the past ten years, using three-year averages at the beginning and the end.
- The exact window: compare the latest three-year average with the three-year average ten years earlier. The classic Dow test compared 1968-70 with 1958-60; the 2003 recalibration compared 2000-02 with 1991-93. That needs about 13 years of EPS history.
- Why include growth at all: without it the typical company would show declining profit per dollar of invested capital. A non-grower could still be a bargain, but only for the enterprising investor (enterprising-selection.md).
- Modern update: +33% over ten years is under 3% a year, a very low hurdle. Use at least +50% (about 4% a year); +100% (about 7% a year) is the strict version.
- Adjust EPS for splits and stock dividends, and use diluted figures throughout.

**Criterion 6: Moderate price/earnings ratio.**
- Rule: current price no more than 15 times average earnings of the past three years.
- Why: criteria 6 and 7 work in the opposite direction from 1-4. They demand more earnings and assets per dollar of price than popular issues offer. When too much of the price depends on ever-rising future earnings, there is no adequate safety factor. Most analysts disagree; they would pay generous prices for choice companies. The reader must choose.
- Modern update: compute it yourself. Never use a forward P/E (price ÷ next year's estimated earnings): David Dreman found that 59% of consensus forecasts missed actual earnings by at least 15% in one direction or the other.
- A 15× maximum on each stock tends to produce a portfolio average of about 12-13×.

**Criterion 7: Moderate ratio of price to assets.**
- Rule: price no more than 1.5 times last reported book value. A P/E below 15 can justify a correspondingly higher asset multiple: as a rule of thumb, P/E × P/B should not exceed 22.5 (= 15 × 1.5). For example, 9 times earnings permits 2.5 times book.
- Price ceiling (algebra from the 22.5 rule): maximum price = √(22.5 × 3-year average EPS × book value per share). It is the highest price meeting the test, not an estimate of value.
- The combined form uses the P/E from criterion 6 (on 3-year average earnings).
- Interpretation: the classic rule treats book value, net asset value and tangible-asset value as synonyms. In that era intangibles were small, so the distinction rarely mattered. Today it does. Compute P/B on both total and tangible book and say which you relied on. When intangibles are large, the tangible figure is the conservative one, and a pass on total book alone should be flagged.

**What the seven do and don't promise.** The five Dow stocks that qualified at end-1970 performed worse as a group than the Dow from December 1970 to early 1972. No system guarantees superior market results. The criteria guarantee only that the buyer gets his money's worth.

## 3. The portfolio test: earnings yield vs the AA bond yield

Rule: the stock portfolio as a whole should have an earnings/price ratio at least as high as the current high-grade (AA) bond yield.
- 1972: AA bonds at 7.5% meant a maximum portfolio P/E of 100 ÷ 7.5 = 13.3. Examples then: AT&T at 11 times its three-year (and current) earnings, and Standard Oil of California under 10 times latest earnings.
- Modern update (early 2003): 10-year AA corporate yield about 4.6%, so the maximum was 100 ÷ 4.6 = 21.7. The classic rule wanted the average about 20% below the maximum, which suggests stocks at no more than about 17 times three-year average earnings were potentially attractive. At December 31, 2002, more than 200 S&P 500 stocks (over 40%) had three-year average P/Es of 17 or less.
- Compute the portfolio figure as a value-weighted average of earnings yields (E/P), not of P/Es. Averaging P/Es overstates the portfolio's earnings when one holding has a very high multiple. Use 3-year average EPS for each holding.
- Read the result two ways: it passes or fails, and it shows how much cushion exists. A pass with the portfolio P/E within about 20% of the maximum is a thin margin.
- Why: the margin of safety for ordinary stocks is the excess of the earnings yield over the bond yield. The cumulative excess over about ten years is the cushion against disappointment (margin-of-safety.md §4).

## 4. Near-misses and waivers (the classic practice)

The classic application admitted two Dow stocks with small deficiencies at end-1970:
- Swift: P/E of 18.1 on three-year average earnings (over 15) and growth of 25% (below one-third), waived in view of its good showing in the poor year 1970.
- Woolworth: current ratio 1.8 (below 2.0), offset by a large margin for additional debt (net current assets 190% of debt).

So the classic practice itself admitted Swift with two shortfalls. The one-near-miss limit below is this skill's own stricter rule, not the classic one. Say so whenever you apply it.

Rules for waivers (this skill's rules, consistent with SKILL.md Workflow A):
- [ ] Allow at most one small near-miss per stock, and only when a measurable strength elsewhere offsets it. State both in the verdict.
- [ ] Never waive criterion 3 (a deficit year) or the price tests by more than a small amount. They are the protection.
- [ ] Never waive more than one criterion to admit a stock you already wanted.
- [ ] A near-miss in a recession year (as with Swift) is easier to justify than one in a boom.
- [ ] A modest current-ratio shortfall is more forgivable when earnings are strong and steady, because a profitable company can always repair its current position with long-term financing (the Air Products case, 1969). Weigh it against the debt and coverage tests rather than waiving it on its own.

## 5. The classic application: the Dow 30 at end-1970

The Dow as a whole passed all seven in aggregate, two just barely:
1. Size: ample for every company.
2. Financial condition: adequate in aggregate, but not for every company.
3. Earnings stability: aggregate earnings stable; no company had a deficit in the prosperous years 1961-69 (Chrysler had a small 1970 deficit).
4. Dividends: every company had paid some dividend since at least 1940.
5. Growth: three-year averages a decade apart rose 77%, about 6% a year, but five companies did not grow by one-third.
6. P/E: 839 ÷ $55.5 = 15, exactly at the limit.
7. Price/net asset value: 839 ÷ 562 = 1.49, just within 1.5.

Only five of the 30 qualified individually, and two of those (Swift, Woolworth) only with small deficiencies waived (§4). An estimated 100 or so issues in the S&P Stock Guide would pass at end-1970.

Issues meeting the criteria at end-1970:

| | American Can | AT&T | Anaconda | Swift | Woolworth | Average of 5 |
|---|---|---|---|---|---|---|
| Price | 39 3/4 | 48 7/8 | 21 | 30 1/8 | 36 1/2 | |
| P/E 1970 | 11.0 | 12.3 | 6.7 | 13.5 | 14.4 | 11.6 |
| P/E on 3-yr avg | 10.5 | 12.5 | 5.4 | 18.1 | 15.1 | 12.3 |
| Price/book | 99% | 108% | 38% | 113% | 148% | about 101% |
| Current ratio | 2.2 | n.a. | 2.9 | 2.3 | 1.8 | 2.3 |
| Net current assets/debt | 110% | n.a. (debt below equity) | 120% | 141% | 190% | 140% |
| Stability index | 85 | 100 | 72 | 77 | 99 | 86 |
| EPS growth (10 yrs) | 55% | 53% | 78% | 25% | 73% | 57% |

Stability index: 100 minus the largest drop in per-share earnings in any of the past ten years, measured against the average of the three preceding years.

Representative passes and failures from the Sept 1971 data (P/E on 1968-70 average EPS, growth 1968-70 vs 1958-60, P/B on net asset value):

| Company | Price | P/E (3-yr) | P/B | Growth | Verdict |
|---|---|---|---|---|---|
| AT&T | 43 | 11.0 | 0.95 | +55% | Passes price and growth tests |
| Anaconda | 15 | 3.9 | 0.28 | +80% | Very cheap, but stopped its dividend (current dividend: none) |
| Eastman Kodak | 87 | 35.6 | 6.35 | +239% | Fails 6 and 7: a great record priced for more |
| General Electric | 61 1/4 | 34.4 | 4.1 | +30% | Fails 5, 6 and 7 |
| U.S. Steel | 29 1/2 | 7.7 | 0.45 | −21.5% | Cheap, but fails growth |
| Chrysler | 28 1/2 | 10.5 | 0.67 | deficit 1958-60 | Fails stability and growth |


## 6. Sector rules: utilities, financial companies, railroads

**Public utilities.**
- Tests: skip the current ratio; require debt ≤ 2× stock equity; apply the price tests as usual.
- 1972 verdict: a defensive investor had a wide choice of utilities meeting every performance and price requirement. They had nearly as good past growth as the Dow industrials, smaller annual fluctuations, lower prices relative to earnings and assets, and significantly higher dividend yields.
- Regulation was more an advantage than a handicap: it entitles the company to rates that attract needed capital, offsetting inflated costs. It was cumbersome, but for decades it allowed a fair return on rising invested capital.
- The central appeal was a moderate price relative to book value. That lets the owner ignore the market, regard himself as part owner of well-established, well-earning businesses, and use quotations only when they offer an opportunity.

Public-utility stocks (Sept 30, 1971), summarized:

| | P/E | P/B | Dividend yield | EPS growth 1960-70 |
|---|---|---|---|---|
| 15 Dow Jones utilities, average | 10.7 | 121% | 6.2% | +65% (range +19% to +135%) |
| Second list of 15 NYSE utilities, average | 11 | 112% | 6.5% | +71% |
| Consolidated Edison (example) | 10 | 80% | 7.4% | |
| American Electric Power (example) | 11 | 138% | 6.5% | |
| Houston Lighting & Power (outlier) | 15 | 222% | 3.1% | |
| AT&T (in the second list) | 11 | 95% | 6.0% | |

Houston L&P shows the screen working: 15 × 2.22 = 33, well above 22.5, so it fails despite its quality.

Relative valuations swing (S&P averages, year-end P/E):

| Year | Industrials | Railroads | Utilities |
|---|---|---|---|
| 1948 | 6.56 | 4.55 | 10.03 |
| 1958 | 19.88 | 12.45 | 18.59 |
| 1963 | 18.18 | 12.78 | 20.44 |
| 1970 | 17.84 | 12.83 | 13.16 |

Industrials and utilities changed places twice in two decades, so a defensive investor's sector mix should follow the price tests, not habit. Utilities were individually more price-stable.

Modern update (2003): utilities became far more volatile (cancelled or decommissioned nuclear plants, bungled deregulation in California). Most investors should hold them through low-cost utility index funds, which were by then widely available. The S&P utility index still beat the NASDAQ Composite over the 30 years to December 2002.

**Financial companies.**
- These are banks, insurers, savings and loans, credit and small-loan companies, mortgage companies and investment companies.
- Their distinguishing trait: few physical assets, and short-term obligations far above stock capital. That makes financial soundness more important, and is why they are regulated.
- Tests: apply the same arithmetic standards of price relative to earnings and to book value. The current ratio does not apply; judge capital adequacy separately. The script reports criterion 2 as INFO for type `financial`.
- Evidence (S&P indexes, 1941-43 = 10):

| Index | 1948 | 1963 | 1970 |
|---|---|---|---|
| Life insurance | 17.1 | 318.1 | 218.0 |
| New York City banks | 11.2 | 36.8 | 44.3 |
| Small-loan companies | 18.4 | 118.2 | 126.8 |
| S&P composite | 13.2 | 75.0 | 92.2 |

  - Financials as a group produced results similar to other common stocks, with large swings between subgroups. Life insurers lost ground from 1963 to 1968 after a huge run; New York banks did well from 1958 to 1968.
- Modern update: the financial-services sector is far broader today, and the soundness caveats apply more than ever.
- [ ] For banks and other lenders, compare growth in the loan-loss reserve with loan growth and with the stage of the credit cycle. Flag reserves barely raised while loans grow late in an expansion, because defaults jump in recessions (the Capital One case, 2000).

**Railroads.**
- There is no compelling reason to own them. Buy only when the value is so large that looking elsewhere would be unreasonable.
- Why: severe competition plus strict regulation. More than half of U.S. rail mileage was in bankruptcy or trusteeship at some time in the preceding 50 years.
- The S&P rail index rose sevenfold from its 1942 low to its 1968 high, not much less than utilities, a rise that was largely unwarranted. Penn Central sold near its highest prices one and two years before its 1970 bankruptcy, after paying continuous dividends for more than 120 years (case-studies.md).
- Modern update: the advice applies at least as well to airlines.

## 7. When to change a defensive portfolio

- [ ] Review each holding periodically against the seven criteria and the price ceiling (the hard-look rule in market-fluctuations.md §1).
- [ ] Review changes at least once a year. If you take advice, take it only from advisers of the highest reputation, and insist they follow the general defensive rules (§14). A competently chosen list needs few and infrequent changes.
- [ ] Sell when a holding has had an apparently excessive advance and can be replaced by a much more reasonably priced qualifying issue. Better to sell and pay the capital-gains tax than to keep it and regret it. Check holding periods and tax placement first (portfolio-policy.md §10).
- [ ] Re-run the portfolio test (§3) after significant price moves or new purchases.
- [ ] Sector reversals are a legitimate reason for occasional changes.
- [ ] Do not sell merely because the price fell. Re-examine the business; if it still qualifies, the lower price is a better offer (market-fluctuations.md §2).
- [ ] A holding that no longer meets criterion 2 or 3 deserves a hard look even if it is cheap. Deterioration in large, formerly strong companies was the main 1970-72 finding.

## 8. The 2003 recalibration

Modern default: a total-market index fund. If you enjoy picking stocks, and have survived a bear market doing it, use **core and explore**: keep about 90% of stock money in an index fund (build it first) and use about 10% for your own picks.

Criterion by criterion, with the early-2003 S&P 500 counts (snapshots, not current figures):

| Classic criterion | 2003 view | S&P 500 companies passing (early 2003) |
|---|---|---|
| 1. Size | Market value ≥ $2 billion; own smaller companies through a low-cost small-cap fund | 437 |
| 2. Financial condition | Unchanged; a basket meeting the 2:1 ratio and debt ≤ working capital yields conservatively financed companies with staying power. The best values are often once-hot stocks gone cold. | about 120 met 2:1 |
| 3. Stability | Unchanged; removes chronic losers without over-restricting | 86% had no deficit 1993-2002 |
| 4. Dividends | Unchanged | 354 paid; 255 for ≥ 20 years; 57 raised ≥ 25 years |
| 5. Growth | +33% is under 3% a year; require ≥ +50% (about 4%), or +100% (about 7%) for the strict version | 264 at +33%; 245 at +50%; 198 at +100% |
| 6. P/E | Compute price ÷ 3-year average EPS yourself; never a forward P/E | 185 at ≤ 15× 2000-02 average |
| 7. P/B | Higher multiples today because valuable intangibles (brands, patents, franchises) are not on the balance sheet at their worth | 123 below 1.5×; 273 (55%) below 2.5× |
| 7. Combined | P/E × P/B ≤ 22.5 still works as an initial screen | at least 142 |

Two checks the modern update adds:
- [ ] **Do your homework.** Read at least five years of annual and quarterly reports and the latest proxy statement (pay, ownership, conflicts of interest) from the regulator's filing database. If you won't read the proxy and compare five years of financial health, you are too defensive to buy individual stocks; use an index fund.
- [ ] **Check the neighborhood.** Institutional ownership above 60% suggests the stock is overowned: institutions tend to sell together, and the stock can collapse when they do. Look at the largest holders. Fund managers whose style resembles yours are a good sign. Avoid the big institutions' most crowded favorites, or own them far more patiently than the institutions do.

Why diversify, even for a stock picker:
- A handful of stocks become superstocks (up 10,000% or more), and they are unpredictable in advance. A 2002 magazine study of the 30 best stocks of the previous 30 years included Southwest Airlines, Worthington Steel, Dollar General and UST Inc.
- Your "next Microsoft" may turn out to be the next MicroStrategy: up 566.7% in 1999, then from $3,130 a share (split-adjusted) in March 2000 to $15.10 at end-2002 (−99.5%), amid SEC accounting-fraud charges that its chairman settled by paying $8.3 million.
- So own the whole haystack (an index fund) to be sure of owning the needles.

The 2002 balance-sheet list: 1999's darlings became financially conservative by early 2003. In December 2002 figures, Linear Technology had a current ratio of 11.7 and no long-term debt; Qualcomm 6.7 and debt only 0.04× working capital; Amgen 4.2 and 0.62×. LSI Logic (1.05×) and Rowan Cos. (1.40×) still failed the debt-to-working-capital test despite current ratios above 4. This is not a buy list, but proof that patient searching through bear-market wreckage turns up financially strong companies.

The 2002 dividend-raiser list: in 2002, 57 S&P companies had raised dividends every year for decades. Examples: Coca-Cola (paying since 1893), Procter & Gamble (since 1891), 3M (since 1916) and Johnson & Johnson (since 1944), each with 40 increases in the past 40 years. Such a record is no guarantee of future increases, but it is a comforting sign. (The "past 40 years" column shows fewer than 40 increases for companies with shorter histories.)

## 9. Procedure: building a defensive portfolio today

**Step 0, for both routes:**
- [ ] Set the stock/bond split (25-75% band, 50-50 default) and the rebalancing rule (portfolio-policy.md §2-3).
- [ ] Write the policy and the owner's contract (assets/investment_policy_template.md).
- [ ] Decide honestly: will you read five years of reports and a proxy statement for every stock? If not, take Route 1 only.

**Route 1: index (the default for nearly every defensive investor).**
1. Choose one very low-cost, broadly diversified total-market fund (or a total-market fund plus a total-international fund). Run the fund checklist in funds-and-advisers.md: costs first, then turnover, then risk; ignore past rankings.
2. Optionally add a low-cost small-cap index fund, since the modern size floor removes small companies from individual picking, and a utility index fund if you want the classic utility exposure (§6).
3. Automate: a fixed amount every month (dollar-cost averaging), plus spare cash when it appears (portfolio-policy.md §8).
4. Check the market level once a year with the market's P/E on average earnings against the AA bond yield, the same test as §3 applied to the index (market-level.md). If the market is far above value standards, lean toward the bond end of the band; never go to 0% stocks.
5. Rebalance on the band or calendar rule. Sell only for rebalancing or when you need the money.

**Route 2: individual stocks (an enterprising level of effort applied with defensive standards).**
1. **Universe.** Start from large companies: sales of at least $100 million × CPI ratio (about $790 million) and preferably a market value of at least $2 billion in 2003 dollars (about $3.5 billion). Exclude railroads and airlines unless the value is overwhelming. Treat utilities and financials with their sector rules (§6). Also apply the general rules' "large and prominent" tests (§14): the top quarter or third of the industry by size (classic rule), and a market value of at least $10 billion in 2003 dollars for a large company. Use them with judgment, not as rigid cut-offs.
2. **Data.** For each candidate, fill in `assets/company_input_template.json`: 13 years of diluted, split-adjusted EPS if available (at least 10); 20+ years of dividend history or `years_of_uninterrupted_dividends`; the latest balance sheet; `institutional_ownership`. Enter amounts in units, not millions, so the size test works.
3. **Screen.** Run `python3 scripts/value_screen.py candidates.json --format json` on the list. Keep stocks passing all seven defensive tests. Note which also pass the 2003 recalibration: +50% growth, the market-value floor, institutional ownership ≤ 60%.
4. **Check by hand** what the script approximates (§11): the growth window when fewer than 13 years of EPS are supplied, and earnings after special charges.
5. **Homework on survivors.** Read five years of annual and quarterly reports and the proxy statement. Run the 10-K checklist and accounting-trick checks (security-analysis.md §7-8) and red-flags.md. Reject anything you cannot explain.
6. **Waivers.** At most one small, offset near-miss per stock (§4). Write the reason down.
7. **Diversify.** 10-30 stocks across several industries, in roughly equal dollar amounts so no single loser dominates. Under core and explore, the picks are only about 10% of stock money, and the index core supplies the breadth.
8. **Buy within the ceiling.** Pay no more than √(22.5 × 3-year average EPS × book value per share). Buy whenever you have money, unless the market as a whole is far above value standards (market-fluctuations.md §1). No price forecast is needed.
9. **Portfolio test.** Run the script on your holdings list with `position_value` for each and `--aa-yield <current AA yield>`. The weighted earnings yield must be at least the AA yield. Prefer the portfolio P/E to be about 20% below 1 ÷ AA yield (§3, §10).
10. **Maintain.** Once or twice a year, at rebalancing, re-run the screen and the portfolio test. Replace excessively advanced holdings with much cheaper qualifiers, and hard-look any holding failing criterion 2 or 3 (§7).

## 10. Worked example: the portfolio test on a holdings list

Inputs: four holdings (hypothetical), AA yield 5.7%.

| Holding | Position value | Price | 3-yr avg EPS | Earnings yield (EPS ÷ price) |
|---|---|---|---|---|
| A (the template company) | $25,000 | $42 | $3.133 | 7.46% |
| B | $20,000 | $60 | $3.00 | 5.00% |
| C | $30,000 | $25 | $2.10 | 8.40% |
| D | $25,000 | $80 | $3.20 | 4.00% |

Computation:
- Weighted earnings yield = (25,000 × 7.46% + 20,000 × 5.00% + 30,000 × 8.40% + 25,000 × 4.00%) ÷ 100,000 = (1,865 + 1,000 + 2,520 + 1,000) ÷ 100,000 = 6.39%.
- Portfolio P/E equivalent = 1 ÷ 0.0639 = 15.7.
- Maximum portfolio P/E = 1 ÷ 0.057 = 17.5. The classic comfort level, about 20% below that, is ≈ 14.0.
- Contrast: a simple average of the four P/Es (13.4, 20.0, 11.9, 25.0) is 17.6, which would wrongly suggest a fail. Weight the yields, not the multiples.

Conclusion: the portfolio passes (6.39% ≥ 5.7%), but the cushion is thin: its P/E of 15.7 is above the ~14 comfort level. Holding D (P/E 25) is the drag, and it individually fails criterion 6. With only four holdings, the portfolio is also below the 10-30 range, which the script flags. Action: replace D with a qualifying issue when convenient, and add holdings toward 10+.

## 11. Feeding and reading value_screen.py

Inputs that drive the defensive tests: `type`, `revenue` (industrials) or `total_assets` (utilities), `current_assets`, `current_liabilities`, `long_term_debt`, `shareholders_equity`, `preferred_stock`, `intangibles`, `eps_history`, `dividends_per_share_history` or `years_of_uninterrupted_dividends`, `price`, `shares_outstanding`, `diluted_shares`, `institutional_ownership`. For the portfolio test add `position_value` to each holding and pass a JSON list; set `--aa-yield` (otherwise the AAA yield or a holding's `aa_bond_yield` is used). Use `--cpi-multiplier` to change the size translation.

How to read its output:
- **"Defensive investor: seven criteria" section:** the seven criteria. "insufficient data" means a field is missing; supply it rather than assuming a pass.
- **"Defensive investor: 2003 recalibration" section:**
  - Market value against $2 billion × CPI multiplier × (40.5 ÷ 184.0), about $3.5 billion at the default 7.9.
  - Growth against +50%, with the strict +100% shown.
  - The institutional-ownership flag above 60%.
  - Notes on the P/E basis (no forward P/E) and on the homework requirement.
- **"Defensive price ceiling"** row (valuation section): the criterion-7 ceiling as a percentage above or below the price.
- **Valuation rows on several earnings bases:** the 8.5 + 2g value, the implied growth rate and the earnings yield against the bond yield are each reported on latest-year, 3-year average and 7-year average EPS (plus a supplied `eps_normal`), as a range. The earnings yield is compared with `aa_bond_yield` when supplied, otherwise AAA. For the defensive verdict the price tests (criteria 6-7, the ceiling and the portfolio test) always use the 3-year average.
- **"Portfolio test"** (list input only): the weighted earnings yield on 3-year average EPS against the AA yield, the maximum portfolio P/E, the weighting basis, and a flag when there are fewer than 10 holdings.

Where the script approximates the classic tests (check these by hand when a result is close):
- Criterion 5 (and the modern growth check) compares three-year averages ten years apart when 13 or more years of EPS are supplied. With 10-12 years it falls back to the first and last three years supplied and says so in the row: a shorter, stricter span, so a pass is safe and a narrow fail should be recomputed with 13 years.
- Criterion 7 is judged on total book value per basic share, and the same row also shows P/B and P/E × P/B on tangible book (per diluted share). It flags a stock that passes on total book only. Report both when intangibles are large.
- The utility debt test is judged on long-term debt against common equity, and the row also reports the broader reading (total debt against equity including preferred). See criterion 2's interpretation note.
- Criterion 3 counts only the EPS figures supplied. Supply earnings after special charges.

## 12. Cases, grouped by lesson

**Meeting the criteria buys value, not outperformance:** the five Dow passers of end-1970 lagged the Dow into early 1972 (§2, §5).

**Strong companies can weaken; re-test financial condition:** the Dow industrials failing the 2:1 ratio went from 2 in 1960 to 12 in 1970 (§2). Woolworth was already slightly below 2.0 in 1970 (§4).

**Great records priced for perfection fail the price tests:** Eastman Kodak at 35.6 times average earnings and 6.35 times book in 1971, General Electric at 34.4 times (§5). Houston Lighting & Power among utilities (§6). For the growth-stock arithmetic see security-analysis.md §4.

**Cheapness without the record is not defensive:** U.S. Steel at 0.45 times book with shrinking earnings; Anaconda at 28% of book after stopping its dividend (§5). These belong, if anywhere, in enterprising-selection.md.

**Long dividend records do not prevent disaster in a weak industry:** Penn Central, 120+ years of dividends, bankrupt in 1970 (§6).

**Sector leadership rotates:** industrial vs utility P/Es in 1948-70; life insurers after 1963 (§6).

**Diversify because winners are unpredictable and losers can be total:** the superstocks list and MicroStrategy (§8).

**Bear markets restore financial strength to former darlings:** the 2002 balance-sheet list (§8).

## 13. Translating to today

- **Size.** Multiply the classic floors by the CPI ratio, about 7.9 by default (CPI-U 1971 average 40.5): roughly $790 million of sales and $395 million of utility assets. The modern $2 billion market value (2003 dollars) is about $3.5 billion today. State which floor you used.
- **Financial condition.** The 2:1 current ratio and debt ≤ working capital remain sound for manufacturers. Many modern service, software and retail businesses run on low working capital by design. Report the failure honestly, then decide whether the debt test (debt/capital < 50%, the coverage table) shows comparable strength. Never silently drop the test.
- **Stability and dividends.** Unchanged. Count share buybacks separately from dividends, and say so if you lean on them.
- **Growth.** Prefer the modern +50% floor; +33% is too easy in an economy with ordinary inflation.
- **P/E.** Always trailing 3-year average EPS, after special charges, on diluted shares.
- **P/B.** Use the 22.5 combined test as the operative criterion, and show P/B on both total and tangible book. For asset-light firms, few will pass on tangible book. Treat that as information about price, not as a reason to relax the rule quietly.
- **Portfolio test.** Use the current AA (or nearest high-grade) corporate yield. The rule is timeless; the 13.3 (1972) and 21.7 (2003) caps are snapshots.
- **Outside the U.S.** Use the local CPI for size floors, the local high-grade corporate yield for the portfolio test, and local filings for the homework. Accounting differences (intangibles, leases, provisions) matter most for criteria 2 and 7.
- **Index route.** The 2003 fund examples are dated. Apply funds-and-advisers.md to whatever very low-cost total-market funds exist now.
- **Not advice.** The procedure describes the classic method. Apply it to the user's stated situation and say what remains their own decision.

## 14. The general defensive stock rules

Four rules apply to every common stock a defensive investor holds (classic rule). The seven criteria (§2) are the stricter, fully quantitative version; these are the minimum. The screening script reports them under "Defensive investor: general stock rules".
- [ ] **Diversify adequately but not excessively:** at least 10 and at most about 30 issues.
- [ ] **Large, prominent and conservatively financed companies.**
  - Large: at least $50 million of assets or of annual sales at early-1970s prices (× CPI ratio, about $395 million at the default 7.9). Modern update: a market value of at least $10 billion in 2003 dollars (about $17 billion today). This "large" test is separate from the $2 billion floor of the 2003 recalibration of criterion 1 (§8).
  - Prominent: in the top quarter or top third of its industry by size.
  - Apply both with common sense, not rigidly. Any reading consistent with the plain meaning of "large" and "prominent" is acceptable.
  - Conservatively financed: common stock at book value at least 50% of total capitalization, including all bank debt, for an industrial company; at least 30% for a railroad or public utility.
- [ ] **A long record of continuous dividends:** classic rule, payments every year for about 20 years. Modern update: at least 10 years as the minimum, though 20 is not overly restrictive (255 S&P 500 companies had paid for 20 years in a row at end-2002). Criterion 4 (§2) keeps the 20-year test.
- [ ] **A price limit:** no more than 25 times average earnings of the past 7 years, and no more than 20 times the latest 12 months' earnings. Effect: it rules out nearly all of the strongest, most popular companies and virtually all growth stocks, whose prices carry a heavy speculative element. That is intended; for the growth-stock arithmetic see security-analysis.md §4.
