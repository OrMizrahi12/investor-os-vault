"""Offline tests. No request leaves this computer. Run: uv run python -m unittest sensors/edgar/test_edgar.py"""

import io
import sys
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import draw  # noqa: E402
import edgar  # noqa: E402


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeResponse(io.BytesIO):
    headers = Message()


class FakeOpener:
    def __init__(self, errors=()):
        self.errors, self.requests = list(errors), []

    def open(self, request, timeout):
        self.requests.append(request)
        if self.errors:
            raise urllib.error.HTTPError(request.full_url, self.errors.pop(0), "x", Message(), None)
        return FakeResponse(b"ok")


def client(rate=8, errors=()):
    clock = FakeClock()
    opener = FakeOpener(errors)
    return edgar.SecClient("me a@b.co", rate, opener, clock, clock.sleep), opener


URL = "https://data.sec.gov/x.json"


class Client(unittest.TestCase):
    def test_stays_under_ten_a_second(self):
        c, _ = client(rate=9.9)
        for _ in range(50):
            c.get(URL)
        self.assertLess(c.busiest_second(), 11)
        gaps = [b - a for a, b in zip(c.sent, c.sent[1:])]
        self.assertGreater(min(gaps), 0.1)

    def test_declares_user_agent(self):
        c, opener = client()
        c.get(URL)
        self.assertEqual(opener.requests[0].get_header("User-agent"), "me a@b.co")

    def test_refuses_other_hosts(self):
        c, opener = client()
        for bad in ("https://example.com/x", "http://www.sec.gov/x", "https://sec.gov.evil.com/x"):
            with self.assertRaises(edgar.EdgarError):
                c.get(bad)
        self.assertEqual(opener.requests, [])

    def test_retries_429_but_not_403(self):
        c, opener = client(errors=[429])
        self.assertEqual(c.get(URL), b"ok")
        self.assertEqual(len(opener.requests), 2)
        c, opener = client(errors=[403])
        with self.assertRaises(edgar.EdgarError):
            c.get(URL)
        self.assertEqual(len(opener.requests), 1)


class Settings(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "s.toml"
            path.write_text(text)
            return edgar.load_settings(path)

    def test_good(self):
        s = self.load('[sec]\nname="n"\nemail="a@b.co"\nrequests_per_second=8\n')
        self.assertEqual(s["user_agent"], "n a@b.co")

    def test_refuses_ten_a_second(self):
        with self.assertRaises(edgar.EdgarError):
            self.load('[sec]\nname="n"\nemail="a@b.co"\nrequests_per_second=10\n')

    def test_refuses_no_email(self):
        with self.assertRaises(edgar.EdgarError):
            self.load('[sec]\nname="n"\nemail="nobody"\nrequests_per_second=8\n')


class Facts(unittest.TestCase):
    ENTRY = {"val": 5, "end": "2025-12-31", "form": "10-K", "filed": "2026-02-12", "accn": "1-2-3"}

    def facts(self, entry):
        return {"facts": {"t": {"C": {"label": "L", "units": {"USD": [entry]}}}}}

    def test_row_keeps_provenance(self):
        filings = [{"accession": "1-2-3", "url": "u"}]
        row = edgar.flatten_facts(self.facts(self.ENTRY), filings)[0]
        self.assertEqual((row["form"], row["filed"], row["accession"], row["filing_url"]),
                         ("10-K", "2026-02-12", "1-2-3", "u"))

    def test_missing_provenance_stops(self):
        for key in ("form", "filed", "accn"):
            bad = {k: v for k, v in self.ENTRY.items() if k != key}
            with self.assertRaises(edgar.EdgarError):
                edgar.flatten_facts(self.facts(bad), [])

    def test_zero_value_is_kept(self):
        row = edgar.flatten_facts(self.facts({**self.ENTRY, "val": 0}), [])[0]
        self.assertEqual(row["value"], 0)


class Filings(unittest.TestCase):
    def column(self, accession, filed):
        return {"accessionNumber": [accession], "form": ["10-K"], "filingDate": [filed], "reportDate": [""],
                "items": [""], "primaryDocument": ["a.htm"], "primaryDocDescription": [""]}

    def test_joins_older_pages_and_dedupes(self):
        subs = {"filings": {"recent": self.column("0-1", "2026-01-01")}}
        rows = edgar.flatten_filings(24741, subs, [self.column("0-0", "2016-01-01"), self.column("0-1", "2026-01-01")])
        self.assertEqual([r["accession"] for r in rows], ["0-1", "0-0"])
        self.assertEqual(rows[1]["url"], "https://www.sec.gov/Archives/edgar/data/24741/00/a.htm")


class Printed(unittest.TestCase):
    def test_reads_printed_numbers(self):
        for cell, number in (("15,629", 15629), ("(497", -497), ("(497)", -497), ("( 497 )", -497)):
            self.assertEqual(draw.parse_printed(cell), number)
        self.assertIsNone(draw.parse_printed("Note 5"))

    def test_full_year_uses_dates_not_the_fy_field(self):
        self.assertTrue(draw.full_year({"start": "2016-01-01", "end": "2016-12-31"}))
        self.assertFalse(draw.full_year({"start": "2016-10-01", "end": "2016-12-31"}))
        self.assertFalse(draw.full_year({"start": None, "end": "2016-12-31"}))


if __name__ == "__main__":
    unittest.main()
