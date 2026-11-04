---
name: thesis
description: Turn what is already in the vault into a dated thesis note for a company that passed triage - the six questions, what the market believes against what the evidence shows, kill criteria with thresholds and dates, and a monitoring plan, with a source or a calc. label on every figure. Use whenever the owner asks to write, draft, redo or refresh a thesis, asks why one might own a company, what the market is pricing against what we know, or what would prove a company's case wrong, even if the word thesis is not used. The note is always a draft for the owner. This skill never marks a thesis approved, never edits a company note and never changes a decision. It runs no valuation of its own (use the valuation skill) and no skeptic's review.
---

# Thesis

Turns the vault into one thesis note, saved in `Research/`, for the owner to read. `Rules/` win over this skill. If they differ, follow the rules and tell the owner where.

Conclusion first, plain words, short sentences.

## What this skill will not do

A written, approved thesis is a gate for buying and trimming. So the owner alone opens that gate, and this skill only prepares the paper.

- **Never marks a thesis approved.** The note's status is always `draft, not approved`. No wording may suggest otherwise, even if the owner asks in the same breath. If the owner says "approve it", say that the approval is theirs to record and that this skill does not write it. Point them to the Thesis section of the company note, and do not edit it.
- **Never changes a decision.** Copy the company's standing decision from the Journal, word for word where you can, and say it stands. Do not write a new action. The note holds no buy, trim or sell view, no size and no price to watch for. If coverage is low, that bars a buy and says nothing about selling.
- **Never sets a line.** A kill line the owner has set is copied as set. Any line you add is labeled `proposed, for you to set`. Only the owner changes one.
- **Never says the thesis survived a skeptic's review.** This skill does not run one. Say whether one has run. You may name the strongest doubts you found, but do not call that a review.
- **Edits nothing else.** Not `Companies/`, `Rules/`, `Portfolio/`, `Catalysts/`, the sensors or an earlier draft. It writes one new file in `Research/`, then the Journal entry. Facts it could not merge stay in the note for the owner to merge.
- **No trades, no guessed holding.** A possible inside tip stays out of every file: recommend no trade in that stock until the news is public, and tell the owner to ask a lawyer.

## Steps

### 1. Check triage first

Read `Research/Rejection log.md` and the newest `Research/* Triage.md`. A company passed triage only if it was sorted **research**, which means it passed all three gates.

- **Passed:** go on.
- **Not passed, or not in any triage:** stop before reading further. Say what triage found (gate, reason, look-again date) and that the thesis needs the owner's say-so. Rejection means no research hours, and a thesis is research hours.
- **The owner says run it anyway, knowing the status:** go on, and put the status in the note's first lines and in the frontmatter. A plain request naming the company is not that say-so, unless the owner has already been told the status in this conversation.

Going on does not change the triage result, the rejection log or the look-again date.

### 2. Read what the vault holds, in this order

1. The three latest Journal entries. Search `Journal/` and `Lessons/` for the company's name. Past decisions bind you: approved chances, set lines, facts the owner dropped.
2. The company note, whole, and its `Catalysts/` notes.
3. Pages and reports: `Research/` reports on the company, marked as not merged wherever you use them, and the root HTML pages. For Corning: `base.html`, `strategic.html`, `priced-in.html`, `parts.html`, `edge.html`, `customers.html`, `rivals.html`, `people.html`, `catalysts.html`, `monitor.html`. Read a page's words, not just its digits.
4. A newer saved valuation run in `sensors/valuation/runs/`, and a set kill-criteria note in `Research/`.

**Do not open an earlier thesis draft or its page until your note is finished.** Copying it would carry its mistakes forward, hide figures with no real source, and leave nothing to check against. When you finish, open it and list what differs under "Against the earlier draft". Do not overwrite it. If the file name is taken, add a number.

**Vault only.** Run no web search, no sensor that fetches and no new valuation. A gap is the finding: write "unknown, not in the vault" and list what would fill it under "How far to trust this". The owner can ask for research, or send it to the `researcher` agent.

### 3. Get the value figures from a saved run

Take them from the newest saved run in `sensors/valuation/runs/`, not from memory or a page. If the company has no run, or a filing is newer than the run, say so at the top, and mark what it blocks as unknown. Do not work out a base value here: that is the valuation skill's job, and its fit check is what makes the number mean anything.

Show **coverage** in the conclusion: base middle ÷ price. Strategic value never counts toward covering the price, so any "value ÷ price" figure sits apart, named as not coverage. Never let it stand where coverage should be.

### 4. Write the note

Follow `references/note-shape.md`. Read it now. It holds the sections, the six questions and the tables.

- **Claims.** Break the thesis into claims C1, C2 and so on. Each must be something that could turn out false. If a kill criteria note in `Research/` lists claims, reuse its numbers and words exactly, because the owner's lines point at them. A new claim takes the next free number. If a claim's words seem wrong, say so under "What I cut", and keep the number and words.
- **The market column is your reading of the price,** not anyone's stated view, unless a dated source in the vault says it. Label it. Tie each belief to a figure from the price, such as growth needed or a multiple.
- **The unknown column is not optional.** Every claim has one, even if it says "nothing found".
- **Status words are your reading,** for the owner to correct. Start with one of: supports, mixed, against, unknown. Add the limit after a comma when the evidence stops short of the claim: `supports, to 2027`. Count them with a script, not by eye.
- **The headline may not outrun the count.** Write it after the table, and put the count right under it. If supports are not most of the claims, words like "real", "solid" or "strong" claim more than the note has shown. "Plausible" or "not shown" is what the evidence allows.
- **Keep the evidence that cuts deepest.** Length is cut from repetition, never from a reading that disagrees with another. For any claim marked against or unknown, keep each distinct reading the vault holds. Every note also has a cash and funding table, because cash is where a good story most often fails. An earlier Corning run left out three cash readings that sat in the company note, then marked the cash claim against with its reasons missing.

### 5. Write the kill criteria

Read `references/kill-and-monitor.md` first. Every line has a measure, a number or a yes-or-no event, and a date. A line that lacks one goes under "What I cut", with why. Crossing opens a review, never a sale.

### 6. Check it with the script

Do the sums with a tool and take the words from its output. A figure typed by hand drifts by a cent, and earlier sessions proved it. Then run:

    python3 .claude/skills/thesis/scripts/check_note.py "Research/<note>.md" --kill-note "Research/<kill criteria note>.md"

Leave out `--kill-note` if the company has none. It looks for a figure with no source or calc. label, a calc. with no inputs, a link with no date, a missing section, a kill line with no threshold or date, a claim or set line that differs from the kill note, a count that differs from the table, a headline stronger than the count, an approval claim and advice words. Fix what it finds by adding the real source, or by cutting the figure. Never add a bare "calc." to quiet it, and never use `--allow` to pass a figure you could not source. It cannot tell if a source is right. So re-open the source of the five figures the conclusion rests on.

### 7. Save and report

- Save as `Research/YYYY-MM-DD <Company> thesis note.md`.
- Write the Journal entry, as `Rules/memory.md` says. A note written is not a decision: the company's standing decision goes in as unchanged.
- Corrections go in `Lessons/`.
- Anything holding a Yahoo price stays on this computer. Never publish it as an artifact.
- Tell the owner in a few lines: the conclusion, triage status, what the note could not fill, and what they must decide. Say plainly that nothing is approved and no decision changed.

## Files

- `references/note-shape.md`: the note's sections and tables. Read in step 4.
- `references/kill-and-monitor.md`: what makes a kill line and how to plan its monitoring. Read in step 5.
- `scripts/check_note.py`: the check in step 6. `scripts/test_check_note.py` tests it.
- `evals/evals.json`: test prompts and checks.
