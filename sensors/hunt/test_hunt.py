"""Tests for the monthly hunt and the event run. No network. Run: .venv/bin/python sensors/hunt/test_hunt.py"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import events  # noqa: E402
import gates  # noqa: E402
import hunt  # noqa: E402
import radar  # noqa: E402

CACHE = ROOT / "sensors/edgar/cache"
# Sorted by hand on Nov. 3, 2026: Research/2026-11-03 Triage.md and Hunt triage.md. True means the record fails Gate 1.
HAND = {723125: False, 24741: False, 936468: False, 1501585: False, 1996810: False, 1050915: False, 80420: False,
        1341439: True, 1571996: True, 2023554: True, 1181412: True, 1446159: True, 1462056: True, 1767042: True, 771266: True}
MIDS = {723125: 850.47, 1996810: 2.44, 1050915: 54.89, 80420: 52.55}


def facts(cik):
    return gates.Facts.load(CACHE / f"CIK{cik:010d}" / "companyfacts.json")


def line(rise=10, step="Q2", acc="a"):
    return {"rise_usd": rise, "label": "RPO", "earlier": 1, "later": 1 + rise, "end_earlier": "2026-03-31", "end_later": "2026-06-30", "accession_later": acc,
            "filing_later": "https://x/f", "frame_later": "CY2026Q2I", "frame_earlier": "CY2026Q1I", "frame_url_later": "https://x/l", "frame_url_earlier": "https://x/e"}


def lead(cik, ticker, name="Co", on_map=None, rise=10):
    return {"cik": cik, "name": name, "ticker": ticker, "on_map": on_map, "lines": [line(rise)], "not_new_growth": ""}


def made_facts(ni=None, ocf=None, capex=None):
    def rows(values):
        return [{"start": f"{y}-01-01", "end": f"{y}-12-31", "val": v, "form": "10-K", "filed": f"{y + 1}-02-01"} for y, v in values.items()]
    gaap = {"NetIncomeLoss": {"units": {"USD": rows(ni or {})}}, "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": rows(ocf or {})}},
            "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": rows(capex or {})}},
            "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": rows({2025: 100e6})}}}
    return gates.Facts({"facts": {"us-gaap": gaap}})


class Gates(unittest.TestCase):
    def test_every_hand_sort_comes_out_the_same(self):
        for cik, failed in HAND.items():
            self.assertEqual(gates.gate1(facts(cik))["state"] == "fail", failed, cik)

    def test_base_matches_the_hand_figures(self):
        for cik, mid in MIDS.items():
            b, why = gates.base(facts(cik), 0.0612, "x 2026", "u", "Nov. 3, 2026")
            self.assertAlmostEqual(b["mid"], mid, places=2, msg=why)

    def test_a_falling_record_is_the_ceiling_and_the_base_still_runs(self):
        years = range(2016, 2026)
        f = made_facts({y: 50e6 for y in years}, {y: 100e6 - (y - 2016) * 5e6 for y in years}, {y: 10e6 for y in years})
        b, why = gates.base(f, 0.0612, "x 2026", "u", "Nov. 3, 2026")
        self.assertIsNotNone(b, why)
        self.assertLess(b["reads"]["growth"], 0)

    def test_a_figure_that_cannot_be_read_stays_open(self):
        states = {t["name"]: t["state"] for t in gates.gate1(made_facts({2025: 1e6}))["tests"]}
        self.assertEqual(states["Profit years"], "open")
        self.assertEqual(states["Debt"], "open")


class Log(unittest.TestCase):
    def test_the_real_log_reads_whole(self):
        text = (ROOT / "Research/Rejection log.md").read_text()
        rows = [ln for ln in text.splitlines() if ln.startswith("| ") and not ln.startswith(("| Date", "|---"))]
        self.assertEqual(len(hunt.read_log(text)), len(rows))
        self.assertEqual(hunt.read_log(text)["POWL"]["look_again"], "2026-11")

    def test_a_row_it_cannot_read_stops_the_run(self):
        with self.assertRaises(hunt.Refused):
            hunt.read_log("| Date | Company | Gate | Reason | Look again |\n|---|\n| x | y |\n")

    def test_month_forms(self):
        self.assertEqual(hunt.look_month("After the 10-K, about late Jan. 2027 (my estimate)."), "2027-01")
        self.assertEqual(hunt.look_month("After its first 10-K, about early 2027 (my estimate)."), "2027-01")
        self.assertIsNone(hunt.look_month("Never."))


class Sort(unittest.TestCase):
    LOG = {"OLD": {"look_again": "2027-02", "words": "After the 10-K, about Feb. 2027", "gate": "Gate 1", "date": "Nov. 3, 2026"},
           "DUE": {"look_again": "2026-11", "words": "After the 10-K, about Nov. 2026", "gate": "Gate 2", "date": "Nov. 3, 2026"}}

    def test_every_lead_meets_the_log(self):
        step = {"later": "Q2", "leads": [lead(1, "OLD"), lead(2, "DUE"), lead(3, "MU"), lead(4, "GLW", on_map="Corning"), lead(5, "NEW"), lead(6, "SEEN")],
                "unit_check": [lead(7, "UNIT")]}
        keep, skipped, count = hunt.sort_leads([step], self.LOG, {"MU": "2026-12"}, {"6": "Q2"}, "2026-11-04")
        self.assertEqual(sorted(r["ticker"] for r in keep), ["DUE", "NEW"])
        self.assertEqual([len(skipped[k]) for k in ("rejection log", "watchlist", "on our map", "tested before on this step", "unit slip")], [1, 1, 1, 1, 1])
        self.assertEqual(count, 6)

    def test_a_new_quarter_is_a_new_lead(self):
        keep, _, _ = hunt.sort_leads([{"later": "Q3", "leads": [lead(6, "SEEN")]}], {}, {}, {"6": "Q2"}, "2026-11-04")
        self.assertEqual(len(keep), 1)

    def sub(self, state="DE", forms=("10-Q",), days=("2026-10-01",)):
        return {"stateOfIncorporation": state, "filings": {"recent": {"form": list(forms), "filingDate": list(days)}}}

    def run_rank(self, pool, frame, look, take=2):
        return hunt.rank(pool, frame, take, True, 25, look)

    def test_a_partial_frame_does_not_keep_a_company_on_top(self):
        rows = {1: 1e9, 2: 1e6, 3: 1e6, 4: 1e6}
        def look(cik):
            return self.sub(), made_rev(rows[cik])
        def made_rev(v):
            return gates.Facts({"facts": {"us-gaap": {"Revenues": {"units": {"USD": [{"start": "2025-01-01", "end": "2025-12-31", "val": v, "form": "10-K", "filed": "2026-02-01"}]}}}}})
        pool = [dict(cik=i, name=str(i), ticker=str(i), line=line(100e6 - i)) for i in rows]
        top, info = self.run_rank(pool, {1: 1e6, 2: 2e6, 3: 2e6, 4: 2e6}, look)
        self.assertNotIn(1, [t["cik"] for t in top])
        self.assertEqual(info["looked_up"], 3)  # true ratios of 2 and 3 beat the next frame ratio, so it stops

    def test_not_us_and_no_new_filing_are_counted_not_tested(self):
        rev = gates.Facts({"facts": {"us-gaap": {"Revenues": {"units": {"USD": [{"start": "2025-01-01", "end": "2025-12-31", "val": 1e6, "form": "10-K", "filed": "2026-02-01"}]}}}}})
        subs = {1: self.sub("A1"), 2: self.sub(), 3: self.sub()}
        pool = [dict(cik=1, name="f", ticker="F", line=line(5e6)), dict(cik=2, name="b", ticker="B", line=line(4e6), back={"since": "2026-11-03", "forms": ["10-K"]}),
                dict(cik=3, name="c", ticker="C", line=line(3e6))]
        top, info = self.run_rank(pool, {1: 1e6, 2: 1e6, 3: 1e6}, lambda c: (subs[c], rev))
        self.assertEqual([t["cik"] for t in top], [3])
        self.assertEqual((len(info["not_us"]), len(info["not_yet"])), (1, 1))

    def test_a_blank_state_needs_a_us_filer(self):
        broadcom = {"stateOfIncorporation": "", "addresses": {"business": {"stateOrCountry": "CA"}}, "filings": {"recent": {"form": ["10-Q"]}}}
        fujikura = {"stateOfIncorporation": "", "addresses": {"business": {"stateOrCountry": "NY"}}, "filings": {"recent": {"form": ["F-6EF"]}}}
        self.assertTrue(hunt.is_us(broadcom)[0])
        self.assertFalse(hunt.is_us(fujikura)[0])


class Idea(unittest.TestCase):
    def sample(self):
        return {"cik": 9, "name": "Co", "ticker": "COO", "line": line(), "ratio": 0.5, "revenue": 1e9, "revenue_year": "2025-12-31", "doc_url": "https://x/d", "rank": 1, "step": "Q2",
                "gate1": {"state": "pass", "tests": [{"name": "Sales", "state": "pass", "read": "ok"}]}, "gate2": {"state": "open", "read": "No price read."}, "lines_file": "x"}

    def test_the_note_has_why_and_source_and_no_view(self):
        note = hunt.idea_note(self.sample(), {"today": "2026-12-15", "retrieved": "2026-12-15"}, {"quote": "contract liabilities rose on a deal", "says": "A deal."})
        self.assertIn("## Why it surfaced", note)
        self.assertIn("[frame CY2026Q2I, retrieved Dec. 15, 2026]", note)
        self.assertIn("never a pick", note)
        self.assertNotRegex(note, r"(?i)\brecommend")

    def test_other_readers_of_inbox_leave_an_idea_alone(self):
        note = hunt.idea_note(self.sample(), {"today": "2026-12-15", "retrieved": "2026-12-15"}, {"quote": "", "read": False})
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "2026-12-15 COO idea.md").write_text(note)
            self.assertEqual(radar.read_inbox(d), {})
            sys.path.insert(0, str(ROOT / "dashboard"))
            try:
                import data
            except ImportError:
                return
            self.assertEqual(data.read_inbox(d), [])

    def test_a_made_up_quote_is_refused(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            f = Path(d) / "lines.txt"
            f.write_text("Contract liabilities rose\nbecause of one deal.\n")
            t = dict(self.sample(), lines_file=str(f.relative_to(ROOT)))
            order = {"ideas": ["COO"], "tested": [t]}
            self.assertEqual(hunt.check(order, {"COO": {"quote": "Contract liabilities rose because of one deal.", "says": "One deal."}}, None), [])
            self.assertTrue(hunt.check(order, {"COO": {"quote": "Contract liabilities fell."}}, None))
            self.assertTrue(hunt.check(order, {"COO": {"quote": "Contract liabilities rose because of one deal.", "says": "Worth buying now."}}, None))
            self.assertTrue(hunt.check(order, {}, None))


class Walk(unittest.TestCase):
    def links(self):
        return radar.read_links(ROOT / "Companies")[0]

    def test_real_graph_reaches_corning_in_one_step(self):
        out = events.reach(self.links(), "Lumen", {"Corning"})
        self.assertEqual([(r["target"], r["step"]) for r in out], [("Corning", 1)])
        self.assertIn("Corning supplies Lumen", out[0]["paths"][0]["text"])

    def test_two_steps_on_one_chain_only(self):
        link = lambda a, b, chain: {"kind": "supplies", "a": a, "b": b, "chain": chain, "what": "", "size": "", "evidence": "Stated", "weak": False, "source": ""}
        out = events.reach([link("A", "B", "fiber"), link("B", "T", "fiber"), link("B", "U", "solar")], "A", {"T", "U"})
        self.assertEqual([r["target"] for r in out], ["T"])
        self.assertEqual(out[0]["step"], 2)
        self.assertIn("A supplies B", out[0]["paths"][0]["text"])

    def test_a_filer_is_not_its_own_target(self):
        self.assertEqual(events.reach(self.links(), "Corning", {"Corning"}), [])

    def test_targets_are_kill_line_theses_and_paper_positions(self):
        targets, problems = events.find_targets()
        self.assertEqual(list(targets), ["Corning"])
        self.assertEqual(problems, [])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.md"
            p.write_text("## Positions\n\n| Ticker | Shares |\n|---|---|\n| META | 10 |\n\n## Changes\n| x |\n")
            self.assertEqual(events.paper_tickers(p), ["META"])
            p.write_text("nothing")
            with self.assertRaises(events.Refused):
                events.paper_tickers(p)

    def test_only_new_item_101_or_102_8ks(self):
        info = {"cik": 1, "sub": {"filings": {"recent": {"form": ["8-K", "8-K", "10-Q", "8-K", "8-K", "8-K", "8-K", "8-K"], "filingDate": ["2026-11-04"] * 4 + ["2026-01-01"] + ["2026-11-04"] * 3,
                "items": ["1.01,9.01", "2.02", "1.01", "1.01", "1.01", "1.02,8.01", "7.01", "8.01,9.01"], "accessionNumber": ["new", "no", "form", "seen", "old", "ended", "fd", "other"], "primaryDocument": list("abcdefgh")}}}}
        self.assertEqual([x["accession"] for x in events.new_items("N", info, {"seen"}, "2026-11-01", None)], ["new", "ended"])

    def test_a_supplier_reaches_each_holding_it_supplies_and_no_one_for_corning(self):
        links = self.links()
        self.assertEqual([r["target"] for r in events.reach(links, "Corning", {"Meta", "AT&T", "Corning"})], ["AT&T", "Meta"])
        self.assertFalse([x for x in links if x["kind"] == "supplies" and x["b"] == "Corning"])


class Readings(unittest.TestCase):
    QUOTE = "AT&T agreed to purchase the fiber business of Lumen for cash."

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.dir.cleanup)
        doc = Path(self.dir.name) / "d.txt"
        doc.write_text(self.QUOTE.replace(" the ", "\nthe ") + "\n")
        reached = [{"target": "Corning", "step": 1, "paths": [{"step": 1, "text": "Corning supplies Lumen", "evidence": "Stated"}]}]
        e = {"accession": "A", "company": "Lumen", "form": "8-K", "filed": "2025-05-21", "url": "https://x/a", "doc": str(doc.relative_to(ROOT)), "reached": reached, "items": ["1.01"]}
        f = dict(e, accession="B", company="AT&T", url="https://x/b")
        self.order = {"events": [e, f]}

    def good(self, **kw):
        return dict({"accession": "A", "target": "Corning", "level": "Info", "rule": "I8", "quote": self.QUOTE, "says": "It says nothing on any claim."}, **kw)

    def test_clean_readings_pass(self):
        self.assertEqual(events.check(self.order, [self.good(), self.good(accession="B", same_event_as="A")]), [])

    def test_every_pair_needs_a_reading(self):
        self.assertTrue(any("No reading" in p for p in events.check(self.order, [self.good()])))

    def bad(self, **kw):
        return [p for p in events.check(self.order, [self.good(**kw), self.good(accession="B")])]

    def test_refusals(self):
        self.assertTrue(self.bad(quote="AT&T agreed to purchase the whole of Corning for a large sum."))
        self.assertTrue(self.bad(level="Orange", rule="I8"))
        self.assertTrue(self.bad(level="Orange", rule="O2", says="A fact on demand."))
        self.assertTrue(self.bad(level="Red", rule="R2", says="C2 is contradicted."))
        self.assertTrue(self.bad(level="Red", rule="R1", says="A deal ended."))
        self.assertTrue(self.bad(says="The owner should trim."))
        self.assertTrue(self.bad(says="The share price says so."))
        self.assertTrue(self.bad(read=False))

    def test_not_read_keeps_the_first_pass(self):
        self.assertEqual(self.bad(read=False, level="Orange", rule="8-K first pass", quote="", says=""), [])

    def test_a_102_alone_stays_red_and_only_there(self):
        for e in self.order["events"]:
            e["items"] = ["1.01"]
        self.order["events"][0]["items"] = ["1.02", "8.01"]
        self.assertTrue(any("stays Red" in p for p in self.bad()))
        self.assertEqual(self.bad(level="Red", rule="R3", says="A credit agreement ended, and it names no customer."), [])
        self.assertEqual(self.bad(level="Red", rule="R1", says="K2 is crossed: made up for this test."), [])
        self.assertTrue(self.bad(read=False, level="Orange", rule="8-K first pass", quote="", says=""))
        self.assertTrue(events.check(self.order, [self.good(level="Red", rule="R3"), self.good(accession="B", level="Red", rule="R3")]))

    def test_a_102_with_a_101_stays_orange_until_read(self):
        self.assertEqual(events.first_pass(["1.01", "1.02"]), ("Orange", "8-K first pass"))
        self.assertEqual(events.first_pass(["1.02"]), ("Red", "R3"))

    def test_a_paper_holding_with_no_numbered_claims_can_reach_orange(self):
        self.order["targets"] = {"Corning": {"kill": None}}
        self.assertEqual(self.bad(level="Orange", rule="O2", says="The supplier's capacity could change the holding's supply."), [])

    def test_a_made_up_red_passes_with_its_line_and_tells_the_owner(self):
        row = self.good(level="Red", rule="R1", says="K2 is crossed: Lumen says its deal was reduced, made up for this test.")
        self.assertEqual(events.check(self.order, [row, self.good(accession="B")]), [])

    def test_one_event_one_alert_at_its_highest_level(self):
        alerts = events.grouped(self.order, [self.good(level="Orange", rule="O2", says="C2 could move."), self.good(accession="B", same_event_as="A")])
        self.assertEqual(len(alerts), 1)
        self.assertEqual((alerts[0]["level"], alerts[0]["filers"]), ("Orange", ["Lumen", "AT&T"]))
        self.assertIn("https://x/a", events.alert_line(alerts[0]))
        self.assertIn("https://x/b", events.alert_line(alerts[0]))


class Samples(unittest.TestCase):
    def test_every_saved_replay_quote_is_in_its_filing(self):
        total = 0
        for name in ("replay-1", "replay-2"):
            folder = HERE / "samples" / name
            for r in json.loads((folder / "readings.json").read_text()):
                text = hunt.squeeze((folder / "docs" / f'{r["accession"]}.txt').read_text())
                self.assertIn(hunt.squeeze(r["quote"]), text)
                total += 1
        self.assertEqual(total, 8)

    def test_the_102_replay_is_all_r3_and_its_quotes_are_in_its_filings(self):
        folder = HERE / "samples" / "replay-3"
        rows = json.loads((folder / "readings.json").read_text())
        self.assertEqual([r["rule"] for r in rows], ["R3"] * 3)
        for r in rows:
            self.assertIn(hunt.squeeze(r["quote"]), hunt.squeeze((folder / "docs" / f'{r["accession"]}.txt').read_text()))

    def test_item_102_counts_from_the_saved_list(self):
        rows = [r for r in json.loads((HERE / "samples/two-years-102.json").read_text()) if r["company"] != "Corning"]
        self.assertEqual((len(rows), sum(r["alone"] for r in rows)), (6, 3))

    def test_two_year_counts_from_the_saved_list(self):
        rows = [r for r in json.loads((HERE / "samples/two-years.json").read_text()) if r["company"] not in ("Corning", "Linde")]
        self.assertEqual(len(rows), 52)
        self.assertEqual(sum("Corning" in r["hits"] for r in rows), 0)


class Prompts(unittest.TestCase):
    def prompt(self, name):
        return re.search(r"```text\n(.*?)\n```", (ROOT / "Playbooks" / name).read_text(), re.S).group(1)

    def test_commands_exist_and_stay_within_bounds(self):
        hunt_p, event_p = self.prompt("Monthly hunt.md"), self.prompt("Event run.md")
        for c in ("hunt.py start", "hunt.py gate2", "hunt.py finish"):
            self.assertIn(c, hunt_p)
        for c in ("events.py start", "events.py finish"):
            self.assertIn(c, event_p)
        self.assertIn("Never run sensors/radar/radar.py or sensors/prices/prices.py", hunt_p)
        self.assertIn("never fetches or reads a price", event_p)

    def test_the_scripts_never_run_the_radar_or_ask_yahoo(self):
        for f in ("hunt.py", "events.py", "gates.py"):
            text = (HERE / f).read_text()
            self.assertNotIn("radar.run(", text)
            self.assertNotIn("yfinance", text)
            self.assertNotRegex(text, r"prices\.(pull|fetch|run|main)")


if __name__ == "__main__":
    unittest.main()
