"""Offline tests for the catalyst radar. Run from the project root:
    .venv/bin/python sensors/radar/test_radar.py
"""

import datetime as dt
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
import radar  # noqa: E402  (sets the path for the two below)
import edgar  # noqa: E402
import frames  # noqa: E402

TODAY = dt.date(2026, 11, 3)
LIMITS = {"min_rise_pct": 25, "min_rise_usd": 10_000_000, "min_later_usd": 25_000_000, "min_days_between": 75, "max_days_between": 105}

CATALYST = """---
ticker: GLW
status: no buy
window: 2027
last checked: "2026-11-03"
{dates}sources:
  - "https://www.sec.gov/x.htm"
---

# Title

## What it is
A catalyst for [[Corning]] and [[Verizon]].

## When
{when}

## Outcome
{outcome}

## Rules this note depends on

- [[facts]]: every fact.
"""
DATES = 'date start: "2026-11-27"\ndate quote: "Nov. 27, 2026"\ndate kind: stated\n'


def row(cik, val, end, accn="a"):
    return {"cik": cik, "entityName": f"Co {cik}", "end": end, "val": val, "accn": accn, "loc": "US-NY"}


def frame(*rows):
    return {"tag": "T", "ccp": "CY", "data": list(rows)}


class FakeClient:
    def __init__(self, bodies=None):
        self.sent, self.bodies = [], bodies or {}

    def get(self, url):
        self.sent.append(url)
        if url not in self.bodies:
            err = edgar.EdgarError(f"SEC answered 404 for {url}")
            err.__cause__ = type("NotFound", (Exception,), {"code": 404})()
            raise err
        return json.dumps(self.bodies[url]).encode()

    def busiest_second(self):
        return 1


class RateLimit(unittest.TestCase):
    def test_requests_are_spaced_under_sec_limit_through_the_edgar_client(self):
        clock = {"t": 0.0}

        class Opener:
            def open(self, request, timeout):
                class R:
                    headers = {}
                    def __enter__(self): return self  # noqa: E301,E704
                    def __exit__(self, *a): return False  # noqa: E301,E704
                    def read(self): return b"{}"  # noqa: E301,E704
                return R()

        client = edgar.SecClient("x a@b.co", 8, opener=Opener(), clock=lambda: clock["t"], sleep=lambda s: clock.__setitem__("t", clock["t"] + s))
        for _ in range(40):
            client.get("https://data.sec.gov/api/xbrl/frames/x.json")
        self.assertLessEqual(client.busiest_second(), 8)

    def test_real_settings_stay_below_ten(self):
        self.assertLess(edgar.load_settings()["rate"], 10)

    def test_the_run_cap_stops_asking(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            client.sent = ["x"] * 5
            fetch = frames.Fetcher(edgar.Cache(tmp, lambda: client, 24), lambda: client, 5)
            with self.assertRaisesRegex(edgar.EdgarError, "cap"):
                fetch("T", "CY2026Q3I", True)
            self.assertEqual(len(client.sent), 5)

    def test_a_second_run_sends_nothing_when_the_cache_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = frames.frame_url("T", "CY2026Q3I")
            client = FakeClient({url: frame(row(1, 5, "2026-09-30"))})
            fetch = frames.Fetcher(edgar.Cache(tmp, lambda: client, 24), lambda: client, 10)
            fetch("T", "CY2026Q3I", True)
            fetch("T", "CY2026Q3I", True)
            self.assertEqual(len(client.sent), 1)

    def test_a_missing_frame_is_noted_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            fetch = frames.Fetcher(edgar.Cache(tmp, lambda: client, 24), lambda: client, 10)
            self.assertIsNone(fetch("T", "CY2030Q1I", True))
            self.assertEqual(fetch.missing, ["T CY2030Q1I"])


class Quarters(unittest.TestCase):
    def test_latest_ended_quarter(self):
        self.assertEqual(frames.latest_ended_quarter(dt.date(2026, 11, 3)), (2026, 3))
        self.assertEqual(frames.latest_ended_quarter(dt.date(2026, 1, 2)), (2025, 4))
        self.assertEqual(frames.latest_ended_quarter(dt.date(2026, 3, 31)), (2025, 4))
        self.assertEqual(frames.latest_ended_quarter(dt.date(2026, 4, 1)), (2026, 1))

    def test_quarters_back_cross_the_year(self):
        self.assertEqual(frames.quarters_back(2026, 1, 3), [(2026, 1), (2025, 4), (2025, 3)])


class Compare(unittest.TestCase):
    def pair(self, a, b, year=(None, None)):
        return [("Q2", frame(a) if a else frame()), ("Q3", frame(b)), ("Y2", frame(year[0]) if year[0] else None), ("Y3", frame(year[1]) if year[1] else None)]

    def test_a_clear_rise_is_a_row_with_a_calc(self):
        rows, _ = frames.compare("T", "L", self.pair(row(1, 100e6, "2026-06-30"), row(1, 200e6, "2026-09-30")), LIMITS)
        self.assertEqual((rows[0]["rise_pct"], rows[0]["rise_usd"]), (100.0, 100e6))

    def test_small_rises_and_small_balances_are_left_out(self):
        for a, b in ((100e6, 110e6), (10e6, 24e6), (100e6, 105e6), (200e6, 100e6)):
            rows, _ = frames.compare("T", "L", self.pair(row(1, a, "2026-06-30"), row(1, b, "2026-09-30")), LIMITS)
            self.assertEqual(rows, [], (a, b))

    def test_two_balances_not_a_quarter_apart_are_not_compared(self):
        rows, counts = frames.compare("T", "L", self.pair(row(1, 100e6, "2026-03-31"), row(1, 200e6, "2026-09-30")), LIMITS)
        self.assertEqual((rows, counts["apart"]), ([], 1))

    def test_zero_or_negative_start_is_counted_not_divided(self):
        rows, counts = frames.compare("T", "L", self.pair(row(1, 0, "2026-06-30"), row(1, 200e6, "2026-09-30")), LIMITS)
        self.assertEqual((rows, counts["not_positive"]), ([], 1))

    def test_a_company_new_to_the_frame_has_no_step(self):
        rows, counts = frames.compare("T", "L", self.pair(None, row(1, 200e6, "2026-09-30")), LIMITS)
        self.assertEqual((rows, counts["both"]), ([], 0))

    def test_unit_slip_is_flagged_and_left_out_of_the_ranking(self):
        self.assertTrue(frames.is_unit_slip(185501, 181772000))  # ePlus in the real CY2026Q2I frame
        self.assertFalse(frames.is_unit_slip(100e6, 200e6))

    def test_same_step_a_year_earlier_is_shown(self):
        rows, _ = frames.compare("T", "L", self.pair(row(1, 100e6, "2026-06-30"), row(1, 200e6, "2026-09-30"),
                                                     (row(1, 100e6, "2025-06-30"), row(1, 150e6, "2025-09-30"))), LIMITS)
        self.assertEqual(rows[0]["year_ago_pct"], 50.0)

    def test_two_rows_for_one_company_stops(self):
        with self.assertRaises(edgar.EdgarError):
            frames.by_company(frame(row(1, 1, "2026-09-30"), row(1, 2, "2026-09-30")))

    def test_a_lead_whose_total_did_not_grow_is_marked(self):
        lead = {"cik": 1, "lines": [{"tag": frames.CURRENT, "year_ago_pct": None}]}
        by = lambda value: {1: {"val": value}}  # noqa: E731
        self.assertEqual(frames.not_new_growth(lead, [by(100), by(150), by(100), by(50)], 25), frames.TOTAL_NOT_UP)
        self.assertIsNone(frames.not_new_growth(lead, [by(100), by(150), by(100), by(60)], 25))

    def test_a_line_outside_the_two_tags_keeps_the_lead(self):
        lead = {"cik": 1, "lines": [{"tag": frames.CURRENT, "year_ago_pct": None}, {"tag": "RevenueRemainingPerformanceObligation", "year_ago_pct": None}]}
        by = lambda value: {1: {"val": value}}  # noqa: E731
        self.assertIsNone(frames.not_new_growth(lead, [by(100), by(150), by(100), by(50)], 25))

    def test_a_missing_total_is_not_a_reason(self):
        lead = {"cik": 1, "lines": [{"tag": frames.CURRENT, "year_ago_pct": None}]}
        self.assertIsNone(frames.not_new_growth(lead, [{}, {}, {}, {}], 25))

    def test_every_line_must_be_up_a_year_earlier(self):
        line = lambda pct: {"tag": "T", "year_ago_pct": pct}  # noqa: E731
        check = lambda *pcts: frames.not_new_growth({"cik": 1, "lines": [line(p) for p in pcts]}, [{}, {}, {}, {}], 25)  # noqa: E731
        self.assertEqual(check(25.0, 44.6), frames.UP_A_YEAR_AGO)
        self.assertIsNone(check(25.0, 24.9))
        self.assertIsNone(check(44.6, None))

    def test_real_frames_tie_to_corning_filings(self):
        """Real files: the 10-Q's own numbers, and the vault's explained Q2 deposit step."""
        cache = HERE / "cache" / "frames"
        for tag, name, want in (("ContractWithCustomerLiabilityCurrent", "CY2026Q3I", 501e6), ("ContractWithCustomerLiabilityNoncurrent", "CY2026Q3I", 2200e6),
                                ("ContractWithCustomerLiabilityCurrent", "CY2026Q2I", 465e6)):
            path = cache / f"{tag}-{name}.json"
            if not path.exists():
                self.skipTest("frames not cached")
            self.assertEqual(frames.by_company(json.loads(path.read_text()))[24741]["val"], want)

    def test_real_frames_whole_range(self):
        files = [p for p in (HERE / "cache" / "frames").glob("*.json") if p.name != "manifest.json"]
        if not files:
            self.skipTest("frames not cached")
        for path in files:
            body = json.loads(path.read_text())
            frames.by_company(body)  # no doubled company in any real frame
            for r in body["data"]:
                dt.date.fromisoformat(r["end"])
                self.assertTrue(r["accn"] and r["cik"], path.name)


class Dates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def note(self, dates=DATES, when="Nov. 27, 2026, stated ([Filing, Nov. 11, 2025](https://www.sec.gov/y.htm)).", outcome="Not known on 2026-11-03."):
        path = self.dir / "C.md"
        path.write_text(CATALYST.format(dates=dates, when=when, outcome=outcome))
        return radar.read_catalyst(path, ["Corning", "Verizon"])

    def bucket(self, **kw):
        return radar.place_dates([self.note(**kw)], TODAY, 90, 120)[0]["bucket"]

    def test_a_date_inside_the_horizon_is_soon(self):
        self.assertEqual(self.bucket(), "soon")

    def test_source_and_companies_are_read(self):
        c = self.note()
        self.assertEqual(c["source"]["label"], "Filing, Nov. 11, 2025")
        self.assertEqual(c["companies"], ["Corning", "Verizon"])

    def test_a_far_date_is_later(self):
        self.assertEqual(self.bucket(dates=DATES.replace("2026-11-27", "2030-01-01")), "later")

    def test_a_passed_date_needs_an_outcome(self):
        dates = DATES.replace("2026-11-27", "2026-08-01")
        self.assertEqual(self.bucket(dates=dates), "passed")
        self.assertEqual(self.bucket(dates=dates, outcome="It happened ([x, Aug. 1, 2026](https://www.sec.gov/z.htm))."), "done")

    def test_a_long_range_near_now_is_wide_not_soon(self):
        dates = 'date start: "2027-01-01"\ndate end: "2027-12-31"\ndate quote: "Nov. 27, 2026"\ndate kind: stated\n'
        self.assertEqual(self.bucket(dates=dates), "wide")

    def test_a_long_range_ending_soon_is_soon(self):
        dates = 'date start: "2026-07-01"\ndate end: "2026-12-31"\ndate quote: "Nov. 27, 2026"\ndate kind: stated\n'
        self.assertEqual(self.bucket(dates=dates), "soon")

    def test_no_fields_is_no_date_not_a_guess(self):
        self.assertEqual(self.bucket(dates="", when="Sometime around Nov. 27, 2026."), "no date")

    def test_a_quote_no_longer_in_the_note_is_a_problem(self):
        c = self.note(when="Moved to next year.")
        self.assertIn("no longer in the When section", c["problem"])

    def test_bad_fields_are_problems(self):
        self.assertTrue(self.note(dates=DATES.replace("2026-11-27", "soon"))["problem"])
        self.assertTrue(self.note(dates=DATES.replace("stated", "rumour"))["problem"])
        self.assertTrue(self.note(dates=DATES + 'date end: "2020-01-01"\n')["problem"])

    def test_all_real_notes_read_with_no_problem(self):
        notes = radar.read_catalysts(radar.Paths())
        self.assertEqual([c["title"] for c in notes if c["problem"]], [])
        self.assertEqual(len(notes), 40)
        for c in notes:
            if c["date_start"]:
                self.assertIn(c["date_quote"], (ROOT / c["file"]).read_text())


class NoteWrite(unittest.TestCase):
    def fresh(self, text, lines=()):
        c = dict(bucket="soon", date_quote="Nov. 27, 2026", date_start="2026-11-27", date_end="2026-11-27", date_kind="stated", days_to_end=24, days_to_start=24)
        return radar.note_with_radar(text, c, "2026-11-03", "2026-11-03 Catalyst radar", list(lines))

    def base(self):
        return CATALYST.format(dates=DATES, when="Nov. 27, 2026", outcome="My own reading stays.")

    def test_only_radar_fields_change(self):
        before, after = self.base(), self.fresh(self.base())
        self.assertIn('radar checked: "2026-11-03"', after)
        self.assertIn('last checked: "2026-11-03"', after)
        stripped = re.sub(r'radar checked: .*\n', "", re.sub(r"## Radar.*?(?=^## )", "", after, flags=re.S | re.M))
        self.assertEqual(stripped, before)

    def test_it_is_placed_before_the_rules(self):
        after = self.fresh(self.base())
        self.assertLess(after.index("## Radar"), after.index("## Rules this note depends on"))

    def test_same_day_rerun_changes_nothing(self):
        once = self.fresh(self.base(), ["- [8-K](https://www.sec.gov/x), GLW: names Verizon. Seen Nov. 3, 2026."])
        self.assertEqual(self.fresh(once, ["- [8-K](https://www.sec.gov/x), GLW: names Verizon. Seen Nov. 3, 2026."]), once)

    def test_old_event_lines_stay(self):
        once = self.fresh(self.base(), ["- old"])
        twice = self.fresh(once, ["- new"])
        self.assertIn("- old", twice)
        self.assertIn("- new", twice)

    def test_last_checked_is_not_moved(self):
        text = self.base().replace('last checked: "2026-11-03"', 'last checked: "2026-01-01"')
        self.assertIn('last checked: "2026-01-01"', self.fresh(text))


class Graph(unittest.TestCase):
    def links(self):
        return [{"kind": "supplies", "a": "Corning", "b": "Verizon", "chain": "fiber", "weak": False, "size": "", "evidence": "Stated", "what": "", "source": ""},
                {"kind": "competes with", "a": "Corning", "b": "Prysmian", "chain": "fiber", "weak": True, "size": "", "evidence": "My reading", "what": "", "source": ""},
                {"kind": "supplies", "a": "Prysmian", "b": "Amazon", "chain": "aluminum", "weak": False, "size": "", "evidence": "Stated", "what": "", "source": ""},
                {"kind": "supplies", "a": "Prysmian", "b": "Molex", "chain": "fiber", "weak": False, "size": "", "evidence": "Stated", "what": "", "source": ""}]

    def test_step_two_stays_on_the_chain(self):
        rows = radar.walk(self.links(), "Corning")
        self.assertEqual({r["node"]: r["step"] for r in rows}, {"Verizon": 1, "Prysmian": 1, "Molex": 2})

    def test_real_links_parse_with_no_problem(self):
        links, problems = radar.read_links(ROOT / "Companies")
        self.assertEqual(problems, [])
        self.assertEqual(len(links), len(set((x["kind"], x["a"], x["b"]) for x in links)))
        self.assertGreaterEqual(len(links), 38)  # graph.html's own count on Nov. 3, 2026

    def test_a_name_inside_a_word_does_not_match(self):
        self.assertEqual(radar.names_in("Pineapple and Metabolic and AT&T.", ["Apple", "Meta", "AT&T", "T"]), ["AT&T"])

    def test_map_never_takes_a_near_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Companies").mkdir()
            (root / "Companies" / "Apple.md").write_text("---\nticker:\n---\n")
            table = {"0": {"cik_str": 9, "ticker": "APLE", "title": "Apple Hospitality REIT, Inc."}, "1": {"cik_str": 5, "ticker": "AAPL", "title": "Apple Inc."}}
            self.assertEqual(radar.map_nodes(radar.Paths(root), table), {5: "Apple"})


class Names(unittest.TestCase):
    def test_a_company_keeps_its_main_ticker_on_the_real_list(self):
        tickers = radar.main_tickers(radar.ticker_table(radar.Paths()))
        self.assertEqual((tickers[1341439], tickers[24741]), ("ORCL", "GLW"))

    def test_a_second_run_the_same_day_gets_its_own_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = radar.Paths(tmp)
            self.assertEqual(radar.run_names(paths, "2026-11-03"), ("2026-11-03-01", "2026-11-03 Catalyst radar"))
            paths.runs.mkdir(parents=True)
            (paths.runs / "2026-11-03-01.json").write_text("{}")
            self.assertEqual(radar.run_names(paths, "2026-11-03"), ("2026-11-03-02", "2026-11-03 Catalyst radar 2"))


class Form4(unittest.TestCase):
    XML = b"""<ownershipDocument><aff10b5One>1</aff10b5One><reportingOwner><reportingOwnerId><rptOwnerName>Doe Jane</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><isOfficer>1</isOfficer><officerTitle>CFO</officerTitle></reportingOwnerRelationship></reportingOwner>
    <nonDerivativeTable><nonDerivativeTransaction><transactionDate><value>2026-10-01</value></transactionDate><transactionCoding><transactionCode>S</transactionCode></transactionCoding>
    <transactionAmounts><transactionShares><value>100</value></transactionShares><transactionPricePerShare><value>50</value></transactionPricePerShare></transactionAmounts></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>"""

    def test_summary(self):
        text = radar.form4_summary(radar.read_form4(self.XML))
        self.assertIn("Doe Jane (CFO): code S, open-market or private sale, 100 shares, about $5,000 (calc.)", text)
        self.assertIn("Plan box", text)

    def test_a_derivative_row_is_named_and_given_no_value(self):
        xml = self.XML.replace(b"</ownershipDocument>", b"<derivativeTable><derivativeTransaction><securityTitle><value>Phantom Stock</value></securityTitle><transactionCoding><transactionCode>A</transactionCode></transactionCoding><transactionAmounts><transactionShares><value>70</value></transactionShares></transactionAmounts></derivativeTransaction></derivativeTable></ownershipDocument>")
        self.assertIn("Phantom Stock, code A, grant or award, 70 units, no value counted", radar.form4_summary(radar.read_form4(xml)))

    GRANT = b"""<ownershipDocument><reportingOwner><reportingOwnerId><rptOwnerName>Doe Jane</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship>ROLES</reportingOwnerRelationship></reportingOwner>
    <derivativeTable><derivativeTransaction><securityTitle><value>Restricted Stock Unit</value></securityTitle><transactionCoding><transactionCode>A</transactionCode></transactionCoding>
    <transactionAmounts><transactionShares><value>268</value></transactionShares></transactionAmounts></derivativeTransaction></derivativeTable>EXTRA</ownershipDocument>"""
    SALE = b"""<nonDerivativeTable><nonDerivativeTransaction><transactionCoding><transactionCode>S</transactionCode></transactionCoding>
    <transactionAmounts><transactionShares><value>10</value></transactionShares></transactionAmounts></nonDerivativeTransaction></nonDerivativeTable>"""

    def grant(self, roles=b"<isDirector>1</isDirector>", extra=b""):
        return radar.is_director_grant(radar.read_form4(self.GRANT.replace(b"ROLES", roles).replace(b"EXTRA", extra)))

    def test_a_director_grant_alone_is_routine(self):
        self.assertTrue(self.grant())

    def test_an_officer_award_stays_an_event(self):
        self.assertFalse(self.grant(b"<isOfficer>1</isOfficer><officerTitle>CEO</officerTitle>"))
        self.assertFalse(self.grant(b"<isDirector>1</isDirector><isOfficer>1</isOfficer><officerTitle>CEO</officerTitle>"))

    def test_a_large_owner_who_is_a_director_stays_an_event(self):
        self.assertFalse(self.grant(b"<isDirector>1</isDirector><isTenPercentOwner>1</isTenPercentOwner>"))

    def test_any_other_row_on_the_form_keeps_it_an_event(self):
        self.assertFalse(self.grant(extra=self.SALE))

    def test_a_form_with_no_rows_stays_an_event(self):
        xml = b"<ownershipDocument><reportingOwner><reportingOwnerRelationship><isDirector>1</isDirector></reportingOwnerRelationship></reportingOwner></ownershipDocument>"
        self.assertFalse(radar.is_director_grant(radar.read_form4(xml)))

    def test_the_four_real_grants_are_routine(self):
        folder = ROOT / "sensors" / "edgar" / "cache" / "CIK0000024741" / "documents" / "insider"
        for accession in ("0000024741-26-000264", "0000024741-26-000265", "0000024741-26-000266", "0000024741-26-000267"):
            files = list(folder.glob(f"{accession}-*"))
            if not files:
                self.skipTest("forms not cached")
            self.assertTrue(radar.is_director_grant(radar.read_form4(files[0].read_bytes())), accession)

    def test_every_saved_real_form_reads(self):
        folder = ROOT / "sensors" / "edgar" / "cache" / "CIK0000024741" / "documents" / "insider"
        files = list(folder.glob("*form4*.xml"))
        self.assertGreater(len(files), 100)
        for path in files:
            self.assertTrue(radar.read_form4(path.read_bytes())["owner"], path.name)


class Wording(unittest.TestCase):
    """The script's own sentences give no view. Data it copies is not checked here."""
    VIEW = re.compile(r"\b(sell|selling|trim|trimming|hold|recommend\w*|undervalued|overvalued|cheap|expensive|fair value|intrinsic|margin of safety|price target|upside|downside|attractive|bargain)\b", re.I)

    def test_report_text_has_no_view(self):
        run = {"run_date": "2026-11-03", "run_file": "x", "horizon_days": 90, "sensors": [], "problems": [], "events": [], "walks": {},
               "dates": {"soon": [], "passed": [], "wide": [], "later_count": 0, "no_date_count": 0},
               "screen": {"status": "skipped", "steps": [], "lead_count": 0}}
        text = radar.render_report(run, 10).replace(radar.NO_VIEW, "")
        self.assertIsNone(self.VIEW.search(text), self.VIEW.search(text))
        self.assertNotRegex(text.replace("[[when-to-buy]]", ""), r"(?i)\bbuy\b")
        self.assertIn(radar.NO_VIEW, radar.render_report(run, 10))
        self.assertIn("never picks", text)

    def test_radar_never_calls_yahoo(self):
        text = (HERE / "radar.py").read_text()
        self.assertNotIn("prices.fetch", text)
        self.assertNotIn("prices.download", text)
        self.assertNotIn("yfinance", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
