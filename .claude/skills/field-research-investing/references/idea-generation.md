# Idea generation: choosing what to investigate

## Contents
1. The goal: a very short list
2. Four kinds of opportunity
3. Why good companies become cheap
4. The first filter: neglect, cheapness, re-emerging growth
5. Stocks below net cash that are stopping the bleed
6. Text screens (warning and improvement phrases)
7. Numeric screens: supply and demand imbalance
8. Cyclical industries
9. Gossip and industry insiders
10. Other triggers worth following
11. Modern equivalents (sources and tools)

---

## 1. The goal: a very short list

Field research is expensive in time and money. Its job is to narrow thousands of listed companies to a handful where firsthand work has a high chance of finding a bargain: a stock cheap relative to its present value (which others ignore) or to its future value (the business is better, or its growth stronger and longer, than the market assumes). Screens and databases only point the way; the money is made after the screen is closed, by calling and visiting.

## 2. Four kinds of opportunity

| Kind | What it is | How it pays | Main risk |
|---|---|---|---|
| Deep value | Trades below book or working capital, low multiple of earnings or cash flow, high yield | Re-rating toward asset or normal value | Value trap; must keep finding new ones; taxable turnover |
| Quality franchise | Customers need it, cannot easily switch, pay willingly; earns well even under ordinary managers | Compounding for years; buy on transitory dips even if not dirt cheap | Paying too much; franchise eroding unnoticed |
| Hypergrowth | Explosive growth phase | Multiples of capital while growth lasts | Losing it all if you stay after growth slows |
| Special situation | A sharp change (restructuring, takeover, contract, collapse) is coming | Buying from (or selling to) those who do not know | Timing, legal care, higher taxes |

Pick the style that suits the user. A strong combination: excellent businesses that have become unjustifiably cheap, researched thoroughly, held until they become growth darlings, then sold to momentum buyers who are happy to carry the risk of slowing growth.

## 3. Why good companies become cheap

- **Product transition gap.** The old product is fading and the new one is not yet selling in volume, while heavier development and capital spending depress profits. Field research tells you whether the transition is on track.
- **Cyclical trough in the niche.** At the peak everyone expected the moon, at the trough they expect zero. Suppliers of truly essential products rarely go to zero.
- **A fixable mess.** Channel stuffing (shipping more to distributors than they can sell and booking it as revenue, often shortly before insiders exercise options and sell), backdated option grants, a botched acquisition or takeover fight, lawsuits against customers, boardroom feuds. Once exposed, the stock collapses, managers are replaced, controls are tightened and the board pays attention: the company is often stronger for a year or two afterwards.
- **A pay-only labor dispute** in a company that is otherwise healthy (see events-and-crises.md for when this does not hold).
- **Disappointed former darlings.** Investors who lost money want to forget the name.

Temporary problems are opportunities only when firsthand evidence shows the fix is under way and the price does not yet reflect it. Some "temporary" problems are death spirals, which are short candidates instead. Do not cut corners deciding which.

## 4. The first filter: neglect, cheapness, re-emerging growth

**Neglect.** Typical sources: former high-flyers that disappointed badly, companies run by managers who embarrassed themselves, stocks orphaned in old retirement accounts, brokers' personal accounts, or portfolios inherited by a new fund manager after the old one was fired. New managers often clean out inherited names in their first weeks regardless of price. If you know more about the stock than the seller, you can buy cheaply. Neglect alone proves nothing: many neglected stocks deserve neglect.

**Cheapness.** Use general value measures (price to book, to working capital, to earnings, to cash flow; dividend yield) or industry-specific ones. Moderate value gives more candidates; deep value fewer but safer. The count of stocks below net working capital (current assets minus all liabilities) is itself a gauge of the market: plentiful when the market is cheap, almost none when it is dear.

**Re-emerging growth.** Without growth you are buying a one-time re-rating. With it, you can hold. Signs:
- Customers are satisfied, competitors are nervous and short-tempered, suppliers are happy. On a rebound the suppliers may be the better investment; check them too.
- Follow where the company *and* its customers are spending time and money: if the company is hiring developers in a technology and its customers are hiring people experienced in using it, you see future demand at the intention stage. Customers' training schedules and space being prepared for future users of a product are also leading signs.
- Growth can take a year or two to show in reported numbers. Expect the position to sit still meanwhile.

## 5. Stocks below net cash that are stopping the bleed

A technology or service company trading below its net cash (cash and investments minus all debt and liabilities) usually carries heavy baggage: past management blunders, analysts who swung from over-optimism to despair, and a cash burn that seems to leave only a few quarters of life. Compute the runway: `python3 scripts/field_math.py runway --cash ... --debt ... --other-liabilities ... --shares ... --price ... --quarterly-burn ...`.

Some deserve their price and run out of money. But when management cuts costs decisively and the burn shrinks (or a credible date for breakeven appears), two things happen: the business proves viable and worth more than its cash, and would-be acquirers who were waiting for the company to come begging must bid now, sometimes against each other. Re-ratings to 50-100% above cash value are common in that phase.

Research order here is the reverse of normal: first verify the cost cuts and the integrity of management, then study the customers (if the first two fail, the business may simply be closed and the customers do not matter). Buy such stocks as a diversified basket, and before selling the winners, study their businesses: in baskets like this the surprises are often on the upside (several can multiply while only one fails, and even a failure may return part of its cash).

## 6. Text screens (warning and improvement phrases)

Search news and company releases for phrases that reveal pressure behind the curtain. Run `python3 scripts/screen_signals.py text <files or ->` to flag them, then read the context yourself. Read every corporate statement with an eye for the self-interest behind it, without holding it against the speaker: everyone is trying to get the better side of a trade.

**Possible trouble (short or avoid candidates):**
- management denies / reiterates that rumors are unfounded
- an officer left "for health reasons", "to pursue other interests", "for personal reasons", especially in sales or marketing
- guidance lowered; a new head of sales hired shortly after a disappointing period
- the company sues short sellers or publicly disputes an analyst's conclusion
- the company accuses an analyst of bias or inaccuracy, or pushes a broker to drop coverage
- auditor change, late filing, restatement, non-reliance on prior statements
- forensic accountants, restructuring advisers or bankruptcy counsel retained

These often mean sales are falling short before it is announced, the accounts are in worse shape than admitted, or management is trying to stop bad news leaking.

**Quiet improvement (long candidates among troubled names):**
- debt reduction ahead of plan; cash growing faster than expected
- a lawsuit settled; a plant, property or division sold
- a new chief executive or new controlling owner who starts cutting costs and buying stock
- an analyst who was wrong all the way down finally gives up (check the rating-history chart at the back of the report: buy near the top, downgrades during the fall, "sell" at the bottom)

The phrase lists are starting points; add phrases that proved meaningful in past research.

## 7. Numeric screens: supply and demand imbalance

The most powerful idea for numeric screens is an imbalance between supply and demand.

**Capacity starvation.** Look for industries so depressed that capital spending has not even covered depreciation for several years: owners are letting capacity rust because they believe bad times are permanent. Historical examples include basic materials after long slumps, an energy source after a major accident, and fuels when the press was proclaiming a permanent glut. Screens (with a database such as Compustat or any fundamentals export):
- sum of capital expenditures over 3 years < sum of depreciation over 3 years
- net property, plant and equipment falling for 2-3 consecutive years
- an industry-specific capacity measure falling (rigs, mills, fabs, seats, acreage)

**Demand turning.** Pair the starved industry with signs of demand:
- accelerating sales growth
- sales rising relative to inventories (demand outrunning what management stocked for)
- gross margins rising (pricing power returning)

In Compustat-style data the usual fields are capital expenditures (`capx`), depreciation and amortization (`dp`), net PP&E (`ppent`), sales (`sale`), inventories (`invt`) and gross profit (`gp`); pick the capacity measure that fits the industry. `python3 scripts/screen_signals.py capacity <csv>` computes these flags from a CSV of company-year (or industry-year) rows. When capacity is falling and demand is firming, call the industry's participants (customers, suppliers, managers, employees) and go and look. The reverse pattern (capacity piling up while demand dries up) points to shorts.

## 8. Cyclical industries

- Some cycles follow the economy (housing, cement, steel, metals); some have their own rhythm (for example semiconductor equipment, roughly with each new chip generation).
- In complex, multi-stage industries, each stage tends to have one or two dominant specialists that are hard to dislodge. Ask engineers and managers in the industry which firm leads each stage in their eyes and which they would most like to own. Those leaders would always look expensive if the industry were steady; the cycle hands you a chance to buy them cheaply.
- Sales of such specialists can rise or fall by half in a year; their stocks can double or triple, or halve and halve again, within two or three years. Becoming expert in one cyclical industry and buying its leaders near the bottom, selling near the top, can be highly rewarding. Field contacts tell you where in the cycle you are.

## 9. Gossip and industry insiders

- Chat with industry participants wherever they gather (trade events, user meetings, the places they unwind). Ask what the players are up to, then mostly listen.
- You will hear about people about to be fired or hired, who is winning and losing, who is leaving to chase an opportunity outsiders have not noticed, products that disappoint and products bought in bulk across whole organizations, lawsuits, accounting tricks, stuffed channels, regulatory inquiries.
- Treat each item as a lead to confirm, not a fact. Never solicit confidential information (legal-ethics-guardrails.md).
- A useful question for any industry veteran: "Which company in your field would you most like to own for good, and hand down?" The answers point to franchises. If they add "...if I could also run it", the business may be excellent but under-managed: a turnaround candidate.

## 10. Other triggers worth following

- **Change of control or new management at a cheap stock.** One of the most fertile sources. Search news for new chief executives, then check cheapness; scan ownership filings for creeping control and activists.
- **Insider buying waves**, especially open-market purchases with personal money by several insiders, and buying by former executives who rejoin.
- **Controversy.** Loud disputes often point to a real problem: follow up public fights between a company and its critics.
- **Coverage events.** An analyst dropping coverage after the company objected (short lead) versus dropping it after a collapse (possible bottom).
- **Strikes at quality companies** over pay alone.
- **Old, solid companies with strong balance sheets in hard times**: research them once they become ridiculously cheap (for example near or below book value), not before.
- **Start close to home.** Most people live within driving distance of the offices, plants or warehouses of many listed companies (a local chamber of commerce can list them). Local companies are easier to observe and to discuss with people who know them, and what you learn is more likely to be exclusive.

## 11. Modern equivalents (sources and tools)

These are current tools that serve the same purpose; they are an extension, not part of the original method.

- Filings full-text search (for example SEC EDGAR full-text search) for the warning and improvement phrases.
- Current-report items that mark trouble or change: officer departures and appointments, auditor changes, non-reliance on prior financial statements, material impairments, late-filing notices.
- Insider transaction reports (Form 4 in the US; SEDI in Canada) and ownership filings (13D/13G; activist letters).
- Fundamentals screens from any data provider; industry statistics from trade associations and government agencies.
- Job postings (company career pages, job boards), especially production and field roles; professional networking profiles for team moves.
- Customer reviews, user forums, app-store and software-review sites; trade-show exhibitor and attendee lists.
- Government procurement databases, import and shipping records, permit and zoning registers, court dockets.
- Commercial alternative data (web traffic, app usage, card spending, satellite or parking imagery) can help, but it is increasingly shared and therefore less exclusive: treat it as a lead, not an edge.
