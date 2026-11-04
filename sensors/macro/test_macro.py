"""Offline tests. No request leaves this computer. Run: uv run python sensors/macro/test_macro.py"""

import ast
import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE), str(HERE.parent / "prices")]
import draw  # noqa: E402
import earnings  # noqa: E402
import macro  # noqa: E402

TODAY = dt.date(2026, 11, 2)


def monthly(series_id, first=dt.date(2010, 1, 1), last=dt.date(2026, 9, 1), value="5.00", blank=()):
    rows, day = [f"observation_date,{series_id}"], first
    while day <= last:
        rows.append(f"{day},{'' if day in blank else value}")
        day = (day + dt.timedelta(days=32)).replace(day=1)
    return "\n".join(rows) + "\n"


def daily(first=dt.date(2010, 1, 1), last=dt.date(2026, 10, 30), blank=()):
    rows, day = ["observation_date,DGS10"], first
    while day <= last:
        if day.weekday() < 5:
            rows.append(f"{day},{'' if day in blank else '4.10'}")
        day += dt.timedelta(days=1)
    return "\n".join(rows) + "\n"


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def write(self, series_id, text):
        (self.folder / f"{series_id}.csv").write_text(text)

    def read(self, series_id):
        return macro.read_series(series_id, self.folder, TODAY)

    def test_missing_file_is_not_an_error(self):
        self.assertIsNone(self.read("AAA"))

    def test_blank_value_stays_blank(self):
        self.write("AAA", monthly("AAA", blank=[dt.date(2025, 10, 1)]))
        s = self.read("AAA")
        self.assertEqual((dict(s["rows"])[dt.date(2025, 10, 1)], s["missing"]), (None, 1))

    def test_dot_means_missing(self):
        self.write("DGS10", daily().replace("2026-10-30,4.10", "2026-10-30,."))
        self.assertIsNone(dict(self.read("DGS10")["rows"])[dt.date(2026, 10, 30)])

    def test_old_date_header_is_accepted(self):
        self.write("AAA", monthly("AAA").replace("observation_date", "DATE"))
        self.assertEqual(self.read("AAA")["id"], "AAA")

    def test_stops_on_the_wrong_file(self):
        self.write("AAA", monthly("DGS10"))
        with self.assertRaisesRegex(macro.MacroError, "right file"):
            self.read("AAA")

    def test_stops_when_the_range_is_too_short(self):
        self.write("AAA", monthly("AAA", first=dt.date(2021, 1, 1)))
        with self.assertRaisesRegex(macro.MacroError, "longest range"):
            self.read("AAA")

    def test_cpi_needs_a_year_more_than_the_others(self):
        text = monthly("CPIAUCSL", first=dt.date(2011, 11, 1), value="300.0")
        self.write("CPIAUCSL", text)
        with self.assertRaisesRegex(macro.MacroError, "longest range"):
            self.read("CPIAUCSL")
        self.write("AAA", monthly("AAA", first=dt.date(2011, 11, 1)))
        self.assertIsNotNone(self.read("AAA"))

    def test_stops_on_percent_change_units(self):
        self.write("CPIAUCSL", monthly("CPIAUCSL", value="3.0"))
        with self.assertRaisesRegex(macro.MacroError, "units"):
            self.read("CPIAUCSL")

    def test_full_cpi_history_is_accepted(self):
        text = monthly("CPIAUCSL", value="300.0").replace("observation_date,CPIAUCSL\n", "observation_date,CPIAUCSL\n1947-01-01,21.480\n", 1)
        rows = text.splitlines()
        # The real file runs monthly from 1947. Keep this one monthly too by starting there.
        day, filled = dt.date(1947, 2, 1), []
        while day < dt.date(2010, 1, 1):
            filled.append(f"{day},21.480")
            day = (day + dt.timedelta(days=32)).replace(day=1)
        self.write("CPIAUCSL", "\n".join(rows[:2] + filled + rows[2:]) + "\n")
        self.assertEqual(self.read("CPIAUCSL")["first"], "1947-01-01")

    def test_stops_on_changed_frequency(self):
        self.write("DGS10", monthly("DGS10"))
        with self.assertRaisesRegex(macro.MacroError, "not daily"):
            self.read("DGS10")
        rows = monthly("AAA").splitlines()
        del rows[50]
        self.write("AAA", "\n".join(rows))
        with self.assertRaisesRegex(macro.MacroError, "one row a month"):
            self.read("AAA")

    def test_manifest_logs_new_contents_only_and_holds_no_data(self):
        self.write("AAA", monthly("AAA"))
        found = {"AAA": self.read("AAA")}
        macro.update_manifest(found, self.folder)
        macro.update_manifest(found, self.folder)
        self.assertEqual(len(macro.update_manifest(found, self.folder)["AAA"]), 1)
        self.write("AAA", monthly("AAA", value="5.10"))
        log = macro.update_manifest({"AAA": self.read("AAA")}, self.folder)["AAA"]
        self.assertEqual(len(log), 2)
        self.assertNotIn("5.10", str(log[-1]["rows"]))


class NoFredRequests(unittest.TestCase):
    def test_macro_and_draw_import_no_network_library(self):
        banned = {"urllib", "http", "requests", "socket", "yfinance", "curl_cffi"}
        for name in ("macro.py", "draw.py", "earnings.py"):
            tree = ast.parse((HERE / name).read_text())
            used = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    used |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    used.add(node.module.split(".")[0])
            self.assertEqual(used & banned, set(), name)


class Inflation(unittest.TestCase):
    def test_change_over_twelve_months(self):
        rows = [(dt.date(2024, 9, 1), 100.0), (dt.date(2025, 9, 1), 103.0)]
        self.assertAlmostEqual(earnings.cpi_yearly_change(rows)[1][1], 3.0)

    def test_blank_month_blanks_both_itself_and_a_year_later(self):
        rows = [(dt.date(2024, 10, 1), 100.0), (dt.date(2025, 10, 1), None), (dt.date(2026, 10, 1), 105.0)]
        out = dict(earnings.cpi_yearly_change(rows))
        self.assertIsNone(out[dt.date(2025, 10, 1)])
        self.assertIsNone(out[dt.date(2026, 10, 1)])


def fact(start, end, value, form, filed, accession, fy=None):
    return {"taxonomy": "us-gaap", "concept": "EarningsPerShareDiluted", "unit": "USD/shares", "start": start, "end": end,
            "value": value, "form": form, "filed": filed, "accession": accession, "filing_url": f"https://x/{accession}", "fy": fy}


FACTS = [
    fact("2024-01-01", "2024-12-31", 0.58, "10-K", "2025-02-13", "k24"),
    fact("2025-01-01", "2025-12-31", 1.83, "10-K", "2026-02-12", "k25"),
    fact("2024-01-01", "2024-12-31", 0.58, "10-K", "2026-02-12", "k25"),  # the older year, in the newer 10-K
    fact("2026-01-01", "2026-09-30", 1.85, "10-Q", "2026-10-29", "q3"),
    fact("2026-07-01", "2026-09-30", 0.78, "10-Q", "2026-10-29", "q3"),  # the 3-month row must not be used
    fact("2025-01-01", "2025-09-30", 1.21, "10-Q", "2026-10-29", "q3", fy=2026),
    fact("2025-07-01", "2025-09-30", 0.50, "10-Q", "2026-10-29", "q3"),
]


class Trailing(unittest.TestCase):
    def test_full_year_plus_this_ytd_minus_last_ytd(self):
        steps = earnings.eps_steps(FACTS)
        self.assertAlmostEqual(steps[-1]["eps"], 2.47)
        self.assertEqual(steps[-1]["full_year_filing"]["accession"], "k25")

    def test_a_10k_uses_its_own_latest_year(self):
        self.assertEqual(earnings.eps_steps(FACTS)[1]["eps"], 1.83)

    def test_no_later_filing_leaks_back(self):
        steps = earnings.eps_steps(FACTS)
        prices = [{"date": "2026-10-28", "close": 100.0, "stock_splits": 0.0},
                  {"date": "2026-10-29", "close": 100.0, "stock_splits": 0.0}]
        series = earnings.yield_series(prices, steps, dt.date(2026, 1, 1))
        self.assertAlmostEqual(series[0]["yield"], 1.83)  # the day before the 10-Q
        self.assertAlmostEqual(series[1]["yield"], 2.47)

    def test_a_loss_gives_a_negative_yield(self):
        steps = [{"filed": "2018-02-15", "eps": -0.66, "accession": "x"}]
        out = earnings.yield_series([{"date": "2018-03-01", "close": 33.0, "stock_splits": 0.0}], steps, dt.date(2018, 1, 1))
        self.assertAlmostEqual(out[0]["yield"], -2.0)

    def test_stops_on_a_split(self):
        steps = [{"filed": "2018-02-15", "eps": 1.0, "accession": "x"}]
        with self.assertRaises(earnings.EarningsError):
            earnings.yield_series([{"date": "2018-03-01", "close": 33.0, "stock_splits": 2.0}], steps, dt.date(2018, 1, 1))

    def test_stops_when_the_window_needs_a_missing_number(self):
        broken = [f for f in FACTS if not (f["accession"] == "q3" and f["start"] == "2025-01-01")]
        with self.assertRaises(earnings.EarningsError):
            earnings.steps_in_window(earnings.eps_steps(broken), dt.date(2026, 1, 1))


class Page(unittest.TestCase):
    def test_month_count_needs_both_values(self):
        months = [{"EY": 6, "AAA": 5}, {"EY": 4, "AAA": 5}, {"EY": 6}, {"AAA": 5}]
        self.assertEqual(draw.beat_count(months), (1, 2))

    def test_months_since_last_above(self):
        months = [{"day": dt.date(2026, 1, 1), "EY": 6, "AAA": 5}, {"day": dt.date(2026, 2, 1), "EY": 4, "AAA": 5},
                  {"day": dt.date(2026, 3, 1), "EY": 5, "AAA": 5}, {"day": dt.date(2026, 4, 1), "EY": 2}]
        self.assertEqual(draw.since_above(months), (dt.date(2026, 1, 1), 2))

    def test_a_gap_breaks_the_line(self):
        start, end = dt.date(2020, 1, 1), dt.date(2020, 1, 6)
        rows = [(dt.date(2020, 1, n), None if n == 3 else 2.0) for n in range(1, 7)]
        svg, _ = draw.chart("c", "x", start, end, [("DGS10", rows)], [{"day": dt.date(2020, 1, 1)}])
        self.assertEqual(svg.count("<polyline"), 2)


if __name__ == "__main__":
    unittest.main()
