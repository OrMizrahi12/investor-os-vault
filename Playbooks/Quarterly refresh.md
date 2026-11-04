# Quarterly refresh

*Written 2026-11-03. Runs as a Desktop task named `quarterly-refresh`. Page: `reviews.html`. Not live until I create the task. Custom schedule: `30 10 * 2,4,5,7,8,10,11 2,5`. Dry run on a scratch copy, Nov. 3, 2026: see the page.*

The prompt below is what goes in the task's instructions box. If you change it here, paste it there too.

## The prompt

```text
Quarterly refresh. Nobody is watching, so never ask a question and never wait for an answer. You report and you propose. You never recommend, and the owner decides.

These steps replace the session-start and session-end steps in Rules/memory.md for this run. Run only the commands below, exactly as written, with no cd, no pipe and no other flag. No web access: filings come through the commands. This run never fetches a price.

You may write only: the run's reads.json, and the one proposal file the order names. Never touch Companies/, Rules/, Portfolio/, Catalysts/, .claude/, or anything else. The finish command refuses if a note, the rules, the portfolio, the valuation inputs or a saved valuation run changed.

1. Run: .venv/bin/python sensors/reviews/quarterly.py start
   Give the Bash call a 600000 ms timeout.
   If it prints NO NEW FILING and nothing else, reply with that line and stop. Read nothing more.
   If it prints NO NEW FILING with an AMENDED notice, add that notice as one line to the end of Journal/<today>.md, reply with it and stop.
   If it prints NEW 10-Q or NEW 10-K, it names an order file. Read it.

2. Read these, in parts where long: sensors/reviews/checklist-GLW.toml, the kill lines in `Research/2026-11-03 Corning kill criteria.md`, and every document under "documents" in the order. Long files: Read with offset and limit. A file you did not finish counts as not read. Reading the whole filing is the job: the balance sheet, cash flow, segment note, equity note, contract liabilities, subsequent events and legal note.

3. For each id under reads in the checklist, fill the order's reads.json by reading the number from its doc, not from the on_file value or from any other note in the vault.
   - "value": the number in $M, a signed number, or shares in millions.
   - "doc": the role named in the order, such as "10-Q".
   - "quote": a stretch of the saved text, copied exactly, that holds the number. For a row of a table, copy from the row's label through the number. For a sum of several lines, give a list of quotes, one per line. Where a filing shows none, give value 0 and quote the sentence or the row label that shows it.
   If the order's "form" is 10-K: the rows reads.json marks "not used at a 10-K" stay as they are, the _fy rows are the year just filed, and opt_ytd_sales and solar_ytd_sales are the full year. Quarter figures, such as opt_sales, core_q and solar_q_sales, come from the release, since Q4 is only there. glass_ni and glass_tax may be the full year, because they give a tax rate.
   If the order's "form" is 10-Q: for opt_rest and solar_rest, take last full year less the same span last year, as a list of quotes.
   Read the column heading for each number. Read every line of a reconciliation for the period. Look for a new line that fits a confirmed kind of item, and for any segment recast.

4. Run: .venv/bin/python sensors/reviews/quarterly.py check
   If it prints REFUSED, fix what it names and run it again, at most three times. Never change a value to match on_file. If a number really is not there, leave it null, and the run stops at step 7's failure line.
   It checks each quote against the saved filing, works the sums, builds the proposed inputs, and runs the valuation skill's value.py on the approved inputs and on the proposed ones. Do no sums by hand.

5. Load the valuation skill with the Skill tool, for what the method says and how to read the result. Its Saving section does not apply: do not copy inputs to assets, do not update the company note and do not run save.py. The owner has not approved. Skip its steps 1 and 2: this prompt sets what you read.

6. Write the proposal to the path in the order's "proposal", using the figures in the run's check.json:

   # Corning refresh proposal, <today>

   **One or two sentences: what moved in the base middle and the buy-below, why, and that nothing has been applied.** Write "Proposal. Not applied." If nothing but the close moved, say so plainly.

   ## Before and after

   A table: base low, middle, high, buy-below, strategic value, trim-above, price, coverage. Columns: Before (approved), After at the same price, After at the newest close. Mark each figure calc., and name the close's date and source. Keep what the filing moved apart from what the close moved.

   ## What changed, and why

   Each changed read and each changed sum, with source and date. Any status RESTATED goes first and says "a restatement". If a re-read differs from the note and the filing did not change, say the note appears wrong and name the note.

   ## Kill lines

   K1 to K9 from check.json, with threshold, reading and state. Say what the threshold's own wording and test date mean for each. K2 and K7 are statements and no 10-Q settles them. If K9's "complete_through" is older than this 10-Q's period, one of the three buyers has not filed: say "K9 pending", and the weekly check reads it later. Apply the Oranges and Reds from Rules/alerts.md: R1 for a crossed line, O1 for one step short, O3 for new shares, O6 for a line moved across the price, O9 for method triggers.

   ## What the filing says that the method does not see

   New or changed facts bearing on a thesis claim C1 to C8, with the place in the filing. Facts only.

   ## What I could not re-verify

   Every row of the ten-year check that says SOME NOT FOUND, anything under not_found in "record", every input not from a filing (Aaa, the chances, past tags, rival multiples, K2, K7), and anything you did not read.

   ## If you say yes

   The exact changes: the new assets file, and the note's `base value`, `strategic value`, `trim above` and `last checked`. Say none of them has been made.

   If the order's "form" is 10-K, add a section, ## The new audited year, first after Before and after. Say that the middle, the high and the ten-year low now rest on the new year's normal earnings, that these are marked unconfirmed, and list each adjustment by kind against the confirmed list in `normal.html` and `Companies/Corning.md`. Any line of a kind not yet confirmed goes to the owner. Add whether the last year's comparative column changed from what is on file. Say that the record growth (`record` in check.json) was not rolled forward.

   Rules for the proposal: every fact has a source link and a date beside it. Mark your arithmetic calc. Label targets as targets. No word of advice: nothing on what the owner should do with a stock. Leave out any possible inside tip, and in your reply tell the owner to ask a lawyer.

7. Run: .venv/bin/python sensors/reviews/quarterly.py finish
   It refuses if a locked file changed, or if the proposal lacks the figures. It adds the session to the end of today's Journal and marks this 10-Q as done.

8. Reply with the proposal's first paragraph and its path.

If a step fails or needs an approval you cannot get, do not try another way. Add one line to the end of Journal/<today>.md, creating it if needed: "Quarterly refresh FAILED at step <n>: <why>." Reply with that line and stop. The filing stays unmarked, so the next run tries again.
```

## When I say yes

Claude does this in a session, with me, and not in the task. Step 1 is behind a wall since Nov. 4, 2026. So Claude writes the new inputs to a file in `Research/` and gives me the line to type: `! python3 .claude/hooks/owner-apply.py <new file> .claude/skills/valuation/assets/corning-<date>.json`. Steps 2 to 4 work as written, because `save.py` only adds a new run. See `guardrails.html`.

1. Copy the run's `after-inputs.json` to `.claude/skills/valuation/assets/corning-<date>.json`, without the `proposal` flag and with the note replaced.
2. Update the note's `base value`, `strategic value`, `trim above` and `last checked`.
3. Update `on_file` and `filing` in `sensors/reviews/checklist-GLW.toml`. After a 10-K, also move the `years` and `record` rows forward, once I have confirmed the new year's adjustments.
4. Run `.venv/bin/python sensors/valuation/save.py`.

## What it does not do

- **It starts on a 10-Q or a 10-K (my decision, Nov. 4, 2026).** The 10-K path has passed tests on made-up figures only. No Claude run has used it.
- It does not roll the growth record forward at a 10-K. It says so, for me to rule.
- It does not change a chance, a grade or a thesis.
- It does not settle K2 or K7. The weekly check reads those.
- It fetches no price. "After at the newest close" is the last close I saved.

## By hand

    .venv/bin/python sensors/reviews/test_reviews.py
