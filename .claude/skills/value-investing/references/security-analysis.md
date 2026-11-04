# Analyzing Securities: Bond Safety, Stock Valuation, Earnings Adjustments, Company Comparison

Use this file when analyzing a specific bond, preferred or common stock: testing senior-security safety, valuing a stock (capitalization factors, the 8.5 + 2g formula, implied growth, two-part appraisal), normalizing per-share earnings, reading a 10-K for red flags, or comparing companies side by side. Selection criteria live in defensive-selection.md and enterprising-selection.md; margin-of-safety tests in margin-of-safety.md; the cross-cutting red-flag list in red-flags.md.

## Contents
1. The analyst's job and the two basic questions
2. Bond and preferred analysis (the coverage table and other tests)
3. Common-stock valuation: method and the five capitalization factors
4. Growth stocks: the 8.5 + 2g formula, implied growth, the 8% problem
5. The two-part appraisal process
6. Per-share earnings: adjustments before any multiplier
7. Accounting tricks to detect
8. The 10-K research checklist
9. Comparing companies side by side (the four-company method)
10. Valuation worked example (full computation)
11. Cases, grouped by lesson
12. Translating to today

---

## 1. The analyst's job and the two basic questions

Tasks:
- [ ] Describe the business. Summarize operating results and financial position.
- [ ] Set out strengths and weaknesses, possibilities and risks.
- [ ] Estimate future earning power under various assumptions, or as a "best guess".
- [ ] Compare the company with others, and with itself over time.
- [ ] Conclude: safety (bonds, investment-grade preferreds) or attractiveness at the price (common stocks).
- [ ] Adjust the reported figures, even audited ones, wherever items mean more or less than they say (§6).

The two basic questions: what are the primary tests of safety for a bond or preferred, and what are the chief factors in valuing a common stock? Reading financial statements is a separate skill; a short primer on interpreting them is worth working through first.

Paradox to keep in mind: mathematical valuation is most used where it is least reliable. The more a value depends on projections that differ from past performance, the more vulnerable it is to serious error. A related warning from 44 years of practice: dependable stock-value calculations never went beyond simple arithmetic or elementary algebra. When calculus or higher algebra appears, suspect that theory is replacing experience and speculation is posing as investment.

## 2. Bond and preferred analysis

Bond safety is the most dependable branch of analysis. Safety rests on earning power, not on collateral or ratings.

**Rule 1: Coverage of fixed charges (the coverage table, calibrated in 1961).** Require that earnings covered total fixed charges by at least these multiples, either on the 7-year average or, alternatively, in the poorest year. Passing either test suffices.

| Type of enterprise | Before taxes: 7-yr average | Before taxes: poorest year | After taxes: 7-yr average | After taxes: poorest year |
|---|---|---|---|---|
| Public-utility operating company | 4× | 3× | 2.65× | 2.10× |
| Railroad | 5× | 4× | 3.20× | 2.65× |
| Industrial | 7× | 5× | 4.30× | 3.20× |
| Retail concern | 5× | 4× | 3.20× | 2.65× |

- **Investment-grade preferreds:** apply the same minimums to pre-tax earnings ÷ (fixed charges + 2 × preferred dividends). The doubling allows for preferred dividends not being tax-deductible, whereas interest is.
- **Not applicable** to utility holding companies, financial companies or real-estate companies (the classic rules give no standards for them).
- **A second railroad figure.** The Penn Central discussion uses a railroad minimum of 5× pre-tax or 2.9× after tax at regular tax rates. The pre-tax bar matches the table; the after-tax bar is slightly lower than the table's 3.20×. Use the table, and rely on the pre-tax test whenever the company pays little tax.

**Rule 2: High-interest-rate alternative.** Seven-times coverage is far harder at 8% interest than at 4.5%, so the classic rules offer a test on debt principal: pre-tax earnings at least **33% of the principal amount of debt for industrials, 20% for utilities, 25% for railroads**. The poorest-year requirement is about two-thirds of the 7-year requirement. Companies' actual average borrowing cost is usually below current rates because older low-coupon issues are still outstanding. Why: from 1950 to 1969 U.S. corporate debt rose about fivefold while pre-tax profits only about doubled, and pre-tax earnings after interest fell from about 30% of debt to 13.2%. Apply the test to the trend as well as the latest year; a falling earnings-to-debt ratio was the economy-wide warning of that era (red-flags.md §5).

**Rule 3: Other tests.**
- [ ] Size: a minimum volume of business for corporations, varying by industrials, utilities and railroads; a minimum population for municipalities. No figure is given here; for the defensive stock floors see defensive-selection.md.
- [ ] Stock/equity ratio = market value of the junior stock (common) ÷ total face amount of debt, or of debt plus preferred. A rough cushion measure that includes the market's view of prospects.
- [ ] Property value: once considered the chief protection, but experience shows safety lies in earning power; when that fails, assets lose most of their value. Asset values remain a separate test only for public utilities (rates depend on the property investment), real-estate companies and investment companies.
- [ ] Industrials: buy their bonds and preferreds only from companies of major size that have shown they can withstand a serious depression. Why: industrials grew faster than railroads and utilities, but individual companies are less stable.
- [ ] Do not relax standards in good times. Few industrial bonds defaulted after 1950, partly because there was no major depression. From 1963 to 1970 interest paid by U.S. nonfinancial firms rose from $9.8 billion to $26.1 billion, taking 29% of pre-interest, pre-tax profits in 1971 against 16% in 1963. Overbonded companies had become all too familiar.

**Why past-record tests work.** Bonds that met stringent past-based tests have, in the great majority of cases, survived the future successfully.
- Railroads: almost every road that failed had long been overbonded, with inadequate coverage even in average prosperity; almost every road that met strict tests escaped trouble. Of the roads reorganized in the 1940s and 1950, all but one started with ample coverage. The exception, the New Haven, earned its new charges only about 1.1 times in 1947 and fell into trusteeship again (for the third time) in 1961.
- Penn Central (1970 bankruptcy): coverage failed conservative standards as early as 1965, so a prudent bondholder would have sold long before (details in case-studies.md).
- Electric utilities: once SEC control and the breakup of holding companies came, soundly capitalized utilities essentially did not go bankrupt. The 1930s troubles came almost entirely from financial excesses visible in their capital structures.

**Feeding the script.** `scripts/value_screen.py` runs Rules 1-2, the stock/equity ratio and the modern debt/capital test. Inputs: `type` (industrial | utility | railroad | retail), `fixed_charges` (and `fixed_charges_avg7` for the exact 7-year test), `fixed_charges_poorest_year`, `pretax_earnings_before_fixed_charges_avg7`, `pretax_earnings_before_fixed_charges_poorest`, optional `aftertax_earnings_before_fixed_charges_avg7` / `_poorest` for the after-tax columns, `preferred_dividends` (adds average and poorest-year preferred coverage), `long_term_debt`, `short_term_debt`. Read the coverage rows together: the issue passes if either the average row or the poorest-year row passes. Prefer the pretax tests when the company pays little tax. Its 25% debt-principal threshold for retailers is an extrapolation; the classic rules give none.

Modern update (2003): roughly 500 corporate bond funds exist, and a diversified individual-bond portfolio needs at least about $100,000, so most individuals should buy a low-cost bond fund and leave credit research to it. Use these tests on individual issues, on preferreds and convertibles, and to sanity-check a fund's holdings.

## 3. Common-stock valuation: method and the five capitalization factors

Ideal procedure: estimate average earnings over a period of future years, multiply by an appropriate capitalization factor, and compare the result with the price.
- Standard way to estimate future earnings: start from average past physical volume, prices and operating margin; project sales from assumed changes in volume and price, grounded first in economic (GDP) forecasts and then in industry and company specifics.
- Group forecasts are far more dependable than individual-company forecasts (Value Line evidence, §11). It is almost impossible to tell in advance which individual forecasts will hold. That is why funds diversify widely, and wide diversification is itself a practical repudiation of Wall Street's lip service to "selectivity". (exceptional analysts can succeed by concentrating, as Philip Fisher's book describes, but not the great body of analysts.)
- Concentration suits proven investors like Buffett. For typical investors, not diversifying is foolish, because more holdings shrink the damage from any one loser and raise the odds of owning the big winners. "Focused" funds holding 25-50 "best ideas" have not clearly outperformed.
- Concentration builds and destroys big fortunes; it almost never builds small ones and rarely keeps big ones. The big single-stock fortunes came mostly from insiders (founders, families, senior employees) whose close relationship justified holding through everything; outsiders keep doubting and sell too early. Forbes 400 evidence: a 1982 member needed only about 4.5% a year to stay on the 2002 list, while stocks returned 13.2% a year, yet only 64 of the 400 (16%) were still on it. Unless the user is a control person with inside knowledge, keep any single stock small.

**The five factors that move the multiplier.** Two companies with the same expected $4 earnings per share might rationally be valued at 40 and 100:
1. **General long-term prospects.** No one really knows the distant future, but views of it drive big P/E differences by company and industry. Market distinctions are often sound, but when they rest mainly on past performance they are as likely to be wrong as right (the chemical-vs-oil case in §11). High returns attract competition: when returns on capital are exceptional, assume new competitors will come in and erode them, and do not project today's margins indefinitely without a demonstrable moat (H&R Block, earning 27% on book in 1969, drew a would-be rival that quickly failed; many 1999 Internet buyers assumed early winners would keep their edge).
2. **Management.** Much is said, little is useful. Assume an outstandingly successful company has good management: it already shows in the record, in the five-year estimates and in the long-term prospects. **Count it once.** Adding it again as a separate bullish factor leads to expensive overvaluation. Management is most useful as a separate factor when a recent change has not yet shown up in the figures (Chrysler in 1921 and 1962, §11).
3. **Financial strength and capital structure.** At the same price and earnings, prefer the company with surplus cash and nothing senior to the common over one with big bank loans and senior securities. Modest bonds or preferreds, or moderate seasonal bank credit, are not necessarily a disadvantage. A top-heavy structure (little common relative to bonds and preferred), i.e. leverage, can produce huge speculative gains in good times.
4. **Dividend record.** One of the most persuasive tests of quality: uninterrupted dividends over many years. 20+ years of continuous payments is an important plus; a defensive investor may justifiably buy only stocks that meet it.
5. **Current dividend rate.** The hardest factor. The "standard" policy was to pay out about two-thirds of average earnings; lower recently (1969 payout: 59.5% for the DJIA stocks, 55% for all U.S. corporations). Where the dividend bears a normal relation to earnings, valuing on either basis gives the same answer. Example: a typical secondary company with expected earnings of $3 and dividend of $2 is worth 12 × $3 = 18 × $2 = $36. Growth companies retaining most earnings raise separate questions (management-and-dividends.md). Modern update: S&P 500 payout was 34.1% at end-2002, with an all-time low of 25.3% in April 2000.

## 4. Growth stocks: the 8.5 + 2g formula, implied growth, the 8% problem

**What counts as a growth stock.** One whose per-share earnings have grown well above the rate for stocks generally and are expected to keep doing so. A common working bar: EPS at least doubling in 10 years, a compound rate of just over 7.1% a year (the 7.2% column of the multiplier table below). Rule of 72: years to double ≈ 72 ÷ growth rate in percent (72 ÷ 7.2 = 10). The stricter modern bar is about 15% a year (superinvestors-and-speculation.md); say which definition you are using.

**Formula:**

    Value = Current (normal) earnings × (8.5 + 2g)

g = expected annual growth rate in percent over the next 7-10 years. 8.5 is the multiplier for zero growth. Note: the formula does not give the "true value" of a growth stock; it only approximates the results of the elaborate calculations then in vogue.
- "Current (normal) earnings" means the current year's earning power after removing special items and temporary distortions, not a long multi-year average. The classic implied-growth examples used single-year EPS, averaging two years only where a strike depressed 1969.
- **Implied growth** (reverse use): g = (P/E − 8.5) ÷ 2.

The classic multiplier table (multipliers by expected growth rate):

| Expected growth rate | 0% | 2.5% | 5% | 7.2% | 10% | 14.3% | 20% |
|---|---|---|---|---|---|---|---|
| Growth over 10 years | 0% | 28% | 63% | 100% | 159% | 280% | 519% |
| Multiplier of current earnings | 8.5 | 13.5 | 18.5 | 22.9 | 28.5 | 37.1 | 48.5 |


Classic implied-growth examples (implied growth at end-1963, then the 1963-69 outcome):

| Issue | P/E 1963 | Implied g 1963 | Actual EPS growth 1963-69 | P/E 1969 | Implied g 1969 |
|---|---|---|---|---|---|
| AT&T | 23.0 | 7.3% | 4.75% | 12.2 | 1.8% |
| General Electric | 29.0 | 10.3% | 4.0% | 20.4 | 6.0% |
| General Motors | 14.1 | 2.8% | 1.17% | 11.6 | 1.6% |
| IBM | 38.5 | 15.0% | ~16% | 44.4 | 17.9% |
| International Harvester | 13.2 | 2.4% | 0.1% | 10.8 | 1.1% |
| Xerox | ~73 | 32.4% | ~29% | 50.8 | 21.2% |
| DJIA | 18.6 | 5.1% | 5.5% | 14.0 | 2.8% |

- The 1965 reading: Xerox's 32.4% against GM's 2.8% reflected doubt that GM's record 1963 earnings (the largest of any corporation in history) could be exceeded much, and speculative enthusiasm for Xerox's achievements and promise. The DJIA's implied 5.1% compared with actual growth of 3.4% a year compounded between 1951-53 and 1961-63.
- Sequel: Xerox and IBM grew about as fast as implied, so their prices rose a lot. The DJIA grew about as projected; its price rose 23% to end-1970 plus 28% in dividends, close to the 7.5% a year posited. AT&T, GE, GM and IH fell short of their implied growth and lagged the DJIA.
- Warning: even right projections do not mean prices will follow; do not treat these numbers as reliable forecasts.

**The 8% problem and the margin of safety:**
- If a company could be assumed to grow at 8% or more indefinitely, its value would be infinite, and no price would be too high. So valuations of high-growth stocks are necessarily conservative relative to the growth rates assumed.
- What a sound valuer does is build in a margin of safety, as an engineer does: set the value so that the target return is achieved (in 1963, 7.5% a year overall) even if actual growth falls well short of the projection. If the projection is met, the excess is a bonus.
- There is no realistic way to value a company expected to grow above about 8% a year: you cannot make realistic assumptions about both the multiplier on current earnings and the multiplier the market will pay on future earnings.
- Any scientific valuation must also allow for future interest rates: higher rates lower the present value of a given stream of earnings. The simple formula was kept because violent rate swings made rate forecasts presumptuous. Via the rule of 72: money doubles in just over 7 years at 10% and just over 10 years at 7%, so higher rates make distant earnings worth less. (A 1962 version of the method added an interest-rate adjustment to this formula; it is a separate refinement, so do not attribute it to the simple formula.)
- Sensitivity example (modern update): $1 of EPS growing 15% a year for 15 years becomes $8.14; at 35 times earnings that is a ~$285 stock. Growing 14% it becomes $7.14, and the disappointed market pays perhaps 20 times, about $140, more than 50% less, from a one-point miss in growth. Long, high growth projections magnify tiny errors (also the Petersburg-paradox argument in market-fluctuations.md §5).
- The market punishes fast growers that report a decline far more than steady moderate growers. A big risk in growth stocks is not that growth stops but that it slows, which over time is virtually certain.

**Base rates against sustained high growth.** Before accepting a growth assumption above about 10% a year, cite them:
- Loomis: from 1960 through 1999 only 8 of the 150 largest Fortune 500 companies raised earnings by at least 15% a year for two decades.
- Sanford C. Bernstein & Co.: only 10% of large U.S. companies grew earnings by 20% for at least five straight years, 3% for ten, and none for fifteen.
- Chan, Karceski and Lakonishok (1951-98): over all 10-year periods, net earnings grew 9.7% a year on average, and only 9.3% for the biggest fifth of companies.
- The bigger they get, the slower they grow. Growth stocks are worth buying at reasonable prices, but once P/Es go much above 25 or 30 the odds turn ugly. General Electric's P/E fell from 48 at end-1999 to 16 in March 2003 and Home Depot's from 97 to 14; their prices fell about 53% and 65% by end-2002, although both businesses had grown strongly every year from 1995 to 1999.

**Industry analysis:** most brokerage industry studies repeat what the public already knows and the market has already priced. They rarely argue convincingly that a popular industry is heading for a fall or an unpopular one for prosperity. Technology change makes field work (visits, interviews with research staff, technical study) potentially valuable. Choose your stance consciously: imaginative investing pays for vision proven sound but risks major miscalculation; conservative investing refuses to pay more than a minor premium for unproved possibilities and must accept forgone golden opportunities.

## 5. The two-part appraisal process

1. **Past-performance value.** What the stock would be worth, absolutely or as a percentage of the DJIA or S&P, if its relative past performance continued unchanged. That includes assuming its relative growth rate over the last seven years continues for the next seven. Compute it mechanically with a formula that weights past profitability, stability and growth, plus current financial condition.
2. **Modification.** Decide how far expected new conditions justify changing that value. Show both the original and the modified value, with the reasons for the change.
- Division of labor: a senior analyst sets the general formula; junior analysts compute the factors mechanically; the senior analyst makes and documents the modifications.
- The results may not be dependable for typical industrials, but the method is still recommended: analysts must value stocks regardless, the method beats common practice, it builds insight, and it accumulates a recorded body of experience, as medicine does. It may work best for public utilities.
- Endpoint: the intelligent analyst eventually confines himself to groups where the future is reasonably predictable, or to cases where past-performance value exceeds the price by so wide a margin that future variations can be risked, just as with well-secured senior securities. Modern suggestion: industries less dependent on interest rates or commodity prices (gaming, cosmetics, alcoholic beverages, nursing homes, waste management).
- ALCOA application: a past-performance value of about 10% of the DJIA meant about $84 a share with the DJIA at 840 (end-1970), so the stock looked attractive at 57 1/4. There was no way to know how much to mark it down for expected adverse developments, such as 1971 EPS as low as $2.50. In 1971 the price fell from 70 (May) to 36 (December) against a book value of 55.

## 6. Per-share earnings: adjustments before any multiplier

Two rules: don't take a single year's earnings seriously; and if you do look at short-term earnings, watch for booby traps in the per-share figures.

Adjustment checklist:
- [ ] **Read every footnote.** There may be several EPS figures: primary, after special charges, fully diluted before and after charges.
- [ ] **Dilution.** Use fully diluted earnings: assume convertibles are converted, and warrants exercised, whenever that would be profitable to the holders. In some cases dilution cuts apparent earnings by half or more. For warrants, prefer adding their market value to the market value of the common (convertibles-warrants.md). Financial services are not always consistent in this.
- [ ] **Special charges.** Find out how each arose. In a diversified company, closing an unprofitable division or losing on a contract is normal, not extraordinary. True earnings = diluted earnings minus the part of special charges attributable to the year. Management and auditors should state that part and charge the rest against ordinary earnings of a suitable number of future years, **not more than five**. If they don't, do it yourself.
- [ ] **Reserves for future losses.** Charging expected losses now means they never appear in any year's operating results. If reserved before the tax credit, later earnings can also be inflated by a tax benefit of about 50% (the 1972 tax rate). Be alert to "big bath" timing: charging everything possible to a bad year the market has already written off leaves the following years nicely fattened. Contrast the opposite old practice, contingency reserves set up in good years to smooth earnings, which accountants rightly opposed.
- [ ] **Tax-loss carryforwards.** Value earning power as if full income tax were paid, then add a separate bonus for the value per share of the temporary tax shield. Modern update (2003): U.S. losses could be carried forward up to 20 years, so severe recent losses can raise future after-tax earnings.
- [ ] **Depreciation method** (straight-line vs accelerated), **research and development** (expensed vs amortized) and **inventory** (FIFO vs LIFO). Restate peers on one basis before comparing them.
- [ ] **Materiality.** Ignore trivial items. Dow Chemical's 21-cent item, which decided whether 1969 growth was 9% or 4.5%, had no bearing on future average earnings or a conservative valuation.
- [ ] **Average earnings.** Use the average over 7-10 years, including special charges and credits, which are part of operating history. This also settles most special-item disputes.
- [ ] **Growth rate.** Compare the average of the last three years with the three-year average ten years earlier. Report both the latest and the average earnings.
- [ ] **Return on capital.** High multipliers persist only where the company maintains better-than-average profitability on capital funds (return on book).

Bottom line: corporate accounting is often tricky, analysis can be complicated, and stock valuations are really dependable only in exceptional cases. Most investors should simply make sure they are getting good value for the price and leave it there. Price and value are almost never identical, but the gap is often too small to cover trading costs and taxes, and you will rarely sell at exactly the quoted price.

**ALCOA 1970, worked example.**

| Per share | 1970 | 1969 |
|---|---|---|
| Primary earnings (before special charges) | $5.20 | $5.58 |
| Net income after special charges | $4.32 | $5.58 |
| Fully diluted, before special charges | $5.01 | $5.35 |
| Fully diluted, after special charges | $4.19 | $5.35 |
| Q4 primary | $1.58 | $1.56 |
| Q4 after special charges | $0.70 | $1.56 |

- Naive reading: Q4 × 4 = $6.32 a year; price 62 → under 10 times earnings (International Nickel was 16). Using Q4 after charges: $0.70 × 4 = $2.80 → 22 times.
- Special charges: $18.8 million in Q4, given as 88 cents a share (82 cents in later figures). They were estimated future costs of closing the manufactured-products division and the ALCOA Castings plants, phasing out ALCOA Credit Co., and $5.3 million to finish a curtain-wall contract, on sales of about $1.5 billion. These are normal events for a large diversified company. The footnote did not say whether the charges were before or after tax.
- Answer: true 1970 earnings = $5.01 (diluted) minus the unknown part of the special charges belonging to 1970. Average EPS including special items: $3.62 (1961-70), $4.62 (1964-70).
- Growth (classic data, deducting three-fifths of the 82-cent charge in 1970): ALCOA's 3-year average EPS was $2.08 in 1958-60 and $4.95 in 1968-70, +141% or 9.0% a year. Sears Roebuck: $1.23 → $2.87, +134%, 8.7% a year. DJIA: $31.49 → $55.40, +75%, 5.7% a year.
- Yet early 1971 ALCOA sold at 11.5 times its 3-year average against 27 times for Sears and 15+ for the DJIA. Its 1959 high of 116 had been 45 times earnings (Sears's adjusted 1959 high, 25 1/2, was 20 times), and it closed 1970 at exactly half that high, while Sears tripled and the DJIA rose nearly 30%. Explanation: ALCOA's return on capital was only average or below. Lesson: past growth alone does not earn a high multiple; profitability does, and the market had overestimated ALCOA's future in 1959.

## 7. Accounting tricks to detect

- [ ] **Pro forma earnings: ignore them.** They show how well a company might have done had it not done as badly as it did. Examples: a quarter presented as if $159.9 million of preferred dividends had not been paid; another as if $193 million of payroll taxes on option exercises had not been paid; another as if $2.5 billion of merger and goodwill charges, a $7 million investment loss and $4 million of payroll taxes had not happened.
- [ ] **Revenue-recognition changes.** Qwest began booking directory revenue on publication although customers paid monthly. That "change in accounting principle", fully disclosed, added $240 million after tax, a fifth of 1999 net income. By 2003 it admitted 2000-01 revenue was overstated by $2.2 billion; the stock fell from $41 (market value $67.9 billion) at end-2000 to about $4. Record context: 330 U.S. public companies restated their accounts in 2002.
- [ ] **Capitalizing operating costs.** Global Crossing in 1998 expensed $178 million (about a third of $600 million+ of construction) as cost of capacity sold, reporting a $96 million loss instead of about an $82 million profit. From October 1999 it treated much of that cost as long-lived capital assets: property rose $575 million while cost of sales rose only $350 million. It was worth $12.6 billion in March 2001 and went bankrupt in January 2002. Understand what is capitalized, and why the method changed.
- [ ] **"Nonrecurring" charges that recur.** Micron wrote down inventory by $261 million in the quarter to May 2001, then took further write-downs in each of the next six quarters. Treat a chronic charge as an operating cost.
- [ ] **Pension income.** SBC Communications' 2001 net income of $7.2 billion included $1.4 billion (13%) of pension income, after raising the assumed return on plan assets from 8.5% to 9.5% because past 10-year returns had exceeded 10%. Berkshire Hathaway cut its assumption from 8.3% to 6.5% the same year; in 2001 Berkshire's plan gained 9.8% while SBC's lost 6.9%. Tests:
  - Is net pension benefit more than 5% of net income? Then ask whether the rest of earnings is acceptable without it.
  - Is the assumed return reasonable? Modern update (2003): anything above 6.5% was implausible, and a rising assumption delusional. Re-base on current bond yields.
- [ ] **Aggressive license-revenue footnotes.** Informix booked revenue when customers committed to minimum fees, before any resale to end users; it later restated away $244 million of "sales".
- Reading method:
  - Read reports backwards, from the last page; what the company wants hidden is at the back.
  - Read every footnote, above all the summary of significant accounting policies (revenue recognition, inventories, installment and contract sales, marketing costs), plus debt, options, loans to customers, loss reserves and risk factors.
  - Watch for the words capitalized, deferred, restructuring, and the change words began, change, however. They are not disqualifying, but they require investigation.
  - Compare the footnotes with at least one close competitor's to judge how aggressive the accounting is.

## 8. The 10-K research checklist (modern update; enterprising effort level)

Gather at least five years of annual reports and at least one year of quarterly reports. If that is too much work, the investor is not suited to picking individual stocks. Answer two questions: what makes the company grow, and where do (and will) its profits come from?

**Long-term prospects: negatives**
- [ ] Serial acquirer: averaging more than two or three acquisitions a year signals trouble. Check the acquisition track record in management's discussion and the footnotes. Watch for companies that swallow deals and later spit them out at heavy losses, and for chronic write-offs proving past overpayment.
- [ ] Other people's money addict: heavy borrowing or stock sales ("cash from financing activities"). Test: if operating cash flow is consistently negative while financing cash flow is consistently positive, the company consumes more cash than its businesses make. (Global Crossing, WorldCom.)
- [ ] One-customer dependence: Sycamore Networks' 1999 IPO prospectus showed one customer providing 100% of its $11 million revenue; it was valued at $15 billion. The customer went bankrupt about two years later, and the stock lost 97% from 2000 to 2002.

**Long-term prospects: positives**
- [ ] A wide moat, from brand strength, monopoly or near-monopoly, economies of scale, a unique intangible asset, or resistance to substitution.
- [ ] A marathoner, not a sprinter: revenue and net earnings grew smoothly over 10 years. Long-run growth of about 10% pre-tax (6-7% after tax) may be sustainable; corporate targets of 15% are delusional; sudden bursts fade.
- [ ] Sows and reaps: spends on research and development. 2002 R&D as a share of sales: about 4% (Procter & Gamble), 6.5% (3M), 10.9% (Johnson & Johnson). A company spending nothing is at least as vulnerable as one spending too much.

**Management**
- [ ] Say-do test: compare past annual-report promises with results. Do managers admit failures, or blame "the economy", "uncertainty" or "weak demand"? Is the chairman's letter consistent, or does it chase fads (a cement company becoming a "software revolution" in 1999)?
- [ ] Pay: a $100 million CEO year needs an extraordinary justification; otherwise the company is run for its managers.
- [ ] Option repricing for insiders: stay away.
- [ ] Option overhang: read the options footnote and value the company on the full share count after potential new shares. Example: 4.5 billion shares outstanding plus options on 657 million more means about 15% more shares to share future earnings.
- [ ] Insider sales (from insider-transaction filings): occasional sales can be innocent; repeated big sales are a bright red flag.
- [ ] Managers or promoters? Complaining the stock is always undervalued (managers should keep the price from going too high as well as too low); quarterly earnings guidance; streams of hype press releases. Better: candid long-term communication without 90-day forecasts.
- [ ] Transparency: "nonrecurring" charges that recur, frequent extraordinary items, emphasis on EBITDA over net income, pro forma figures that hide losses.

**Financial strength and capital structure**
- [ ] Cash from operations grew steadily over 10 years. A good business generates more cash than it consumes.
- [ ] Owner earnings = net income + depreciation and amortization − normal capital expenditures. Also subtract the cost of stock options, any unusual, nonrecurring or extraordinary charges, and any pension income. Test: owner earnings per share grew at a steady average of at least 6-7% a year over 10 years.
- [ ] Long-term debt, including preferred, under 50% of total capital.
- [ ] Fixed-rate or variable-rate debt? Variable rates become costly if rates rise.
- [ ] The ratio of earnings to fixed charges is at least above 1 (Amazon's 2002 earnings fell $145 million short of interest costs, after a $1.1 billion shortfall two years earlier). For investment-grade safety, apply the coverage table (§2).

**Dividends and share policy**
- [ ] The company must prove you are better off without a dividend: acceptable only if it consistently outperforms competitors in good and bad markets.
- [ ] Repeated, hyped stock splits: the company treats its owners as dolts (two $50 shares are not worth more than one $100 share).
- [ ] Buybacks should happen when the stock is cheap, not near record highs to offset option exercises. Talk of "enhancing shareholder value" seldom means it. (Policy detail: management-and-dividends.md.)

**Script mapping:** `value_screen.py` checks the OPM-addict pattern (`operating_cash_flow_history`, `financing_cash_flow_history`), owner earnings (`net_income`, `depreciation_amortization`, `maintenance_capex`, `stock_option_cost`, `pension_income`), serial acquisitions (`acquisitions_per_year`), recurring "nonrecurring" charges (`years_with_nonrecurring_charges_last5`), option overhang and debt/capital. It does not test owner-earnings growth; compute that from the 10-year history.

## 9. Comparing companies side by side (the four-company method)

Build this grid for the candidates and at least one peer:

| Block | Items |
|---|---|
| Capitalization | price; shares; market value of common; bonds and preferred; total capitalization |
| Income | sales; net income; EPS latest; EPS 3-yr averages now, 5 years ago and 10 years ago; current dividend |
| Balance sheet | current assets; current liabilities; net assets for common; book value per share |
| Ratios | P/E (latest; 3-yr average); price/book; net/sales; net per share/book; dividend yield; current ratio; working capital/debt; EPS growth (3-yr average vs 5 and 10 years earlier) |
| Price record | long-run low and high; latest bear-market low; latest high |

Six elements to judge:
1. **Profitability:** earnings on book value (net per share/book) and operating income to sales for manufacturers. A high return on capital often goes with high EPS growth.
2. **Stability:** the largest drop in per-share earnings in any one of the past ten years, measured against the average of the three preceding years. No drop = 100% stability.
3. **Growth:** compare with the DJIA or S&P over the same span.
4. **Financial position:** manufacturers should have at least $2 of current assets per $1 of current liabilities, with low long-term debt. Service companies may differ (the classic comparison excused the air-freight forwarder). Treat convertible preferred as converted.
5. **Dividends:** what counts is an uninterrupted record; payout variations matter little.
6. **Price history:** the long-run low-to-high range, and the latest bear-market decline.

The four-company example (end-1970):

| | ELTRA | Emerson Electric | Emery Air Freight | Emhart |
|---|---|---|---|---|
| Price (12/31/70) | 27 | 66 | 57 3/4 | 32 3/4 |
| P/E 1970 | 10.0 | 30.0 | 38.5 | 11.9 |
| P/E on 1968-70 avg | 9.7 | 33.0 | 45.0 | 11.7 |
| Price/book | 1.00 | 6.37 | 14.3 | 1.22 |
| Net/sales | 4.6% | 8.5% | 5.4% | 5.7% |
| Net per share/book | 10.0% | 22.2% | 34.5% | 10.2% |
| Dividend yield | 4.45% | 1.78% | 1.76% | 3.65% |
| Current ratio | 2.9 | 4.3 | 1.7 | 3.4 |
| Working capital/debt | very large | 5.6 | no debt | 3.4 |
| EPS growth vs 1963-65 | +81% | +87% | +135% | +14% |
| EPS growth vs 1958-60 | +400% | +250% | very large | +132% |
| Long-run low → high (1936-68) | 3/4 → 50 3/4 | 1 → 61 1/2 | 1/8 → 66 | 3 5/8 → 58 1/4 |

- The finding: P/Es (9.7-45 times average earnings, against 15.5 for the DJIA) varied far more than performance or financial condition. Emerson and Emery had higher returns on capital and 100% stability. ELTRA and Emhart fell only 8% each in the poor year 1970 (DJIA 7%), grew faster than the Dow, yielded about twice as much, and sold near book. Emhart had paid dividends since 1902. Emery's 34-year range was 528 to 1 (66 ÷ 1/8), Emhart's 17 to 1, the DJIA's about 11 to 1.
- Emerson: $163 million of low-dividend convertible preferred, treated as converted, cut EPS by about 10 cents (4%). It was valued at about $1.6 billion, over $1 billion of it for intangible earning power; the comparison case is Zenith (§11).
- Goodwill payback: compute (market value − tangible equity) ÷ normal annual earnings, the years of earnings needed just to cover the premium paid over assets. The longer the period, the more the price depends on the distant future (example and flag: red-flags.md §3).
- Emery: growth from a tiny base ($570,000 of net earnings in 1958) is harder to continue once large. Its earnings rose even in 1970, the air-passenger industry's worst year, but that raised questions about future competition and airline arrangements. More than 60 times recent earnings (64 times 1971 earnings in March 1972) could be justified only by someone with exceptionally firm, optimistic, in-depth conclusions.
- Conclusion: ELTRA at 27 and Emhart at 33 had enough value behind the price to be reasonably protected investments, bought at about the money the balance sheet shows invested, and they passed the seven defensive criteria (defensive-selection.md). Market action is not a valid reason to choose a stock; faster growth is valid only within limits. Do not urge a holder of the glamour pair to switch unless he understands the philosophy: momentum can persist indefinitely, and the real basis is a considered preference for value-type over glamour-type investments.
- Outcome: Emery fell 58% by late 1974 as its P/E went from 64 to 15. It lost 72.8% after inflation from 1972 to 1982, and $1,000 put in it in 1972 was worth only $839 in 1999.

The 1999 repeat, the same lesson in a bubble:

| At 12/31/1999 | Emerson Electric | EMC | Exodus Communications | Expeditors International |
|---|---|---|---|---|
| 1999 total return | −3.1% | +157.1% | +1,005.8% | +109.1% |
| P/E | 17.7 | 103.1 | NM (losses) | 39.4 |
| Price/book | 3.7 | 22.9 | NM | 7.8 |
| Market cap/revenue | 1.7 | 16.5 | 59.3 | 1.5 |
| Debt | moderate | small | $2.6 billion | none |
| Return 2000-02 | ended 2002 within 4% of its 1999 price | −88% | bankrupt (Sept 2001) | +51% |

- Emerson: earnings up 42 years in a row and dividend raised 43; 1999 sales $14.4 billion and net income $1.3 billion; five-year EPS growth 8.3%; net margin about 9% and return on capital about 18% through the 1990s.
- EMC: up over 81,000% in the 1990s. Margins slipped from 19.0% to 17.4% and return on capital from 26.8% to 21% (1995-99). Excluding the Data General acquisition (about $1.1 billion of revenue), revenue grew only 3.6%, from $5.4 billion to $5.6 billion. The CEO's $10 billion target for 2001 ended at $7.1 billion of revenue and a $508 million loss.
- Exodus: revenue $242.1 million, a loss of $130.3 million, $971 million borrowed in December alone, and more than $400 million of cash burned in 1999; split 2-for-1 three times that year.
- Expeditors: revenue growth 19.8% a year, EPS growth 25.8%, no debt, little-known (32% institutional ownership).
- Lessons: separate the stock from the business; strip acquisitions out to find organic growth; check cash burn and debt service; splits create nothing.

## 10. Valuation worked example (full computation)

Inputs: the sample company in `assets/company_input_template.json` (hypothetical; amounts as given there). Price $42.00; 100M basic and 103M diluted shares; EPS history 2015-24 = 2.10, 2.25, 1.95, 2.40, 2.60, 2.20, 2.90, 3.10, 3.00, 3.30; equity $2.70B; intangibles $0.40B; current assets $2.10B; current liabilities $0.90B; long-term debt $1.00B; short-term debt $0.10B; expected growth 4%; AAA yield 5.5%; pre-tax earnings before fixed charges $480M (7-year average) and $360M (poorest year); fixed charges $60M now, $58M on the 7-year average, $55M in the poorest year.

Step 1, normalize earnings (§6). The template's EPS figures are taken as already including every special charge, so no restatement is needed. (Had the company excluded, say, a $0.45 restructuring charge from its own "adjusted" figure for a 2023-25 program, you would put it back and spread it at $0.15 a year.) If the EPS figures are basic, also look at them on diluted shares: × 100/103, so the latest 3-year average becomes 3.133 × 0.971 = $3.04.

Step 2, averages:
- Latest 3-year average (2022-24): (3.10 + 3.00 + 3.30) ÷ 3 = $3.133 (basic).
- 7-year average (2018-24): 19.50 ÷ 7 = $2.786.
- Growth: the classic method needs the 3-year average ten years earlier (2012-14), which this 10-year history lacks. On the available window, 2015-17 average 2.10 → 3.133 = +49% over a span of about 7 years, which passes the one-third test even on the stricter shorter span.

Step 3, defensive price tests (defensive-selection.md):
- P/E on the 3-year average = 42 ÷ 3.133 = 13.4 (≤ 15 ✓; 13.8 on diluted EPS).
- Book value per share = 2,700 ÷ 100 = $27.00, so P/B = 1.56 (just over 1.5). The combined test 13.4 × 1.56 = 20.9 ≤ 22.5 ✓ (22.1 if both EPS and book are put on diluted shares: 13.8 × 1.60, still a pass).
- Price ceiling = √(22.5 × 3.133 × 27.00) = √1,903 = $43.6, so the price is about 4% below the ceiling.
- Tangible book = (2,700 − 400) ÷ 103 = $22.33; price/tangible book = 1.88, above the 1.33 near-book guide.
- Financial condition: current ratio 2.10 ÷ 0.90 = 2.33 ✓; working capital $1.20B ≥ long-term debt $1.00B ✓.
- Other defensive tests: sales $4.2B against the $100M × 7.9 = $790M floor ✓; no deficit in 10 years ✓; dividends for 31 years ✓.
- The 2003 recalibration: market value $4.2B against the ~$3.5B CPI-translated floor ✓; institutional ownership 58% ≤ 60% ✓ (barely); growth +49% against +50% ✗, a miss by one point, on the short window.

Step 4, growth formula (§4):
- Value = E × (8.5 + 2 × 4) = E × 16.5.
  - E = latest normal year ($3.30): value $54.5.
  - E = 3-year average ($3.133): value $51.7.
  - E = 7-year average ($2.786): value $46.0. This is the conservative floor. The script reports all three as a range.
- Implied growth at $42: (13.4 − 8.5) ÷ 2 = 2.5% on the 3-year average; (12.7 − 8.5) ÷ 2 = 2.1% on $3.30. The price assumes less growth than the 4% expected, and the 2015-24 record shows about 5% a year, which leaves some margin.

Step 5, senior-security safety (§2):
- Coverage: 480 ÷ 58 = 8.3× on the 7-year average (8.0× against current charges of 60) (industrial minimum 7× ✓) and 360 ÷ 55 = 6.5× in the poorest year (minimum 5× ✓).
- Debt-principal alternative: 480 ÷ 1,100 = 44% (≥ 33% ✓).
- Debt/capital: 1,000 ÷ (2,700 + 1,100) = 26% (< 50% ✓).

Step 6, cash and quality (§8):
- Owner earnings = 335 + 140 − 120 − 15 − 0 = $340M = $3.30 per diluted share, equal to reported EPS, so earnings are backed by cash.
- Payout = 5-year average dividend $1.16 ÷ 5-year average EPS $2.90 = 40%.

Step 7, margin-of-safety cross-check (margin-of-safety.md): earnings yield 3.133 ÷ 42 = 7.5% against a 5.5% AAA yield, a 2-point spread (about 20% of the price accumulated over 10 years). On 7-year average earning power: 2.786 ÷ 42 = 6.6%, a 1.1-point spread (~11% over 10 years). The script reports both versions, against the AA yield when `aa_bond_yield` is supplied (the template's 5.7%), otherwise AAA. Either way it is positive but thinner than the classic example (9% against 4%, about 50% of the price).

Conclusion template: passes all seven defensive tests, though only narrowly on P/B (it relies on the 22.5 combined rule), and narrowly misses the modern +50% growth bar. Value by the growth formula is $46-55, against $42. Bond-type safety is ample. The margin of safety is moderate, not wide. Then state what price would widen the margin (for example, at or below the 7-year-average value of $46 minus a cushion), not a forecast.

## 11. Cases, grouped by lesson

**Individual forecasts are unreliable; group forecasts less so.**
- Value Line's mid-1964 forecasts for 1967-69 against actual 1968 results. For the 30 DJIA stocks combined: EPS forecast 52.00 (DJIA units) against 56.00 actual (57.89 in 1968; 56.26 for 1967-69); price forecast 820 against 918 actual, so the aggregate was slightly low. Six years earlier the forecasts had been too optimistic on earnings but used a low multiplier, so the price estimate came out about right. Individual misses were large:

| Stock | EPS forecast 1967-69 | Actual 1968 | Price mid-1964 | Price forecast | Actual avg 1968 |
|---|---|---|---|---|---|
| Eastman Kodak | $5.00 | $9.32 | 133 | 100 | 320 |
| Allied Chemical | 3.70 | 1.46 | 54 1/2 | 67 | 36 1/2 |
| Union Carbide | 7.35 | 5.20 | 126 1/2 | 165 | 90 |
| Anaconda | 6.00 | 8.12 | 44 1/2 | 70 | 106 |
| United Aircraft | 4.00 | 7.65 | 49 1/2 | 50 | 106 |
| General Motors | 6.25 | 6.02 | 88 | 78 | 81 1/2 |

**Market multiples based on past performance can be wrong.** Chemicals vs oils in the DJIA. At end-1963 the chemicals sold at an average 25.3 times earnings (Allied 19.8, Union Carbide 22.7) and the oils at 15.3 (Standard Oil of California 13.2, Standard Oil of New Jersey 16.0, Texaco 16.3). By 1970 the chemicals had made practically no earnings gain: Allied fell from $2.77 to $1.56, Union Carbide from $2.66 to $2.60, Du Pont went from $6.55 to $6.76. The oils grew about as their multiples implied: $4.50 → $5.36, $4.74 → $5.90, $2.15 → $3.02. Wall Street's sector consensus is most cheerful when the stocks are dearest; build decisions that don't depend on forecasts.

**Management changes matter only when not yet in the numbers.** Chrysler: in 1921 Walter Chrysler revived the moribund Maxwell Motors. In 1962, after new owners linked to Consolidation Coal took over, EPS went from $1.24 (1961) to the equivalent of $17 (1963) and the price from 38 1/2 to the equivalent of nearly 200 a year later, helped by two 2-for-1 splits in 1963. Iacocca's 1980s rescue was real; "Chainsaw" Al Dunlap's Sunbeam turnaround (after taking Scott Paper stock up 225% in 18 months) was a fraud that fooled famous money managers. Identifying turnaround managers is harder than it looks.

**High valuations carry high risks.** Zenith Radio: a brilliant growth record, a $1.7 billion market value in 1966; profits fell from $43 million in 1968 to half that in 1970, and the price from 89 to 22 1/2.

**Coverage tests predict bond trouble.** The New Haven railroad at 1.1× coverage and Penn Central failing the tests by 1965 (§2).

**Accounting can create or hide earnings.** ALCOA (§6); Northwest Industries planned a $264 million special charge ($200 million loss on selling its railroad to employees, plus a write-down of a recent stock purchase), about $35 a share, twice the market price. The loss would shelter about $400 million of future profits from tax within five years, and convertibles and warrants would more than double the share count. Trane reported 1970 EPS of $3.29 against $2.76 (+20%), half of it from switching back to straight-line depreciation for reporting while keeping accelerated depreciation for tax. The Qwest, Global Crossing, Micron, SBC and Informix cases are in §7.

## 12. Translating to today

- The coverage table was calibrated in 1961 (rates about 4.5%); the 1972 debt-principal alternative (33/20/25%) was for an 8% world. Run both at current rates. When rates are high, the debt-principal test keeps strong companies from failing on coverage alone.
- 8.5 + 2g: the 8.5 zero-growth multiplier reflects 1960s high-grade yields. Treat the output as a rough check, never a target price. Present a range across normal-earnings definitions, as in §10, and the implied growth rate. Distrust any g above about 8% and any value depending mostly on distant growth.
- The two-thirds payout "standard" is history (34% in 2002, lower since). Judge retention by the returns on retained capital (management-and-dividends.md).
- "Extraordinary item" labels have changed in modern accounting standards, but the discipline is the same: count every recurring charge as a cost, spread one-offs over ≤ 5 years or average them over 7-10, use diluted shares, and tax-normalize carryforward-sheltered earnings.
- The four-company comparison grid and six elements are timeless. For asset-light firms, lean on return on capital, stability and cash conversion rather than price/book, and say so.
- The 2003 examples (pension assumptions above 6.5%, growth above 10% pre-tax) are calibrated to 2003 yields. Re-anchor them to current bond yields and nominal GDP growth.
