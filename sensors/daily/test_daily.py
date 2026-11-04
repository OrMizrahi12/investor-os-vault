"""Tests for the daily run. No network. Run: .venv/bin/python sensors/daily/test_daily.py"""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect  # noqa: E402
import publish  # noqa: E402

LINES = {"buy_below": 28.97, "trim_above": 36.06, "run_file": "v1.json"}
SRC = {"url": "https://example.com/y", "label": "Yahoo"}
GOOD = "### Red\n\n- Nothing.\n\n### Orange\n\n- Results, 0000024741-26-000273, [8-K, filed Oct. 27, 2026](https://sec.gov/x).\n\n### Info\n\n- Nothing.\n"


def rows(*closes):
    return [{"date": f"2026-11-{i + 1:02d}", "close": c} for i, c in enumerate(closes)]


def digest(items=()):
    return {"items": list(items), "today": "2026-11-04", "since": None, "sensors": [], "stem": "x", "run_local": "2026-11-04T08:04+00:00",
            "not_read": "News not read.", "radar_report": "Research/r.md", "sec_list": {"url": "https://sec.gov/l", "fetched": "2026-11-04T08:00:00+00:00"},
            "stands": {"close": 123.2, "date": "2026-11-03", "source_label": "Yahoo", "source_url": "https://y"}}


ORANGE = {"id": "0000024741-26-000273", "level": "Orange", "rule": "8-K first pass", "summary": "Results"}


class Levels(unittest.TestCase):
    def test_red_items_and_102_rule(self):
        self.assertEqual(collect.eight_k_level(["4.02", "9.01"])[:2], ("Red", "R3"))
        self.assertEqual(collect.eight_k_level(["1.02"])[0], "Red")
        self.assertEqual(collect.eight_k_level(["1.01", "1.02"])[0], "Orange")

    def test_routine_is_info_and_unknown_is_orange(self):
        self.assertEqual(collect.eight_k_level(["5.07", "9.01"])[0], "Info")
        self.assertEqual(collect.eight_k_level(["6.01"])[0], "Orange")
        self.assertEqual(collect.eight_k_level([])[0], "Orange")

    def test_forms(self):
        self.assertEqual(collect.form_level("UPLOAD")[:2], ("Orange", "O10"))
        self.assertEqual(collect.form_level("10-Q")[:2], ("Info", "I3"))
        self.assertEqual(collect.form_level("10-Q/A")[:2], ("Orange", "O9"))
        self.assertEqual(collect.form_level("SCHEDULE 13D")[:2], ("Orange", "O12"))

    def test_insider_forms_roll_into_one_line_but_a_market_purchase_stands_alone(self):
        ev = [{"id": str(i), "kind": "filing", "form": "4", "filed": "2026-11-03", "url": "u", "ticker": "GLW", "company": "Corning",
               "summary": s} for i, s in enumerate(["x, code S, sale", "y, code S, sale", "z, code P, purchase"])]
        out = collect.filing_items(ev, {}, {})
        self.assertEqual([(i["rule"], i.get("count")) for i in out], [("O12", None), ("I4", 2)])
        self.assertEqual(out[1]["sales"], 2)


class Yahoo(unittest.TestCase):
    def test_the_run_never_runs_the_price_sensor(self):
        self.assertFalse([s for s in collect.SENSORS if "prices" in " ".join(s[1])])
        self.assertEqual([s[0] for s in collect.SENSORS], ["8-K watcher", "Radar"])


class Text(unittest.TestCase):
    def test_a_one_line_release_becomes_short_lines(self):
        body = ("<html><style>x{}</style><p>Core sales &amp; more</p><table><tr><td>Optical</td><td>$1,000</td></tr></table>" + "<p>" + "word " * 200 + "</p></html>").encode()
        out = collect.plain_text(body)
        self.assertIn("Core sales & more", out)
        self.assertIn("Optical | $1,000", out)
        self.assertNotIn("x{}", out)
        self.assertLessEqual(max(map(len, out.splitlines())), 180)


class Price(unittest.TestCase):
    def go(self, closes, through="2026-11-01", held=False, old=LINES, lines=LINES):
        return collect.price_items(rows(*closes), through, old, lines, held, SRC)

    def test_a_big_move_alone_is_nothing(self):
        self.assertEqual(self.go([123.2, 80.0]), [])

    def test_a_crossing_fires_once(self):
        out = self.go([30, 28, 27, 26])
        self.assertEqual([i["rule"] for i in out], ["O4"])

    def test_it_rearms_after_a_close_back_above(self):
        self.assertEqual([i["rule"] for i in self.go([30, 28, 30, 28])], ["O4", "O4"])

    def test_a_crossing_between_runs_is_seen(self):
        self.assertEqual([i["filed"] for i in self.go([30, 31, 28, 31])], ["2026-11-03"])

    def test_trim_only_on_a_holding(self):
        self.assertEqual(self.go([35, 37]), [])
        self.assertEqual([i["rule"] for i in self.go([35, 37], held=True)], ["O5"])

    def test_a_refresh_across_the_price_is_o6(self):
        new = dict(LINES, buy_below=40.0, run_file="v2.json")
        self.assertEqual([i["rule"] for i in self.go([35], through="2026-11-01", lines=new)], ["O6"])

    def test_no_word_of_change(self):
        for i in self.go([30, 28]):
            self.assertNotIn("%", i["summary"])


class Dates(unittest.TestCase):
    C = {"bucket": "soon", "start": "2026-12-04", "end": "2026-12-04", "quote": "Dec. 4", "kind": "stated", "days": 30, "file": "f", "url": "u"}

    def go(self, old, new):
        return [i["rule"] for i in collect.date_items(old, new, "2026-11-04")]

    def test_no_change_no_line(self):
        self.assertEqual(self.go({"a": self.C}, {"a": self.C}), [])

    def test_entering_the_horizon_seven_days_passing_and_moving(self):
        self.assertEqual(self.go({}, {"a": self.C}), ["I6"])
        self.assertEqual(self.go({"a": self.C}, {"a": dict(self.C, days=7)}), ["I6"])
        self.assertEqual(self.go({"a": dict(self.C, days=6)}, {"a": dict(self.C, days=5)}), [])
        self.assertEqual(self.go({"a": self.C}, {"a": dict(self.C, bucket="passed")}), ["O13"])
        self.assertEqual(self.go({"a": self.C}, {"a": dict(self.C, start="2027-01-01", quote="Jan. 1")}), ["O13"])

    def test_a_forecast_passing_is_info(self):
        self.assertEqual(self.go({"a": dict(self.C, kind="a forecast")}, {"a": dict(self.C, kind="a forecast", bucket="passed")}), ["I6"])


class Checks(unittest.TestCase):
    def test_good_brief_passes(self):
        self.assertEqual(publish.check(GOOD, digest([ORANGE])), [])

    def test_undashed_accession_counts(self):
        self.assertEqual(publish.check(GOOD.replace("0000024741-26-000273", "000002474126000273"), digest([ORANGE])), [])

    def refused(self, text, items=(ORANGE,)):
        return publish.check(text, digest(items))

    def test_refusals(self):
        self.assertTrue(self.refused("### Orange\n- x\n### Red\n### Info\n"))
        self.assertTrue(self.refused(GOOD.replace("(https://sec.gov/x)", "")))
        self.assertTrue(self.refused(GOOD.replace("Oct. 27, 2026", "last week")))
        self.assertTrue(self.refused(GOOD.replace("Results,", "You should sell. Results,")))
        self.assertTrue(self.refused(GOOD + "- The close fell 5%, [x, Nov. 3, 2026](https://y).\n"))
        self.assertTrue(self.refused(GOOD.replace("0000024741-26-000273", "another")))

    def test_buy_below_and_trim_above_are_not_advice(self):
        text = GOOD.replace("Results,", "Close $1, buy-below $2, trim-above $3. Results,")
        self.assertEqual(publish.check(text, digest([ORANGE])), [])

    def test_a_presumed_red_cannot_leave_red(self):
        red = dict(ORANGE, level="Red", rule="R3")
        self.assertTrue(publish.check(GOOD, digest([red])))
        moved = GOOD.replace("### Red\n\n- Nothing.", "### Red\n\n- Item 4.02, 0000024741-26-000273, [8-K, Oct. 27, 2026](https://s).")
        self.assertEqual(publish.check(moved, digest([red])), [])


class Runs(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        base = Path(self.t.name)
        for name in ("journal", "inbox", "runs"):
            (base / name).mkdir()
        self.j, self.i, self.r = base / "journal", base / "inbox", base / "runs"
        self.state = base / "state.json"
        self.state.write_text("{}")
        for patcher in (mock.patch.object(publish, "JOURNAL", self.j), mock.patch.object(publish, "INBOX", self.i),
                        mock.patch.object(publish, "RUNS", self.r), mock.patch.object(publish, "HERE", base), mock.patch.object(publish, "ROOT", base)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self.t.cleanup)

    def write(self, **kw):
        d = dict(digest(), brief_path="runs/x.brief.md", quiet=True, briefed=False, **kw)
        (self.r / "x.json").write_text(json.dumps(d))

    def test_quiet_day_is_one_line_with_sources_and_dates(self):
        self.write()
        out = publish.publish()
        self.assertEqual(out["line"].count("\n"), 0)
        self.assertIn("nothing needs me", out["line"])
        self.assertTrue(publish.SOURCE.search(out["line"]) and publish.DATE.search(out["line"]))
        text = (self.j / "2026-11-04.md").read_text()
        for head in ("# 2026-11-04", "### What we did", "### What we decided", "### What we left open"):
            self.assertIn(head, text)

    def test_the_journal_keeps_every_earlier_byte_and_the_brief_is_on_top(self):
        old = "# 2026-11-04\n\n## Session: earlier\n\n- A line.\n\n- Another.\n"
        (self.j / "2026-11-04.md").write_text(old)
        self.write()
        publish.publish()
        new = (self.j / "2026-11-04.md").read_text()
        self.assertIn(old[len("# 2026-11-04\n\n"):].rstrip(), new)
        self.assertLess(new.index("Daily brief"), new.index("Session: earlier"))
        self.assertLess(new.index("Session: earlier"), new.index("Session: daily run"))

    def test_a_second_quiet_run_adds_nothing(self):
        self.write()
        publish.publish()
        first = (self.j / "2026-11-04.md").read_text()
        self.write()
        self.assertIsNone(publish.publish()["line"])
        self.assertEqual((self.j / "2026-11-04.md").read_text(), first)

    def test_busy_needs_a_brief_and_files_inbox_only_after_it_passes(self):
        item = {"id": "0000024741-26-000279", "level": "Info", "rule": "I3", "form": "10-Q", "filed": "2026-10-29", "url": "https://sec.gov/q", "ticker": "GLW",
                "company": "Corning", "summary": "10-Q.", "file_in_inbox": True}
        d = dict(digest([item]), brief_path="runs/x.brief.md", quiet=False, briefed=False)
        (self.r / "x.json").write_text(json.dumps(d))
        with self.assertRaises(publish.Refused):
            publish.publish()
        self.assertEqual(list(self.i.iterdir()), [])
        (self.r / "x.brief.md").write_text("### Red\n\n- Nothing.\n\n### Orange\n\n- Nothing.\n\n### Info\n\n- 10-Q came, refresh due, [10-Q, filed Oct. 29, 2026](https://sec.gov/q).\n")
        out = publish.publish()
        self.assertEqual(out["filed"], ["2026-10-29 GLW 10-Q 0000024741-26-000279.md"])
        self.assertIn('form: "10-Q"', (self.i / out["filed"][0]).read_text())
        self.assertIn("## Daily brief, Nov. 4, 2026, 08:04", (self.j / "2026-11-04.md").read_text())


class Carry(unittest.TestCase):
    def test_a_digest_never_briefed_comes_forward(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            runs, radar, val = base / "runs", base / "radar", base / "val"
            for f in (runs, radar, val):
                f.mkdir()
            (val / "a.json").write_text(json.dumps(dict(LINES, run_file="a")))
            (runs / "2026-11-03-01.json").write_text(json.dumps({"stem": "2026-11-03-01", "briefed": False, "items": [dict(ORANGE, filed="2026-10-27")]}))
            state = {"closes_through": "2026-11-03", "dates": {}, "problems": [], "lines": LINES, "o16": [], "last_brief": "2026-11-02"}
            (base / "state.json").write_text(json.dumps(state))
            (base / "seen.json").write_text("{}")
            (base / "readings.toml").write_text("")
            with mock.patch.multiple(collect, RUNS=runs, RADAR_RUNS=radar, VALUATION_RUNS=val, STATE=base / "state.json", SEEN=base / "seen.json", PORTFOLIO=base):
                with mock.patch.object(collect.prices, "read_latest", return_value=(rows(123.2, 124.0, 125.0), {"started_utc": "2026-11-03T08:00:00+00:00"})):
                    d = collect.collect(now=dt.datetime(2026, 11, 4, 8, 4, tzinfo=dt.timezone.utc), sensors=lambda: [{"name": "Prices", "ok": False, "out": "Stopped"}], documents=lambda items: None)
            self.assertEqual(d["since"], "2026-11-02")
            self.assertEqual(sorted(i["rule"] for i in d["items"]), ["8-K first pass", "O16"])
            self.assertFalse(d["quiet"])
            self.assertTrue(json.loads((runs / "2026-11-03-01.json").read_text())["briefed"])


if __name__ == "__main__":
    unittest.main()
