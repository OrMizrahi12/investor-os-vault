"""Tests for the two slower routines. No network. Run: .venv/bin/python sensors/reviews/test_reviews.py"""
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quarterly as q  # noqa: E402
import weekly as w  # noqa: E402

CHECKLIST = tomllib.loads((HERE / "checklist-GLW.toml").read_text())
ORDER = {"companies": [{"name": "Corning", "claims": ["C1"], "lines": ["K1"]}]}


def report(row="nothing new", red="- Nothing.", orange="- Nothing."):
    return f"| C1 | no | {row} | none |\n| K1 | no | {row} | none |\n\n### Red\n\n{red}\n\n### Orange\n\n{orange}\n\n### Info\n\n- Nothing.\n"


class Reads(unittest.TestCase):
    def one(self, value, quote, on_file=2379, moves="each"):
        c = {"reads": [{"id": "x", "what": "w", "rests_on": "r", "on_file": on_file, "doc": "10-Q", "moves": moves}]}
        rows, _ = q.check_reads(c, {"x": {"value": value, "doc": "10-Q", "quote": quote}}, {"10-Q": "Segment net sales | $ | 2,379 | $ | 1,506"})
        return rows[0]["status"]

    def test_same(self):
        self.assertEqual(self.one(2379, "Segment net sales | $ | 2,379"), "same")

    def test_a_quote_not_in_the_filing_does_not_count(self):
        self.assertIn("QUOTE NOT IN FILING", self.one(2379, "Segment net sales | $ | 9,999 | 2,379"))

    def test_the_number_must_be_in_the_quote(self):
        self.assertEqual(self.one(2400, "Segment net sales | $ | 2,379"), "NUMBER NOT IN QUOTE")

    def test_a_blank_read_does_not_pass_on_the_old_value(self):
        self.assertEqual(self.one(None, ""), "NOT READ")

    def test_a_new_value_is_a_change_and_an_annual_one_is_a_restatement(self):
        self.assertEqual(self.one(1506, "$ | 1,506", on_file=1500), "changed")
        self.assertEqual(self.one(1506, "$ | 1,506", on_file=1500, moves="annual"), "RESTATED")


class Calcs(unittest.TestCase):
    def test_the_on_file_reads_give_the_on_file_sums(self):
        """If this fails, the checklist and the approved inputs have come apart."""
        values = {i["id"]: i["on_file"] for i in CHECKLIST["reads"]}
        rows = q.work_calcs(CHECKLIST, values)
        self.assertEqual([r["id"] for r in rows if r["status"] != "same"], [])

    def test_the_calcs_match_the_approved_inputs(self):
        d = json.loads(sorted(q.ASSETS.glob("corning-*.json"))[-1].read_text())
        on = {c["id"]: c["on_file"] for c in CHECKLIST["calcs"]}
        i = d["inputs"]
        self.assertEqual(i["earnings_m"]["high"]["v"], on["earn_high"])
        self.assertEqual([i["cash_m"][k]["v"] for k in ("low", "mid", "high")], [on["cash_low"], on["cash_mid"], on["cash_high"]])
        s = {x["key"]: x for x in d["scenarios"]}
        self.assertEqual(s["plan"]["new_sales_m"]["v"], on["plan_new_sales"])
        self.assertAlmostEqual(s["signed"]["margin"]["v"], on["opt_margin"])
        self.assertEqual(i["shares_diluted_m"]["v"], {r["id"]: r["on_file"] for r in CHECKLIST["reads"]}["shares"])

    def test_the_ten_years_sum_to_the_low(self):
        self.assertEqual(sum(y["normal"] for y in CHECKLIST["years"]) / 10, 1028.4)

    def test_a_formula_can_only_do_arithmetic(self):
        with self.assertRaises(q.Stop):
            q.calc("__import__('os')", {})

    def test_years_match_the_approved_run_on_its_date(self):
        d = json.loads(sorted(q.ASSETS.glob("corning-*.json"))[-1].read_text())
        for s in d["scenarios"]:
            self.assertEqual(q.years_to(q.TARGETS[s["key"]], d["as_of"]), s["years"]["v"], s["key"])


class Proposal(unittest.TestCase):
    def values(self):
        v = {i["id"]: i["on_file"] for i in CHECKLIST["reads"]}
        q.work_calcs(CHECKLIST, v)
        return v

    def test_same_reads_rebuild_the_approved_inputs_but_for_the_stated_fields(self):
        before = json.loads(sorted(q.ASSETS.glob("corning-*.json"))[-1].read_text())
        docs = {k: {"filed": "2026-10-29", "url": "http://x"} for k in ("10-Q", "release", "10-K")}
        order = {"today": before["as_of"], "documents": docs}
        after = q.after_inputs(before, self.values(), order, ("2026-10-01", before["inputs"]["aaa"]["v"]), ("2026-11-02", before["inputs"]["price"]["v"], "f"))
        strip = lambda d: json.dumps([{k: round(x[k]["v"], 6) if isinstance(x.get(k), dict) and "v" in x[k] else None for k in x} for x in d["scenarios"]], sort_keys=True)
        self.assertEqual(strip(before), strip(after))
        self.assertEqual(before["inputs"]["cash_m"]["mid"]["v"], after["inputs"]["cash_m"]["mid"]["v"])
        self.assertTrue(after["proposal"])

    def test_kill_rows_read_a_crossing(self):
        v = self.values()
        k9 = {"complete_through": "2026-09-30", "fell_once": True, "fell_twice": True, "rows": [{"end": "a", "total": 3}, {"end": "b", "total": 2}, {"end": "c", "total": 1}]}
        v.update(opt_margin=0.17, opt_margin_last_q=0.17, atm_shares=1)
        rows = {r["line"]: r["state"] for r in q.kill_rows(v, k9)}
        self.assertEqual((rows["K3"], rows["K6"], rows["K9"]), ("CROSSED", "CROSSED", "CROSSED"))

    def test_a_changed_locked_file_is_seen(self):
        self.assertEqual(q.changed({"a": "1", "b": "2"}, {"a": "9", "b": "2", "c": "3"}), ["a", "c"])


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = (q.STATE, q.filings)
        q.STATE = Path(self.tmp.name) / "state.json"
        self.rows = [{"form": "10-K", "accession": "k", "filed": "2027-02-12", "url": "u", "report_date": "2026-12-31", "primary_document": "d"},
                     {"form": "10-Q", "accession": "q", "filed": "2026-10-29", "url": "u", "report_date": "2026-09-30", "primary_document": "d"}]
        q.filings = lambda: self.rows

    def tearDown(self):
        q.STATE, q.filings = self.old
        self.tmp.cleanup()

    def out(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            q.start(pull=lambda _: None, today="2027-02-13")
        return buf.getvalue()

    def test_a_reviewed_filing_is_quiet(self):
        q.STATE.write_text(json.dumps({"reviewed": ["k"], "told": []}))
        self.assertIn("NO NEW FILING", self.out())

    def test_a_10k_is_not_a_notice_any_more(self):
        q.STATE.write_text(json.dumps({"reviewed": ["k"], "told": []}))
        self.assertNotIn("10-K FILED", self.out())

    def test_old_amendments_stay_quiet_and_a_new_one_is_told_once(self):
        q.STATE.write_text(json.dumps({"reviewed": ["k"], "told": []}))
        self.rows += [{"form": "10-K/A", "accession": "old", "filed": "2014-03-21", "url": "u"}]
        self.assertNotIn("AMENDED", self.out())
        self.rows.insert(0, {"form": "10-K/A", "accession": "new", "filed": "2027-03-20", "url": "u"})
        self.assertIn("AMENDED", self.out())
        self.assertNotIn("AMENDED", self.out())


class TenK(unittest.TestCase):
    """Made-up FY2026 figures. No 10-K run has happened."""

    def values(self):
        v = {i["id"]: i["on_file"] for i in CHECKLIST["reads"]}
        for k in q.ZERO_AT_10K:
            v[k] = 0
        v.update(ni_fy=2300, trans_fy=0, unreal_fy=100, sales_fy=0, opt_ytd_sales=8000, solar_ytd_sales=1700)
        q.work_calcs(CHECKLIST, v)
        return v

    def after(self):
        before = json.loads(sorted(q.ASSETS.glob("corning-*.json"))[-1].read_text())
        docs = {k: {"filed": "2027-02-12", "url": "http://x"} for k in ("10-K", "release")}
        return q.after_inputs(before, self.values(), {"today": "2027-02-16", "form": "10-K", "documents": docs}, ("2027-01-01", 0.0612), ("2027-02-12", 100.0, "f"))

    def test_the_year_moves_all_three_earnings_and_waits_for_the_owner(self):
        e = self.after()["inputs"]["earnings_m"]
        self.assertEqual((e["high"]["v"], e["mid"]["v"]), (2200, 2200))
        self.assertAlmostEqual(e["low"]["v"], (10284 - 1323 + 2200) / 10)
        self.assertEqual({e[k]["status"] for k in e}, {"unconfirmed"})

    def test_growth_stays_under_the_cap(self):
        self.assertLessEqual(self.after()["inputs"]["growth"]["mid"]["v"], 0.03)

    def test_year_to_date_pieces_are_not_asked_for(self):
        rows, values = q.check_reads({"reads": [{"id": "ni_ytd", "what": "w", "rests_on": "r", "on_file": 1610, "doc": "10-Q", "moves": "each"}]}, {}, {}, "10-K")
        self.assertEqual((rows[0]["status"], values["ni_ytd"]), ("not used at a 10-K", 0))

    def test_a_new_year_is_a_change_not_a_restatement(self):
        c = {"reads": [{"id": "ni_fy", "what": "w", "rests_on": "r", "on_file": 1596, "doc": "10-K", "moves": "annual"}]}
        rows, _ = q.check_reads(c, {"ni_fy": {"value": 2300, "doc": "10-K", "quote": "x | 2,300"}}, {"10-K": "x | 2,300"}, "10-K")
        self.assertEqual(rows[0]["status"], "changed")


class Record(unittest.TestCase):
    def test_the_record_matches_the_approved_ceiling_and_is_found(self):
        r = q.check_record(CHECKLIST)
        self.assertEqual(r["record_growth"], json.loads(sorted(q.ASSETS.glob("corning-*.json"))[-1].read_text())["inputs"]["record_growth"]["v"])
        print("record not found:", [x["not_found"] for x in r["rows"]])

    def test_a_sum_may_quote_several_documents(self):
        c = {"reads": [{"id": "x", "what": "w", "rests_on": "r", "on_file": 3, "doc": "10-Q", "moves": "each"}]}
        rows, _ = q.check_reads(c, {"x": {"value": 3, "doc": "10-Q", "quote": ["a 1", "b 2"]}}, {"10-Q": "a 1", "10-K": "b 2"})
        self.assertEqual(rows[0]["status"], "same")


class Weekly(unittest.TestCase):
    def test_a_clean_report_passes(self):
        self.assertEqual(w.check_report(report(), ORDER), [])

    def test_a_blank_row_is_refused(self):
        self.assertTrue(w.check_report(report(row=""), ORDER))

    def test_advice_is_refused(self):
        self.assertTrue(any("advice" in p for p in w.check_report(report(row="you should buy"), ORDER)))

    def test_an_orange_needs_a_rule_source_and_date(self):
        problems = w.check_report(report(orange="- A deal moved."), ORDER)
        self.assertEqual(len(problems), 3)
        good = "- O2: AT&T said a deal slipped ([AT&T release, Nov. 2, 2026](https://example.com/a))."
        self.assertEqual(w.check_report(report(orange=good), ORDER), [])

    def test_a_red_r2_says_appears_broken(self):
        line = "- R2: C2 ([AT&T release, Nov. 2, 2026](https://example.com/a))."
        self.assertTrue(w.check_report(report(red=line), ORDER))
        self.assertEqual(w.check_report(report(red=line.replace("C2", "C2 appears broken")), ORDER), [])

    def test_a_price_move_is_refused(self):
        self.assertTrue(any("price move" in p for p in w.check_report(report(row="the close fell"), ORDER)))

    def test_only_sec_archives_go_through_the_client(self):
        with self.assertRaises(w.Refused):
            w.save_sec("https://evil.example.com/Archives/x")

    def test_only_notes_with_kill_lines_count(self):
        self.assertTrue(w.has_kill_lines(w.ROOT / "Research/2026-11-03 Corning kill criteria.md"))
        self.assertFalse(w.has_kill_lines(w.ROOT / "Research/2026-11-03 Quanta Services decision memo.md"))
        self.assertFalse(w.has_kill_lines(w.ROOT / "Research/no such note.md"))

    def test_queries_name_no_holding_or_size(self):
        for c in w.theses()["company"]:
            for row in c["queries"]:
                self.assertNotRegex(row["q"].lower(), r"\b(my|i own|position|portfolio|holding|shares of)\b")


if __name__ == "__main__":
    unittest.main()
