---
name: catalyst-radar
description: Run the catalyst radar. Checks what the sensors saved (new 8-Ks, Forms 4, prices), catalyst dates due soon in Catalysts/, walks the Typed links graph for each new event, screens SEC's free XBRL frames for companies whose contract liabilities or remaining performance obligations rose sharply in a quarter, updates catalyst notes and writes a dated report that the dashboard's catalyst panel reads. Use when the owner asks to run the radar, or asks what is due or new across catalysts. Leads are things to read, never picks.
---

# Catalyst radar

The script does the counting. You do the reading. Conclusion first, plain words, short sentences.

## Limits

- **No buy, trim or sell view.** This skill does not use base value. `Rules/when-to-buy.md` and `Rules/when-to-trim.md` decide, not this skill.
- **A screen lead is a lead to read, never a pick.** Do not rank leads by appeal or call one interesting as an investment. A rise can be a deal, a deposit, an acquisition, a reclassification, a season or a data slip.
- **A price is never an event.** Do not compute or report a price change here. `Rules/monitoring.md` bars an alert on a price move alone.
- **Do not run `sensors/prices/prices.py` from this skill.** Yahoo's terms bar automated collection, and my decision was to run it by hand. Read the saved close and say its date.
- **A graph step means a link exists, not that the event reaches that company.** Say which links are weak.
- Possible inside tips stay out of every file. Tell me to ask a lawyer, and recommend no trade in that stock.

## Steps

1. **Read first.** Follow `Rules/memory.md`: the three latest Journal entries, and `Companies/` notes for companies you discuss. Search `Journal/` and `Lessons/` for their names.

2. **Refresh 8-Ks.** Run this one at a time, never alongside another SEC job, so the combined rate stays under SEC's limit of 10 requests per second:

       .venv/bin/python sensors/8k-watch/watch.py --cached

   It reuses a filing list under 24 hours old, and writes new notes to `Inbox/`.

3. **Run the radar.**

       .venv/bin/python sensors/radar/radar.py

   Add `--no-screen` to skip the frames. Its output names the report and the saved run. If it prints a problem, show me the problem. Do not hide it or fix a date field to make it pass.

4. **Open the report** in `Research/` and read it whole. Then do the reading:
   - **New events.** Open each filing that has a new fact. Use the saved copy in `sensors/edgar/cache/`, or `sensors/edgar/edgar.py <ticker> --document <accession>`. Read 8-K items in the filing, not the index. Check whether the vault already has the fact.
   - **Catalysts named against an event.** A name match is not a reading. Read the filing against the note and decide if it bears on the catalyst.
   - **Dates passed, Outcome not written.** Find what happened from a source, or say it is unknown.
   - **Dates due within 30 days.** Check that the date still stands, from a source. Built-in search first, then `Playbooks/Web search with Agent Reach.md`.
   - **Screen leads on our map.** Read the filing behind them. Other leads stay on the list unless I ask.
   - **Thesis check.** For each owned position in `Portfolio/`, say whether the thesis holds and why. If nothing is owned or no thesis is written, say so.

5. **Update the notes you read against.** Under "Outcome" or the note's own sections, with source and date next to each fact. Mark your arithmetic "calc." Update "last checked" only on notes you actually read against a source. The script writes "radar checked" and the "Radar" section. Do not edit that section. Do not change a date field unless the When section changes with it, from a source. New company facts: propose them to me, as with a researcher's report, unless I ask you to merge.

6. **Write the report's "Reading" section,** replacing its placeholder. What you read, what it changes, what you did not read. Every fact gets a source and a date. Keep leads as leads.

7. **The dashboard needs no restart for new runs.** It reads the newest file in `sensors/radar/runs/` when the page reloads. It never runs the radar.

8. **Write the Journal entry** under `Rules/memory.md`. Put any correction in `Lessons/`.

## Tell me

Conclusion first: what is due, what is new, and what you read. Then what you did not read. End with what waits on me. Never present a lead as an idea to act on.

## What the script hides

These stay in the saved run and are counted in the report, and the dashboard lists them in folded rows. The owner chose these on Nov. 3, 2026. Do not add to them without asking.

- **A Form 4 from a director and nobody else, where every row is a code A grant.** Any officer's award, any 10% owner, and any other row on the form stay events.
- **The second graph step when only a screen lead started the walk.** Filings and other real events keep both steps.
- **A lead that may not be new growth, unless the company is on our map:** current plus noncurrent did not grow, or every flagged line was also up by the limit on the same step a year earlier. A rise a year earlier suggests a season but does not prove one.

Never hidden: other Forms 4, a Schedule 13D, a lead on our map, a date passed with no Outcome, wide date windows, date problems and unit-slip rows. The newest quarter is labelled as still filling, not dropped.

## What the script does not do

- It does not read a 10-Q, a 10-K or an exhibit. It matches names in 8-K reasons and first paragraphs, and those matches can be wrong or miss things.
- A frame has one number per company per quarter, in US GAAP dollars. Foreign filers, companies that report these only in a 10-K or in text, and tag changes do not show. An earlier figure may be restated.
- A Form 4 summary puts a dollar value only on non-derivative rows with a price.
- The link shown beside a date is the first link in the note's When section. It may not be the source of that date, so open the note.
- Screen limits and date horizons are in `sensors/radar/settings.toml`.
