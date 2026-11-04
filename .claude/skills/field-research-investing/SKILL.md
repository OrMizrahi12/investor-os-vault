---
name: field-research-investing
description: Investigative primary-research stock analysis that finds an edge the filings cannot give by studying a company's customers, suppliers, competitors, employees, product, plants and surroundings, then verifying with physical evidence. Use it to pick stocks worth deep research (neglected, cheap, in transitory trouble, capacity-starved industries, red-flag news), plan due diligence and scuttlebutt or channel checks, prepare interviews with customers, suppliers, competitors, staff or management, plan a site visit, reconcile reported revenue with counted shipments, triage a sudden stock drop, scandal, strike or suspected fraud, watch for takeovers, restructurings or demand surges, map relationships, and turn field notes into a buy, sell, short or no-go decision, within legal limits (no inside information, no pretexting). Use it whenever the user wants to dig deeper than the numbers, mentions scuttlebutt, channel checks, talking to customers, site visits or short research, or asks whether a company's story is true.
---

# Field-Research Investing: an edge from firsthand evidence

This skill turns investigative, firsthand research into procedures, question sets, checklists and calculators. It treats a stock as a stake in a real group of people, products and places, and looks for facts that are true, material and not yet known to the market. Present findings as analysis and evidence; the decision stays with the user. Do not present the output as personalized financial or legal advice, and say so briefly when the user asks "should I buy?" or "is this legal?".

## The core model

1. **A company is people paid by customers.** A business is a team doing work that customers pay for. Its value moves when the flow of customer payments changes: more, less, sooner, later, or to someone else. So trace the payments physically: which person pays, to whom, for what, by what means, on what schedule, and why that person signs.
2. **Public data is necessary, rarely sufficient.** Ignoring filings can lose money. But what everyone can read is already in the price, and cleverer handling of the same data seldom wins. The edge comes from facts gathered firsthand.
3. **Three tests for any piece of information.** It must be *true* (not spin from someone paid to sell), *material* (it moves future payments or value; price statistics do not), and *exclusive* (not yet reflected in the price). If any test fails, take no position: holding cash is a legitimate result.
4. **Where firsthand facts live, in order of value:** (a) people: the company's own staff, its customers' buyers and users, its suppliers, advisers and other outsiders who deal with it; (b) product: its own, the inputs it consumes, competitors' products; (c) plant and periphery: the sites where work happens and everything around them that leaves visible traces.
5. **Customers before management.** Customers tell you whether payments will grow. Management is consulted last, once you know almost as much as they do and can bring them something useful.
6. **Things over words.** Documents, press releases and models are summaries of reality. Where you can, look, count, handle, listen and compare. A statement read on a screen can mean the opposite of the same words heard in person.
7. **Judgment beats technique.** Most money is made by holding a few deeply understood, excellent businesses for years, bought when a temporary problem makes them cheap. Event-driven trades are secondary and riskier. Choosing where to apply the skills matters more than the skills.
8. **Humility.** Field knowledge breeds overconfidence. Still read every filing (debt terms above all), remember that pride, loyalty and fear move people as much as money does, and never stake everything on one conclusion.

## Operating rules (apply to every task)

1. **Lawful and honest methods only.** No material non-public information (MNPI), no misrepresenting who you are, no paying or inducing anyone to breach a duty of confidence, no trespass, no covert tracking of individuals. Document how each fact was obtained. Read references/legal-ethics-guardrails.md before advising any tactic that involves observation, payments, recordings, options around events, or publishing a short thesis. If a source volunteers what looks like MNPI, stop, record it, do not trade, and tell the user to consult counsel.
2. **Professional information only about people.** Research roles, track records, incentives, public statements and professional networks. Do not compile home addresses, family details, health, or private-life material on anyone, and do not help photograph or follow private individuals.
3. **Source and date every fact.** Tag each item by tier: `filing/public`, `firsthand observation`, `interview` (role, date, how contacted), or `inference`. Never fill gaps from memory for prices, financials or events. Use web and filing tools when available and say which checks could not be run.
4. **Split the work honestly.** Do the desk research yourself when tools allow: filings, news searches, screens, maps, calculations. Prepare the field work the user (or people they hire) must do: calls, visits, purchases, counts. Then analyze the notes they bring back.
5. **Customer evidence before conviction.** Never call a stock a buy for field-research reasons until at least three key customers (more for a large position) have been heard firsthand.
6. **Confidentiality.** Advise the user to keep findings, sources and positions private: it protects sources, keeps future sources willing, and avoids handing the edge to others. Never pass gossip between a company and its customers.
7. **Label the operation.** Is this long-term ownership research (business quality) or a discontinuity bet (an expected event)? The second is shorter, riskier, taxed more heavily, and needs stricter legal care.

## Route the request

| The user wants... | Do this | Read |
|---|---|---|
| Ideas worth researching (neglected, cheap, turnaround, short candidates) | Workflow 1 | idea-generation.md; `scripts/screen_signals.py` |
| A due-diligence plan or deep dive on one company | Workflow 2 | research-plan.md, then the area files below |
| To prepare a conversation (customer, supplier, competitor, employee, management, local source) | Workflow 3 | interview-guides.md + customer-research.md / people-and-management.md |
| To judge customers, the buying process, or whether the business is worth owning | Workflow 2, step 4 | customer-research.md |
| To judge management, insiders, incentives, culture | Workflow 2, step 9 | people-and-management.md |
| To check suppliers, competitors, a commodity's supply and demand | Workflow 2, steps 5-6; Workflow 9 | suppliers-and-competitors.md |
| To examine the product, plan a site visit, map production | Workflow 2, steps 7-8 | product-and-operations.md |
| To test reported revenue or volume against physical counts | Workflow 4 | verification-and-red-flags.md; `scripts/field_math.py unitcount` |
| Help with a sudden drop, scandal, strike, debt crisis, suspected fraud | Workflow 5 | events-and-crises.md |
| To anticipate a takeover, restructuring, big contract or demand surge | Workflow 6 | events-and-crises.md, product-and-operations.md, relationship-mapping.md |
| A map of who is connected to whom | Workflow 7 | relationship-mapping.md; `scripts/relationship_map.py` |
| To turn notes into a decision, size it, plan selling and monitoring | Workflow 8 | decision-and-risk.md |
| A worked example of a pattern | Pick the matching pattern | case-patterns.md |
| "Is this tactic legal / ethical?" | Answer from the guardrails | legal-ethics-guardrails.md |

All paths are relative to this skill's folder: `references/`, `scripts/`, `assets/`.

**Load lightly.** Most tasks need two to four reference files, not all fourteen; the workflows below already carry the essentials. Read the files the row above names, open others only for a specific gap, and use each file's Contents list to read just the sections you need. A full research plan is usually covered by research-plan.md, customer-research.md, interview-guides.md and legal-ethics-guardrails.md.

---

## Workflow 1 — Find stocks worth investigating

1. **Pick the style the user is comfortable with:** deep value (cheap on assets, earnings, cash flow or yield); quality franchise (customers depend on it and cannot easily leave; fine to pay up, better when a transitory problem knocks it down); hypergrowth (ride it while growth lasts, exit in time); special situation (a sharp change is coming). The method favors quality businesses that became temporarily cheap, held until the momentum crowd wants them.
2. **First filter: neglect + cheapness + signs of re-emerging growth.** Neglect alone is not enough; many neglected stocks deserve it.
3. **Mine the sources** (details and phrase lists in idea-generation.md):
   - News text with warning phrases (shorts) or quiet-improvement phrases (longs): `python3 scripts/screen_signals.py text <files>`.
   - Industries starving their capacity (capital spending below depreciation for years) while demand firms up: `python3 scripts/screen_signals.py capacity <csv>`.
   - Transitory troubles: product transition gap, cyclical trough, accounting mess cleaned up by new management, a pay-only strike, a botched deal.
   - Change of control, new chief executive, activist or creeping-control filings, waves of insider buying.
   - Analyst behavior: a company pressuring an analyst to drop coverage (short lead); an analyst capitulating after a long slide (possible bottom).
   - Stocks trading below net cash that are cutting their burn (`python3 scripts/field_math.py runway ...`).
   - Industry insiders: "Which company in your field would you most like to own for good?"
4. **Output** a short list (3-10). For each: why it might be mispriced, which category, the one or two field questions that would settle it, and an initial "business worth owning?" view. Expect to discard most names; run two or three deep dives at a time.

## Workflow 2 — Research campaign on one company

1. **Gate the business.** Is this business worth doing at all (returns, cyclicality, control over costs)? Would you be content to own it indefinitely? Are its customers worth serving? Do you understand the product well enough? If not, stop, or treat it explicitly as an event trade. Smaller, focused companies are easier to research (fewer key people, products, customers).
2. **Build the public baseline, in detail.** Annual and quarterly reports, proxy (pay and option structure), insider transactions, ownership filings, debt agreements and covenants (and who holds the debt), customer concentration, legal proceedings, officer departures, auditor changes, permits, job postings, user-community sites. Never skip this: firsthand knowledge does not protect against a public fact you missed.
3. **Write the research brief** (`assets/research_brief_template.md`): the few tasks the company must get right now; 5-10 key questions; the key roles (names where public); planned sources; time budget; kill criteria. Expect to answer only about half the questions. If the questions turn out wrong, the digging will reveal the right ones quickly.
4. **Customers first** (customer-research.md): the four customer questions; the three buying roles (user, approver, payer) and whether one person holds all three; whether the benefit is personal to the buyer as well as organizational; sales-cycle length; retention through bad times; worthiness of the customers. Start with user groups and customer communities. At least three key customers before any conclusion.
5. **Competitors and defectors** (suppliers-and-competitors.md): competitors' product managers, customers who left, customers who switched in, then the company's answer, then the competitor's rebuttal. Triangulate.
6. **Suppliers and service providers:** capacity to meet growth, inputs that move one-for-one with units sold, suppliers for whom the company is a large share of business, bankers, auditors and lawyers.
7. **The product itself** (product-and-operations.md): buy it the way a customer would; record the purchase experience; examine build, packaging, shipping origin; compare with rivals.
8. **Sites and surroundings:** visit or tour (persistence usually earns a tour); sketch the production flow; identify bottlenecks and the costliest steps; ask what happens at +25%, +50%, +100% volume and in a slump; note what is visible from public places; capture impressions at once in an unstructured note.
9. **Management last** (people-and-management.md): lead with useful customer feedback; ask about their background, their plan, the people they rely on, the plan's weak points; ask for no forecasts and nothing unpublished. Read incentives (salary vs options vs open-market buying), group dynamics, congruence between words and manner.
10. **Synthesize and decide** (Workflow 8). Typical span: a few weeks to about three months per company, with several candidates in parallel.

## Workflow 3 — Prepare and debrief a conversation

1. Pick the guide in interview-guides.md for the source type; fill in the research brief's questions.
2. Write hypotheses about the person before contact (role, incentives, likely concerns) and plan how to test them in conversation.
3. Open honestly (who you are, that you are an investor researching the company or industry), then ask about *their* job and how the product fits it. Listen far more than you talk. Ask the sensitive question (why did you really buy it, who resisted) late, after trust exists. Ask for other people to speak with.
4. Never ask for unpublished financial results, forecasts, deal information or anything confidential. Redirect if offered.
5. Debrief immediately with `assets/interview_log_template.md`: facts, verbatim phrases, manner and congruence, new names, follow-ups, legal flags, three-test rating.

## Workflow 4 — Verify reported numbers with physical counts

1. Find a countable unit with a stable link to revenue: shipments, loaded trucks or containers, packaging units, shifts, cars in the staff lot, inbound inputs.
2. Establish conversion factors from public or legitimately obtained sources: units per load (spec sheets, legal axle limits, weigh-station rules), price per unit (price lists, an ordinary quote), operating days.
3. Design the sample: days and hours covered, observers (vetted, paid by the user, never trespassing), time-stamped logs, photographs only from public places.
4. Compute: `python3 scripts/field_math.py unitcount --counts ... --units-per-load ... --price ... --period-days ... --reported ...`. Report the range, not just the point estimate, and an upper bound using maximum load.
5. Cross-check inventory direction (warehouse filling or emptying) and other channels or sites before concluding.
6. If the gap is large: put a specific question in writing to the company; note whether the reply addresses the physical evidence or deflects (jargon, "follow guidance", attacks on the questioner). Deflection plus a large gap is a serious red flag (verification-and-red-flags.md).

## Workflow 5 — Triage a sudden drop or crisis

1. Rises usually come with a reason; unexplained falls deserve suspicion. Frame two hypotheses: **terminal** (sell or short) vs **transitory or unjustified** (buy). The first bad surprise is often not the last.
2. Reassuring company statements and brokers' "buy the dip" notes are not evidence; neither are healthy-looking ratios computed from the same reports.
3. When management and middle managers go quiet, go to the edges: rank-and-file staff, local business people, local press, creditors' public filings, trade contacts. In suspected fraud, prefer rank-and-file over supervisors (supervisors may report your interest upward).
4. Check the balance sheet and debt terms first: covenants and aggressive debt holders can transfer the equity to creditors.
5. Strikes and labor disputes: a pay-only dispute is usually transitory; a dispute about respect can explode beyond economic logic.
6. Decide with references/events-and-crises.md and Workflow 8. Physical-safety risk to the user is real in some places: say so.

## Workflow 6 — Watch for discontinuities

1. List the observable signals that would precede the event: for demand surges (overtime, extra shifts, full parking lots late, temporary storage, outside overflow vendors, production hiring, suppliers ramping); for takeovers (deal advisers' involvement, prior working relationships between the two companies' people, corporate-development activity); for distress (restructuring advisers, missed payments in creditors' filings).
2. Check each signal for lawful observability (public places, public records, voluntary conversations) before planning to watch it.
3. Set several watch plans; most never fire. When one fires, confirm with at least two independent sources before acting, and run the MNPI check in the guardrails.
4. Short-dated options magnify both the gain and the legal scrutiny; flag both.

## Workflow 7 — Relationship map

Build a map of the company's people, its customers' buyers, suppliers, advisers and competitors with professional links (shared former employers, schools, boards, deals). Use `python3 scripts/relationship_map.py nodes.csv edges.csv` (examples in `assets/`). Use it to spot likely acquirers (shared work history), competitive threats (a rival hires someone close to your company's key buyers), hubs and blind spots. Professional information only (relationship-mapping.md).

## Workflow 8 — From notes to decision

1. Rate each key finding on the three tests (true, material, exclusive) and on source tier. Discard what fails.
2. Write the story: what the market believes, what the evidence shows, why the gap exists (neglect, broker incentives, complexity, distance), and what will close it.
3. Run the trap checklist in decision-and-risk.md: debt and covenants, who holds the debt, top-of-the-pyramid technology, customers ecstatic rather than satisfied, insider buying under a charismatic leader, conflicts between user and approver, pride after a past mistake.
4. Decide: buy, add, hold, trim, sell, short, or no position (cash). Size with humility: never a position whose failure would ruin the user.
5. Set the monitoring plan (which sources, how often) and the selling rules (scale out as the gain grows large and the price stops looking cheap; sell when the evidence turns; be wary when the story reaches mass media).
6. Use `assets/decision_memo_template.md`.

## Workflow 9 — Commodity or industry imbalance

Build a physical balance: every material producer and consumer, current and planned capacity, inventories; audit a random sample of entries in person or through primary sources; track proxy inputs that move with consumption; test demand elasticity (if the input is a small share of the user's cost, a price jump barely dents demand: `python3 scripts/field_math.py costshare ...`). Details in suppliers-and-competitors.md.

---

## Output templates

**Research brief** → `assets/research_brief_template.md`. **Interview log** → `assets/interview_log_template.md`. **Decision memo** → `assets/decision_memo_template.md`.

Single-company summary, when the user wants it in chat:

```
# <Company> (<ticker>) — field-research view, as of <date>
Operation: long-term ownership | event bet (what event)    Status: idea | in research | decided
Bottom line: <one or two sentences: what the evidence says and the decision it supports>

## What the market believes vs what the evidence shows
## Evidence table  (finding | source tier | date | true? material? exclusive?)
## Customers and buying process
## People and incentives
## Product, operations, physical checks
## Risks, traps and red flags (incl. debt terms)
## Decision, sizing logic, monitoring and exit plan
## Open questions and next field steps (who does what)
Sources: <filings, interviews by role and date, observations>. Analysis of the evidence above; not personalized financial or legal advice.
```

Keep prose tight, put evidence in tables, and mark anything beyond the core method as `modern equivalent` or `my judgment`.

## Quick reference

- Hear at least 3 key customers before any field-based buy; more for a big position.
- Research brief: 5-10 questions; answering about half is normal.
- Persistence earns a site tour most of the time; deep questions about operations raise suspicion, so explain your purpose and offer references.
- Researching a company's customers usually prompts the company to call you; silence can mean management is heads-down on a turnaround.
- Management avoiding investors is not necessarily bad (focused, busy, or buying stock themselves); heavy promotion is a reason to cool off.
- Companies that generate cash and never issue stock get little broker coverage: a source of neglect and opportunity.
- Selling to committees of clerks is slow and weak; selling to one person who uses, approves and pays, and who gains personally, is the strongest position.
- Customers should be satisfied, not ecstatic: ecstasy can mean the vendor is doing them a favor in a shrinking niche.
- A stock below net cash whose burn is stopping can re-rate well above its cash; acquirers who were waiting for desperation must move.
- Exclusive information may take a year or two to reach the price; a flat portfolio in the meantime is normal.
- Few businesses deserve long-term ownership; aim for a handful of great decisions, not constant activity.
- Debt always gets repaid, if not by the borrower then by the lender through a loss: in doubt about a cheap stock with debt, stay out.

## Reference files (load only what the task needs)

Each file opens with a Contents list; read the sections you need.

- `references/core-principles.md`: the philosophy, the three tests, information vs symbols, edge, concentration, holding period, humility.
- `references/idea-generation.md`: categories, why good companies get cheap, neglect/cheapness/growth filter, text and numeric screens, cyclicals, net-cash stocks, gossip.
- `references/research-plan.md`: gating, public baseline checklist (with modern sources), the research brief, prioritizing people, delegation, time budget.
- `references/customer-research.md`: the four questions, buying roles, ideal and near-ideal customers, worthiness, sales cycle, conflicts, customer calls.
- `references/people-and-management.md`: motivation and incentives, insider buying, background, group dynamics, site observation, reading congruence, meeting management.
- `references/suppliers-and-competitors.md`: supplier signals, service providers, the competitor triangulation loop, commodity balances.
- `references/product-and-operations.md`: sample purchase, product examination, site tour, production map, bottlenecks, surge and slump signals.
- `references/verification-and-red-flags.md`: physical counting, reconciliation, company response patterns, accounting and behavior red flags.
- `references/events-and-crises.md`: sudden drops, fraud, workouts, strikes, takeovers, confirming public clues.
- `references/relationship-mapping.md`: building and using the map, the investigation room.
- `references/decision-and-risk.md`: decision rules, traps, sizing, selling, monitoring, mistakes.
- `references/interview-guides.md`: ready question sets for every source type.
- `references/legal-ethics-guardrails.md`: the legal lines, compliant alternatives to risky tactics, documentation.
- `references/case-patterns.md`: anonymized worked patterns and their lessons.

Scripts (standard-library Python 3; `--help` on each): `scripts/field_math.py` (unitcount, runway, capacity, costshare), `scripts/screen_signals.py` (text, capacity), `scripts/relationship_map.py`. Templates and example CSVs are in `assets/`.
