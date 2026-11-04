#!/usr/bin/env python3
"""Tests for check_note.py. Run: python3 .claude/skills/thesis/scripts/test_check_note.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_note import check  # noqa: E402

SRC = "[10-Q, filed Oct. 29, 2026](https://sec.gov/x.htm)"
GOOD = f"""---
company: "[[X]]"
status: draft, not approved
triage: research
skeptic review: not run
---

# X thesis note

**The case is plausible, but coverage is 17.6% (calc., $21.73 ÷ $123.20).**

**Claim count:** 1 claims: 0 supports, 1 mixed, 0 against, 0 unknown (my count).

No buy recommendation. The thesis is not approved.

## Six questions

### 1. The mechanism
Sales were $2,379M ({SRC}).
### 2. The value in dollars
Value is $21.73 (calc., `run.md`, Nov. 3, 2026).
### 3. The probability
A 40% chance, approved by the owner on `strategic.html`, Nov. 3, 2026.
### 4. The timing
Test in 2027.
### 5. What today's price already implies
21.8% a year (calc., `run.md`, Nov. 3, 2026).
### 6. What would prove it wrong
See below.

## What the market believes, against what the evidence shows

| Claim | Status | Market seems to believe (my reading) | Our evidence shows | We simply do not know |
|---|---|---|---|---|
| **C1.** Fiber stays short. | mixed | 21.8% growth (calc., `run.md`, Nov. 3, 2026) | $2,379M ({SRC}) | Nothing found |

## Cash and funding evidence

| Reading | Period | Figure | What it leaves in or out | Source |
|---|---|---|---|---|
| Free cash flow | FY2025 | $1,413M | Deposits in | {SRC} |
| Deposit-out cash | FY2025 | $1,145M | Deposits out | {SRC} |

## Kill criteria

| Line | Claim | Measure | Threshold | Test date | Today | Status | Set by | Source |
|---|---|---|---|---|---|---|---|---|
| K1 | C1 | Sales | At or below $2,379M | Q4 2027 | $2,379M | Not crossed | owner, Nov. 3, 2026 | {SRC} |

## Monitoring plan
A person reads it.
## What I cut
Nothing.
## How far to trust this
Fine.
## Against the earlier draft
None.
"""


class Check(unittest.TestCase):
    def test_good_note_is_clean(self):
        self.assertEqual(check(GOOD), [])

    def test_status_approved_fails(self):
        out = check(GOOD.replace("status: draft, not approved", "status: approved"))
        self.assertTrue(any("status must say" in f for f in out))

    def test_approval_claim_fails(self):
        out = check(GOOD.replace("The thesis is not approved.", "The thesis is approved."))
        self.assertTrue(any("claim of approval" in f for f in out))

    def test_skeptic_claim_fails(self):
        out = check(GOOD.replace("Nothing.\n", "It survived a skeptic's review.\n"))
        self.assertTrue(any("claim of approval" in f for f in out))

    def test_negated_approval_passes(self):
        out = check(GOOD.replace("Nothing.\n", "This has not survived a skeptic's review.\n"))
        self.assertEqual(out, [])

    def test_buy_recommendation_fails_but_no_buy_passes(self):
        out = check(GOOD.replace("No buy recommendation.", "A buy recommendation follows."))
        self.assertTrue(any("reads as advice" in f for f in out))

    def test_bare_figure_in_prose_fails(self):
        out = check(GOOD.replace("Test in 2027.", "Margin was 22.4% in the quarter."))
        self.assertTrue(any("figure with no source" in f for f in out))

    def test_bare_figure_in_cell_fails(self):
        out = check(GOOD.replace("21.8% growth (calc., `run.md`, Nov. 3, 2026)", "21.8% growth"))
        self.assertTrue(any("figure with no source" in f for f in out))

    def test_undated_link_fails(self):
        out = check(GOOD.replace("10-Q, filed Oct. 29, 2026", "10-Q"))
        self.assertTrue(any("no date in its text" in f for f in out))

    def test_decimals_in_dates_not_split(self):
        out = check(GOOD.replace("Test in 2027.", f"Sales were $1.5 billion, up 5% ({SRC})."))
        self.assertEqual(out, [])

    def test_missing_section_fails(self):
        out = check(GOOD.replace("## What I cut", "## Other"))
        self.assertTrue(any("missing section: What I cut" in f for f in out))

    def test_missing_question_fails(self):
        out = check(GOOD.replace("### 3. The probability", "### 3. Odds"))
        self.assertTrue(any("missing question 3" in f for f in out))

    def test_kill_line_without_threshold_fails(self):
        out = check(GOOD.replace("At or below $2,379M", "Sales disappoint"))
        self.assertTrue(any("no number or event" in f for f in out))

    def test_kill_line_without_date_fails(self):
        out = check(GOOD.replace("| Q4 2027 |", "| soon |"))
        self.assertTrue(any("no date" in f for f in out))

    def test_kill_line_without_setter_fails(self):
        out = check(GOOD.replace("| owner, Nov. 3, 2026 |", "| Claude |"))
        self.assertTrue(any("who set it" in f for f in out))

    def test_empty_market_cell_fails(self):
        out = check(GOOD.replace("| Nothing found |", "|  |"))
        self.assertTrue(any("empty cell" in f for f in out))

    def test_no_coverage_fails(self):
        out = check(GOOD.replace("coverage is", "the share is"))
        self.assertTrue(any("coverage is not stated" in f for f in out))

    def test_bare_calc_fails(self):
        out = check(GOOD.replace("Test in 2027.", "Margin was 22.4% (calc.)."))
        self.assertTrue(any("figure with no source" in f for f in out))

    def test_calc_with_named_inputs_passes(self):
        out = check(GOOD.replace("Test in 2027.", "Margin was 22.4% (calc., $532M ÷ $2,379M)."))
        self.assertEqual(out, [])

    def test_calc_pointer_needs_a_source_on_the_line(self):
        out = check(GOOD.replace("Test in 2027.", "Margin was 22.4% (calc., same source)."))
        self.assertTrue(any("figure with no source" in f for f in out))
        out = check(GOOD.replace("Test in 2027.", f"Sales rose ({SRC}). Margin was 22.4% (calc., same source)."))
        self.assertEqual(out, [])

    def test_assumed_covers_only_a_near_figure(self):
        out = check(GOOD.replace("Test in 2027.", "Use an assumed 5% rise."))
        self.assertEqual(out, [])
        far = "Use an assumed rise, and in another part of this very long sentence sales were $900M."
        out = check(GOOD.replace("Test in 2027.", far))
        self.assertTrue(any("$900M" in f for f in out))

    def test_status_with_limit_passes(self):
        text = GOOD.replace("| mixed | 21.8%", "| supports, to 2027 | 21.8%").replace("0 supports, 1 mixed", "1 supports, 0 mixed")
        self.assertEqual(check(text), [])

    def test_unknown_status_word_fails(self):
        out = check(GOOD.replace("| mixed | 21.8%", "| promising | 21.8%"))
        self.assertTrue(any("status must start" in f for f in out))

    def test_count_must_match_table(self):
        out = check(GOOD.replace("0 supports, 1 mixed", "1 supports, 0 mixed"))
        self.assertTrue(any("claim count for mixed" in f for f in out))

    def test_missing_count_fails(self):
        out = check(GOOD.replace("**Claim count:**", "Count:"))
        self.assertTrue(any("no claim count" in f for f in out))

    def test_headline_cannot_outrun_count(self):
        out = check(GOOD.replace("The case is plausible", "The case is real"))
        self.assertTrue(any("headline says 'real'" in f for f in out))
        text = GOOD.replace("The case is plausible", "The case is real").replace("| mixed | 21.8%", "| supports | 21.8%").replace("0 supports, 1 mixed", "1 supports, 0 mixed")
        self.assertEqual(check(text), [])

    def test_cash_section_needs_two_readings(self):
        out = check(GOOD.replace(f"| Deposit-out cash | FY2025 | $1,145M | Deposits out | {SRC} |\n", ""))
        self.assertTrue(any("two readings" in f for f in out))

    def test_kill_note_match(self):
        kill = """
| Claim | Words |
|---|---|
| C1 | Fiber stays short. |

| Line | Claim | Number or event | Threshold | Today | Status | Source |
|---|---|---|---|---|---|---|
| **K1** | C1 | Sales | At or below $2,379M | x | x | x |
"""
        self.assertEqual(check(GOOD, (), kill), [])
        out = check(GOOD.replace("Fiber stays short.", "Fiber demand beats supply."), (), kill)
        self.assertTrue(any("C1 differs" in f for f in out))
        out = check(GOOD.replace("At or below $2,379M", "At or below $2,400M"), (), kill)
        self.assertTrue(any("K1 is not copied" in f for f in out))

    def test_vault_page_needs_a_date(self):
        out = check(GOOD.replace("Test in 2027.", "Margin was 22.4% on `strategic.html`."))
        self.assertTrue(any("figure with no source" in f for f in out))


if __name__ == "__main__":
    unittest.main()
