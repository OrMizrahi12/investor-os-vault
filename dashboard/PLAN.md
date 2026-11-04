# Control board: plan

*Approved by me, Nov. 4, 2026. Steps 0 to 6 built Nov. 4, 2026, step 4 before step 3 at your request. **This is version 1 of the board.** Wireframes: `board-plan.html`. Home on two days: `board-home.html`. Session: `Journal/2026-11-04.md`. In this file "you" is me, the owner, and "I" is Claude.*

**Settled by building step 6, Nov. 4, 2026:** one part draws at a time, by a row of choices, because What we decided and What we left open run over 460 rows each (calc., `data.journal_view`, Nov. 4, 2026). Session folds are plain markup, not Streamlit's, so a heading can hold a digit with its source beside it and opening one asks nothing of the server. A local file cannot be a link, so a Lesson folds open to its words, and its path stays beside its title. Each Journal block or row names its file and day as its source. A figure in one is what the file said that day, and the page says so. **My choices, for you to correct:** the newest session comes first in a day, and no Journal line carries the Company page's "no dated source" tag, because an entry is never rewritten and the tag could never be filled.

**Settled by building, Nov. 4, 2026:** `AppTest` handles `st.navigation` if each screen is a file, so they are in `screens/`. Live Streamlit loads in headless Chrome when driven over its debugging port (`tools/chrome.py`). Home's row limits are 5 waiting, 7 coming up, 3 Info and 5 where things stand (`view.py`). Home needs 572 px on the busiest day, against the 650 px estimate (calc., `tools/measure_home.py`). The figure test covers Home and every Company page, and the other screens when their steps convert them. The `Ruled:` line is not in `Rules/alerts.md` until you type it.

**One read-only local app with five screens, built from the Streamlit dashboard we already have. Most of the data is already saved. What is new is the order on the page, the morning view, a page that works for any company, and a way to read the Journal.**

## Context

`dashboard/app.py` is one long page with nine panels, in the order they were built. Three of them work only for Corning. It answers "what is saved?", not "what needs me this morning?". `Rules/alerts.md` asks me to act on a Red the same day and an Orange within a week, and nothing shows what is still waiting.

**What exists today (read Nov. 4, 2026):**

- **Dashboard:** Streamlit 1.66.1, with `app.py`, `data.py`, `view.py` and `health.py`. 93 tests, 1 failing: `test_the_real_saved_run_is_read_and_draws`, because it assumes the newest radar run has events.
- **Companies:** 24 notes. Only Corning has a valuation run, kill lines and a saved price. The others say "base value: not defined yet".
- **Portfolio:** no real holdings or cash on file. The paper note has $100,000 and no positions.
- **Alerts:** 0 Red, Orange or Info lines in the Journal so far. The daily run last left a record on Nov. 3. The event run, monthly hunt, weekly check and quarterly refresh have left none.
- **Journal:** 3 daily files, the longest 2,691 lines (`Journal/2026-11-03.md`), and 2 coach decision files.

**Settled by building step 4, Nov. 4, 2026:** the address takes a ticker or a note's name, and with neither it lists the notes and assumes no company. Catalysts come from `Catalysts/`, not the radar run, because a run holds only counts for later and undated notes. A local file cannot be a link from a browser, so History shows paths. The Watchlist moved to the list at `/company`, so one company's close never shows on another's page. A running Streamlit keeps the `data.py` and `view.py` it first imported, so `tools/look_company.py` starts its own board. Figures inside a chart are checked only as far as each chart having a dated source above it.

**Settled by building step 3, Nov. 4, 2026:** your request set the order on the screen: pipeline, rejection log, then alerts, with jump links at the top. The stages come from what the files say, nine on the path and Rejected off it. Each company sits at one, its newest dated step, and on the same day the furthest. So Corning sits at Decision and is still a row in the log, which says so. The 23 other notes sit at "On the map", since no gate result is on file for them. Screen rows now live in the pipeline, not in the radar panel. The real Journal holds no alert line yet, so the filters were driven on a labelled busy copy.

**Settled by building step 5, and the work on trust, Nov. 4, 2026:** the figure test now covers all five screens and every Company page, headings and folded-section labels too, so counts left the headings and sit in a sourced line. Fixed words may hold names and dates, and any other digit needs a dated source. Anything missing must say what would fill it, and a test checks that. Your age limits are in `age_limits.toml`, approved Nov. 4, 2026. Past one, the board says so in words, in the same look, and it stays no alert. Home's Where things stand counts lines, not rows, so a day of old sources still fits: 649 px on a made-up worst day, against the 650 px estimate (calc., `tools/measure_home.py`). **My choice, for you to correct:** every screen also shows what the Daily run's newest digest says about a failed sensor or a missing brief. It is read from `sensors/daily/runs/`, it holds no level, and it is not on the waiting list. The break on a test copy is why (`Lessons/Break a sensor before trusting a quiet board.md`). `tools/broken_copy.py` runs that break.

## My two rulings, Nov. 4, 2026

1. **Company page shows status and thesis, labelled.** This replaces your Nov. 3 decision, "No status or thesis on the dashboard yet" (`Journal/2026-11-03.md`). The Journal entry will say so.
2. **A `Ruled:` line in the Journal decides what is still waiting.** The board writes nothing. Sessions write the line when you rule.

## The rules every screen follows

| Rule | How it is held |
|---|---|
| **Read-only** | No orders, no broker, no fetch, no writes. No button starts a sensor. The existing test bans network imports and write calls, and it extends to every new file. |
| **No advice** | No action, size, grade, score or "what to do". `VIEW_WORDS` and `ALERT_WORDS` stay as they are. The price-against-value panel stays the only exception. |
| **Source and date on every figure** | One new helper, `view.fig(value, source, date)`. A test fails any tile or table figure with no source and date on it or on its table. A source is a link, a vault file path, or "calc." with its inputs. |
| **Unknown stays unknown** | A missing file shows "Not on file" and what would fill it. There is no fallback figure. |
| **Old sources in words** | Past your limit in `age_limits.toml`, the board says how old, with no colour and no level. A test holds the values. A source's age alone stays no alert. |
| **Raises nothing new** | The board shows what routines wrote. It never compares a close to a line, so O4 and O5 stay by hand. |
| **Real and paper never mix** | They are separate blocks, and paper always carries its label. |
| **Stays local** | Stays on 127.0.0.1, because it holds Yahoo and Moody's data. |

## The five screens

### 1. Home: the morning

Answers "does anything need me today?" on one laptop screen, with no scrolling. The target is a 1366 × 768 laptop, which leaves about 650 px of page height inside the browser (my estimate; step 2 measures it).

```
+------------------------------+---------------------------+
| WAITING FOR ME               | COMING UP                 |
|                              | nearest date first        |
+------------------------------+---------------------------+
| SINCE THE LAST BRIEF         | WHERE THINGS STAND        |
+------------------------------+---------------------------+
| ROUTINES: one line                                       |
+----------------------------------------------------------+
```

- **Waiting for me:** Reds first, then Oranges, oldest first, each with no `Ruled:` line. One line each: level, rule, date, days since, source. The level's heading gives what `Rules/alerts.md` asks. If none: "Nothing waiting."
- **Since the last brief:** the brief's "Since" sentence and its Info lines.
- **Coming up:** catalyst dates within the radar's 90-day horizon and the kill lines that can fire on the next report, together, nearest first. Kill-line report dates are labelled estimates, as the calendar labels them. **It always sits above Where things stand,** as you asked.
- **Where things stand:** real holdings (none on file), paper cash and level, names against bets, and for each company with a saved value run its last close, date and two lines, with no verdict (I9).
- **Routines:** one line, the last record of each of the five and any failed line. No colour by age. It says plainly that a run that did not happen leaves no line.

**What fitting one screen costs:**

| Block | Rows shown (to tune in step 2) | The rest |
|---|---|---|
| Waiting for me | 5 | "And 2 more: 1 Red, 1 Orange", linked to Ideas and alerts |
| Since the last brief | 1 sentence, 3 Info lines | "And N more", linked to the Journal |
| Coming up | 5 | "And N more". The Nov. 3 radar run alone has 10 dates in its horizon, so this limit applies from day one (`sensors/radar/runs/2026-11-03-04.json`, Nov. 3, 2026) |
| Where things stand | 4 | "And N more", linked to Portfolio and cash, or the Company page |

- **A Red is never dropped silently.** Reds come first, and the count below the list always names how many Reds and Oranges are not shown.
- **No folded sections on Home,** because opening one would make the page scroll. Guardrail stops and source ages move to Ideas and alerts.
- **Source and date stay on every figure,** in small type on the same line. Long text is cut with an ellipsis, and the full line is on the linked screen.
- **Below laptop width,** the blocks stack in the same order and the page scrolls. One screen holds for laptops and wider.

| Reads | |
|---|---|
| `Journal/*.md` | Alerts, briefs, routine records, `Ruled:` lines |
| `sensors/radar/runs/` newest | Dates |
| `Research/* kill criteria.md` | Calendar of checks |
| `Portfolio/*.md` | Cash, positions |
| `sensors/valuation/runs/` newest, `sensors/prices/cache/` | I9 |

**Have:** `journal_alerts`, `routine_table`, `radar_dates_table`, `paper_portfolio`, `last_price`.
**New:** the screen and its compact layout, trimming Streamlit's page padding, row limits with their counts, the brief reader, `Ruled:` matching, the waiting list, the calendar reader.

### 2. Company page

One page for any of the 24 notes, chosen from a list, with its own address (`?company=GLW`).

- **Top:** name, ticker, status word, last checked.
- **Thesis:** the note's Thesis section, word for word.
- **Draft, not approved:** claims C1 to C8, the kill-line table and the calendar, each as written with its date. This fixed label cannot be turned off.
- **Price against value:** the existing panel. The last saved close sits beside it, each with its own date, since they can differ: the run uses $123.20 of Nov. 2, and the newest saved close is $126.14 of Nov. 3 ([Yahoo through yfinance, fetched Nov. 3, 2026](https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d)).
- **Financial health, earnings yield:** the existing Corning panels.
- **Catalysts, filings, links:** this company's rows only.
- **History:** decision files, and Journal and Lessons mentions, as links by date.
- **The other 23 companies:** each panel says "Not on file", and the note's own sections still show.

| Reads | |
|---|---|
| `Companies/<name>.md` | Status, thesis, links, health |
| `Research/* <name> kill criteria.md`, `* thesis draft.md` | Draft claims, lines |
| `sensors/valuation/runs/`, `sensors/radar/runs/` newest | Value, dates |
| `Inbox/*.md`, `sensors/prices/cache/` | Filings, close |
| `Journal/`, `Lessons/` | Mentions |

**Have:** `latest_valuation` and its panel, `health.py` and its charts, `yield_view`, `filings_table`, `_note_table`.
**New:** the picker, the note section reader, the kill-line reader, filters by company, mentions. Run the note's text through the existing escape. Add the copied text to the word test's leave-outs, as radar and Inbox text already are.

A fixed line at the top: "About to decide? The coach comes first." `Rules/recommendations.md` wants your view before you see anything on the stock, and a page can't know you are about to decide.

### 3. Portfolio and cash

- **Real, first:** "No real holdings or cash on file" until a real note exists.
- **Paper, labelled:** cash, share, level on `Rules/cash.md`, positions, last checked, and cash above 50% since when, with months so far out of 24.
- **Positions:** shares, date, cost, last close and its date, value today, share of the portfolio, link to the thesis note.
- **Changes log:** the note's own table.
- **Room under the 5% limit and names against bets:** "Not on file" until a saved run of `pm.py` exists. There are no positions today, so nothing is lost. The board shows those fields only, never the script's action or size.

**Reads:** `Portfolio/*.md`, `sensors/prices/cache/`, later a saved `pm.py` output.
**Have:** `paper_portfolio`, `cash_level`, the three paper tables, `last_price`.
**New:** the screen, the real/paper split, and prices. **One fix:** the panel counts positions at cost, but `Rules/cash.md` says stocks at today's prices. A position with no saved close shows its share as "Unknown", and so does the cash share, rather than falling back to cost.

### 4. Ideas and alerts

**Alerts:**
- Every line the routines wrote, by level, filterable by level, rule, routine and date.
- Each shows waiting or ruled, with your ruling's words.
- Also the routine table, the guardrail record and the source ages table, all in full.

**Ideas, in funnel order. Every lead is labelled "a lead to read, never a pick":**
- Radar: events, graph walks, screen leads.
- Hunt: idea notes in `Inbox/`, funnel reports, and proposed rejections waiting for you.
- Rejection log, with its look-again dates.

**Reads:** `Journal/*.md`, `Inbox/`, `sensors/radar/runs/` newest, `Research/` hunt reports, `Research/Rejection log.md`, `.claude/guardrails/blocked.jsonl`.
**Have:** the whole Alerts panel, the whole radar panel, `filings_table`, `sources_table`.
**New:** filters, ruled state, idea note reader, hunt report reader, rejection log table. The hunt has not run, so I read its real file names at build time. Until then it says "No run on file".

### 5. Journal

- **By day:** a day list, then each session folded under its heading.
- **Across days:** every "What we decided" together, every "What we left open" together, and "For me:" items as a filter. Left-open items have no closed state, so they show by date with a line saying so.
- **Decisions:** date, company, stage, my view, what I then decided, and the file path. "The system's view" is left out, because it is a recommendation and the board gives none.
- **Lessons:** title and date, linked to the file.
- **Search:** plain text across the Journal and Lessons.

**Reads:** `Journal/*.md`, `Journal/decisions/*.md`, `Lessons/*.md`.
**Have:** the file loop in `journal_alerts`, `_inline` for safe text.
**New:** all of the screen and its readers.

## Build order

Each step ends with its tests passing and the screen viewed in a browser, and nothing moves on until then.

| Step | What | Why here |
|---|---|---|
| 0 | Fix the one failing test | A clean baseline |
| 1 | Five-screen shell with `st.navigation`. Move today's panels unchanged. Add `view.fig` and its test. | Nothing new can break, and nothing is lost |
| 2 | **Home**, with `Ruled:` | The reason for the board, and it needs your one line (below) |
| 3 | **Ideas and alerts** | Reuses Home's readers, mostly existing panels |
| 4 | **Company page** | The largest step: Corning first, then the other 23 as "Not on file" |
| 5 | **Portfolio and cash** | Small, and no position exists yet to read |
| 6 | **Journal** | All new, and useful without being urgent |
| Later | Saved `pm.py` output for room under the limit | Only when a first position exists |

## What I need from you at build time

- **One line in `Rules/alerts.md`, through your door,** saying a ruling adds `- Ruled: <day> <rule ID>. <my words>` to the Journal. Without it, sessions won't know to write the line. I show the exact text first.
- A second alert with the same day and rule needs its own line. A `Ruled:` line matching no alert shows as a problem, not hidden.

## Claude's choices, for you to correct

- No grade, score, size or `pm.py` action anywhere on the board.
- Coach files show your view and your decision, not the system's view.
- The board never compares a close to a line. `Rules/alerts.md` would need changing, and so would the test, if it did.
- Days since on a Red or Orange counts the alert's age. It is not a source's age, which stays free of any signal.
- Keep Streamlit rather than start over.
- `board-plan.html` is a hand-written page, with no `draw.py`, since it is a plan and not a data page. Its wireframes use field names and placeholders such as `$000.00 · source · date`, not real figures, so nothing in it needs a source.

## Verification

**For the build later:**
- **Home fits:** in Chrome at 1366 × 768, the page height must not pass the window height, on today's files and on a busy made-up set with many Reds, Oranges and dates. If Chrome can't load live Streamlit, this check waits and I say so. A test also checks that `Coming up` comes before `Where things stand`, and that the hidden-row count is right.
- `.venv/bin/python dashboard/test_dashboard.py`, covering all five screens through `AppTest`. I have not yet confirmed `AppTest` handles `st.navigation`; step 1 settles that.
- **Word test, no-write test and figure test** on every screen.
- **Broken copies:** a figure with no source, a view word, a `Ruled:` line with no match, a mixed real and paper note. Each must fail.
- **A real browser.** On Nov. 4 headless Chrome did not finish loading live Streamlit, so step 1 must solve that or ask you to look.

## What this does not say

That any company is a buy or a sell. Corning stays no buy, and `Rules/`, `Companies/` and `Portfolio/` do not change. Nothing here is an investing decision.
