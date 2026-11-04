## Alerts

**Status: approved by me, Nov. 3, 2026: the map, the levels, what I do at each, and the decisions below.** **Running since Nov. 4, 2026, as Desktop tasks on this computer: the daily run, `event-run` on weekdays at 8:30 and `monthly-hunt` on the 15th.** **Since Nov. 4, 2026, a Red goes to my phone through Telegram, as the last step of the run that wrote it (`phone.html`).** An Orange or an Info waits in the Journal until I open it or the run's session. Nothing else sends an alert. Page: `alerts.html`. Test: `sensors/alerts/`.

**Over two years on Corning, the map gives 0 Reds that count, 27 Oranges and 401 Info items (calc.). Today's sensors would surface 12 of the 27. The other 15 came from news and calls no sensor reads (calc.).** So the first thing to fix before automating is the news gap, not the levels.

### The three levels

| Level | When | Goes out | What I do |
|---|---|---|---|
| **Red** | A kill line is hit or the thesis breaks. | At once | **The same day:** read the source myself. Add nothing to that position or its group. Then rule whether the claim still holds, and why. If it is broken, reassess the whole position, whatever the price is doing. |
| **Orange** | The thesis moves, or the price enters a buy or trim zone, or a limit breaks. | Journal, next time I open it | **Within a week, and before any decision on that stock:** read it and say whether a claim moved, and which way. A chance or grade may change only on this dated event. A buy-below hit: refresh value and run the three gates (`Rules/cash.md`). A trim-above hit: read `Rules/when-to-trim.md`. A limit broken: add nothing. |
| **Info** | Everything else worth a line. | Daily brief, only on a day with something new | **Nothing is required.** Skim or skip. Info can never change a chance, a grade or a size. |

**On every level:**

- An alert states the condition, the source and the date. It gives no recommendation (`Rules/recommendations.md`). If I then want to act, the coach goes first.
- **No alert sells anything.** A Red opens a review. Selling stays with `when-to-trim` and a broken thesis.
- **When I rule on a Red or an Orange, the session adds one line to the Journal:** `- Ruled: <day> <rule ID>. <my words>`, where `<day>` is the alert's Journal day as YYYY-MM-DD. Until that line is there, the alert shows as waiting on the board's Home. A second alert with the same day and rule needs its own line.
- **With no holding, a Red only reopens the draft.** Corning today is no position and a draft thesis, so that is all it could do.
- **One event, one alert.** A filing and its exhibit are one event, and so are a deal in the news and the same deal in a later filing, unless the filing adds a fact.
- **One alert per crossing.** A line stays crossed without a repeat. It re-arms only after it clears.
- **Never an alert:** a price move alone (`Rules/monitoring.md`), or a source's age alone. **Never anywhere:** a possible inside tip. It stays out of every level, and I am told to ask a lawyer.

### The map

| ID | Signal | Condition | Level | Who reads it today |
|---|---|---|---|---|
| R1 | Kill lines K1 to K9 | A line is crossed, on its own wording and test date. | Red | A person. Sensors only say a filing came. The event run reads a graph company's Item 1.01 or 1.02 against the lines. |
| R2 | Thesis claims C1 to C8 | A dated fact contradicts a claim the thesis rests on. Claude says it appears broken. I rule. | Red | A person. The event run on a graph company's Item 1.01 or 1.02. |
| R3 | 8-K items 1.03, 2.04, 2.06, 3.01, 4.02, 5.01, or 1.02 with no 1.01 | Presumed Red until read. I can drop it to Orange by ruling. | Red | 8-K watcher for Corning. Event run for 1.02 with no 1.01 from the graph's other US filers. |
| R4 | Shared exposures | One event crosses a kill line in one position and a line or load-bearing claim in another. One alert, naming them all. | Red | Nothing yet. No position is on file. |
| O1 | K3, K8, K9 | One step short of a two-quarter line: one quarter at or below K3's line, or one fall on K8 or K9, outside Q1. | Orange | A person |
| O2 | Thesis claims C1 to C8 | A dated fact from a filing, release, call or customer could change a claim, a chance or a grade, in either direction. | Orange | A person. The event run on a graph company's Item 1.01 or 1.02. |
| O3 | 8-K 3.02, an 8.01 share program, a 424B5 for new shares | New shares become possible. This is K6's starting point. | Orange | 8-K watcher, radar |
| O4 | Buy-below | A close falls under it. Once per crossing. It re-arms only after a close back above. | Orange | By hand. No sensor compares them. |
| O5 | Trim-above | A rise takes the close above it, on a position I hold. Once per crossing. | Orange | By hand. No sensor compares them. |
| O6 | Buy-below and trim-above | A refresh moves a line across the price, with no price move. | Orange | A person, after a refresh |
| O7 | Sizing limit | A position or group is over 5% at a refresh. Add nothing. It never forces a sale. | Orange | portfolio-manager script, when run |
| O8 | Cash and counts | Cash under the 5% floor at a refresh. Cash above 50% for 24 months. More than 20 positions. | Orange | portfolio-manager script, when run |
| O9 | Method triggers | Aaa moves a point from 6.12%. Segments are recast. Core changes. A 10-K/A or 10-Q/A. A late-filing notice. | Orange | A person |
| O10 | SEC letters | A staff letter opens a thread, or tells the company to change something. Later letters in a thread and a closing letter are Info. | Orange | Radar lists them as plain filings. Nothing reads them. |
| O11 | 8-K item 5.02 | CEO, CFO or COO arrives or leaves. A director change is Info after reading. | Orange | 8-K watcher |
| O12 | Ownership | A Schedule 13D. An officer or director buys on the open market. A holder named in a catalyst note exits. | Orange | Radar |
| O13 | Catalyst dates | A stated date passes with no Outcome written, or a stated date moves. | Orange | Radar |
| O14 | Shared exposures and grades | A dated event calls for a new group or a new grade. Claude proposes. I rule. | Orange | A person |
| O15 | A claim with no kill line | The same claim goes against us on three reports running. I decide if it needs a line. | Orange | A person |
| O16 | The system itself | A sensor fails, or a results date is three trading days past with no reading on file. | Orange | A run's own failure line in the Journal. Since Nov. 4, 2026, every screen of the board also shows what the Daily run's newest digest says about a failed sensor or a missing brief, with no level and off the waiting list. Nothing notices a run that did not happen. |
| I1 | 8-K item 2.02, read, no claim moved | Results are in. Each kill line's reading is listed. | Info | 8-K watcher, then a person |
| I2 | Routine 8-K items | A 7.01 conference notice, 5.07 votes, 5.03, 9.01, a routine 1.01 credit line, a director under 5.02. | Info | 8-K watcher. Event run for a routine 1.01. |
| I3 | 10-Q, 10-K | The filing came, and the refresh is done or due. Old and new base value, buy-below and trim-above. | Info | Radar, then the valuation skill |
| I4 | Forms 3, 4, 144 | One line a day: how many forms, how many sales. No line for each form. | Info | Radar |
| I5 | 13G, proxy, 11-K, SD, shelf, Form 25, CORRESP | Listed once. | Info | EDGAR list |
| I6 | Catalyst dates | Once on entering the 90-day horizon, and again at 7 days. Not every day. | Info | Radar |
| I7 | Radar screen leads | A count and a link. A lead is never a pick. | Info | Radar. The monthly hunt tests the top five, and writes any idea to `Inbox/`, not as an alert. |
| I8 | Radar graph walks | Which notes an event touches. A link does not mean the event reaches that company. | Info | Radar. Event run, for each thesis or paper holding reached. |
| I9 | Where the price stands | Last close, its date and the two lines. No change and no percent move. | Info | Saved close |
| I10 | Where the book stands | Names against bets, cash level and room under the limit, at a refresh. | Info | portfolio-manager script, when run |
| I11 | K8, K9 lone Q1 fall; K1, K4, K5 before their test | A reading only. | Info | A person |
| I12 | Source ages | How old each saved source is, and which sensors ran. | Info | Dashboard |

**8-K items:** the first-pass level for every item, and what reading does to it, are on `alerts.html`. A first pass is what an item number says before anyone opens the filing. Reading can lower or raise it, and the note says who did.

### The test: Corning, Nov. 3, 2024 to Nov. 2, 2026

**Read this first: it is a test with hindsight.** The thesis and the kill lines were written on Nov. 3, 2026, so no line existed during these two years. The levels on events are my reading, knowing how things turned out. No position was held. Each event, with its source and date, is on `alerts.html`.

| Level | Count (calc.) | Made up of |
|---|---|---|
| **Red** | **0** that count | No line was crossed on a fair reading. Run back as written, K3 gives 1, a false one. No Red 8-K item was filed. |
| **Orange** | **27** | 9 8-Ks, 2 SEC letters, 1 catalyst date, and 15 facts from news or calls. About 1.1 a month, and 19 of the 27 fell in 2026 (calc.). |
| **Info** | **401** | 378 filings, 13 8-Ks and 10 news items read and dropped, on 148 days in the two years (calc.). |
| Price, sizing, cash, shared | **0** | The close stayed above both lines, with a low of $39.07. No position or group was on file. |

**Where it would have been noisy:**

- **Insider forms.** 344 of 403 filings are Forms 3, 4 or 144, or 85% (calc., [EDGAR filing list, retrieved Nov. 2, 2026](https://data.sec.gov/submissions/CIK0000024741.json)). 64 of the Forms 4 report a sale, and none a purchase on the market (calc.). As Oranges, the sales alone would have more than tripled the count. So they are Info, in one line.
- **8-K items alone.** My flag list marks 21 of 22 8-Ks, so it sorts nothing (calc.). 7 of the 22 are conference notices. The proposed first pass gives 14 Oranges, and reading drops 5: two director changes, a replaced credit line, and two quiet results days (calc.).
- **K3 run back.** The line sits at the level of 2025, so all five reports from Q4 2024 to Q4 2025 read as crossed, with Optical margin from 14.0% to 17.9% (calc., [Q4 release, Jan. 29, 2025](https://www.sec.gov/Archives/edgar/data/24741/000162828025002912/glw-20241231xex99xq42024.htm); [Q1 release, Apr. 28, 2026](https://www.sec.gov/Archives/edgar/data/24741/000002474126000198/glw-20260328xex991xq12026.htm)). That is an effect of setting the line in hindsight. It can first fire on Q1 2027.
- **Q1 falls.** Optical sales fell in Q1 2025, $1,368M to $1,355M ([Q1 release, Apr. 29, 2025](https://www.sec.gov/Archives/edgar/data/24741/000162828025020470/glw-20250429xex991.htm)), and Q1 fell in 7 of 9 years (calc., `Research/2026-11-03 Corning kill criteria.md`). K9 fell in 5 of 9 Q1s from 2018 to 2026 (calc., [SEC company facts, Meta](https://data.sec.gov/api/xbrl/companyfacts/CIK0001326801.json), [Amazon](https://data.sec.gov/api/xbrl/companyfacts/CIK0001018724.json) and [Microsoft](https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json), saved Nov. 3, 2026). So a lone Q1 fall is Info.
- **News.** Of 25 news facts in the vault, I would drop 10 after reading (calc.). The real figure would be worse, because the vault holds only what we kept.
- **Dates and leads.** The radar lists 17 catalyst dates and 117 leads on each run (`sensors/radar/runs/2026-11-03-03.json`, Nov. 3, 2026). Repeated every day, they would bury the rest, so they appear on a change only.

**Where it would have missed something:**

- **Most deals.** For the six deals since Nov. 2025, the first Corning filing naming the customer came the same day for NVIDIA, 1 day later for Meta, 28 for AT&T, 49 for Verizon and 50 for Amazon. Zayo was unnamed after 74 days (calc., `Companies/Corning.md`). No sensor reads news, customers' releases or calls.
- **K2, K7 and K9 rest on a person.** Nothing reads a call or a customer's cash flow statement.
- **SEC letters.** Staff told Corning to remove the adjustment behind most of the gap to core ([SEC staff letter, Feb. 26, 2026](https://www.sec.gov/Archives/edgar/data/24741/000000000026002022/filename1.pdf)). We counted that letter and did not read it, until a later check caught it (`Lessons/Read the SEC letters before explaining a change.md`). The radar lists such letters unread. They also come late: SEC releases them no earlier than 20 business days after a review ends ([SEC filing review page, undated, retrieved Nov. 3, 2026](https://www.sec.gov/files/divisions/corpfin/cffilingreview.htm)). This review closed on Apr. 27, 2026 ([SEC staff letter, Apr. 27, 2026](https://www.sec.gov/Archives/edgar/data/24741/000000000026004267/filename1.pdf)), after core changed on Apr. 1, 2026 ([Q3 release, Oct. 27, 2026](https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm)). So O10 explains a change. It cannot warn of one.
- **Investor events.** Only the notice is filed. It is Info, and the plan change happens on a webcast ([8-K, filed Mar. 17, 2025](https://www.sec.gov/Archives/edgar/data/24741/000120677425000133/glw4455141-8k.htm); [8-K, filed May 13, 2025](https://www.sec.gov/Archives/edgar/data/24741/000120677425000358/glw4484671-8k.htm)).
- **A claim wearing away.** Solar slipped in three reports running: "running behind" ([Q1 call, Apr. 28, 2026, third-party transcript](https://www.fool.com/earnings/call-transcripts/2026/04/28/corning-glw-q1-2026-earnings-transcript/)), a wafer plant shutdown ([Q2 release, July 28, 2026](https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000253/glw-20260728xex99xq22026.htm)) and "a slower pace than anticipated" ([Q3 release, Oct. 27, 2026](https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm)). C6 has no kill line, so a slow slip never reaches Red. O15 is there for this. A dated fact that contradicts C6 outright is still Red, under R2.
- **The price, on purpose.** The close went from $255.69 on June 29, 2026 to $123.20 on Nov. 2, down 52% (calc., [Yahoo through yfinance, fetched Nov. 2, 2026](https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d)). The map says nothing about that, as rule 6 asks. Line I9 still shows where the price stands against the lines.

**What the test cannot show:**

- **Red, in a downturn.** K8 and K9 never fell two quarters running in these two years. Outside the window K8 fired on Q4 2019 and Q1 2023, and K9 on Q1 2023. Both times K8 fired, Optical sales passed the starting figure seven quarters later (calc., `Research/2026-11-03 Corning kill criteria.md`). So a fire opens a review. It does not prove a break.
- **Price alerts.** The closes stayed above both of today's lines, $28.97 and $36.06, all window. The last close under them was Dec. 6, 2023 and May 29, 2024 (calc., same Yahoo file; lines, `sensors/valuation/runs/2026-11-03-01.md`, Nov. 3, 2026). Past lines were not rebuilt.
- **Sizing and cash.** Only as a drill on a made-up $5,000 position that the gates would have barred: one Orange at the Aug. 1, 2025 refresh, at 5.02% (calc., `alerts.html`).
- **Item-based Reds.** None in the window. Across 279 8-Ks since Oct. 2004, three would fire: impairments in 2004 and 2005, and a restatement in 2006 (calc., [8-K, Oct. 7, 2004](https://www.sec.gov/Archives/edgar/data/24741/000002474104000467/form8k.txt); [8-K, Sept. 21, 2005](https://www.sec.gov/Archives/edgar/data/24741/000002474105000549/sept218k.txt); [8-K, Apr. 25, 2006](https://www.sec.gov/Archives/edgar/data/24741/000002474106000199/q1068k.txt)).

### What I decided, Nov. 3, 2026

1. **Red before I own anything: yes.** With nothing held, a Red only reopens the draft. This replaces my decision of Nov. 2, 2026 on no red level for now.
2. **Red items:** 1.03, 2.04, 2.06, 3.01, 4.02, 5.01, and 1.02 with no 1.01, as in R3. This closes what I left open on Nov. 2, 2026. They would have fired about once in seven years here (calc.), and last in 2006.
3. **A lone Q1 fall on K8 or K9 is Info.** The lines stay as set. Only the Orange step before them changes. Without this, the test adds 1 Orange (calc.).
4. **The news gap:** a weekly web search for each company with a thesis, by the `Playbooks/` rules, with results read before any Orange goes out. Not set up yet.
5. **SEC letters:** I approved adding UPLOAD to the radar's list, on a wrong premise. The radar already lists them, so nothing is added (`Lessons/Read a sensor's code before saying what it skips.md`). What they need is a reading, as in O10.
6. **C6 gets a kill line on Solar's segment result.** Its threshold and date are not set, so there is no line yet.
7. **No schedule for the Yahoo close, for now.** My Nov. 3 decision stands: by hand, at most once a day. So O4 and O5 compare only when someone saves a close, and a crossing between those days can go unseen.

**What changed, Nov. 3, 2026:** one line in `CLAUDE.md` loads this file. Nothing was automated then, and Claude applied the map only in a session. The code came as a separate step. `dashboard/test_dashboard.py` bars alerts on price, so it would need changing if the dashboard shows O4 or O5. `rules.md`, `my-rules.md`, the kill lines and the 8-K watcher's ratings did not change. Changing the method needs my approval. The levels on past events stay Claude's reading.

### What I decided, Nov. 4, 2026

1. **The event run's trigger is Item 1.01 and Item 1.02 from any US company in the graph.** A customer ending a deal is kill line K2. Items 7.01 and 8.01 stay out, so a deal filed under them raises nothing from this run: T1's wafer deal with Corning came under 8.01 ([8-K, filed Aug. 15, 2025](https://www.sec.gov/Archives/edgar/data/1992243/000121390025077036/ea0253426-8k_t1energy.htm)).
2. **R3's Red holds for those filers too.** A 1.02 with no 1.01 from any of them stays Red until I drop it, even if it says nothing on a claim. Three filings in two years would have fired, and none ended a deal with Corning (calc., `sensors/hunt/samples/two-years-102.json`).
3. **The monthly hunt only proposes rejections.** I add them to `Research/Rejection log.md` myself.
4. **Red goes to my phone through Telegram, and nothing else.** Each one once. Orange and Info stay in the Journal.
5. **No extra script for presumed Reds.** With Desktop closed or the computer off, there is no run, so no Red is written and none is sent.

**What changed, Nov. 4, 2026:** the map's levels and conditions did not change. Only "who reads it today" and the status line did. Prompts: `Playbooks/Event run.md` and `Playbooks/Monthly hunt.md`. Page: `hunt-events.html`. **Claude's reading in the event run's prompt, for me to correct:** a level comes from what the filing says about a claim, not from how near the link is.

**What changed for the phone, Nov. 4, 2026:** the status line and Orange's "Goes out" cell. The map's levels and conditions did not change, and neither did what I do at each level. Script: `sensors/phone/phone.py`. My test message arrived and `phone.py check` passed, my report. No real Red has gone out yet.

**It does not say:** that Corning's thesis is sound or broken, or that 27 is the right number of Oranges. Corning stays no buy.
