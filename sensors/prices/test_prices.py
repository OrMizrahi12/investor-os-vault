"""Offline tests. No request leaves this computer. Run: uv run python sensors/prices/test_prices.py"""

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import prices  # noqa: E402

UTC = dt.timezone.utc


def frame(days):
    index = pd.DatetimeIndex(days, tz=ZoneInfo("America/New_York"))
    n = len(days)
    return pd.DataFrame({"Open": [10.0] * n, "High": [11.0] * n, "Low": [9.0] * n, "Close": [10.5] * n,
                         "Adj Close": [8.0] * n, "Volume": [100] * n, "Dividends": [0.0] * n,
                         "Stock Splits": [0.0] * n}, index=index)


class Fake:
    def __init__(self, result=None, error=None):
        self.calls, self.result, self.error = 0, result, error

    def __call__(self, ticker):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result, 2


NOV2_EVENING = dt.datetime(2026, 11, 2, 23, 0, tzinfo=UTC)  # 18:00 in New York
NOV2_MIDDAY = dt.datetime(2026, 11, 2, 16, 0, tzinfo=UTC)  # 11:00 in New York


class Rows(unittest.TestCase):
    def test_keeps_close_and_adj_close_apart(self):
        row = prices.to_rows(frame(["2026-10-30"]), NOV2_EVENING)[0]
        self.assertEqual((row["close"], row["adj_close"]), (10.5, 8.0))

    def test_drops_todays_unfinished_row(self):
        rows = prices.to_rows(frame(["2026-10-30", "2026-11-02"]), NOV2_MIDDAY)
        self.assertEqual([r["date"] for r in rows], ["2026-10-30"])

    def test_keeps_todays_row_after_the_close(self):
        rows = prices.to_rows(frame(["2026-10-30", "2026-11-02"]), NOV2_EVENING)
        self.assertEqual(rows[-1]["date"], "2026-11-02")

    def test_stops_on_a_table_without_adj_close(self):
        with self.assertRaises(prices.PriceError):
            prices.to_rows(frame(["2026-10-30"]).drop(columns="Adj Close"), NOV2_EVENING)

    def test_stops_on_a_future_date(self):
        with self.assertRaises(prices.PriceError):
            prices.to_rows(frame(["2026-11-03"]), NOV2_EVENING)

    def test_stops_on_a_bad_close(self):
        table = frame(["2026-10-30"])
        table["Close"] = [float("nan")]
        with self.assertRaises(prices.PriceError):
            prices.to_rows(table, NOV2_EVENING)


class OncePerDay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.good = frame(["2026-10-30"])

    def test_second_run_same_day_sends_nothing(self):
        fake = Fake(self.good)
        prices.fetch(self.tmp.name, downloader=fake, clock=lambda: NOV2_MIDDAY)
        _, fetched = prices.fetch(self.tmp.name, downloader=fake, clock=lambda: NOV2_EVENING)
        self.assertEqual((fake.calls, fetched), (1, False))

    def test_next_day_fetches_and_keeps_both_dated_files(self):
        fake = Fake(self.good)
        prices.fetch(self.tmp.name, downloader=fake, clock=lambda: NOV2_EVENING)
        prices.fetch(self.tmp.name, downloader=fake, clock=lambda: NOV2_EVENING + dt.timedelta(days=1))
        names = sorted(p.name for p in Path(self.tmp.name).glob("*.csv"))
        self.assertEqual((fake.calls, names), (2, ["2026-11-02.csv", "2026-11-03.csv"]))

    def test_failed_try_uses_up_the_day_and_old_data_survives(self):
        prices.fetch(self.tmp.name, downloader=Fake(self.good), clock=lambda: NOV2_EVENING)
        later = NOV2_EVENING + dt.timedelta(days=1)
        with self.assertRaises(prices.PriceError):
            prices.fetch(self.tmp.name, downloader=Fake(error=OSError("down")), clock=lambda: later)
        again = Fake(self.good)
        _, fetched = prices.fetch(self.tmp.name, downloader=again, clock=lambda: later)
        self.assertEqual((again.calls, fetched), (0, False))
        self.assertEqual(prices.read_latest(self.tmp.name)[1]["file"], "2026-11-02.csv")

    def test_crash_during_the_request_still_counts(self):
        def crash(ticker):
            manifest = prices.load_manifest(self.tmp.name)
            self.assertEqual(manifest["attempts"][-1]["status"], "started")
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            prices.fetch(self.tmp.name, downloader=crash, clock=lambda: NOV2_EVENING)
        fake = Fake(self.good)
        prices.fetch(self.tmp.name, downloader=fake, clock=lambda: NOV2_EVENING)
        self.assertEqual(fake.calls, 0)

    def test_read_latest_refuses_an_edited_file(self):
        prices.fetch(self.tmp.name, downloader=Fake(self.good), clock=lambda: NOV2_EVENING)
        (Path(self.tmp.name) / "2026-11-02.csv").write_text("date\n")
        with self.assertRaises(prices.PriceError):
            prices.read_latest(self.tmp.name)


if __name__ == "__main__":
    unittest.main()
