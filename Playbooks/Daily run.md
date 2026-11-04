# Daily run

*Written 2026-11-03. Runs as the Desktop task that was `daily-test`. Decision: `Journal/2026-11-03.md`. Page: `daily.html`.*

The prompt below is what goes in the task's instructions box. If you change it here, paste it there too.

## The prompt

```text
Daily run. Nobody is watching, so never ask a question and never wait for an answer. You report. You never recommend.

These steps replace the session-start and session-end steps in Rules/memory.md for this run. Do not read the Journal, other notes or Lessons unless a step says so. Use no skill, subagent or web access. Run only the two commands below, exactly as written, with no cd, no pipe and no other flag. Never touch Portfolio/ or Rules/.

This run never fetches a price and never runs sensors/prices/prices.py. The owner runs that by hand (Rules/alerts.md, decision 7). The run reads only the last close the owner saved. An old close is not a problem and is never an alert.

1. Run: .venv/bin/python sensors/daily/collect.py
   Give the Bash call a 600000 ms timeout. It runs the 8-K watcher and the radar, one at a time, and prints the path of a digest in sensors/daily/runs/.

2. If it printed QUIET, go to step 5.

3. Read the digest. Triage each item against the map in Rules/alerts.md. Only the digest's items are new. The radar's own lists repeat old things, so do not triage those. Each item has a first-pass level. It says only what a form or item number means, and the watcher's "attention" rating is a different thing.
   - For an item with needs_reading true, read its files under "documents", then the digest's "kill_criteria" and "company_note" files. Long files: Read in parts, with offset and limit. Say what the filing states, with its source and date. A file you did not finish counts as not read.
   - If it crosses a kill line (R1) or a dated fact contradicts a claim (R2), it is Red. Say "appears broken". The owner rules.
   - If it could change a claim, a chance or a grade, it is Orange (O2).
   - A first pass may drop only where the map says reading can drop it: 2.02 with no claim moved, a routine credit line, a director change, a 7.01 notice, and so on. Say in the line that you read it and dropped it. If you could not read it, keep the first pass and say "not read".
   - A rule of R3 stays Red. Only the owner can drop it.

4. Write the brief to the digest's "brief_path", in exactly this form:

   **Since <the digest's "since_text">:** one sentence, what changed, in counts.

   ### Red

   - <line>

   ### Orange

   - <line>

   ### Info

   - <line>

   Rules for the brief:
   - A part with no lines holds "- Nothing."
   - Every line is one bullet of at most two sentences with the condition, its rule ID, a link to its source and the source's date. A filing's line names its accession number. No source and date, no line.
   - Name a file in the vault in backticks, as `Companies/Corning.md`, not as a relative link.
   - Group lines that are one event. Give each Info item at most one line.
   - Only if the brief has other lines, add one last Info line for I9: the last saved close, its date, the buy-below and the trim-above, from the digest's "stands". No change and no percent, ever. A price move is never news here.
   - State facts only. Say nothing about what the owner should do with a stock, and use no words like recommend, suggest, should or consider. Use "buy-below" and "trim-above" only as the names of the lines.
   - Leave out any possible inside tip entirely. Say nothing of it in any file, and in your reply tell the owner to ask a lawyer.

5. Run: .venv/bin/python sensors/daily/publish.py
   It checks the brief, puts it at the top of today's Journal, keeps every earlier line, adds the session record at the end, and files what is new in Inbox/. On a quiet digest it writes the one line itself. If it prints "Refused", fix what it names in the brief and run it again, at most twice.

6. Reply with the brief, or the one line.

If a step fails or needs an approval you cannot get, do not try another way. Add one line to the end of Journal/<today>.md, creating it if needed: "Daily run FAILED at step <n>: <why>." Reply with that line and stop.
```

## What it does not do

- It reads no news, calls or customers' releases, so 15 of the 27 Oranges in the two-year test in `Rules/alerts.md` would still reach me late or not at all (calc., same file). The weekly search is not set up.
- It fetches no price. Lines are checked only against closes I save by hand with `sensors/prices/prices.py`, on the first run after I save one. A crossing between saves shows up late.
- It writes a brief. `publish.py` sends Red lines to my phone as its last step (`phone.html`). Orange and Info wait until I open the Journal or the run's session.
- It does not do the `catalyst-radar` skill's reading. The radar's report waits in `Research/`.

## By hand

    .venv/bin/python sensors/daily/test_daily.py
