# Sensors

Small scripts that pull our data. Each one does one fixed job.

Run one from the project root with `uv run python sensors/<name>.py`.

## edgar

Pulls a company's filing list and financial facts from SEC, and caches them. Settings, including the contact email, are in `edgar/settings.toml`.

    uv run python sensors/edgar/edgar.py GLW
    uv run python sensors/edgar/edgar.py GLW --refresh
    uv run python sensors/edgar/edgar.py GLW --document 0000024741-26-000124
    uv run python sensors/edgar/draw.py
    uv run python -m unittest sensors/edgar/test_edgar.py

The cache lasts 24 hours unless you use `--refresh`. `draw.py` builds `edgar.html` from the cache and is Corning-only for now.

## 8k-watch

Reads `8k-watch/watchlist.toml`, uses the edgar sensor to find new 8-Ks, reads each one, and writes one note per filing to `Inbox/`. Each note names the items and flags the ones on the watchlist's `flag_items`.

    uv run python sensors/8k-watch/watch.py
    uv run python sensors/8k-watch/watch.py --cached
    uv run python sensors/8k-watch/draw.py
    uv run python sensors/8k-watch/test_watch.py

`watch.py` asks SEC for a fresh filing list unless you use `--cached`. `seen.json` records what has been handled, so a note you delete is not written again, and a note you edit is not overwritten. A new filing's attention rating comes from its item numbers. A `[[reading]]` in `readings.toml` replaces it, in the note and on `watch.html`. `draw.py` builds `watch.html`.

## graph

Pulls nothing. Builds `graph.html` from the "Typed links" tables in `Companies/`, and stops if the two sides of a link differ or a link has no dated source. A new company needs a colour type and a place on the map in `draw.py`. Events for the walk are written in `draw.py` too.

    uv run python sensors/graph/draw.py

This script takes no flags. `--help` is ignored and the page is rebuilt, so read the file to see what it does.

## radar

Checks what the sensors saved, the dates in `Catalysts/`, walks the Typed links for each new event, and screens SEC's free XBRL frames. It makes no buy or trim call. A screen row is a lead to read, never a pick. Use the `catalyst-radar` skill to run it, because the skill also does the reading.

    .venv/bin/python sensors/8k-watch/watch.py --cached
    .venv/bin/python sensors/radar/radar.py
    .venv/bin/python sensors/radar/radar.py --no-screen
    .venv/bin/python sensors/radar/test_radar.py

It writes `radar/runs/YYYY-MM-DD-NN.json`, which the dashboard reads, and `Research/YYYY-MM-DD Catalyst radar.md`. In each catalyst note it writes only `radar checked` and the "Radar" section. It leaves "last checked" alone, because that means someone read the note against a source. A second run the same day gets its own files. `state.json` records what was reported, so an event is reported once.

**Dates** come from `date start`, `date end`, `date quote` and `date kind` in each note, not from parsing its text. If the quote leaves the note's When section, the radar shows a problem instead of a date.

**What it hides:** a director-only Form 4 where every row is a code A grant, the second graph step when only a screen lead started the walk, and off-map leads that may not be new growth (current plus noncurrent did not grow, or every flagged line was also up by `min_rise_pct` on the same step a year earlier). Each is counted in the report and kept in the saved run, under `hidden`, `hidden_leads` and `hidden_step2`.

**Forms 4:** there is no separate Form 4 sensor. The radar finds them on the EDGAR sensor's saved filing list, reads the saved XML, and saves any it lacks through the EDGAR client.

**Prices:** it reads the saved close and never asks Yahoo. It computes no change, so a price cannot become an event.

**SEC's limits:** [SEC's limit is 10 requests per second, Developer Resources, last reviewed March 10, 2025](https://www.sec.gov/about/developer-resources). All requests go through the EDGAR client, which runs at 8 per second, declares the contact address in `edgar/settings.toml`, honours Retry-After and stops on a 403. Frames are cached, 24 hours for the two newest quarters and 7 days for older ones, and a run stops at `max_requests_per_run`. A first run takes 28 requests. Run one SEC job at a time, because each client spaces only its own requests. EDGAR content is "free to access and reuse" ([SEC webmaster FAQ, last reviewed Aug. 23, 2024](https://www.sec.gov/about/webmaster-frequently-asked-questions)). Screen limits and the date horizon are in `radar/settings.toml`.

## prices

**My decision, Nov. 3, 2026: keep it, once a day.** This goes against [Yahoo's terms, updated Nov. 1, 2026](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html), which bar collecting data by automated means for any purpose without its express, prior permission. Yahoo has not given permission. See `Journal/2026-11-03.md`.

Pulls Corning's daily prices from Yahoo through yfinance, for my personal use only. SEC and FRED stay our backbone, so this is not a source of company facts, and nothing built from it gets published.

    uv run python sensors/prices/prices.py
    uv run python sensors/prices/test_prices.py

Nothing runs it on a schedule. Run it by hand after a new 10-Q or 10-K, or before a decision. It asks Yahoo at most once per UTC day. A failed try counts, and there is no override. Each fetch is a dated file in `prices/cache/GLW/`, and `manifest.json` logs every try. It keeps Close and Adj Close apart. Today's row is dropped until the New York session has closed.

## macro

Reads three FRED files that I download by hand: DGS10, AAA and CPIAUCSL. It makes no FRED requests, because [FRED's terms, undated, retrieved Nov. 2, 2026](https://fred.stlouisfed.org/legal/), bar scripts from collecting its data and bar storing a cache without written consent, and they allow a personal download.

To refresh, open each series page, choose the longest range, then Download, CSV (data). Save as `macro/downloads/<ID>.csv`, replacing the old file.

    uv run python sensors/macro/macro.py
    uv run python sensors/macro/draw.py
    uv run python sensors/macro/test_macro.py

`macro.py` takes the file's modified time as the date downloaded, logs new files in `downloads/manifest.json`, and stops on a wrong file, a short range, or changed units or frequency. `draw.py` builds `economy.html`, leaving off any line not downloaded yet. Keep that page on this computer, because it holds Yahoo and Moody's data.

## multiples

Pulls nothing. Builds `multiples.html` from the EDGAR, prices and macro caches: Corning's P/E, EV/EBIT and free cash flow yield at the last ten year ends and the latest saved close, its earnings yield against Aaa and the 10-year Treasury, and a peer strip. Not a valuation method, and it gives no buy or trim view.

    .venv/bin/python sensors/multiples/draw.py
    .venv/bin/python sensors/multiples/test_multiples.py

Rival figures are in `multiples/peers.toml`, read by hand from one outside page. No script refreshes them, and the price sensor stays Corning-only. Keep the page on this computer, because it holds Yahoo and Moody's data.

## parts

Pulls nothing. Builds `parts.html`, Corning as the sum of its parts, from filing figures typed into `parts/model.py` and rival multiples in `multiples/peers.toml` and `parts/peers.toml`, read by hand from one outside page. No script refreshes them. Keep the page on this computer, because it holds Yahoo's price.

    .venv/bin/python sensors/parts/draw.py
    .venv/bin/python sensors/parts/test_parts.py

The test shares no code with the page and checks the inputs against the saved filings.

## valuation

Saves one Corning valuation for the dashboard's price against value panel. By hand, no network, and it holds a Yahoo price, so it stays on this computer.

    .venv/bin/python sensors/valuation/save.py
    .venv/bin/python sensors/valuation/test_save.py

All sums are `value.py`'s, from the valuation skill. It uses the newest inputs in `.claude/skills/valuation/assets/` and the newest saved prices. It stops if the inputs disagree with the Corning note, if a newer 10-Q or 10-K is on the saved SEC list, or if Aaa changed. Each run writes `runs/YYYY-MM-DD-NN.md` and `.json`, and a second run the same day gets its own files. The what-ifs change one assumption at a time and are labeled as not the method's answer. The test checks them against `sensors/strategic/model.py`, which shares no code with `value.py`.

## strategic

Works out a proposed strategic value and trim-above for Corning, and draws `strategic.html`. A proposal: nothing is saved to `Rules/` or the company note until I approve. No network.

    .venv/bin/python sensors/strategic/draw.py
    .venv/bin/python sensors/strategic/test_strategic.py

## concentration

Pulls nothing. Builds `concentration.html`, a lesson on how many holdings to keep, from random portfolios of companies on the Nov. 2016 S&P 500 list. Not a screen and not a source of company facts. No stock in it is a pick.

    .venv/bin/python -I sensors/concentration/prepare.py <price folder> <wiki file> <check folder>
    .venv/bin/python -I sensors/concentration/simulate.py
    .venv/bin/python -I sensors/concentration/draw.py
    .venv/bin/python -I sensors/concentration/test_concentration.py

`cache/manifest.json` lists the downloads, which went to Hugging Face and Wikipedia, not Yahoo. The raw files are not kept, so `prepare.py` needs them fetched again, while the other three run from `cache/`. **The prices are someone else's copy of Yahoo's data, so keep the page and the cache on this computer.** `prices.py` stays Corning-only. My decision, Nov. 3, 2026: this copy fits my Yahoo decision, the data stays and the page stays local. See `Journal/2026-11-03.md`.

## overlap

Pulls nothing. Builds `overlap.html`, a lesson on what five paper names share and how many real bets they are, from the concentration lesson's saved returns, the map inside `graph.html`, and SEC filings read through `edgar`. Not a screen, and no name in it is a pick. The change to `Rules/sizing.md` shown on the page was approved and made on Nov. 3, 2026. Keep the page and cache on this computer, since they rest on the copy of Yahoo's data. Rebuild `graph.html` first if the Typed links change.

    .venv/bin/python -I sensors/overlap/analyze.py
    .venv/bin/python -I sensors/overlap/draw.py
    .venv/bin/python -I sensors/overlap/test_overlap.py

## sizing

Pulls nothing. Builds `sizing.html`, a lesson on the proposed method in `Rules/sizing.md`, from the Corning valuation run and two made-up ideas. I approved the whole method on Nov. 3, 2026, and added the test for one thesis the same day (see `overlap.html`). Keep the page on this computer, since it holds a Yahoo price.

    .venv/bin/python -I sensors/sizing/draw.py
    .venv/bin/python -I sensors/sizing/test_sizing.py

## portfolio

Pulls nothing. Builds `portfolio.html`, a lesson on the `portfolio-manager` skill and the paper portfolio I set up on Nov. 3, 2026: Corning, the five names from `overlap.html` and the two made-up ideas from `Rules/sizing.md`. Not advice. Keep the page on this computer, since it holds a Yahoo price. The sums are the skill's, in `.claude/skills/portfolio-manager/scripts/pm.py`, which writes nothing and places no order.

    .venv/bin/python -I sensors/portfolio/draw.py
    .venv/bin/python -I sensors/portfolio/test_portfolio.py
    .venv/bin/python -I .claude/skills/portfolio-manager/scripts/test_pm.py

`test_portfolio.py` shares no code with the page or the script and works the figures out again.

## coach

Pulls nothing. Builds `coach.html`, a lesson on the `coach` subagent: the flow, the owner's view against the system's on Corning, and a review of the Nov. 2 no-buy. It reads `Journal/decisions/2026-11-03 Corning.md`. Not advice. Keep the page on this computer, since it holds a Yahoo price.

    .venv/bin/python -I sensors/coach/draw.py
    .venv/bin/python -I sensors/coach/test_coach.py
    .venv/bin/python -I sensors/coach/test_guard.py

`test_guard.py` calls `.claude/hooks/coach-guard.py` as Claude Code does, on a temporary copy, including one whole run in order.

## cash

Reads saved downloads and builds `cash-reserve.html`, a lesson on cash as a position, and the evidence behind `Rules/cash.md`, which I approved on Nov. 3, 2026 as a fixed 15% with no gauge. Not a market forecast. The gauge stays on the page as the test it failed.

    uv run --no-project --with xlrd python -I sensors/cash/prepare.py
    .venv/bin/python -I sensors/cash/analyze.py
    .venv/bin/python -I sensors/cash/draw.py
    .venv/bin/python -I sensors/cash/test_cash.py

**Sources, in `cash/downloads/`, fetched once by hand on Nov. 3, 2026.** No script fetches them, and `cache/manifest.json` logs each file's address and hash. To refresh, download each again from its page. Nothing goes to Yahoo or FRED.

- **Stocks and the gauge:** [Shiller's file, dated Oct. 6, 2026](https://shillerdata.com/). His page states no licence and his disclaimer takes no responsibility. **The file carries S&P data, so keep it and the page on this computer.**
- **Bills:** [Treasury's daily bill rates, through Nov. 2, 2026](https://home.treasury.gov/interest-rates-data-csv-archive). A [data.gov record, undated, retrieved Nov. 3, 2026](https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-bill-rates), lists them as CC0. Treasury's own page was not found saying so.
- **Second copy, and bills before 2002:** [Damodaran's returns, Jan. 2026](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html). His page states no licence, and his bill sheet is drawn from FRED.

`test_cash.py` shares no code with the page and works every figure out again. `draw.py` stops if a word claim stops being true.

## demo

Runs one hunt's pick and draws `demo.html`: the funnel from the radar's leads to positions, where each candidate stopped, and the paper portfolio with its cash. A lesson, not advice. Keep the page on this computer, as the other pages are.

    .venv/bin/python sensors/demo/pick.py
    .venv/bin/python sensors/demo/check.py <cik> ...
    .venv/bin/python sensors/demo/record.py <cik> ...
    .venv/bin/python -I sensors/demo/draw.py
    .venv/bin/python -I sensors/demo/test_demo.py

`pick.py` ranks the radar's leads by the rise against revenue, from SEC's annual frames (four requests through the EDGAR client). A frame can hold a partial line, so check the top of the ranking against company facts with `check.py`. `record.py` prints the saved Gate 1 record. `draw.py` makes no request. Its sums for the book are `pm.py`'s, and `test_demo.py` works the figures out again.

## alerts

Pulls nothing. Runs the alert map in `Rules/alerts.md`, which I approved on Nov. 3, 2026, over Corning's saved record for Nov. 3, 2024 to Nov. 2, 2026, and draws `alerts.html`. Nothing here sends an alert. The levels on events, in `alerts/alertmap.py`, are Claude's reading with hindsight, for me to correct. Keep the page and `cache/` on this computer, since they hold a Yahoo price and Moody's data.

    .venv/bin/python -I sensors/alerts/analyze.py
    .venv/bin/python -I sensors/alerts/draw.py
    .venv/bin/python -I sensors/alerts/test_alerts.py

`test_alerts.py` shares no code with the others and works the counts out again from the saved lists, releases and prices.

## daily

The daily run. `collect.py` runs the 8-K watcher and the radar, one at a time, and writes a digest of what is new since the last brief to `daily/runs/`, each item with a first-pass level from `alerts/alertmap.py`. `publish.py` checks the brief, puts it at the top of today's Journal, adds the session record at the end and files new filings in `Inbox/`. The prompt is in `Playbooks/Daily run.md`. `draw.py` builds `daily.html` from that prompt and `daily/samples/`. Keep the page and `samples/` on this computer, since they hold a Yahoo price.

    .venv/bin/python sensors/daily/collect.py
    .venv/bin/python sensors/daily/publish.py
    .venv/bin/python sensors/daily/test_daily.py
    .venv/bin/python -I sensors/daily/draw.py

Both scripts take no arguments, so Desktop's "always allow" can match each one exactly. `collect.py` calls SEC only. It never runs `prices.py` and never asks Yahoo, by my decision of Nov. 3, 2026: it reads the saved closes and checks the lines against any new one, on the first run after I save it by hand. Sensors remember what they reported, so a digest not yet briefed carries into the next one.

## reviews

The two slower routines, the weekly thesis check and the quarterly refresh. The prompts are in `Playbooks/`, and the page is `reviews.html`. Nothing here changes a note, recommends anything or asks Yahoo.

    .venv/bin/python sensors/reviews/weekly.py start | finish
    .venv/bin/python sensors/reviews/quarterly.py start | check | finish
    .venv/bin/python sensors/reviews/test_reviews.py
    .venv/bin/python -I sensors/reviews/draw.py

`checklist-GLW.toml` lists every number Corning's base value and kill lines rest on. `theses.toml` lists which companies the weekly covers, its searches and the sites it may open. `samples/dry-run/` is the dry run of Nov. 3, 2026, a record. `reviews.html` holds a Yahoo price, so keep it on this computer.

## hunt

The monthly hunt and the event run. The prompts are in `Playbooks/Monthly hunt.md` and `Playbooks/Event run.md`, and the page is `hunt-events.html`. Both tasks are live in Desktop since Nov. 4, 2026, my report. Nothing here recommends anything, changes a note or asks Yahoo.

    .venv/bin/python sensors/hunt/hunt.py start | gate2 | finish
    .venv/bin/python sensors/hunt/events.py start | finish
    .venv/bin/python sensors/hunt/test_hunt.py
    .venv/bin/python -I sensors/hunt/draw.py

`hunt.py` calls the radar's screen, not the radar, because a full radar run marks new filings as reported and the daily run would lose them. It checks every lead against `Research/Rejection log.md`, takes the top five by rise ÷ revenue, and runs Gate 1 and Gate 2 from `gates.py`. Gate 2 takes a price from one StockAnalysis page per survivor, opened by the session and not by a script. `events.py` asks SEC for 12 graph companies' filing lists each run, and walks each new Item 1.01 or 1.02 8-K with the radar's own `walk`. `samples/` holds the replays, and `hunt-events.html` holds a StockAnalysis price, so keep both on this computer.


## guardrails

The deny rules in `.claude/settings.json` and the one hook, `.claude/hooks/guardrails.py`, stop any session or routine changing my rules, my portfolio, the method or the alert map, or doing anything that looks like a trade or a broker. Page: `guardrails.html`. The record of what they stopped: `.claude/guardrails/blocked.jsonl`, shown on the dashboard.

    python3 sensors/guardrails/test_guardrails.py      crafted calls, no network and no model
    python3 sensors/guardrails/attempts.py             real attempts through Claude on throwaway copies, one to block and one to pass
    python3 sensors/guardrails/routines.py             the five real prompts, whole, on a throwaway copy
    python3 sensors/guardrails/draw.py                 redraws the page from the saved runs

My door, for when I say yes to a change behind a wall: `python3 .claude/hooks/owner-apply.py <new text> <walled file>`. Only I can run it.

## phone

Sends Red lines from the daily run and the event run to a Telegram bot, each once. Plain Python, no model. `publish.py` and `events.py` call it as their last step, so the task prompts did not change. Orange and Info never go. Page: `phone.html`.

    .venv/bin/python sensors/phone/phone.py setup
    .venv/bin/python sensors/phone/phone.py test
    .venv/bin/python sensors/phone/phone.py check
    .venv/bin/python sensors/phone/phone.py send
    .venv/bin/python sensors/phone/phone.py send --every 900
    .venv/bin/python sensors/phone/test_phone.py
    .venv/bin/python -I sensors/phone/draw.py

The token lives only in the file named at the top of `phone/phone.py`, outside the vault. `sent.json` records what went, by accession. A failed send stays waiting, and the Journal gets one line a day (O16).

## decisions

Pulls nothing. Builds `decisions.html`, a lesson on what would make us add, hold, trim, sell or stop on Corning, from the valuation run, the saved close and two made-up paper cases. Not advice. Keep the page on this computer, since it holds a Yahoo price. The test shares no code with the page and also runs the cases through the `portfolio-manager` skill's `pm.py` on temporary files.

    .venv/bin/python -I sensors/decisions/draw.py
    .venv/bin/python -I sensors/decisions/test_decisions.py
