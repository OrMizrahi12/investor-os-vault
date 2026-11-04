"""Offline tests. No request leaves this computer. Run: uv run python sensors/8k-watch/test_watch.py"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import draw  # noqa: E402
import watch  # noqa: E402

FLAGS = ["1.01", "2.01", "2.02", "5.02", "3.02", "7.01", "8.01"]
COMPANY = {"name": "Corning", "ticker": "GLW", "since": "2025-11-02", "cik": 24741}


def filing(accession, filed, items="7.01", form="8-K"):
    return {"accession": accession, "form": form, "filed": filed, "report_date": filed, "items": items,
            "primary_document": "d.htm", "url": f"https://www.sec.gov/Archives/edgar/data/24741/{accession}/d.htm"}


DOC = b"<p>Item 7.01 Regulation FD Disclosure.</p><p>The company will speak at a conference next week about things.</p>"


class ReadItems(unittest.TestCase):
    def read(self, text):
        return list(watch.read_items(text))

    def test_real_heading_shapes(self):
        # Each shape below is copied from a Corning 8-K.
        self.assertEqual(self.read("<div>Item\n7.01 Regulation FD Disclosure.</div>"), ["7.01"])
        self.assertEqual(self.read("<p>ITEM 8.01.</p><p>Other Events.</p>"), ["8.01"])
        self.assertEqual(self.read("<p>Item 3.02Unregistered Sales of Equity\nSecurities.</p>"), ["3.02"])
        self.assertEqual(self.read("<p>Item&nbsp;2.02.&#160;Results of Operations</p>"), ["2.02"])
        self.assertEqual(self.read("<table><tr><td>Item 5.07.</td><td>Submission</td></tr></table>"), ["5.07"])

    def test_cross_references_are_not_headings(self):
        doc = ("<p>Item 2.02 Results</p>"
               "<p>As detailed within Item 7.01 in this Current Report.</p>"
               "<p>Item 7.01 of this Current Report on Form 8-K shall not be deemed filed.</p>"
               "<p>Pursuant to Item\n7.01 of this report.</p>")
        self.assertEqual(self.read(doc), ["2.02"])

    def test_keeps_first_real_paragraph_and_skips_boilerplate(self):
        doc = ("<p>Item 7.01 Regulation FD</p><p>The information furnished pursuant to this item is not filed anywhere.</p>"
               "<p>Corning will host investors at the exchange on May 6, 2026 to talk.</p><p>Second paragraph of real text here, long enough.</p>"
               "<p>SIGNATURE</p><p>Pursuant to the requirements of the Exchange Act, the registrant signed.</p>")
        self.assertEqual(watch.read_items(doc)["7.01"], "Corning will host investors at the exchange on May 6, 2026 to talk.")

    def test_no_headings(self):
        self.assertEqual(self.read("<p>Nothing here.</p>"), [])


class Items(unittest.TestCase):
    def test_union_keeps_item_index_left_out(self):
        self.assertEqual(watch.combine_items(["2.02", "7.01"], ["2.02", "7.01", "9.01"]), ["2.02", "7.01", "9.01"])

    def test_union_keeps_item_filing_parse_missed(self):
        self.assertEqual(watch.combine_items(["3.02"], []), ["3.02"])

    def test_rule_rating(self):
        self.assertEqual(watch.rule_rating(["3.02", "7.01", "9.01"])[0], "high")
        self.assertEqual(watch.rule_rating(["4.02"])[0], "high")  # not a flag, still high
        self.assertEqual(watch.rule_rating(["8.01", "9.01"])[0], "medium")
        self.assertEqual(watch.rule_rating(["5.07"])[0], "low")
        self.assertEqual(watch.rule_rating([])[0], "medium")

    def test_every_flag_and_rule_item_has_a_name(self):
        for number in set(FLAGS) | watch.HIGH_ITEMS | watch.MEDIUM_ITEMS:
            self.assertIn(number, watch.ITEM_NAMES)


class Config(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "x.toml"

    def tearDown(self):
        self.dir.cleanup()

    def bad(self, loader, text):
        self.path.write_text(text)
        with self.assertRaises(watch.WatchError):
            loader(self.path)

    def test_watchlist_refuses_bad_files(self):
        self.bad(watch.load_watchlist, 'flag_items=["7.01"]\n')
        self.bad(watch.load_watchlist, 'flag_items=["7.01"]\n[[company]]\nname="C"\nticker="GLW"\n')
        self.bad(watch.load_watchlist, 'flag_items=["7.01"]\n[[company]]\nname="C"\nticker="GLW"\nsince="soon"\n')
        self.bad(watch.load_watchlist, 'flag_items=["7.77"]\n[[company]]\nname="C"\nticker="GLW"\nsince="2026-01-01"\n')

    def test_real_watchlist_starts_with_corning_and_the_seven_flags(self):
        flags, companies = watch.load_watchlist()
        self.assertEqual(sorted(flags), sorted(FLAGS))
        self.assertEqual(companies[0]["ticker"], "GLW")

    def test_readings_refuse_bad_rows(self):
        self.bad(watch.load_readings, '[[reading]]\naccession="a"\nattention="urgent"\nreason="r"\nread="2026-01-01"\n')
        self.bad(watch.load_readings, '[[reading]]\naccession="a"\nattention="low"\nread="2026-01-01"\n')
        row = '[[reading]]\naccession="a"\nattention="low"\nreason="r"\nread="2026-01-01"\n'
        self.bad(watch.load_readings, row + row)


class Flow(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        self.inbox = root / "Inbox"
        self.inbox.mkdir()
        self.seen_path = root / "seen.json"
        self.seen = {}
        self.fetched = []

    def tearDown(self):
        self.dir.cleanup()

    def fetch(self, f):
        self.fetched.append(f["accession"])
        return DOC

    def write(self, filings, readings=None):
        return watch.write_new(COMPANY, filings, self.fetch, self.seen, FLAGS, readings or {}, self.inbox, self.seen_path, "2026-11-02")

    def test_writes_one_note_per_8k_and_skips_other_forms_and_old_filings(self):
        written = self.write([filing("a", "2026-05-06"), filing("b", "2026-05-07", form="8-K/A"),
                              filing("c", "2026-05-08", form="10-Q"), filing("d", "2025-11-01"),
                              filing("e", "2025-11-02")])
        self.assertEqual({e["accession"] for e in written}, {"a", "b", "e"})
        self.assertEqual(len(list(self.inbox.iterdir())), 3)

    def test_second_run_finds_nothing_and_fetches_nothing(self):
        self.write([filing("a", "2026-05-06")])
        self.fetched.clear()
        self.assertEqual(self.write([filing("a", "2026-05-06")]), [])
        self.assertEqual(self.fetched, [])

    def test_deleted_note_stays_deleted(self):
        self.write([filing("a", "2026-05-06")])
        next(self.inbox.iterdir()).unlink()
        self.assertEqual(self.write([filing("a", "2026-05-06")]), [])
        self.assertEqual(list(self.inbox.iterdir()), [])

    def test_seen_survives_a_restart(self):
        self.write([filing("a", "2026-05-06")])
        self.seen = watch.load_seen(self.seen_path)
        self.assertIn("a", self.seen)

    def test_stop_mid_run_keeps_earlier_notes(self):
        def broken(f):
            if f["accession"] == "b":
                raise watch.WatchError("boom")
            return DOC
        with self.assertRaises(watch.WatchError):
            watch.write_new(COMPANY, [filing("a", "2026-01-01"), filing("b", "2026-01-02")], broken, self.seen,
                            FLAGS, {}, self.inbox, self.seen_path, "2026-11-02")
        self.assertEqual(list(watch.load_seen(self.seen_path)), ["a"])

    def test_note_names_items_and_flags(self):
        self.write([filing("a", "2026-05-06", items="3.02,7.01,9.01")])
        text = next(self.inbox.iterdir()).read_text()
        self.assertIn("| 3.02 | Unregistered Sales of Equity Securities | yes |", text)
        self.assertIn("| 9.01 | Financial Statements and Exhibits | no |", text)
        self.assertIn('flagged: ["3.02", "7.01"]', text)
        self.assertIn("attention: high", text)
        self.assertIn("filed May 6, 2026", text)

    def test_note_does_not_quote_the_exhibit_list(self):
        doc = b"<p>Item 9.01 Financial Statements and Exhibits</p><p>104 Cover Page Interactive File with embedded tags here</p>"
        watch.write_new(COMPANY, [filing("a", "2026-05-06", items="9.01")], lambda f: doc, self.seen,
                        FLAGS, {}, self.inbox, self.seen_path, "2026-11-02")
        self.assertNotIn("Cover Page", next(self.inbox.iterdir()).read_text())

    def test_note_reports_index_gap_both_ways(self):
        self.write([filing("a", "2026-05-06", items="2.02")])
        self.assertIn("leaves out 7.01", next(self.inbox.iterdir()).read_text())

    def test_note_says_when_no_heading_could_be_read(self):
        watch.write_new(COMPANY, [filing("a", "2026-05-06", items="8.01")], lambda f: b"<p>none</p>", self.seen,
                        FLAGS, {}, self.inbox, self.seen_path, "2026-11-02")
        text = next(self.inbox.iterdir()).read_text()
        self.assertIn("No item headings could be read", text)
        self.assertIn("attention: medium", text)

    def test_form_slash_is_safe_in_file_name(self):
        self.write([filing("a", "2026-05-06", form="8-K/A")])
        self.assertTrue(next(self.inbox.iterdir()).name.endswith("8-K-A a.md"))

    def test_reading_overrides_rule_and_is_labelled(self):
        reading = {"accession": "a", "attention": "high", "reason": "Why.", "read": "2026-11-02"}
        self.write([filing("a", "2026-05-06", items="8.01")], {"a": reading})
        text = next(self.inbox.iterdir()).read_text()
        self.assertIn("attention: high", text)
        self.assertIn("rated by: reading", text)

    def test_later_reading_updates_an_untouched_note(self):
        self.write([filing("a", "2026-05-06", items="8.01")])
        reading = {"accession": "a", "attention": "high", "reason": "Why.", "read": "2026-11-02"}
        updated, skipped = watch.sync_readings(self.seen, FLAGS, {"a": reading}, self.inbox, self.seen_path)
        self.assertEqual((len(updated), skipped), (1, []))
        self.assertIn("attention: high", next(self.inbox.iterdir()).read_text())

    def test_later_reading_leaves_an_edited_note_alone(self):
        self.write([filing("a", "2026-05-06", items="8.01")])
        path = next(self.inbox.iterdir())
        path.write_text(path.read_text() + "\nMy own thought.\n")
        reading = {"accession": "a", "attention": "high", "reason": "Why.", "read": "2026-11-02"}
        updated, skipped = watch.sync_readings(self.seen, FLAGS, {"a": reading}, self.inbox, self.seen_path)
        self.assertEqual((updated, len(skipped)), ([], 1))
        self.assertIn("My own thought.", path.read_text())


class Page(unittest.TestCase):
    def entries(self):
        seen, inbox = {}, None
        with tempfile.TemporaryDirectory() as d:
            inbox = Path(d)
            watch.write_new(COMPANY, [filing("a", "2026-05-06", items="8.01"), filing("b", "2026-02-01")],
                            lambda f: DOC, seen, FLAGS, {}, inbox, inbox / "s.json", "2026-11-02")
        return seen

    def test_every_filing_is_drawn_with_its_reason(self):
        seen = self.entries()
        page = draw.build_page(FLAGS, [COMPANY], seen, {}, "2026-11-02")
        self.assertEqual(page.count('class="row"'), 2)
        self.assertEqual(page.count('class="mark"'), 4)  # wide chart and phone chart
        self.assertIn("Rule only, not read yet", page)

    def test_escapes_text_from_outside(self):
        seen = self.entries()
        reading = {"accession": "a", "attention": "high", "reason": "<script>x</script>", "read": "2026-11-02"}
        page = draw.build_page(FLAGS, [COMPANY], seen, {"a": reading}, "2026-11-02")
        self.assertNotIn("<script>x", page)
        self.assertIn("&lt;script&gt;x", page)

    def test_position_is_by_date(self):
        self.assertLess(draw.x_of("2026-01-01", "2025-11-02", "2026-11-02"), draw.x_of("2026-06-01", "2025-11-02", "2026-11-02"))

    def test_refuses_empty_page(self):
        with self.assertRaises(watch.WatchError):
            draw.build_page(FLAGS, [COMPANY], {}, {}, "2026-11-02")


if __name__ == "__main__":
    unittest.main()
