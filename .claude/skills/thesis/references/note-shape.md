# The note's shape

Use these sections, in this order. Cut words, not sections. If a section has nothing, say so in one line.

```
---
company: "[[Name]]"
ticker: XXX
track: thesis note
written: YYYY-MM-DD
status: draft, not approved
triage: <research | rejected at Gate N, run at owner's request | ...>
valuation run: <path, or none>
skeptic review: not run
---

# <Company> thesis note, <date>

**<One or two sentences: the conclusion.>**

**Claim count:** <N> claims: <n> supports, <n> mixed, <n> against, <n> unknown (my count).

<Coverage line: base middle, price, coverage, buy-below, each sourced or calc.>
<The thesis in one sentence, with its targets labeled as targets.>
<Status block: draft, not approved; the standing decision, unchanged; triage status; skeptic's review not run.>

## Six questions
### 1. The mechanism
### 2. The value in dollars
### 3. The probability
### 4. The timing
### 5. What today's price already implies
### 6. What would prove it wrong

## What the market believes, against what the evidence shows
## Cash and funding evidence
## Kill criteria
## Monitoring plan
## What I cut
## How far to trust this
## Against the earlier draft
```

## The six questions

Each answer opens with one bold sentence that answers it. Then only what backs that sentence up.

1. **The mechanism.** How does the money get made, step by step? Number the steps, each with its evidence. Name the weakest link.
2. **The value in dollars.** A table from the saved run: base low, middle, high, buy-below, strategic value, trim-above, price, coverage. Say which way the method leans. Add a total value in dollars only as calc. with its share count.
3. **The probability.** Copy the scenarios and chances from the run, and say whose chances they are and whether the owner approved them. Say if the vault has no base rate. Never multiply chances that share a cause, and say so. If a chance has no owner approval, label it `proposed`.
4. **The timing.** When is the first real test, when is the full test, and how does that sit against the five-year hold? Separate stated dates, targets, forecasts and your estimates. Do not state a holding unless `Portfolio/` shows one.
5. **What today's price already implies.** The growth the price needs, in plain scale against the record, and with the plan granted. Give the assumptions behind it, and label them.
6. **What would prove it wrong.** One line per kill criterion, pointing to the section below. Add the loss if wrong: the fall from the price to base middle and low (calc.), "a distance, not a forecast". Add what would prove **our doubt** wrong, so that the note can lose both ways.

## The market table

| Claim | Status | Market seems to believe (my reading) | Our evidence shows | We simply do not know |

- One row per claim. Evidence for and against in the same cell, with sources.
- A figure from a source that is a copy, transcript or summary keeps that label in the link text: `third-party transcript`, `read through a summarizing fetch`, `search copy`.
- A figure from a report not yet merged says so.
- Say whose figure it is when two companies share a sentence.
- Above the table: say the market column is your reading, and the price's own history if the vault has it. If the vault cannot say why the price moved, say that.
- Below the table: a status count from a script, and "Status words are my reading, for you to correct."

## Cash and funding evidence

| Reading | Period | Figure | What it leaves in or out | Source |

Give every distinct reading the vault holds, even when they disagree, and say what separates them:

- Free cash flow as filed, and each reading with customer money taken out.
- Money from customers or partners behind the capex: deposits, prepayments, warrants, shares sold to them. Show each one's share of capex (calc.).
- New shares sold, or a program to sell them.

If a reading is not in the vault, write a row that says "unknown, not in the vault". The table needs at least two rows.

## How far to trust this

Short bullets, only what changes how the owner reads it:

- Age of the price and the run.
- Figures resting on copies, transcripts or summaries, not checked against a filing.
- Assumptions with no source that the numbers lean on.
- Conflicts between vault notes. Report them; do not resolve them quietly.
- Gaps: what is unknown, and what would fill it.
- Open items in the Journal that touch this note.

## Against the earlier draft

Write this last, after opening any earlier draft. Figures that differ, claims added or dropped, and lines that changed. If there is no earlier draft, say so.

## Figure labels

Every figure needs one of these beside it, in the same sentence or table cell, or a table-level line right under the table that covers it:

- A link with a date in its text: `[10-Q, filed Oct. 29, 2026](url)`. With no date on the page: `undated, retrieved Nov. 3, 2026`.
- `calc.` with its inputs: a dated link or vault page in the same sentence or row, or the numbers themselves, as in `(calc., $21.73 ÷ $123.20)`. A bare "calc." fails the check, because `Rules/facts.md` asks for the numbers behind it. `(calc., same source)` passes only if a dated source is on the same line or row.
- A vault page or run with its date: `` `strategic.html`, Nov. 3, 2026 ``.
- `my estimate`, `my count`, `my reading` or `assumed`, right beside the figure it covers. It does not cover other figures further along the sentence.

Targets and forecasts say so, every time. A chance is `approved` or `proposed`, and never looks like a fact.
