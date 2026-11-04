"""Offline tests for the saved valuation run. Run from the project root:
    .venv/bin/python sensors/valuation/test_save.py

sensors/strategic/model.py shares no code with value.py or save.py, so a figure that matches both was worked out twice.
"""

import ast
import copy
import datetime as dt
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import save  # noqa: E402

_s = importlib.util.spec_from_file_location("strategic_model", ROOT / "sensors/strategic/model.py")
model = importlib.util.module_from_spec(_s)
_s.loader.exec_module(model)

NOW = dt.datetime(2026, 11, 3, 12, tzinfo=dt.timezone.utc)
RUN, REPORT = save.build(save.newest_inputs(), NOW)
ROWS = {r["key"]: r for r in RUN["what_if"]["rows"]}
INPUTS = json.loads(save.newest_inputs().read_text())


def reading(key, text):
    return next(x for x in ROWS[key]["readings"] if x["text"] == text)


class TheMethod(unittest.TestCase):
    def test_figures_match_the_independent_model(self):
        b = model.base_value()
        self.assertAlmostEqual(RUN["base"]["low"], b["low"], places=6)
        self.assertAlmostEqual(RUN["base"]["mid"], b["mid"], places=6)
        self.assertAlmostEqual(RUN["base"]["high"], b["high"], places=6)
        self.assertAlmostEqual(RUN["strategic"], model.strategic(), places=6)
        self.assertAlmostEqual(RUN["trim_above"], model.trim_above(), places=6)
        self.assertAlmostEqual(RUN["buy_below"], b["mid"] / .75, places=6)

    def test_the_saved_report_is_value_py_and_agrees_with_the_json(self):
        for figure in ("**$14.06**", "**$21.73**", "**$30.03**", "Buy-below: $28.97", "Strategic value: $14.33", "Trim-above: $36.06", "Coverage: 17.6%"):
            self.assertIn(figure, REPORT)
        self.assertEqual(f'{RUN["coverage"]["mid"]:.1%}', "17.6%")
        self.assertNotIn("WHAT-IF", REPORT)

    def test_the_zone_today(self):
        self.assertEqual(RUN["zone"], "above")
        self.assertEqual(save.zone(21.73, 28.0, 28.97, 36.06), "under")
        self.assertEqual(save.zone(21.73, 30.0, 28.97, 36.06), "between")
        self.assertEqual(save.zone(21.73, 36.06, 28.97, 36.06), "between")
        self.assertEqual(save.zone(75, 100, 100, 200), "under")  # exactly 75%
        self.assertEqual(save.zone(74.9, 100, 99.9, 200), "between")  # 74.9% does not round up

    def test_the_price_never_moves_value(self):
        a, b = save.work(INPUTS, 123.2), save.work(INPUTS, 1.0)
        for key in ("low", "base", "high", "strategic", "buy", "trim"):
            self.assertEqual(a[key], b[key])

    def test_a_what_if_leaves_the_method_constants_as_they_were(self):
        before = save.value.RATE, dict(save.value.VOTES), save.value.cash_sum
        save.work(INPUTS, 123.2, rate=.08, votes=dict(earn=1, cash=0, bond=0))
        self.assertEqual((save.value.RATE, dict(save.value.VOTES), save.value.cash_sum), before)
        self.assertEqual(save.work(INPUTS, 123.2)["base"], RUN["base"]["mid"])

    def test_the_inputs_file_is_not_changed_by_a_what_if(self):
        self.assertEqual(json.loads(save.newest_inputs().read_text()), INPUTS)


class WhatIfsTieOut(unittest.TestCase):
    """Against model.py, which worked these on strategic.html, and the owner's own what-if in the Journal."""

    def same(self, got, want):
        self.assertAlmostEqual(got, want, places=6)

    def test_the_rate_reaches_every_vote_and_scenario(self):
        for r, text in ((.08, "8%"), (.10, "10%")):
            self.same(reading("rate", text)["trim"], model.base_mid_at(r) + model.strategic(r=r))
            self.same(reading("rate", text)["base"], model.base_mid_at(r))

    def test_margin_with_the_rival_cut_following_it(self):
        self.same(reading("margin", f"{model.OPT_INCREMENTAL * 100:.1f}%")["trim"], model.trim_above(margin=model.OPT_INCREMENTAL))
        self.same(reading("margin", f"{model.OPT_MARGIN_LOW * 100:.1f}%")["trim"], model.trim_above(margin=model.OPT_MARGIN_LOW))

    def test_the_ladder_still_adds_up_when_a_step_changes(self):
        self.same(reading("new_share", "50%")["trim"], model.trim_above(new_share=.5))
        self.same(reading("new_share", "100%")["trim"], model.trim_above(new_share=1))
        self.same(reading("display_rise", "10%")["trim"], model.trim_above(display_rise=.10))
        self.same(reading("display_rise", "0%")["trim"], model.trim_above(display_rise=0))

    def test_capital_both_ends(self):
        self.same(reading("capital", "none: customers fund every plant")["trim"], model.trim_above(capital=False))
        self.same(reading("capital", "lost when a fiber scenario fails")["trim"], model.trim_above() - model.failed_capital())

    def test_base_high_start(self):
        self.same(reading("from_high", "base high")["trim"], model.base_value()["high"] + model.strategic())

    def test_chances_match_the_owners_what_if_of_nov_3(self):
        for key, text, want in (("signed", "100%", 37.98), ("plan", "80%", 42.35), ("scaleup", "40%", 37.63), ("solar", "70%", 37.02), ("display", "100%", 37.07), ("rival", "80%", 34.56)):
            self.assertEqual(round(reading(f"chance_{key}", text)["trim"], 2), want)

    def test_chances_and_scenario_sizes_leave_the_base_alone(self):
        for key, row in ROWS.items():
            if row["scope"] == "trim":
                self.assertAlmostEqual(row["swing"]["base"], 0, places=9, msg=key)
                self.assertAlmostEqual(row["swing"]["buy"], 0, places=9, msg=key)

    def test_buy_below_is_always_the_middle_over_the_bar(self):
        for row in ROWS.values():
            for x in row["readings"]:
                self.assertAlmostEqual(x["buy"], x["base"] / .75, places=9)

    def test_a_hand_sum_for_earnings_at_the_high(self):
        e = 2051 / 871
        cash = 1256 / 871 * (1 + INPUTS["inputs"]["growth"]["mid"]["v"]) / (.09 - INPUTS["inputs"]["growth"]["mid"]["v"])
        self.same(reading("earnings", "$2,051M")["base"], .4 * e / .09 + .4 * cash + .2 * e / .0612)

    def test_the_flags_mark_what_breaks_the_ladder(self):
        self.assertTrue(reading("chance_plan", "80%")["flags"])
        self.assertTrue(reading("chance_signed", "35%")["flags"])
        self.assertFalse(reading("earnings", "$2,051M")["flags"])

    def test_most_skips_far_ends_and_broken_shapes_and_those_rows_stay(self):
        most = RUN["what_if"]["most"]
        for out, key in most.items():
            row = ROWS[key]
            self.assertFalse(row["ends"])
            self.assertFalse(any(x["flags"] for x in row["readings"]))
            self.assertIn(key, RUN["what_if"]["ranked"][out])
        self.assertIn("votes", RUN["what_if"]["ranked"]["trim"])
        self.assertIn("chance_plan", RUN["what_if"]["ranked"]["trim"])

    def test_no_reading_uses_a_size_without_a_basis(self):
        for row in ROWS.values():
            self.assertRegex(row["basis"], r"20\d\d")


class SkillChecks(unittest.TestCase):
    def test_a_note_that_disagrees_stops(self):
        with tempfile.TemporaryDirectory() as f:
            note = Path(f) / "n.md"
            note.write_text(save.NOTE.read_text().replace("trim above: \"$36.06", "trim above: \"$40.00"))
            method = save.work(INPUTS, 123.2)
            with self.assertRaisesRegex(save.Stop, "disagree"):
                save.check_note(method, note)

    def test_a_changed_aaa_stops(self):
        with tempfile.TemporaryDirectory() as f:
            csv = Path(f) / "a.csv"
            csv.write_text("observation_date,AAA\n2026-11-01,6.50\n")
            with self.assertRaisesRegex(save.Stop, "refresh"):
                save.check_aaa(INPUTS, csv)

    def test_aaa_a_point_away_reopens_the_rate(self):
        moved = copy.deepcopy(INPUTS)
        moved["inputs"]["aaa"]["v"] = .0712
        with tempfile.TemporaryDirectory() as f:
            csv = Path(f) / "a.csv"
            csv.write_text("observation_date,AAA\n2026-11-01,7.12\n")
            with self.assertRaisesRegex(save.Stop, "reopens"):
                save.check_aaa(moved, csv)

    def test_a_newer_filing_stops(self):
        with tempfile.TemporaryDirectory() as f:
            path = Path(f) / "f.jsonl"
            path.write_text(json.dumps({"form": "10-K", "filed": "2027-02-12"}) + "\n")
            with self.assertRaisesRegex(save.Stop, "newer"):
                save.check_filing(INPUTS, path)

    def test_a_newer_8k_does_not_stop(self):
        with tempfile.TemporaryDirectory() as f:
            path = Path(f) / "f.jsonl"
            path.write_text(json.dumps({"form": "10-Q", "filed": "2026-10-29"}) + "\n" + json.dumps({"form": "8-K", "filed": "2027-02-12"}) + "\n")
            self.assertIn("as used", save.check_filing(INPUTS, path))

    def test_an_unsourced_input_stops(self):
        bad = copy.deepcopy(INPUTS)
        bad["inputs"]["shares_diluted_m"]["src"] = "memory"
        with self.assertRaisesRegex(save.Stop, "no dated source"):
            save.work(bad, 123.2)


class TheFile(unittest.TestCase):
    def test_saved_run_matches_a_fresh_build(self):
        saved = json.loads(max(save.RUNS.glob("*.json")).read_text())
        fresh = json.loads(json.dumps(RUN))
        for key in ("base", "coverage", "buy_below", "strategic", "trim_above", "zone", "price", "series", "worked_out", "what_if", "scenarios", "no_vote"):
            self.assertEqual(saved[key], fresh[key], key)
        report = max(save.RUNS.glob("*.md")).read_text()
        self.assertEqual(report, REPORT)

    def test_a_second_run_gets_its_own_files(self):
        with tempfile.TemporaryDirectory() as f:
            self.assertEqual(save.next_stem("2026-11-03", f), "2026-11-03-01")
            (Path(f) / "2026-11-03-01.json").write_text("{}")
            self.assertEqual(save.next_stem("2026-11-03", f), "2026-11-03-02")

    def test_no_fetch_and_no_write_outside_runs(self):
        source = (HERE / "save.py").read_text()
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertFalse(imported & {"yfinance", "requests", "urllib", "socket", "http", "httpx", "curl_cffi", "edgar", "watch"})
        self.assertNotIn("prices.fetch", source)
        self.assertEqual(re.findall(r"\(RUNS / [^)]*\)\.write_text", source).__len__(), 2)
        self.assertNotIn("yfinance", sys.modules)


if __name__ == "__main__":
    unittest.main(verbosity=1)
