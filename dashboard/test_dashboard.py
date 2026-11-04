"""Offline tests for the dashboard. Run from the project root:
    .venv/bin/python dashboard/test_dashboard.py
"""

import ast
import contextlib
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
os.chdir(HERE)  # Streamlit reads .streamlit/config.toml from here, so the tests use the real settings
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import data  # noqa: E402
import health  # noqa: E402
import prices  # noqa: E402
import view  # noqa: E402

UTC = dt.timezone.utc
NOTE = """---
ticker: GLW
company: "Corning"
form: 8-K
filed: "{filed}"
accession: {accession}
items: ["2.02", "9.01"]
flagged: ["2.02"]
attention: {attention}
rated by: rule
reason: {reason}
sources:
  - "{url}"
---

# Body
"""


def write_note(folder, filed="2026-10-27", accession="0000024741-26-000273", attention="high", reason='"Why."',
               url="https://www.sec.gov/x.htm"):
    text = NOTE.format(filed=filed, accession=accession, attention=attention, reason=reason, url=url)
    (Path(folder) / f"{filed} GLW 8-K {accession}.md").write_text(text)


def write_prices(folder, close="50.25"):
    folder = Path(folder) / "GLW"
    folder.mkdir(parents=True)
    body = (",".join(prices.COLUMNS) + "\n"
            f"2026-10-30,1,1,1,49,49,1,0,0\n2026-11-02,1,1,1,{close},{close},1,0,0\n").encode()
    (folder / "2026-11-02.csv").write_bytes(body)
    (folder / "manifest.json").write_text(json.dumps({"attempts": [
        {"started_utc": "2026-11-02T23:57:06+00:00", "status": "ok", "file": "2026-11-02.csv", "rows": 2,
         "sha256": hashlib.sha256(body).hexdigest(), "first": "2026-10-30", "last": "2026-11-02", "source": "Yahoo test"}]}))


class Watchlist(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.toml = self.dir / "w.toml"
        self.toml.write_text('[[company]]\nname="Corning"\nticker="GLW"\nsince="2025-11-02"\n'
                             '[[company]]\nname="Other"\nticker="OTH"\nsince="2025-11-02"\n')

    def test_price_and_its_date(self):
        write_prices(self.dir)
        row = data.watchlist_rows(self.toml, self.dir)[0]
        self.assertEqual((row["price"]["close"], row["price"]["date"]), (50.25, "2026-11-02"))

    def test_company_with_no_price_is_unknown_and_no_folder_is_made(self):
        row = data.watchlist_rows(self.toml, self.dir)[1]
        self.assertIsNone(row["price"])
        self.assertFalse((self.dir / "OTH").exists())
        self.assertIn("No price on file", view.watchlist_table([row], dt.datetime(2026, 11, 3, tzinfo=UTC)))

    def test_changed_price_file_is_a_problem_not_a_number(self):
        write_prices(self.dir)
        with open(self.dir / "GLW" / "2026-11-02.csv", "a") as f:
            f.write("tampered")
        row = data.watchlist_rows(self.toml, self.dir)[0]
        self.assertIsNone(row["price"])
        self.assertIn("does not match", row["problem"])


class Inbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_newest_first_and_readme_skipped(self):
        write_note(self.dir, "2026-01-01", "a")
        write_note(self.dir, "2026-09-01", "b")
        (self.dir / "README.md").write_text("# Inbox")
        self.assertEqual([n["filed"] for n in data.read_inbox(self.dir)], ["2026-09-01", "2026-01-01"])

    def test_attention_sets_the_colour_class(self):
        for level in ("high", "medium", "low"):
            write_note(self.dir, attention=level, accession=level)
        table = view.filings_table(data.read_inbox(self.dir))
        for level in ("high", "medium", "low"):
            self.assertIn(f'class="lvl-{level}"', table)

    def test_odd_attention_is_unknown_not_a_guess(self):
        write_note(self.dir, attention="urgent")
        self.assertEqual(data.read_inbox(self.dir)[0]["attention"], "unknown")

    def test_broken_note_is_listed_not_hidden(self):
        (self.dir / "2026-02-02 broken.md").write_text("no front matter")
        note = data.read_inbox(self.dir)[0]
        self.assertTrue(note["problem"])
        self.assertIn("Could not read", view.filings_table([note]))

    def test_nothing_in_a_note_can_make_the_browser_fetch(self):
        write_note(self.dir, reason=json.dumps('<img src="http://evil.test/a.png"> ![x](http://evil.test/b.png) <script>x</script>'),
                   url="javascript:alert(1)")
        table = view.filings_table(data.read_inbox(self.dir))
        self.assertNotIn("<img", table)
        self.assertNotIn("<script", table)
        self.assertNotIn("javascript:", table)
        self.assertNotIn("href", table)


class Ages(unittest.TestCase):
    def test_age_text(self):
        now = dt.datetime(2026, 11, 3, 12, tzinfo=UTC)
        self.assertEqual(data.age_text(now - dt.timedelta(minutes=5), now), "under 1 hour")
        self.assertEqual(data.age_text(now - dt.timedelta(hours=1), now), "1 hour")
        self.assertEqual(data.age_text(now - dt.timedelta(days=3), now), "3 days")
        self.assertEqual(data.age_text(dt.date(2026, 11, 3), now.date()), "today")
        self.assertEqual(data.age_text(dt.date(2026, 10, 31), now.date()), "3 days")

    def test_monthly_series_counts_from_the_month_end(self):
        rows = {r["name"]: r for r in data.source_rows(dt.datetime(2026, 11, 3, tzinfo=UTC))}
        self.assertEqual(rows["FRED, Moody's Aaa"]["data_end"].day, 31)

    def test_every_source_has_an_age_or_says_why_not(self):
        for r in data.source_rows():
            self.assertTrue(r["problem"] or (r["retrieved"] and r["data_end"]), r["name"])


class MatchesEconomyPage(unittest.TestCase):
    def test_counts_come_from_the_same_code(self):
        y = data.yield_view()
        months = y["months"]
        self.assertEqual((y["above"], y["compared"]), data.draw.beat_count(months))
        self.assertAlmostEqual(y["yield"], y["eps"] / y["close"] * 100)


class Chart(unittest.TestCase):
    def test_no_field_name_can_break_vega(self):
        """An apostrophe in a field name stops the chart in the browser only, with no Python error."""
        spec = view.yield_chart(data.yield_view()).to_dict()
        fields = []

        def walk(node):
            if isinstance(node, dict):
                if isinstance(node.get("field"), str):
                    fields.append(node["field"])
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(spec)
        self.assertTrue(fields)
        for rows in spec["datasets"].values():
            fields.extend(rows[0])
        for field in fields:
            self.assertRegex(field, r"^[A-Za-z_]+$")


def app_files():
    """Every file the board runs. A new screen is covered by being in screens/. tools/ writes and starts Chrome, so the board may never import it."""
    return ["app.py", "data.py", "view.py", "health.py", *sorted(f"screens/{p.name}" for p in (HERE / "screens").glob("*.py"))]


class Local(unittest.TestCase):
    def test_the_board_never_imports_the_tools(self):
        self.assertEqual(len(app_files()), 9)
        for name in app_files():
            for node in ast.walk(ast.parse((HERE / name).read_text())):
                if isinstance(node, ast.Import):
                    found = {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom):
                    found = {(node.module or "").split(".")[0]}
                else:
                    continue
                self.assertFalse(found & {"tools", "chrome", "busy_copy", "measure_home", "look_company", "look_ideas", "look_journal", "publish", "phone", "launch", "board"}, f"{name}: {found}")

    def test_settings_file(self):
        conf = tomllib.loads((HERE / ".streamlit" / "config.toml").read_text())
        self.assertEqual(conf["server"]["address"], "127.0.0.1")
        self.assertIs(conf["server"]["headless"], True)
        self.assertIs(conf["browser"]["gatherUsageStats"], False)

    def test_source_has_no_network_or_write_path(self):
        banned_imports = {"edgar", "watch", "yfinance", "curl_cffi", "requests", "urllib", "http", "socket", "httpx", "subprocess"}
        banned_calls = {"fetch", "download", "pull", "update_manifest", "write_text", "write_bytes", "open", "mkdir", "unlink",
                        "save_manifest", "_write_atomic"}
        for name in app_files():
            tree = ast.parse((HERE / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    found = {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom):
                    found = {(node.module or "").split(".")[0]}
                else:
                    found = set()
                self.assertFalse(found & banned_imports, f"{name}: {found}")
                if isinstance(node, ast.Call):
                    call = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                    self.assertNotIn(call, banned_calls, f"{name}: {call}()")


NO_VIEW_LINES = ("Only the price against value panel sets price against base value. It shows where the price sits and gives no buy or trim recommendation. The rest of this page gives no view.",
                 "It does not use base value, so it says nothing about buying or trimming.")
VIEW_WORDS = re.compile(r"\b(buy|buying|sell|selling|trim|trimming|hold|recommend\w*|undervalued|overvalued|cheap|expensive|"
                        r"fair value|intrinsic|margin of safety|price target|target price|upside|downside|attractive|bargain|"
                        r"covers?|covered)\b", re.I)
ALERT_WORDS = re.compile(r"\b(alert\w*|warn\w*|stale|overdue|out of date|too old|urgent|surg\w*|plung\w*|soar\w*|crash\w*|"
                         r"spik\w*|jump\w*|tumbl\w*|rall\w*|moved?|rose|fell)\b", re.I)


# The owner asked for these two lines on the page on Nov. 3, 2026, after approving the method. Only these two names leave the word check.
LINE_NAMES = re.compile(r"\b(buy-below|trim-above)\b", re.I)


def plain(markup):
    """What a reader sees: tags gone, escapes undone, spaces collapsed."""
    return " ".join(html.unescape(re.sub(r"<style.*?</style>|<[^>]+>", " ", markup, flags=re.S)).split())


def own_words(markup):
    """A piece of a screen without the words copied from a file. A separate test checks that those words really are in the vault."""
    tree = parse(markup)

    def walk(node):
        if "d-copied" in node["classes"] or "d-src" in node["classes"] or node["tag"] in ("style", "cite"):
            return ""
        return " ".join(child if isinstance(child, str) else walk(child) for child in node["kids"])

    return html.escape(walk(tree))


def tags_only(markup):
    return re.sub(r">[^<]*<", "><", markup)


def yield_fixture(value, aaa=6.12):
    day = dt.date(2026, 11, 2)
    return {"yield": value, "aaa": aaa, "aaa_month": dt.date(2026, 10, 1), "date": "2026-11-02", "eps": 2.47, "close": 123.2,
            "step": {"url": "https://www.sec.gov/x.htm", "form": "10-Q", "filed": "2026-10-29"}, "above": 1, "compared": 2,
            "last_above": day, "since": 1, "fetched": dt.datetime(2026, 11, 2, tzinfo=UTC),
            "aaa_downloaded": dt.datetime(2026, 11, 3, tzinfo=UTC), "aaa_url": "https://fred.stlouisfed.org/series/AAA"}


def price_row(close, date="2026-11-02"):
    return {"name": "Corning", "ticker": "GLW", "problem": None,
            "price": {"close": close, "date": date, "fetched": dt.datetime(2026, 11, 2, tzinfo=UTC), "file": "f.csv", "source": "Yahoo test"}}


SCREENS = ("screens/home.py", "screens/company.py", "screens/portfolio.py", "screens/ideas.py", "screens/journal.py")


def run_screens(company="GLW"):
    """The real app on the real files, each screen through st.navigation. AppTest can switch to a file-based page, once it has run once."""
    from streamlit.testing.v1 import AppTest

    page = AppTest.from_file(str(HERE / "app.py"), default_timeout=60).run()
    out = {}
    for screen in SCREENS:
        page.switch_page(screen)
        if screen == "screens/company.py" and company:
            page.query_params["company"] = company
        page.run()
        assert not page.exception, (screen, list(page.exception))
        out[screen] = {"titles": [t.value for t in page.title], "headers": [h.value for h in page.header], "expanders": [x.label for x in page.expander],
                       "html": [h.proto.body for h in page.get("html")]}
    return out


def page_text():
    """The real screens' text, leaving out the reasons in Inbox notes. Those describe filings: "may sell up to $2B of new shares"."""
    parts = []
    for screen in run_screens().values():
        parts += screen["titles"] + screen["headers"] + screen["expanders"] + [own_words(h) for h in screen["html"]]
    text = plain(" ".join(parts))
    brief = data.last_brief()  # the brief as the routine wrote it, copied as written
    if brief:
        for line in [brief["since"], *brief["info"]]:
            text = text.replace(plain(view._inline(line)), "")
    text = text.replace("Ideas and alerts", "")  # the screen's name, in my approved plan
    for row in data.guard_events():  # the hook's record names what it stopped, such as a broker
        text = text.replace(" ".join(row["target"].split()), "")
    for note in data.read_inbox():
        text = text.replace(" ".join(note["reason"].split()), "")
    for words in sorted(radar_data_text(data.latest_radar()), key=len, reverse=True):
        text = text.replace(" ".join(words.split()), "")
    for words in sorted(valuation_data_text(data.latest_valuation()), key=len, reverse=True):
        text = text.replace(" ".join(words.split()), "")
    book = data.journal_alerts()  # lines the routines wrote, copied as written
    for row in book["alerts"]:
        text = text.replace(plain(view._inline(row["text"])), "")
    for words in view.GUARD_NAMES.values():
        text = text.replace(words, "")
    text = text.replace("Rules/alerts.md", "").replace("Alerts", "")  # the panel's name and the rule it names, asked for by the owner on Nov. 4, 2026
    for change in data.paper_portfolio()["changes"]:  # my own words in the note's log, copied as written
        for words in (change["change"], change["yes"]):
            text = text.replace(" ".join(words.split()), "")
    return LINE_NAMES.sub("", text.replace(view.ZONE_LINE, ""))


def valuation_data_text(run):
    """What the run copied from the inputs: "Display price rises hold", "Downside: ...". The panel's own wording stays in the word checks."""
    if run is None:
        return []
    words = [t for r in run["inputs"] for t in (r["label"], r["src"])]
    words += [re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", r["src"]).replace("`", "") for r in run["inputs"]]
    words += [s["name"] for s in run["scenarios"]] + [str(run["price"]["source"])]
    return [w for w in words if VIEW_WORDS.search(w) or ALERT_WORDS.search(w)]  # a label such as "Price" stays in the text


def radar_data_text(run):
    """Names and words the radar copied from notes, filings and SEC: "BEAD Buy America priority", a company called Rally.

    Only data fields come out. The panel's own wording stays in the word checks.
    """
    if run is None:
        return []
    words = [t for ev in run["events"] for t in (ev["summary"], ev["company"], ev["label"], ", ".join(ev["named"]))]
    words += [t for ev in run["events"] for b in ev["catalysts"] for t in (f'{b["title"]} ({b["why"]})',)]
    words += ["; ".join(f'{b["title"]} ({b["why"]})' for b in ev["catalysts"]) for ev in run["events"]]
    d = run["dates"]
    for c in d["soon"] + d["passed"] + d["wide"]:
        words += [c["title"], (c.get("source") or {}).get("label", "")]
    for step in run["screen"]["steps"]:
        for lead in step["leads"] + step.get("hidden_leads", []):
            words += [lead["name"], lead.get("ticker") or ""]
    words += [t for ev in run.get("hidden", {}).get("grants", []) for t in (ev["summary"], ev["company"], ev["label"])]
    for start, walk in run["walks"].items():
        words += [start, ", ".join(walk["chains"]), ", ".join(walk["named"])]  # chain names come from the notes: "cover glass"
    words += list(run["problems"])
    return [w for w in words if w]


class NoBuyOrTrimView(unittest.TestCase):
    """Rule 6: this page does not set price against base value, so nothing on it may read as a view on value."""

    def test_real_page_says_so_and_gives_no_view(self):
        text = page_text()
        for line in NO_VIEW_LINES:
            self.assertIn(line, text)
            text = text.replace(line, "")
        self.assertIsNone(VIEW_WORDS.search(text), VIEW_WORDS.search(text))

    def test_no_view_whichever_side_of_aaa_the_yield_is(self):
        for value in (50.0, 6.12, 0.5, -5.0):
            y = yield_fixture(value)
            text = plain(view.yield_summary(y))
            self.assertIn(NO_VIEW_LINES[1], text)
            text = text.replace(NO_VIEW_LINES[1], "")
            self.assertIn("This is not a valuation method.", text)
            self.assertIsNone(VIEW_WORDS.search(text), (value, text))

    def test_the_sentence_is_the_one_in_the_view(self):
        self.assertEqual(NO_VIEW_LINES[0], view.NO_VIEW_LINE)


class NoAlertOnPriceOrAge(unittest.TestCase):
    """Rule 7: no alert on a price move alone. Since Nov. 4, 2026 I have set limits, so an age past one is said in words, in the same look, and it is still no alert."""

    def test_a_huge_price_move_looks_the_same(self):
        now = dt.datetime(2026, 11, 3, tzinfo=UTC)
        calm, wild = price_row(123.2), price_row(1.0)
        self.assertEqual(tags_only(view.watchlist_table([calm], now)), tags_only(view.watchlist_table([wild], now)))

    def test_an_old_price_looks_the_same(self):
        now = dt.datetime(2026, 11, 3, tzinfo=UTC)
        new, old = price_row(123.2), price_row(123.2, "2020-01-02")
        without_words = lambda markup: re.sub(r'<div class="d-age">.*?</div>', "", markup)  # noqa: E731
        self.assertEqual(tags_only(view.watchlist_table([new], now)), tags_only(without_words(view.watchlist_table([old], now))))  # the words are the only difference
        self.assertIn("past my limit", plain(view.watchlist_table([old], now)))
        self.assertIsNone(ALERT_WORDS.search(plain(view.watchlist_table([old], now))))

    def test_old_sources_raise_nothing(self):
        recent = dt.datetime(2026, 11, 3, 12, tzinfo=UTC)
        later = dt.datetime(2036, 11, 3, tzinfo=UTC)
        rows = data.source_rows(recent)
        table_now, table_later = view.sources_table(rows, recent), view.sources_table(data.source_rows(later), later)
        self.assertEqual(tags_only(table_now), tags_only(table_later))
        self.assertNotIn("d-problem", table_later)
        self.assertIsNone(ALERT_WORDS.search(plain(table_later)))

    def test_real_page_has_no_alert_wording(self):
        text = page_text()
        self.assertIsNone(ALERT_WORDS.search(text), ALERT_WORDS.search(text))

    def test_no_price_change_is_computed_and_no_alert_element_is_used(self):
        self.assertEqual(set(price_row(1.0)["price"]), {"close", "date", "fetched", "file", "source"})
        banned = {"pct_change", "diff", "shift", "warning", "toast", "error", "success", "info", "exception", "balloons", "snow"}
        for name in app_files():
            for node in ast.walk(ast.parse((HERE / name).read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, banned, f"{name}: {node.func.attr}()")

    def test_real_price_row_holds_no_change_field(self):
        price = data.watchlist_rows()[0]["price"]
        self.assertEqual(set(price), {"close", "date", "fetched", "file", "source", "folder"})


def radar_fixture(**changes):
    near = {"title": "Near", "date_start": "2026-11-04", "date_end": "2026-11-04", "date_kind": "stated", "days_to_start": 1, "days_to_end": 1,
            "source": {"label": "Filing, Oct. 1, 2026", "url": "https://www.sec.gov/x.htm"}}
    line = {"tag": "ContractWithCustomerLiability", "label": "Contract liabilities", "earlier": 100_000_000, "later": 200_000_000,
            "end_earlier": "2026-06-30", "end_later": "2026-09-30", "rise_pct": 100.0, "rise_usd": 100_000_000, "year_ago_pct": None,
            "accession_earlier": "a", "accession_later": "b", "filing_later": "https://www.sec.gov/f.htm", "frame_later": "CY2026Q3I",
            "frame_url_later": "https://data.sec.gov/api/xbrl/frames/x.json", "unit_slip": False, "rounded_differently": False}
    step = {"earlier": "CY2026Q2I", "later": "CY2026Q3I", "filers_earlier": 100, "filers_later": 10, "filling": True, "year_ago_step": "CY2025Q2I to CY2025Q3I",
            "leads": [{"cik": 1, "name": "Some Co", "ticker": "SC", "on_map": None, "lines": [line]}], "unit_check": []}
    run = {"schema": 1, "run_date": "2026-11-03", "run_utc": "2026-11-03T10:00:00+00:00", "report": "Research/x.md", "sensors": [], "problems": [],
           "horizon_days": 90, "leads_line": "Leads, never picks.", "walks": {}, "events": [],
           "dates": {"soon": [near], "passed": [], "wide": [], "later_count": 0, "no_date_count": 0},
           "screen": {"status": "ok", "lead_count": 1, "steps": [step]}}
    run.update(changes)
    return run


class CatalystRadar(unittest.TestCase):
    """The panel reads the radar's saved run. It starts nothing, and a closer date or a larger rise looks the same."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_no_run_on_file_is_none_and_the_source_says_why(self):
        self.assertIsNone(data.latest_radar(self.dir))
        self.assertIn("No radar run", data._guarded("x", "y", lambda: data._radar_source(self.dir))["problem"])

    def test_the_newest_run_is_read(self):
        (self.dir / "2026-11-02-01.json").write_text(json.dumps(radar_fixture(run_date="2026-11-02")))
        (self.dir / "2026-11-03-01.json").write_text(json.dumps(radar_fixture(report="first")))
        (self.dir / "2026-11-03-02.json").write_text(json.dumps(radar_fixture(report="second")))
        self.assertEqual(data.latest_radar(self.dir)["report"], "second")

    def test_a_wrong_file_is_a_problem_not_a_blank(self):
        (self.dir / "2026-11-03-01.json").write_text(json.dumps({"schema": 1}))
        with self.assertRaises(ValueError):
            data.latest_radar(self.dir)

    def test_the_real_saved_run_is_read_and_draws(self):
        run = data.latest_radar()
        self.assertIsNotNone(run)
        self.assertIn("never picks", run["leads_line"])
        for step in run["screen"]["steps"]:
            self.assertIn("<table", view.radar_leads_table(step["leads"]))
        self.assertIn("<table", view.radar_dates_table(run["dates"]["soon"]))
        # A quiet run has no events. It must say so rather than draw an empty table.
        self.assertIn("<table" if run["events"] else "No new events", view.radar_events_table(run["events"]))

    def test_nothing_in_a_run_can_make_the_browser_fetch(self):
        evil = '<img src="http://evil.test/a.png"> ![x](http://evil.test/b.png) <script>x</script>'
        run = radar_fixture()
        near = run["dates"]["soon"][0]
        near.update(title=evil, source={"label": evil, "url": "javascript:alert(1)"})
        lead = run["screen"]["steps"][0]["leads"][0]
        lead["name"] = evil
        lead["lines"][0].update(filing_later="http://evil.test/x", frame_url_later="javascript:alert(1)")
        events = [{"filed": "2026-10-27", "company": evil, "url": "javascript:alert(1)", "label": evil, "summary": evil, "named": [evil], "catalysts": [{"title": evil, "why": evil}]}]
        markup = view.radar_dates_table(run["dates"]["soon"]) + view.radar_leads_table([lead]) + view.radar_events_table(events)
        self.assertNotIn("<img", markup)
        self.assertNotIn("<script", markup)
        self.assertNotIn("javascript:", tags_only(markup))
        self.assertNotIn("href", markup)

    def hidden_run(self):
        run = radar_fixture()
        step = run["screen"]["steps"][0]
        hid = json.loads(json.dumps(step["leads"][0]))
        hid.update(name="Hidden Co", not_new_growth="Current plus noncurrent total did not grow")
        step["hidden_leads"] = [hid]
        link_row = {"step": 2, "node": "Far Co", "kind": "supplies", "a": "A", "b": "Far Co", "chain": "fiber", "evidence": "Stated"}
        run["walks"] = {"Near Co": {"rows": [], "hidden_step2": [link_row], "events": 1, "step1": 0, "step2": 0, "weak": 0, "chains": [], "named": []}}
        run["hidden"] = {"grants": [], "grant_count": 4, "lead_count": 1, "step2_count": 1}
        return run, step

    def test_the_hidden_counts_show(self):
        run, step = self.hidden_run()
        line = plain(view.radar_summary(run))
        self.assertIn("4 director stock grants, 1 screen leads", line)
        self.assertIn("1 second-step links", line)
        self.assertEqual(view.radar_hidden_line(radar_fixture()), "")

    def test_the_hidden_rows_are_listed_with_why(self):
        run, step = self.hidden_run()
        table = plain(view.radar_leads_table(step["hidden_leads"]))
        self.assertIn("Hidden Co", table)
        self.assertIn("did not grow", table)
        self.assertIn("Far Co", plain(view.radar_hidden_links(run["walks"])))

    def test_the_hidden_wording_gives_no_view_and_no_alert(self):
        run, step = self.hidden_run()
        text = " ".join(plain(x) for x in (view.radar_hidden_line(run), view.radar_leads_table(step["hidden_leads"]), view.radar_hidden_links(run["walks"])))
        self.assertIsNone(VIEW_WORDS.search(text), text)
        self.assertIsNone(ALERT_WORDS.search(text), text)

    def test_a_hidden_link_cannot_make_the_browser_fetch(self):
        run, _ = self.hidden_run()
        evil = '<img src="http://evil.test/a.png"><script>x</script>'
        run["walks"]["Near Co"]["hidden_step2"][0].update(node=evil, chain=evil)
        markup = view.radar_hidden_links(run["walks"])
        self.assertNotIn("<img", markup)
        self.assertNotIn("<script", markup)

    def test_a_closer_date_looks_the_same(self):
        far = dict(radar_fixture()["dates"]["soon"][0], date_start="2034-01-01", date_end="2034-01-01", days_to_start=2600, days_to_end=2600)
        passed = dict(far, days_to_start=-100, days_to_end=-100)
        near = radar_fixture()["dates"]["soon"][0]
        self.assertEqual(tags_only(view.radar_dates_table([near])), tags_only(view.radar_dates_table([far])))
        self.assertEqual(tags_only(view.radar_dates_table([near])), tags_only(view.radar_dates_table([passed])))

    def test_a_huge_rise_looks_the_same(self):
        small = radar_fixture()["screen"]["steps"][0]["leads"][0]
        huge = json.loads(json.dumps(small))
        huge["lines"][0].update(later=9e12, rise_pct=9_000_000.0)
        self.assertEqual(tags_only(view.radar_leads_table([small])), tags_only(view.radar_leads_table([huge])))

    def test_the_panel_wording_gives_no_view_and_no_alert(self):
        run = radar_fixture()
        step = run["screen"]["steps"][0]
        text = " ".join(plain(x) for x in (view.radar_summary(run), view.radar_dates_table(run["dates"]["soon"]), view.radar_step_line(step), view.radar_leads_table(step["leads"])))
        self.assertIsNone(VIEW_WORDS.search(text), text)
        self.assertIsNone(ALERT_WORDS.search(text), text)

    def test_no_price_reaches_the_panel(self):
        self.assertNotIn("close", radar_fixture())
        run = data.latest_radar()
        self.assertFalse([e for e in run["events"] if "Yahoo" in e["form"] or e["kind"] == "price"])


class FinancialHealth(unittest.TestCase):
    """The panel reads the note's summary, and the check reads the saved filings."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.text = health.NOTE.read_text()

    def note_with(self, old, new):
        self.assertIn(old, self.text)
        path = Path(self.tmp.name) / "Corning.md"
        path.write_text(self.text.replace(old, new))
        return health.read_note(path)

    def test_every_figure_in_the_summary_has_a_check_row(self):
        note = health.read_note()
        items = {r["item"]: r for r in health.checks(note)["rows"] if r["group"] == "Summary"}
        for row in note["summary"]:
            for label, figure in row["parts"].items():
                name = f'{row["measure"]}: {label}' if label else row["measure"]
                self.assertIn(name, items)
                self.assertEqual(items[name]["ours"], figure)

    def test_real_note_ties_with_one_known_difference(self):
        rows = health.checks()["rows"]
        results = [(r["item"], r["tenk_result"], r["other_result"]) for r in rows]
        self.assertFalse([x for x in results if health.UNREAD in x])
        diffs = [x[0] for x in results if health.DIFF in x]
        self.assertEqual(diffs, ["Ladder added, against balance sheet total debt"])

    def test_the_latest_10k_is_the_one_read(self):
        self.assertEqual(health.latest_10k()["accession"], "0000024741-26-000124")

    def test_a_wrong_note_shows_a_difference_and_its_size(self):
        note = self.note_with("| Sales, FY2025 | $15,629M |", "| Sales, FY2025 | $15,729M |")
        row = [r for r in health.checks(note)["rows"] if r["item"] == "Sales, FY2025"][0]
        self.assertEqual((row["tenk"], row["tenk_result"], row["gap"]), ("$15,629M", health.DIFF, "$100M"))
        self.assertIn("≠ Difference $100M", view.check_table([row]))

    def test_a_wrong_older_year_shows_against_its_own_filing(self):
        note = self.note_with("| FY2018 | 39.5% |", "| FY2018 | 38.5% |")
        row = [r for r in health.checks(note)["rows"] if r["item"] == "FY2018 gross margin"][0]
        self.assertEqual((row["tenk_result"], row["other_result"]), (health.ABSENT, health.DIFF))

    def test_the_rounded_deposit_reads_as_approximate(self):
        note = health.read_note()
        rows = {r["item"]: r for r in health.checks(note)["rows"]}
        without = rows["Free cash flow, nine months of 2026: without"]
        deposit = rows["Free cash flow, nine months of 2026: deposit"]
        self.assertEqual((deposit["ours"], deposit["other"], deposit["other_result"]), ("about $1.0 billion", "$1.0 billion", health.MATCH))
        self.assertEqual((without["ours"], without["other"], without["other_result"]), ("about $841M", "$841M", health.APPROX))
        self.assertIn("≈ Match, approximate", view.check_table([without]))
        self.assertIn("$792M to $891M", without["how"])
        self.assertEqual(health.millions(deposit["ours"]), 1000)

    def test_the_watch_table_agrees_with_the_summary(self):
        note = health.read_note()
        row = [w for w in note["watch"] if w["period"] == "Nine months 2026"][0]
        parts = [r for r in note["summary"] if r["measure"] == "Free cash flow, nine months of 2026"][0]["parts"]
        self.assertEqual((row["fcf"], row["deposits"], row["without"]), (parts["with deposit"], parts["deposit"], parts["without"]))

    def test_the_second_deposit_reading_ties_to_the_filing(self):
        rows = {r["item"]: r for r in health.checks(health.read_note())["rows"]}
        for item, ours in (("Nine months 2026 filed deposits line", "+$639M"), ("Nine months 2026 without the filed line", "$1,202M"),
                           ("Nine months 2025 filed deposits line", "−$49M"), ("Nine months 2025 without the filed line", "$842M")):
            self.assertEqual((rows[item]["ours"], rows[item]["other_result"]), (ours, health.MATCH), item)

    def test_a_wrong_second_reading_shows_a_difference(self):
        note = self.note_with("| +$639M | $1,202M |", "| +$639M | $1,302M |")
        row = [r for r in health.checks(note)["rows"] if r["item"] == "Nine months 2026 without the filed line"][0]
        self.assertEqual(row["other_result"], health.DIFF)

    def test_both_deposit_readings_appear_on_the_panel(self):
        table = view.deposit_line_table(health.read_note())
        self.assertIn("$1,202M", table)
        self.assertIn("$842M", table)

    def test_the_estimate_ties_to_the_filing_and_reads_as_approximate(self):
        rows = {r["item"]: r for r in health.checks(health.read_note())["rows"]}
        self.assertEqual((rows["Nine months 2026 older deposits applied"]["ours"], rows["Nine months 2026 older deposits applied"]["other_result"]), ("$237M", health.MATCH))
        self.assertEqual((rows["Nine months 2025 older deposits applied"]["ours"], rows["Nine months 2025 older deposits applied"]["other_result"]), ("$94M", health.MATCH))
        self.assertEqual((rows["Nine months 2026 estimate, both sides out"]["ours"], rows["Nine months 2026 estimate, both sides out"]["other_result"]), ("about $1,078M", health.APPROX))
        self.assertEqual((rows["Nine months 2025 estimate, both sides out"]["ours"], rows["Nine months 2025 estimate, both sides out"]["other_result"]), ("$887M", health.MATCH))
        self.assertIn("An estimate", rows["Nine months 2026 estimate, both sides out"]["how"])

    def test_a_wrong_estimate_shows_a_difference(self):
        note = self.note_with("| $237M | about $1,078M |", "| $237M | about $1,178M |")
        row = [r for r in health.checks(note)["rows"] if r["item"] == "Nine months 2026 estimate, both sides out"][0]
        self.assertEqual(row["other_result"], health.DIFF)

    def test_the_deposit_bar_is_drawn_at_its_size(self):
        rows = next(iter(view.deposit_chart(health.read_note()).to_dict()["datasets"].values()))
        bar = [r for r in rows if r["Period"] == "Nine months 2026"]
        self.assertEqual([r["Amount"] for r in bar], [841, 1000])

    def test_only_fy2023_to_fy2025_tie_to_the_latest_10k(self):
        rows = [r for r in health.checks()["rows"] if r["group"] == "Margins chart"]
        for r in rows:
            year = int(r["item"][2:6])
            self.assertEqual(r["tenk_result"], health.MATCH if year >= 2023 else health.ABSENT, r["item"])

    def test_filing_we_cannot_read_never_reads_as_a_match(self):
        note = self.note_with("[k20]: https://www.sec.gov/Archives/edgar/data/24741/000156276221000023/glw-20201231x10k.htm",
                              "[k20]: https://www.sec.gov/Archives/edgar/data/24741/000156276221000023/missing.htm")
        rows = [r for r in health.checks(note)["rows"] if r["item"] == "FY2018 gross margin"]
        self.assertEqual(rows[0]["other_result"], health.UNREAD)

    def test_counts_are_not_called_filing_numbers(self):
        rows = [r for r in health.checks()["rows"] if r["item"].startswith(("Classic value tests", "Red flags"))]
        self.assertEqual(len(rows), 7)
        for r in rows:
            self.assertEqual((r["tenk_result"], r["other_result"]), (health.NO_FILING, health.MATCH))

    def test_meaning_lines_hold_no_number_that_escapes_the_check(self):
        for row in health.read_note()["summary"]:
            self.assertIsNone(re.search(r"\$|%|\d[\d.,]*[Mx]\b", row["means"]), row["means"])

    def test_every_summary_row_names_a_dated_filing(self):
        for row in health.read_note()["summary"]:
            self.assertTrue(row["filings"], row["measure"])
            for text, url in row["filings"]:
                self.assertRegex(text, r"\b(19|20)\d\d\b")
                self.assertTrue(url and url.startswith("https://www.sec.gov/"), text)

    def test_a_missing_section_is_a_problem_not_a_blank(self):
        path = Path(self.tmp.name) / "Corning.md"
        path.write_text(self.text.replace("## Financial health summary", "## Something else"))
        with self.assertRaises(ValueError):
            health.read_note(path)

    def test_note_text_cannot_make_the_browser_fetch(self):
        note = self.note_with("The largest of the ten years in this note.", '<img src="http://evil.test/a.png"> ![x](http://evil.test/b.png)')
        table = view.health_summary(note, [])
        self.assertNotIn("<img", table)
        for href in re.findall(r'href="([^"]+)"', table):
            self.assertTrue(href.startswith("https://www.sec.gov/"), href)

    def test_chart_columns_are_plain(self):
        note = health.read_note()
        for build in (view.margins_chart, view.gaap_core_chart, view.fcf_chart, view.deposit_chart, view.ladder_chart):
            for rows in build(note).to_dict()["datasets"].values():
                for field in rows[0]:
                    self.assertRegex(field, r"^[A-Za-z_]+$", build.__name__)

    def test_chart_points_come_from_the_note(self):
        spec = view.ladder_chart(health.read_note()).to_dict()
        rows = next(iter(spec["datasets"].values()))
        self.assertEqual([r["Amount"] for r in rows], [804, 401, 296, 302, 298, 6379])


def valuation_fixture(close=123.2, **changes):
    series = [["2026-10-30", 123.31], ["2026-11-02", close]]
    mid, strategic = 21.73, 14.33
    trim, buy = mid + strategic, mid / .75
    row = lambda key, label, a, b, **more: dict(key=key, label=label, method="m", scope="base", basis="Basis.", ends=False,  # noqa: E731
                                                swing=dict(base=b - a, buy=(b - a) / .75, trim=b - a), **more,
                                                readings=[dict(text=t, base=v, buy=v / .75, trim=v + strategic, coverage=v / close, zone=data.valuation_zone(v, close, v + strategic), flags=[]) for t, v in (("low", a), ("high", b))])
    run = {"schema": 1, "company": "Corning", "ticker": "GLW", "worked_out": "2026-11-03", "run_utc": "2026-11-03T12:00:00+00:00", "run_file": "sensors/valuation/runs/x.json",
           "price": {"close": close, "date": "2026-11-02", "src": "close of Nov. 2, 2026, [Yahoo, fetched Nov. 2, 2026](https://query1.finance.yahoo.com/x)", "file": "f.csv", "source": "Yahoo test"},
           "series": series, "base": {"low": 14.06, "mid": mid, "high": 30.03},
           "coverage": {"mid": mid / close, "low": 14.06 / close, "high": 30.03 / close, "bar": .75, "met": mid / close >= .75},
           "buy_below": buy, "strategic": strategic, "trim_above": trim, "zone": data.valuation_zone(mid, close, trim),
           "scenarios": [{"key": "s", "name": "A step", "full": 7.0, "chance": .7, "value": 4.9, "status": "approved"}],
           "no_vote": [{"name": "Own past multiples", "low": 1.0, "mid": 2.0, "high": 3.0}], "growth_needed": {"from_high": .2, "from_mid": .3},
           "inputs": [{"label": "aaa", "v": .0612, "src": "[FRED, Oct. 2026](https://fred.stlouisfed.org/series/AAA)"}], "checks": ["Checked."], "open": [],
           "what_if": {"label": "What-if, one assumption at a time. Not the method's answer.", "rows": [row("earnings", "Normal earnings", 17.17, 26.22), row("cash", "Cash", 19.9, 23.33)],
                       "ranked": {"base": ["earnings", "cash"], "buy": ["earnings", "cash"], "trim": ["earnings", "cash"]}, "most": {"base": "earnings", "buy": "earnings", "trim": "earnings"},
                       "zone_changes": [], "not_run": ["Line."], "highest_coverage": .21, "slopes": [{"label": "Rate", "base": -.008, "trim": -.01}]}}
    return {**run, **changes}


def write_valuation(folder, run, name="2026-11-03-01.json"):
    (Path(folder) / name).write_text(json.dumps(run))


PANEL = ("value_summary", "value_table", "value_no_vote", "value_inputs_table", "what_if_lead", "what_if_table", "what_if_slopes")


def panel_html(run):
    return " ".join(getattr(view, name)(run) for name in PANEL)


class PriceAgainstValue(unittest.TestCase):
    """The panel reads one saved run. It shows lines and a zone, and it is not a recommendation or an alert."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def test_no_run_on_file_is_none_and_the_source_says_why(self):
        self.assertIsNone(data.latest_valuation(self.folder.name))
        rows = data.source_rows(valuation_runs=self.folder.name)
        self.assertIn("No valuation run", next(r for r in rows if r["name"] == "Valuation, saved run")["problem"])

    def test_the_newest_run_is_read(self):
        write_valuation(self.folder.name, valuation_fixture(), "2026-11-03-01.json")
        write_valuation(self.folder.name, valuation_fixture(worked_out="2027-02-20"), "2026-11-03-02.json")
        self.assertEqual(data.latest_valuation(self.folder.name)["worked_out"], "2027-02-20")

    def test_a_file_that_disagrees_with_itself_is_a_problem_not_a_figure(self):
        good = valuation_fixture()
        for bad in (dict(zone="under"), dict(trim_above=50.0), dict(buy_below=50.0), dict(coverage={**good["coverage"], "mid": .9}),
                    dict(base={"low": 30.0, "mid": 21.73, "high": 14.0}), dict(price={**good["price"], "close": 99.0}), dict(schema=2)):
            write_valuation(self.folder.name, {**good, **bad})
            with self.assertRaises(ValueError, msg=bad):
                data.latest_valuation(self.folder.name)
        broken = dict(good)
        del broken["what_if"]
        write_valuation(self.folder.name, broken)
        with self.assertRaises(ValueError):
            data.latest_valuation(self.folder.name)

    def test_zones_on_the_exact_figures(self):
        self.assertEqual(data.valuation_zone(21.73, 123.2, 36.06), "above")
        self.assertEqual(data.valuation_zone(21.73, 30.0, 36.06), "between")
        self.assertEqual(data.valuation_zone(21.73, 36.06, 36.06), "between")
        self.assertEqual(data.valuation_zone(21.73, 28.0, 36.06), "under")
        self.assertEqual(data.valuation_zone(75, 100, 200), "under")  # exactly 75% meets the bar
        self.assertEqual(data.valuation_zone(74.9, 100, 200), "between")  # 74.9% does not round up
        self.assertEqual(data.valuation_zone(21.73, 28.0, 25.0), "under_and_above")
        for key in ("under", "between", "above", "under_and_above"):
            self.assertIn(key, view.ZONE_WORDS)

    def test_the_real_run_draws_and_shows_each_asked_for_figure(self):
        run = data.latest_valuation()
        text = plain(panel_html(run))
        for figure in ("$14.06 to $30.03", "$28.97", "$36.06", "17.6%", "Nov. 3, 2026", "Nov. 2, 2026", "$123.20"):
            self.assertIn(figure, text)
        self.assertEqual(run["worked_out"], "2026-11-03")
        for out in ("base", "buy", "trim"):
            self.assertIn("Normal earnings, middle", view.what_if_frames(run, out)[0])

    def test_every_zone_looks_the_same_and_only_the_words_differ(self):
        """A zone is words on a page. It never turns red, green or bold, whichever side the price is on."""
        wide = {c: tags_only(panel_html(valuation_fixture(close=c))) for c in (123.2, 30.0, 25.0, 1.0)}
        self.assertEqual(len(set(wide.values())), 1)
        for c in (123.2, 30.0, 25.0, 1.0):
            self.assertNotIn("d-problem", panel_html(valuation_fixture(close=c)))
            self.assertNotIn("lvl-", panel_html(valuation_fixture(close=c)))

    def test_the_chart_looks_the_same_in_every_zone(self):
        colours = lambda spec: sorted(set(re.findall(r"#[0-9a-f]{6}", json.dumps(spec))))  # noqa: E731
        first = colours(view.value_chart(valuation_fixture()).to_dict())
        for c in (30.0, 25.0, 1.0):
            self.assertEqual(colours(view.value_chart(valuation_fixture(close=c)).to_dict()), first)

    def test_panel_wording_gives_no_view_and_no_alert_in_any_zone(self):
        for c in (123.2, 30.0, 25.0, 1.0):
            run = valuation_fixture(close=c)
            text = LINE_NAMES.sub("", plain(panel_html(run)).replace(view.ZONE_LINE, ""))
            for words in valuation_data_text(run):
                text = text.replace(" ".join(words.split()), "")
            self.assertIsNone(VIEW_WORDS.search(text), (c, VIEW_WORDS.search(text)))
            self.assertIsNone(ALERT_WORDS.search(text), (c, ALERT_WORDS.search(text)))

    def test_the_real_panel_wording_gives_no_view_and_no_alert(self):
        run = data.latest_valuation()
        text = LINE_NAMES.sub("", plain(panel_html(run)).replace(view.ZONE_LINE, ""))
        for words in sorted(valuation_data_text(run), key=len, reverse=True):
            text = text.replace(" ".join(words.split()), "")
        self.assertIsNone(VIEW_WORDS.search(text), VIEW_WORDS.search(text))
        self.assertIsNone(ALERT_WORDS.search(text), ALERT_WORDS.search(text))

    def test_the_zone_line_says_what_else_the_rules_need(self):
        for words in ("not a recommendation", "written thesis", "skeptic's review", "rise through the line", "holding on file", "neither thesis nor holding"):
            self.assertIn(words, " ".join(view.ZONE_LINE.split()))
        self.assertIn(view.ZONE_LINE, plain(view.value_summary(valuation_fixture())))

    def test_the_panel_names_no_zone_for_any_close(self):
        """My ruling, Nov. 4, 2026: I read the zone myself. The zone table lists all of them, the same whichever one a close is in."""
        for c in (123.2, 30.0, 25.0, 1.0):
            run = valuation_fixture(close=c)
            text = plain(panel_html(run))
            for words in view.ZONE_WORDS.values():
                self.assertNotIn(words, text, c)
            self.assertEqual(view.value_summary(run), view.value_summary(valuation_fixture()))
            one = view.price_zones(run, None)
            for words in (view.ZONE_WORDS["under"], view.ZONE_WORDS["between"], view.ZONE_WORDS["above"]):
                self.assertEqual(plain(one).count(words), 1, c)

    def test_no_status_thesis_or_holding_reaches_the_panel(self):
        run = data.latest_valuation()
        self.assertFalse({"status", "thesis", "holding", "gates"} & set(run))

    def test_what_ifs_are_labelled_as_not_the_method(self):
        self.assertIn("Not the method's answer.", plain(view.what_if_lead(data.latest_valuation())))

    def test_panel_reads_only_the_run(self):
        """No price file, note or macro file behind these functions, and value.py is not imported. The run is all they get."""
        source = (HERE / "view.py").read_text()
        tree = ast.parse(source)
        names = set(PANEL) | {"value_chart", "what_if_chart", "what_if_frames", "_inline", "_money", "_row_mark", "_method_figure"}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {f"{n.value.id}.{n.attr}" for n in ast.walk(node) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
                self.assertFalse({"health", "health.read_note"} & used, node.name)
                self.assertEqual({x for x in used if x.startswith("data.")} - {"data.nice_date"}, set(), node.name)
        for node in ast.parse((HERE / "data.py").read_text()).body:
            if isinstance(node, ast.FunctionDef) and node.name == "latest_valuation":
                used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
                self.assertFalse({"prices", "macro", "health", "earnings", "draw"} & used)
        for name in app_files():
            self.assertNotIn("value.py", re.sub(r"#.*", "", (HERE / name).read_text()).replace("sensors/valuation/save.py", ""))
            self.assertNotIn("import save", (HERE / name).read_text())

    def test_a_link_in_a_run_cannot_make_the_browser_fetch(self):
        evil = valuation_fixture(inputs=[{"label": "<img src=x>", "v": 1, "src": "<iframe src=x> ![a](http://evil.example/x.png) <img src=y> [b](javascript:alert(1)) `c` <script>"}])
        markup = view.value_inputs_table(evil)
        self.assertNotIn("<img", markup)
        self.assertNotIn("<iframe", markup)
        self.assertNotIn("<script", markup)
        self.assertNotIn('href="http://', markup)
        self.assertNotIn('href="javascript', markup)

    def test_chart_columns_are_plain(self):
        run = data.latest_valuation()
        for chart in [view.value_chart(run)] + [view.what_if_chart(run, o) for o in ("base", "buy", "trim")]:
            for rows in chart.to_dict()["datasets"].values():
                for field in rows[0]:
                    self.assertRegex(field, r"^[A-Za-z_]+$")

    def test_the_band_and_lines_are_the_run_figures(self):
        run = data.latest_valuation()
        spec = json.dumps(view.value_chart(run).to_dict()["datasets"])
        for figure in (run["base"]["low"], run["base"]["high"], run["buy_below"], run["trim_above"], run["price"]["close"]):
            self.assertIn(str(figure), spec)
        self.assertEqual(len(run["series"]), 4234)

    def test_every_row_keeps_its_label(self):
        """The browser dropped every other label at half width, and one of them was the row that matters most."""
        spec = json.dumps(view.what_if_chart(data.latest_valuation(), "base").to_dict())
        self.assertIn('"labelOverlap": false', spec)

    def test_line_labels_are_pushed_apart_but_the_lines_are_not(self):
        placed = view._spread([123.2, 36.06, 28.97, 21.73], 255.69)
        ordered = sorted(placed)
        self.assertTrue(all(b - a >= 255.69 / 340 * 16 - 1e-9 for a, b in zip(ordered, ordered[1:])))
        self.assertEqual(placed[3], 21.73)
        self.assertEqual(placed[0], 123.2)
        spec = view.value_chart(data.latest_valuation()).to_dict()
        rows = [r for rows in spec["datasets"].values() for r in rows]
        self.assertIn(data.latest_valuation()["trim_above"], [r.get("Close") for r in rows if r.get("Series") == "Trim-above"])

    def test_a_what_if_bar_starts_at_the_method_and_ends_at_the_reading(self):
        run = data.latest_valuation()
        order, bars, ends = view.what_if_frames(run, "trim")
        self.assertEqual(set(bars["Start"]), {run["trim_above"]})
        self.assertLessEqual(len(order), view.TOP_ROWS)
        widths = [run["what_if"]["rows"][[r["key"] for r in run["what_if"]["rows"]].index(k)]["swing"]["trim"] for k in run["what_if"]["ranked"]["trim"]]
        self.assertEqual(widths, sorted(widths, reverse=True))


def _tree_state():
    """Size, time and path of every project file, leaving out the virtualenv and bytecode."""
    state = {}
    for path in ROOT.rglob("*"):
        if path.is_file() and ".venv" not in path.parts and "__pycache__" not in path.parts and ".obsidian" not in path.parts:
            stat = path.stat()
            state[str(path)] = (stat.st_size, stat.st_mtime_ns)
    return state


class PageLoad(unittest.TestCase):
    """Runs the real app.py on the real files, with every outside connection recorded."""

    def test_page_load_reads_only(self):
        connections = []

        def hook(event, args):
            if event == "socket.connect":
                address = args[1]
                if isinstance(address, tuple) and address[0] not in ("127.0.0.1", "::1", "localhost"):
                    connections.append(address)
            elif event == "socket.getaddrinfo" and args[0] not in ("127.0.0.1", "::1", "localhost", None):
                connections.append(args[0])

        sys.addaudithook(hook)
        before = _tree_state()
        screens = run_screens()
        self.assertEqual(connections, [])
        self.assertEqual(before, _tree_state())
        self.assertNotIn("yfinance", sys.modules)
        self.assertNotIn("edgar", sys.modules)
        # Step 1 of the plan: the nine panels that were on the one long page, each on one screen.
        self.assertEqual({k: v["headers"] for k, v in screens.items()},
                         {"screens/home.py": [], "screens/company.py": ["What is missing, and what is on file", "Thesis status", "Price against value", "Catalysts", "Graph neighbors", "Latest 8-Ks", "Corning financial health", "Corning earnings yield against Aaa", "The note's other sections", "History"],
                          "screens/portfolio.py": ["Real", "Paper, made-up money", "Room under the limit, names against bets"], "screens/ideas.py": ["Ideas, from the first lead to a decision", "Rejection log", "Alerts", "The hunt's reports", "Catalyst radar", "Latest 8-Ks", "How old each source is"], "screens/journal.py": ["By day"]})
        self.assertEqual([v["titles"] for v in screens.values()], [[], ["Company"], ["Portfolio and cash"], ["Ideas and alerts"], ["Journal"]])

    def test_the_real_board_carries_no_test_copy_label(self):
        self.assertFalse((ROOT / "TEST_COPY.txt").exists())
        self.assertIsNone(data.test_copy_label())
        self.assertNotIn("TEST COPY", " ".join(" ".join(s["html"]) for s in run_screens().values()))


class PaperPortfolioPanel(unittest.TestCase):
    NOTE = """---
kind: paper
cash: 83000
as of: "2026-11-03"
cash above 50% since: "2026-11-03"
last checked: "2026-11-03"
---

# Paper

## Positions

| Ticker | Shares | Bought on | Cost a share | Thesis note |
|---|---|---|---|---|
| AAA | 100 | Nov. 3, 2026 | $170.00 | [[A]] |

## Changes

| Date | Change | Cash after | My yes |
|---|---|---|---|
| Nov. 3, 2026 | Made up | $83,000 | Yes |
"""

    def write(self, text):
        folder = tempfile.mkdtemp()
        path = Path(folder) / "Paper portfolio.md"
        path.write_text(text)
        return path

    def test_reads_cash_positions_and_the_log(self):
        book = data.paper_portfolio(self.write(self.NOTE))
        self.assertEqual(book["cash"], 83000)
        self.assertEqual(book["positions"][0]["cost"] * book["positions"][0]["shares"], 17000)
        self.assertEqual(book["changes"][0]["cash"], "$83,000")

    def test_cash_levels_follow_the_rule(self):
        self.assertEqual([data.cash_level(x) for x in (.151, .15, .05, .049)], ["Above normal", "Normal", "Normal", "Floor"])

    def test_a_note_not_marked_paper_is_refused(self):
        with self.assertRaises(ValueError):
            data.paper_portfolio(self.write(self.NOTE.replace("kind: paper", "kind: real")))

    def test_the_real_note_reads_and_the_panel_says_made_up(self):
        book = data.paper_portfolio()
        markup = view.PAPER_LABEL + view.book_block(book)
        self.assertIn("Made-up money", plain(markup))
        self.assertIsNone(VIEW_WORDS.search(plain(markup)))
        self.assertIsNone(ALERT_WORDS.search(plain(markup)))


BRIEF = """# 2026-11-05

**Since the brief of Nov. 4, 2026:** 3 new items.

### Red

- [Corning 8-K 1, Nov. 4, 2026](https://www.sec.gov/x), R3: item 1.03.

### Orange

- [Corning 8-K 2, Nov. 4, 2026](https://www.sec.gov/y), read: a fact on C6 (O2).

### Info

- Nothing.

## Session: first talk

### What we did

- Talked. Daily run FAILED at step 1: this sentence quotes one and is no failure line.

## Session: daily run, 08:01

### What we did

- Ran.

## Session: event run

### What we did

- Read 1.

**Red**

- [Lumen 8-K](https://www.sec.gov/z), R1, K2: a customer ended a deal.

**Orange**

- javascript link [bad](javascript:alert(1)) <img src=x onerror=y>, O2.

### What we decided

- Nothing.

Monthly hunt FAILED at step 2: no prices.
"""


class AlertsPanel(unittest.TestCase):
    """The panel only shows what the routines wrote. It judges nothing, and the words around it give no view."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        (self.folder / "2026-11-05.md").write_text(BRIEF)
        (self.folder / "2026-11-04.md").write_text("# 2026-11-04\n\n## Session: weekly thesis check, Corning\n\n### What we did\n\n- Checked.\n\n**Orange**\n\n- A fact, O1.\n")
        (self.folder / "README.md").write_text("### Red\n\n- not a daily file\n")
        self.book = data.journal_alerts(self.folder)

    def tearDown(self):
        self.temp.cleanup()

    def test_every_form_a_routine_writes_is_read(self):
        got = [(a["day"], a["level"], a["rule"], a["routine"]) for a in self.book["alerts"]]
        self.assertEqual(got, [("2026-11-05", "Red", "R3", "Daily run"), ("2026-11-05", "Orange", "O2", "Daily run"), ("2026-11-05", "Red", "R1", "Event run"), ("2026-11-05", "Orange", "O2", "Event run"),
                               ("2026-11-05", "Orange", "O16", "Monthly hunt"), ("2026-11-04", "Orange", "O1", "Weekly thesis check")])

    def test_each_routines_last_record(self):
        self.assertEqual(self.book["last_run"], {"Daily run": "2026-11-05", "Event run": "2026-11-05", "Monthly hunt": "2026-11-05", "Weekly thesis check": "2026-11-04"})
        self.assertIn("No record yet", view.routine_table(self.book))

    def test_a_session_about_a_routine_is_no_run_of_it(self):
        (self.folder / "2026-11-03.md").write_text("# 2026-11-03\n\n## Session: the monthly hunt and the event run\n\n### What we did\n\n- Built them.\n")
        book = data.journal_alerts(self.folder)
        self.assertEqual(book["last_run"]["Monthly hunt"], "2026-11-05")
        (self.folder / "2026-11-05.md").write_text("# 2026-11-05\n")
        self.assertNotIn("Monthly hunt", data.journal_alerts(self.folder)["last_run"])

    def test_a_person_talking_about_red_is_no_alert(self):
        self.assertFalse([a for a in self.book["alerts"] if "first talk" in a["text"] or "quotes one" in a["text"]])

    def test_text_is_escaped_and_only_https_links(self):
        table = view.alerts_table(data.alert_rows(self.book, TODAY)["rows"])
        self.assertNotIn("<img", table)
        self.assertNotIn("javascript:", tags_only(table))
        self.assertIn('href="https://www.sec.gov/x"', table)

    def test_the_panels_own_words_give_no_view_and_no_price_move(self):
        words = plain(view.alerts_summary(data.alert_rows(self.book, TODAY)["rows"], 3, "Nov. 5, 2026").replace("Rules/alerts.md", "") + view.alerts_table([]) + view.routine_table(self.book) + view.guard_summary([]) + view.guard_table([]))
        self.assertIsNone(VIEW_WORDS.search(words), VIEW_WORDS.search(words))
        self.assertIsNone(re.search(r"\b(stale|overdue|out of date|too old|urgent|surg\w*|plung\w*|soar\w*|crash\w*|spik\w*|jump\w*|tumbl\w*|rall\w*|moved?|rose|fell)\b", words, re.I))

    def test_a_quiet_journal_reads_as_none(self):
        (self.folder / "2026-11-05.md").write_text("# 2026-11-05\n\n## Session: daily run, 08:00\n\n### What we did\n\n- Quiet.\n")
        (self.folder / "2026-11-04.md").unlink()
        book = data.journal_alerts(self.folder)
        self.assertEqual(book["alerts"], [])
        self.assertIn("None on file", view.alerts_table(book["alerts"]))

    def test_the_real_journal_reads(self):
        book = data.journal_alerts()
        self.assertGreater(book["days_read"], 0)
        for row in book["alerts"]:
            self.assertIn(row["level"], view.ALERT_LEVELS)

    def test_the_guard_record_reads_and_escapes(self):
        path = self.folder / "blocked.jsonl"
        self.assertEqual(data.guard_events(self.folder / "none.jsonl"), [])
        path.write_text(json.dumps({"when": "2026-11-05T08:00:00+00:00", "rule": "W1", "how": "before the call", "tool": "Edit", "target": "<b>Rules/cash.md</b>"}) + "\n")
        rows = data.guard_events(path)
        self.assertIn("&lt;b&gt;", view.guard_table(rows))
        self.assertIn("1 calls stopped", plain(view.guard_summary(rows)))

    def test_it_writes_nothing(self):
        before = sorted((p.name, p.read_bytes()) for p in self.folder.iterdir())
        data.journal_alerts(self.folder)
        self.assertEqual(before, sorted((p.name, p.read_bytes()) for p in self.folder.iterdir()))


VOID_TAGS = ("br", "img", "hr", "input", "meta", "link")
A_YEAR = re.compile(r"\b(?:19|20)\d\d\b")
# On purpose not view.NOTE_FIGURE: a check that borrows the code it checks would agree with it.
MONEY_OR_SHARE = re.compile(r"\$\s?\d|\d\s?%|\b\d[\d,.]*\s?(?:M|B|million|billion|trillion)\b")


def parse(markup):
    """Markup as a tree of {tag, classes, kids}. A kid is a string or another node."""
    root = {"tag": "root", "classes": [], "kids": []}
    stack = [root]

    class Reader(HTMLParser):
        def handle_starttag(self, tag, attrs):
            node = {"tag": tag, "classes": (dict(attrs).get("class") or "").split(), "kids": []}
            stack[-1]["kids"].append(node)
            if tag not in VOID_TAGS:
                stack.append(node)

        def handle_endtag(self, tag):
            if tag not in VOID_TAGS and len(stack) > 1:
                stack.pop()

        def handle_data(self, text):
            stack[-1]["kids"].append(text)

    Reader().feed(markup)
    return root


def flat(node):
    return "".join(kid if isinstance(kid, str) else flat(kid) for kid in node["kids"])


def inside(node, test):
    """Every node under this one that passes the test."""
    found = []
    for kid in node["kids"]:
        if isinstance(kid, dict):
            if test(kid):
                found.append(kid)
            found += inside(kid, test)
    return found


def dated_source(node):
    """A d-src or a cited source under this node, with a year in its words. A bare class is not enough."""
    marks = inside(node, lambda n: "d-src" in n["classes"] or n["tag"] == "cite")
    return any(A_YEAR.search(flat(m)) for m in marks)


# Digits in fixed words that are names or dates, not figures: a dated day, a time, a rule ID, a form, a quarter, a fiscal year, a file path, a step of the plan, a count of what this screen itself shows.
NOT_A_FIGURE = re.compile(r"""
    \b(?:Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)[a-z]*\.?\ \d{1,2}(?:,\ \d{4})?(?:\ to\ \d{1,2})?
  | \b(?:Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)[a-z]*\.?\ \d{4}\b
  | \b\d{4}-\d{2}-\d{2}\b | \b\d{2}:\d{2}\ UTC\b | \b(?:19|20)\d\d\b
  | \b[A-Za-z]+\d[\dA-Za-z]*\b | \b(?:8|10)-[KQ]s?\b | \bStep\ \d\b | \bGate\ \d\b | \bSection\ \d+\b
  | \S*/\S*\.(?:md|json|py|toml|csv)\b
  | \bAnd\ \d+\ more\b | \bShowing\ \d+\ of\ \d+\ lines?\b | \b5%\ limit\b | \b\d+\ of\ 24\ months\b
""", re.X)


def figures_in_words(text):
    """What is left in fixed words once names and dates are out. Any digit left is a figure, and fixed words have no source of their own."""
    left = NOT_A_FIGURE.sub(" ", text)
    return bool(re.search(r"\d", left))


def bare_figures(markup, strict=True):
    """Figures with no source and date, on the words a reader sees. A year in the small print is what passes, not the markup around it.

    A digit is fine in a d-fig, a table row or a table caption that holds a dated source. d-text holds fixed words: names and dates pass, and any other digit there
    needs "calc." or a dated source on its own line, row or block. d-age is the limit's own words, which carry their own count. Words in d-copied, copied from a file, may hold a
    money or share figure only if a dated source, "calc." or the page's own "no dated source" tag sits on the same line or row. `strict` is kept for old callers: every screen now runs strict."""
    found = []

    def line_ok(scope):
        return bool(dated_source(scope) or "calc." in flat(scope) or inside(scope, lambda n: "d-nosrc" in n["classes"]) or "undated, retrieved" in flat(scope))

    def walk(node, covered, scope):
        names = node["classes"]
        if node["tag"] == "style":
            return
        if "d-age" in names:
            if not re.search(r"old, past my limit of \d+ days?\.|Unknown|Past my age limits", flat(node)):
                found.append(f"age words of the wrong form: {flat(node)[:120]}")
            return
        if "d-src" in names and node["tag"] == "small":
            if not A_YEAR.search(flat(node)):
                found.append(f"source with no date: {flat(node)[:120]}")
            return
        if "d-copied" in names:
            if MONEY_OR_SHARE.search(flat(node)) and not covered and not line_ok(scope):
                found.append(f"copied with no source: {' '.join(flat(node).split())[:120]}")
            return
        if "d-text" in names:
            if not covered and figures_in_words(flat(node)) and not ("calc." in flat(node) and A_YEAR.search(flat(node))) and not line_ok(scope):
                found.append(f"fixed words with a figure: {' '.join(flat(node).split())[:120]}")
            return
        if "d-fig" in names:
            if not inside(node, lambda n: "d-src" in n["classes"]) or not dated_source(node):
                found.append(f"no date: {' '.join(flat(node).split())[:120]}")
            covered = True
        elif node["tag"] == "table":
            captions = inside(node, lambda n: n["tag"] == "caption")
            if captions and not A_YEAR.search(flat(captions[0])):
                found.append(f"caption with no date: {flat(captions[0])[:120]}")
            covered = covered or bool(captions)
        elif node["tag"] == "tr":
            scope = node
            covered = covered or dated_source(node)
        elif "d-block" in names or "h-row" in names:
            scope = node
        for kid in node["kids"]:
            if isinstance(kid, str):
                if re.search(r"\d", kid) and not covered:
                    found.append(kid.strip())
            else:
                walk(kid, covered, scope)

    root = parse(markup)
    walk(root, False, root)
    return found


def bare_labels(page):
    """Titles, headings and folded-section labels are drawn outside the markup, with no small print of their own, so they may hold names and dates and no figure."""
    out = []
    for kind in ("title", "header", "subheader", "expander"):
        for item in page.get(kind):
            words = getattr(item, "label", None) or getattr(item, "value", "")
            if figures_in_words(str(words)):
                out.append(f"{kind}: {words}")
    return out


NOT_THERE = re.compile(r"\b(?:not on file|unknown|no record|not stated|no saved close|none on file|no run on file|no [\w' -]{0,40} on file)\b", re.I)


def missing_with_no_fill(markup):
    """A block, row or line that says something is missing must also say what would fill it. It looks at the smallest piece that holds the words."""
    found = []

    def own(node):
        """Words copied from a file say what the file says. The fill is the page's own job."""
        return " ".join(k if isinstance(k, str) else ("" if "d-copied" in k["classes"] or "d-runtext" in k["classes"] else own(k)) for k in node["kids"])

    def walk(node):
        if node["tag"] == "style" or "d-copied" in node["classes"] or "d-src" in node["classes"] and node["tag"] == "small":
            return
        if node["tag"] == "tr" or (node["tag"] in ("p", "li", "div") and "d-wrap" not in node["classes"] and not inside(node, lambda n: n["tag"] in ("table", "section", "p", "li") and n is not node)):
            text = " ".join(own(node).split())
            if NOT_THERE.search(text) and not re.search(r"would (?:fill|write|save|put)|needs? extending|Its first run", text):
                found.append(text[:160])
            return
        for kid in node["kids"]:
            if not isinstance(kid, str):
                walk(kid)

    walk(parse(markup))
    return found


def shape(markup):
    """The tags and classes alone. Hover text and link addresses hold the row's own words, so they are left out when comparing looks."""
    return re.sub(r' (title|href)="[^"]*"', "", tags_only(markup))


def home_copy(today=dt.date(2026, 11, 5)):
    """A throwaway folder set, with Home's readers pointed at it."""
    temp = tempfile.TemporaryDirectory()
    folder = Path(temp.name)
    for name in ("Journal", "Research", "runs", "values", "notes", "cache"):
        (folder / name).mkdir()
    return temp, folder, dict(today=today, journal=folder / "Journal", research=folder / "Research", radar_runs=folder / "runs", valuation_runs=folder / "values", notes=folder / "notes", cache=folder / "cache")


def alert(day, level, rule, text=None, routine="Daily run"):
    return {"day": day, "level": level, "rule": rule, "routine": routine, "text": text or f"[8-K, filed {day}](https://www.sec.gov/{rule}), {rule}: a fact."}


def ruled(day, rule, written="2026-11-05", words="My words.", routine=None):
    return {"line": f"Ruled: {day} {rule}. {words}", "written": written, "routine": routine, "day": day, "rule": rule, "words": words}


TODAY = dt.date(2026, 11, 5)


UNSOURCED_LINES = 31  # counted Nov. 4, 2026 (Journal/2026-11-04.md): Corning 27, Broadcom 3, NVIDIA 1

APPROVED_LIMITS = {"close": 4, "sec_copy": 4, "radar_run": 4, "run_daily": 4, "run_event": 4, "run_weekly": 10, "run_monthly": 35, "run_quarterly": 110, "portfolio_note": 30,
                   "catalyst_note": 45, "value_run": 110, "company_note": 110, "research_file": 110, "periodic_filing": 110, "tenk": 380, "fred_monthly": 50}


def screen_page(screen, company=None):
    from streamlit.testing.v1 import AppTest

    page = AppTest.from_file(str(HERE / "app.py"), default_timeout=90).run()
    page.switch_page(screen)
    if company:
        page.query_params["company"] = company
    page.run()
    assert not page.exception, (screen, company, list(page.exception))
    return page, "".join(h.proto.body for h in page.get("html"))


ALL_SCREENS = ("screens/home.py", "screens/company.py", "screens/portfolio.py", "screens/ideas.py", "screens/journal.py")


class AgeLimits(unittest.TestCase):
    """Mine, approved Nov. 4, 2026. Past a limit the board says so in words, and it stays no alert. A changed value here needs my approval."""

    def test_the_file_holds_what_i_approved(self):
        self.assertEqual({k: v["days"] for k, v in data.age_limits().items()}, APPROVED_LIMITS)

    def test_the_words_start_the_day_after_the_limit(self):
        day = dt.date(2026, 11, 1)
        self.assertEqual(data.past_limit("close", day, dt.date(2026, 11, 5)), "")
        self.assertEqual(data.past_limit("close", day, dt.date(2026, 11, 6)), "This close is 5 days old, past my limit of 4 days.")
        self.assertIn("Within my limit of 4 days", data.against_limit("close", day, dt.date(2026, 11, 5)))

    def test_a_limit_that_cannot_be_read_is_never_within(self):
        real, data.AGE_LIMITS = data.AGE_LIMITS, Path("/nonexistent/age_limits.toml")
        self.addCleanup(setattr, data, "AGE_LIMITS", real)
        words = data.past_limit("close", dt.date(2026, 11, 1), dt.date(2026, 11, 1))
        self.assertIn("Unknown", words)
        self.assertIn("would fill", words)

    def test_the_words_are_no_alert_and_no_view(self):
        for kind, limit in data.age_limits().items():
            words = data.past_limit(kind, dt.date(2020, 1, 1), dt.date(2026, 11, 4))
            self.assertIn(f'past my limit of {limit["days"]} days', words)
            self.assertIsNone(ALERT_WORDS.search(words), words)
            self.assertIsNone(VIEW_WORDS.search(words), words)

    def test_the_words_have_no_colour_of_their_own(self):
        rule = re.search(r"\.d-age,\.d-run\{([^}]*)\}", view.CSS)[1]
        self.assertNotRegex(rule, r"color|background|border")

    def test_every_source_names_its_limit_or_why_it_has_none(self):
        for r in data.source_rows():
            self.assertTrue(r["problem"] or r["kind"] or (r["no_limit"] or "").startswith("No limit:"), r["name"])

    def test_every_limit_is_used_by_a_source(self):
        kinds = {r["kind"] for r in data.source_rows()}
        kinds |= {data.ROUTINE_LIMITS[name] for name in data.ROUTINES}  # a routine with no record yet has a problem row, and its kind is still in use
        self.assertEqual(set(APPROVED_LIMITS) - kinds, set())

    def later(self, days):
        """The real app on the real files, with the clock moved and nothing written. The app has no switch for this. Only a test can do it."""
        real_now, real_today = data.now_utc, data.local_today
        self.addCleanup(setattr, data, "now_utc", real_now)
        self.addCleanup(setattr, data, "local_today", real_today)
        data.now_utc = lambda: real_now() + dt.timedelta(days=days)
        data.local_today = lambda: real_today() + dt.timedelta(days=days)

    def test_each_screen_says_it_in_words_when_the_clock_moves(self):
        self.later(120)
        expect = {("screens/home.py", None): ["Past my age limits", "This radar run is", "This portfolio note is"],
                  ("screens/company.py", "GLW"): ["This company note is", "This close is", "This value run is", "This thesis or kill-line file is", "The latest 10-Q or 10-K is", "This catalyst note is", "This monthly FRED figure is"],
                  ("screens/portfolio.py", None): ["This portfolio note is"],
                  ("screens/ideas.py", None): ["This radar run is", "The Daily run's last record is", "This copy from SEC is", "This close is"]}
        for (screen, company), lines in expect.items():
            page, markup = screen_page(screen, company)
            for line in lines:
                self.assertIn(line, html.unescape(plain(markup)), (screen, line))
            self.assertEqual(bare_figures(markup), [], screen)

    def test_home_keeps_a_close_and_its_age_words_together(self):
        """On fixed days, because the real close moves. A row and its words are never split by the row limit."""
        row = data.where_it_stands(data.latest_valuation())
        day = dt.date.fromisoformat(row["price"]["date"]) + dt.timedelta(days=9)
        text = plain(view._stand_row(row, day))
        self.assertIn("This close is 9 days old, past my limit of 4 days.", text)
        self.assertLess(text.index(f'${row["price"]["close"]:.2f}'), text.index("This close is"))


class FiguresOnEveryScreen(unittest.TestCase):
    """Every figure on every screen has a source and a date, and everything missing says what would fill it."""

    def test_every_screen(self):
        for screen in ALL_SCREENS:
            page, markup = screen_page(screen)
            self.assertEqual(bare_figures(markup), [], screen)
            self.assertEqual(bare_labels(page), [], screen)
            self.assertEqual(missing_with_no_fill(markup), [], screen)

    def test_every_company_page(self):
        for row in data.company_list():
            page, markup = screen_page("screens/company.py", row["ticker"] or row["name"])
            self.assertEqual(bare_labels(page), [], row["name"])
            self.assertEqual(missing_with_no_fill(markup), [], row["name"])

    def test_every_source_is_a_link_a_path_calc_or_a_named_fetch(self):
        shape_of_source = re.compile(r"calc\.|\.(?:md|json|csv|toml|jsonl|html|py)\b|/|Yahoo|FRED|SEC|filed", re.I)
        for screen in ALL_SCREENS:
            _, markup = screen_page(screen)
            for mark in inside(parse(markup), lambda n: "d-src" in n["classes"] and n["tag"] == "small"):
                if not inside(mark, lambda n: n["tag"] == "a"):
                    self.assertRegex(flat(mark), shape_of_source, (screen, flat(mark)))

    def test_lines_the_notes_leave_unsourced_are_counted_and_cannot_grow(self):
        """The test passes these only because the page says plainly that the note gives no dated source. Sourcing a line in the note brings the count down. Lower the number then."""
        tags, say = 0, set()
        for row in data.company_list():
            _, markup = screen_page("screens/company.py", row["ticker"] or row["name"])
            found = inside(parse(markup), lambda n: "d-nosrc" in n["classes"] and n["tag"] == "small")
            tags += len(found)
            say |= {flat(f) for f in found}
        self.assertLessEqual(tags, UNSOURCED_LINES)
        self.assertEqual(say, {view.NO_SOURCE})
        self.assertIn("would fill", view.NO_SOURCE)

    def test_broken_copies_fail(self):
        fill = view.missing("a thing.", "a file.")
        self.assertEqual(missing_with_no_fill(fill), [])
        self.assertTrue(missing_with_no_fill("<p>Not on file.</p>"))
        self.assertTrue(missing_with_no_fill("<table><tr><td>x</td><td>Unknown</td></tr></table>"))
        self.assertTrue(bare_figures('<p class="d-text">14 rows in the log.</p>'))
        self.assertEqual(bare_figures('<p class="d-text">Files read Nov. 4, 2026, 04:13 UTC. Rule O16 and FY2025 in Research/2026-11-03 A.md</p>'), [])
        self.assertTrue(bare_figures('<div class="d-age">This close is old.</div>'))
        page = type("P", (), {"get": lambda self, kind: [type("I", (), {"value": "Lead on the screen: 123"})()] if kind == "subheader" else []})()
        self.assertEqual(bare_labels(page), ["subheader: Lead on the screen: 123"])


class AFailedSensor(unittest.TestCase):
    """A run can die after its sensors and before its brief. On Nov. 4, 2026 the break on a test copy showed Home saying "Nothing waiting" then, and no screen naming the failure."""

    def digest(self, briefed, sensors=(("8-K watcher", False), ("Radar", True))):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        (Path(temp.name) / "2026-11-04-01.json").write_text(json.dumps({"today": "2026-11-04", "briefed": briefed, "sensors": [{"name": n, "ok": ok} for n, ok in sensors]}))
        return temp.name

    def test_a_clean_briefed_run_says_nothing(self):
        self.assertIsNone(data.run_trouble(self.digest(True, (("8-K watcher", True), ("Radar", True)))))
        self.assertEqual(view.run_trouble_lines(None), "")

    def test_no_digest_says_nothing_here(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(data.run_trouble(temp))

    def test_a_failure_names_the_sensor_what_it_feeds_the_file_and_what_clears_it(self):
        words = plain(view.run_trouble_lines(data.run_trouble(self.digest(True))))
        for part in ("The 8-K watcher failed in the Daily run of Nov. 4, 2026", "sensors/daily/runs/2026-11-04-01.json", "Latest 8-Ks", "would clear"):
            self.assertIn(part, words)
        self.assertNotIn("no brief", words)

    def test_a_run_that_died_says_it_left_no_brief(self):
        self.assertIn("left no brief", plain(view.run_trouble_lines(data.run_trouble(self.digest(False)))))
        self.assertIn("no brief yet", plain(view.run_trouble_lines(data.run_trouble(self.digest(False, (("Radar", True),))))))

    def test_a_digest_that_cannot_be_read_is_a_problem_not_silence(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "2026-11-04-01.json").write_text("{")
            self.assertTrue(data.run_trouble_or_problem(temp)[1])

    def test_it_has_no_colour_no_alert_word_and_no_bare_figure(self):
        markup = view.run_trouble_lines(data.run_trouble(self.digest(False)))
        self.assertNotRegex(re.search(r"\.d-age,\.d-run\{([^}]*)\}", view.CSS)[1], r"color|background|border")
        self.assertIsNone(ALERT_WORDS.search(plain(markup)), plain(markup))
        self.assertIsNone(VIEW_WORDS.search(plain(markup)), plain(markup))
        self.assertEqual(bare_figures(markup), [])

    def test_every_screen_says_it(self):
        real, data.DAILY_RUNS = data.DAILY_RUNS, Path(self.digest(False))
        self.addCleanup(setattr, data, "DAILY_RUNS", real)
        for screen in ALL_SCREENS:
            _, markup = screen_page(screen)
            self.assertIn("The 8-K watcher failed", plain(markup), screen)
            self.assertIn("left no brief", plain(markup), screen)
        _, corning = screen_page("screens/company.py", "GLW")
        self.assertGreaterEqual(plain(corning).count("The 8-K watcher failed"), 2)  # also where its figures are



class PortfolioScreen(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        (self.folder / "notes").mkdir()
        (self.folder / "cache").mkdir()

    def note(self, name, kind, cash, rows, since=None):
        table = "\n".join(f"| {t} | {s} | Nov. 1, 2026 | $10.00 | Note |" for t, s in rows)
        line = f'cash above 50% since: "{since}"\n' if since else ""
        (self.folder / "notes" / name).write_text(f'---\nkind: {kind}\ncash: {cash}\nas of: "2026-11-01"\n{line}last checked: "2026-11-01"\n---\n\n## Positions\n\n| Ticker | Shares | Bought on | Cost a share | Thesis note |\n|---|---|---|---|---|\n{table}\n\n## Changes\n\n| Date | Change | Cash after | My yes |\n|---|---|---|---|\n| Nov. 1, 2026 | Bought | $1,000 | Yes |\n')

    def book(self, name="A.md"):
        return data.read_book(self.folder / "notes" / name, self.folder / "cache", dt.date(2026, 11, 3))

    def test_shares_at_the_saved_close_not_at_cost(self):
        write_prices(self.folder / "cache", close="100.00")
        self.note("A.md", "paper", 1000, [("GLW", "90")])
        book = self.book()
        p = book["positions"][0]
        self.assertEqual((p["value"], book["total"]), (9000, 10000))
        self.assertAlmostEqual(p["share"], .9)
        self.assertAlmostEqual(book["share"], .1)
        self.assertEqual(book["level"], "Normal")
        text = plain(view.book_block(book))
        self.assertIn("$9,000", text)
        self.assertIn("90.0%", text)
        self.assertEqual(bare_figures(view.book_block(book)), [])

    def test_no_close_is_unknown_all_the_way_with_no_cost_fallback(self):
        write_prices(self.folder / "cache", close="100.00")
        self.note("A.md", "paper", 1000, [("GLW", "90"), ("NONE", "5")])
        book = self.book()
        self.assertEqual((book["total"], book["share"], book["level"]), (None, None, None))
        self.assertEqual([p["share"] for p in book["positions"]], [None, None])
        markup = view.book_block(book)
        text = plain(markup)
        self.assertIn("Not on file: the close for NONE.", text)
        self.assertIn("would fill", text)
        self.assertIn("Nothing falls back to cost", text)
        self.assertNotIn("$1,050", text)  # cash plus five shares at the $10 cost
        self.assertEqual(missing_with_no_fill(markup), [])
        self.assertEqual(bare_figures(markup), [])

    def test_home_and_this_screen_read_the_same_book(self):
        write_prices(self.folder / "cache", close="100.00")
        self.note("A.md", "paper", 1000, [("GLW", "90")])
        books = data.position_notes(self.folder / "notes", self.folder / "cache")
        self.assertAlmostEqual(books["paper"][0]["share"], self.book()["share"])

    def test_months_above_half_are_shown_and_a_note_that_disagrees_says_so(self):
        self.note("A.md", "paper", 1000, [], since="2024-11-03")
        self.assertIn("24 of 24 months", plain(view.book_summary(self.book())))
        write_prices(self.folder / "cache", close="100.00")
        self.note("B.md", "paper", 100, [("GLW", "90")], since="2024-11-03")
        self.assertIn("not above 50%", plain(view.book_summary(self.book("B.md"))))

    def test_a_broken_row_or_a_note_marked_neither_is_a_problem_and_not_a_figure(self):
        self.note("A.md", "both", 1000, [])
        (self.folder / "notes" / "B.md").write_text('---\nkind: paper\ncash: 5\nlast checked: "2026-11-01"\n---\n\n## Positions\n\n| T | S |\n|---|---|\n| GLW | 90 |\n')
        books = data.position_notes(self.folder / "notes", self.folder / "cache")
        self.assertEqual((books["real"], books["paper"], len(books["problems"])), ([], [], 2))

    def test_the_real_screen_real_first_paper_labelled_nothing_at_cost(self):
        page, markup = screen_page("screens/portfolio.py")
        text = plain(markup)
        self.assertEqual([h.value for h in page.header][:2], ["Real", "Paper, made-up money"])
        self.assertLess(text.index(view.REAL_MISSING[0]), text.index(view.PAPER_LABEL))
        self.assertIn("Room under the 5% limit", text)
        self.assertNotIn("at cost", text)
        self.assertIsNone(VIEW_WORDS.search(plain(own_words(markup))))

    def test_an_age_past_the_limit_is_said_for_a_close_and_the_note(self):
        write_prices(self.folder / "cache", close="100.00")
        self.note("A.md", "paper", 1000, [("GLW", "90")])
        book = self.book()
        words = plain(view.book_block(book, None, dt.date(2030, 1, 1)))
        self.assertIn("This close is", words)
        self.assertIn("This portfolio note is", words)



class ThePublishedBriefIsRead(unittest.TestCase):
    """The reader once missed every line of a real busy brief, because publish.py heads it "## Daily brief" and the test's made-up brief had no heading."""

    def setUp(self):
        sys.path[:0] = [str(ROOT / "sensors" / "daily"), str(ROOT / "sensors" / "phone")]
        import publish

        self.publish = publish
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.real_journal, publish.JOURNAL = publish.JOURNAL, self.folder
        self.addCleanup(setattr, publish, "JOURNAL", self.real_journal)

    def write(self, text, day="2026-11-05", time="08:01"):
        block = f"## Daily brief, Nov. 5, 2026, {time}\n\n{text.strip()}"
        digest = {"sensors": [], "run_local": f"{day}T{time}", "stem": day, "not_read": "Not read."}
        self.publish.add_to_journal(block, self.publish.session_record(digest, False), day)

    def test_a_red_in_a_real_brief_reaches_home(self):
        self.write("**Since the brief of Nov. 4, 2026:** 1 new.\n\n### Red\n\n- [8-K, filed Nov. 5, 2026](https://www.sec.gov/x), R3: item 1.03.\n\n### Orange\n\n- Nothing.\n\n### Info\n\n- [Form 4, Nov. 5, 2026](https://www.sec.gov/y), I4: one form.")
        book = data.journal_alerts(self.folder)
        self.assertEqual([(a["level"], a["rule"], a["routine"]) for a in book["alerts"]], [("Red", "R3", "Daily run"), ("Info", "I4", "Daily run")])
        self.assertEqual(data.waiting_list(book, TODAY)["rows"][0]["rule"], "R3")
        self.assertEqual(data.last_brief(self.folder)["info"], ["[Form 4, Nov. 5, 2026](https://www.sec.gov/y), I4: one form."])

    def test_the_second_brief_of_a_day_is_the_last_brief(self):
        self.write("**Since the brief of Nov. 4, 2026:** first.\n\n### Red\n\n- Nothing.\n\n### Orange\n\n- Nothing.\n\n### Info\n\n- Nothing.")
        self.write("**Since the brief of Nov. 5, 2026:** second.\n\n### Red\n\n- Nothing.\n\n### Orange\n\n- Nothing.\n\n### Info\n\n- Nothing.", time="17:00")
        self.assertIn("second", data.last_brief(self.folder)["since"])

    def test_the_real_quiet_brief_reads(self):
        (self.folder / "2026-11-03.md").write_text("# 2026-11-03\n\n**Daily brief, Nov. 3, 2026: nothing needs me.** Since the last radar run: no new filing.\n\n## Session: daily run, 23:25\n\n- Ran.\n")
        self.assertEqual(data.last_brief(self.folder)["since"], "Since the last radar run: no new filing.")

    def test_a_session_quoting_a_brief_is_no_brief(self):
        (self.folder / "2026-11-05.md").write_text("# 2026-11-05\n\n## Session: talk\n\n**Since the brief of Nov. 4, 2026:** quoted.\n\n### Info\n\n- quoted.\n")
        self.assertIsNone(data.last_brief(self.folder))


class RuledLines(unittest.TestCase):
    """A Ruled: line decides what still waits. What cannot be matched is shown, never dropped."""

    def book(self, alerts, rulings):
        return {"alerts": alerts, "rulings": rulings, "last_run": {}}

    def test_written_as_the_rule_says_it_is_read_and_is_no_alert(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "2026-11-05.md").write_text(BRIEF.replace("## Session: first talk", "## Session: my ruling\n\n### What we decided\n\n- Ruled: 2026-11-05 R3. I read it, and the claim holds.\n\n## Session: first talk"))
            book = data.journal_alerts(temp)
        self.assertEqual([(r["day"], r["rule"], r["words"], r["routine"]) for r in book["rulings"]], [("2026-11-05", "R3", "I read it, and the claim holds.", None)])
        self.assertFalse([a for a in book["alerts"] if "Ruled" in a["text"]])
        out = data.waiting_list(book, TODAY)
        self.assertEqual(out["closed"][0]["ruled"], "I read it, and the claim holds.")
        self.assertNotIn(("Red", "R3"), [(r["level"], r["rule"]) for r in out["rows"]])
        self.assertEqual(out["problems"], [])

    def test_a_line_under_a_level_in_a_routine_is_no_alert_and_closes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "2026-11-05.md").write_text("# 2026-11-05\n\n## Session: event run\n\n**Red**\n\n- [8-K, Nov. 5, 2026](https://www.sec.gov/x), R1: a fact.\n- Ruled: 2026-11-05 R1. A routine wrote this.\n")
            out = data.waiting_list(data.journal_alerts(temp), TODAY)
        self.assertEqual([r["rule"] for r in out["rows"]], ["R1"])
        self.assertIn("a routine does not rule", out["problems"][0])

    def test_a_second_alert_needs_its_own_line(self):
        alerts = [alert("2026-11-05", "Orange", "O2", "first, O2."), alert("2026-11-05", "Orange", "O2", "second, O2.")]
        one = data.waiting_list(self.book(alerts, [ruled("2026-11-05", "O2")]), TODAY)
        self.assertEqual([r["text"] for r in one["rows"]], ["second, O2."])
        self.assertIn("each needs its own line", one["problems"][0])
        two = data.waiting_list(self.book(alerts, [ruled("2026-11-05", "O2"), ruled("2026-11-05", "O2")]), TODAY)
        self.assertEqual((two["rows"], two["problems"]), ([], []))

    def test_what_cannot_match_is_a_problem(self):
        a = alert("2026-11-04", "Red", "R1")
        for ruling, words in ((ruled("2026-11-04", "R2"), "matches no alert"), (ruled("2026-11-03", "R1"), "matches no alert"),
                              (ruled("2026-11-04", "R1", written="2026-11-03"), "dated before"), (ruled("2026-11-04", "R1", routine="Daily run"), "a routine does not rule"),
                              ({"line": "Ruled: tomorrow R1.", "written": "2026-11-05", "routine": None, "day": None, "rule": None, "words": None}, "cannot be read"),
                              (ruled("2026-13-40", "R1"), "cannot be read")):
            out = data.waiting_list(self.book([a], [ruling]), TODAY)
            self.assertEqual([r["rule"] for r in out["rows"]], ["R1"], words)
            self.assertIn(words, out["problems"][0])

    def test_a_ruling_on_an_info_line_closes_nothing(self):
        out = data.waiting_list(self.book([alert("2026-11-04", "Info", "I3")], [ruled("2026-11-04", "I3")]), TODAY)
        self.assertEqual(out["rows"], [])
        self.assertIn("matches no alert", out["problems"][0])

    def test_an_alert_with_no_rule_stays_and_says_why(self):
        out = data.waiting_list(self.book([alert("2026-11-04", "Red", "", "A line with no rule.")], []), TODAY)
        self.assertEqual(len(out["rows"]), 1)
        self.assertIn("no rule ID", out["problems"][0])
        self.assertIn("no rule", plain(view._home_waiting({"waiting": out})))

    def test_reds_first_then_oldest_with_the_alerts_own_age(self):
        out = data.waiting_list(self.book([alert("2026-11-05", "Red", "R3"), alert("2026-11-01", "Orange", "O2"), alert("2026-11-03", "Red", "R1"), alert("2026-11-04", "Info", "I3")], []), TODAY)
        self.assertEqual([(r["rule"], r["days"]) for r in out["rows"]], [("R1", 2), ("R3", 0), ("O2", 4)])

    def test_the_address_of_a_link_is_no_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "2026-11-05.md").write_text("# 2026-11-05\n\n### Orange\n\n- [8-K, Nov. 5, 2026](https://www.sec.gov/R9/x), read: a fact (O2).\n")
            self.assertEqual(data.journal_alerts(temp)["alerts"][0]["rule"], "O2")


def home_model(**over):
    model = {"today": TODAY, "book": {"alerts": [], "rulings": [], "last_run": {"Daily run": "2026-11-05"}}, "book_problem": None, "waiting": {"rows": [], "closed": [], "problems": []},
             "brief": {"day": "2026-11-05", "file": "Journal/2026-11-05.md", "quiet": True, "since": "Since the last radar run: no new filing.", "info": []}, "brief_problem": None,
             "coming": [], "coming_problems": [], "radar_date": "2026-11-03", "books": {"real": [], "paper": [], "problems": []}, "books_problem": None, "stands": [], "stands_problems": []}
    return {**model, **over}


def waiting_of(alerts, rulings=()):
    return data.waiting_list({"alerts": alerts, "rulings": list(rulings)}, TODAY)


def stand_row(close, name="Corning"):
    price = {"close": close, "date": "2026-11-03", "fetched": dt.datetime(2026, 11, 3, tzinfo=UTC), "file": "f.csv", "source": "Yahoo test"}
    return {"company": name, "ticker": "GLW", "price": price, "buy_below": 28.97, "trim_above": 36.06, "run_file": "sensors/valuation/runs/x.json", "worked_out": "2026-11-03"}


def coming_row(n):
    return {"sort": TODAY + dt.timedelta(days=n), "rank": 1, "when": f"Dec. {n + 1}, 2026", "kind": "stated", "title": f"Thing {n}", "source": {"label": "Filing, Nov. 1, 2026", "url": "https://www.sec.gov/x"}, "file": "Catalysts/x.md", "written": "2026-11-03"}


NOW = dt.datetime(2026, 11, 5, 8, tzinfo=UTC)


class HomeScreen(unittest.TestCase):
    """Does anything need me today? One screen: row limits with their counts, and no figure without a source and date."""

    def test_a_red_is_never_dropped_silently(self):
        rows = [alert(f"2026-10-{d:02d}", "Red", "R1") for d in range(1, 21)] + [alert("2026-11-01", "Orange", "O2")]
        markup = view.home(home_model(waiting=waiting_of(rows)), NOW)
        self.assertIn("Waiting for me: 20 Red, 1 Orange.", plain(markup))
        self.assertIn(f"And 16 more: 15 Red, 1 Orange", plain(markup))
        self.assertEqual(markup.count('class="h-row h-red"'), view.WAITING_ROWS)

    def test_every_hidden_row_is_counted(self):
        for count in (0, 1, view.COMING_ROWS, view.COMING_ROWS + 1, 40):
            markup = view._home_coming(home_model(coming=[coming_row(n) for n in range(count)]))
            self.assertEqual(markup.count('class="h-row"'), min(count, view.COMING_ROWS))
            hidden = count - view.COMING_ROWS
            self.assertEqual(f"And {hidden} more" in plain(markup), hidden > 0)
        brief = {"day": "2026-11-05", "file": "Journal/2026-11-05.md", "quiet": False, "since": "Since now: x.", "info": [f"[Form, Nov. 1, 2026](https://www.sec.gov/{n}), I4: {n}." for n in range(9)]}
        self.assertIn("And 6 more", plain(view._home_since(home_model(brief=brief))))
        stands = [stand_row(10.0, f"C{n}") for n in range(9)]
        self.assertIn("And 7 more", plain(view._home_stands(home_model(stands=stands))))  # 3 fixed rows and 9 companies, 5 shown

    def test_coming_up_sits_above_where_things_stand_on_any_width(self):
        blocks = re.findall(r'data-block="([^"]+)"', view.home(home_model(), NOW))
        self.assertEqual(blocks, ["Waiting for me", "Coming up", "Since the last brief", "Where things stand", "Routines"])

    def test_nothing_waiting_says_so(self):
        text = plain(view.home(home_model(), NOW))
        self.assertIn("Nothing waiting.", text)
        self.assertIn("Newest daily record: Nov. 5, 2026.", text)
        self.assertIn("A run that did not happen leaves no line.", text)

    def test_an_unreadable_journal_is_unknown_not_nothing_waiting(self):
        text = plain(view.home(home_model(book=None, waiting=None, book_problem="OSError: gone", brief=None, brief_problem="OSError: gone"), NOW))
        self.assertIn("Unknown", text)
        self.assertNotIn("Nothing waiting", text)

    def test_problems_take_one_line_a_block_with_a_count(self):
        many = [f"Problem {n}" for n in range(30)]
        markup = view.home(home_model(coming_problems=many, stands_problems=many, waiting={"rows": [], "closed": [], "problems": many}, books={"real": [], "paper": [], "problems": many}), NOW)
        self.assertEqual(markup.count('class="h-bad'), 3)
        self.assertIn("And 29 more.", plain(markup))

    def test_every_row_stays_on_one_line_at_laptop_width(self):
        for css in (".h-row,.h-note,.h-ask,.h-more{white-space:nowrap", ".h-since{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3"):
            self.assertIn(css, view.HOME_CSS)
        self.assertNotIn("expander", (HERE / "screens/home.py").read_text())

    def test_a_close_either_side_of_the_lines_looks_the_same(self):
        shapes = {shape(view._stand_row(stand_row(close))) for close in (1.0, 30.0, 123.2, 99999.0)}
        self.assertEqual(len(shapes), 1)
        text = plain(view._stand_row(stand_row(1.0)))
        self.assertIsNone(re.search(r"\b(under|above|below|between|cheap|near)\b", text.replace("buy-below", "").replace("trim-above", ""), re.I), text)

    def test_a_closer_date_looks_the_same(self):
        self.assertEqual(shape(view._coming_figure(coming_row(0))), shape(view._coming_figure(coming_row(80))))

    def test_old_alerts_look_the_same_as_new_ones(self):
        one = view._home_waiting({"waiting": waiting_of([alert("2026-11-05", "Orange", "O2")])})
        old = view._home_waiting({"waiting": waiting_of([alert("2020-11-05", "Orange", "O2")])})
        self.assertEqual(shape(one), shape(old))

    def test_the_words_give_no_view_and_no_alarm(self):
        model = home_model(waiting=waiting_of([alert("2026-11-04", "Red", "R1", "x, R1."), alert("2026-11-04", "Orange", "O2", "x, O2.")]), coming=[coming_row(1)], stands=[stand_row(1.0)])
        text = LINE_NAMES.sub("", plain(view.home(model, NOW)))
        self.assertIsNone(VIEW_WORDS.search(text), VIEW_WORDS.search(text))
        self.assertIsNone(ALERT_WORDS.search(text.replace("Ideas and alerts", "")), ALERT_WORDS.search(text))

    def test_copied_text_cannot_make_the_browser_fetch(self):
        bad = "[bad](javascript:alert(1)) <img src=x onerror=y> ![i](https://evil.example/a.png), R1."
        model = home_model(waiting=waiting_of([alert("2026-11-04", "Red", "R1", bad)]), brief={"day": "2026-11-05", "file": "Journal/x.md", "quiet": False, "since": bad, "info": [bad]},
                           coming=[{**coming_row(1), "title": bad}])
        markup = view.home(model, NOW)
        self.assertNotIn("<img", markup)
        self.assertNotRegex(tags_only(markup), r'(href|src)="javascript')  # a hover text may show the words, escaped. It is no link.
        self.assertNotIn(' src="', tags_only(markup))

    def test_a_screen_link_stays_on_this_board(self):
        self.assertEqual(view.screen_link("ideas", "And 2 more"), '<a href="/ideas" target="_self">And 2 more</a>')
        self.assertIn('href="/ideas"', view._home_waiting({"waiting": waiting_of([alert("2026-11-04", "Orange", "O2")] * 9)}))


class FigureRule(unittest.TestCase):
    def test_fig_refuses_a_figure_with_no_source_or_date(self):
        for source, date in ((None, "Nov. 3, 2026"), ("", "Nov. 3, 2026"), ("Portfolio/x.md", None), ("Portfolio/x.md", ""), ((None, "https://www.sec.gov/x"), "Nov. 3, 2026")):
            with self.assertRaises(ValueError):
                view.fig("$1.00", source, date)

    def test_fig_shows_both_and_keeps_the_date_when_the_source_is_cut(self):
        text = plain(view.fig("$1.00", "Portfolio/x.md", "Nov. 3, 2026"))
        self.assertEqual(text, "$1.00 Nov. 3, 2026, Portfolio/x.md")
        self.assertEqual(plain(view.fig("$1.00", ("Release, Nov. 3, 2026", "https://www.sec.gov/x"), "Nov. 3, 2026")), "$1.00 Release, Nov. 3, 2026")
        self.assertIn('href="https://www.sec.gov/x"', view.fig("$1.00", ("Release, Nov. 3, 2026", "https://www.sec.gov/x"), "Nov. 3, 2026"))
        self.assertNotIn("href", view.fig("$1.00", ("Release, Nov. 3, 2026", "javascript:alert(1)"), "Nov. 3, 2026"))

    def test_the_real_home_has_no_bare_figure(self):
        self.assertEqual(bare_figures(view.home(data.home_view(), NOW)), [])

    def test_a_busy_home_has_no_bare_figure(self):
        note = {"cash": 9000.0, "positions": [{"ticker": "A", "shares": 1.0}], "last_checked": "2026-11-05", "file": "Portfolio/P.md", "share": .5, "level": "Normal", "missing": [], "newest_close": "2026-11-03"}
        markup = view.home(home_model(waiting=waiting_of([alert("2026-11-04", "Red", "R1"), alert("2026-11-01", "Orange", "O2", "no source, O2.")]), coming=[coming_row(1)], stands=[stand_row(1.0)],
                                      books={"real": [note], "paper": [note], "problems": []}), NOW)
        self.assertEqual(bare_figures(markup), [])

    def test_a_broken_copy_fails_the_check(self):
        """The check must catch what it exists to catch."""
        good = view.home(home_model(stands=[stand_row(126.14)]), NOW)
        self.assertEqual(bare_figures(good), [])
        self.assertEqual(bare_figures(good.replace('<div class="h-grid">', '<div class="h-grid"><div class="h-row">$123.20</div>')), ["$123.20"])
        self.assertTrue(bare_figures('<span class="d-fig"><b class="d-val">$1.00</b><small class="d-src">a file with no date</small></span>'))

def company_screen(address):
    """The real Company screen on the real files, at one address."""
    from streamlit.testing.v1 import AppTest

    page = AppTest.from_file(str(HERE / "app.py"), default_timeout=60).run()
    page.switch_page("screens/company.py")
    page.query_params["company"] = address
    page.run()
    assert not page.exception, (address, list(page.exception))
    return page


def body_of(page):
    return [h.proto.body for h in page.get("html")]


def source_words(text):
    """A file's words as the page shows them: link targets, backticks, stars and comment marks gone."""
    text = re.sub(r"%%.*?%%", " ", text, flags=re.S)
    text = re.sub(r"!?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m[2] or m[1], text)
    text = re.sub(r"!?\[([^\]]+)\]\([^)\s]*\)", r"\1", text)
    text = re.sub(r"!?\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    return " ".join(text.replace("`", "").replace("*", "").split())


class CompanyPageFigures(unittest.TestCase):
    """A figure with no source fails, on all 24 notes through the real app, and on broken copies."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {data.company_slug(r): company_screen(data.company_slug(r)) for r in data.company_list()}

    def test_there_is_a_page_for_every_note(self):
        notes = {p.stem for p in (ROOT / "Companies").glob("*.md")} - {"README"}
        self.assertEqual(len(notes), 24)
        self.assertEqual({r["name"] for r in data.company_list()}, notes)
        for row in data.company_list():
            self.assertIn(row["name"], plain(" ".join(body_of(self.pages[data.company_slug(row)]))))

    def test_no_page_has_a_bare_figure(self):
        for slug, page in self.pages.items():
            self.assertEqual([b for h in body_of(page) for b in bare_figures(h, strict=True)], [], slug)

    def test_no_heading_or_fold_holds_a_figure(self):
        """A heading has nowhere to carry a source."""
        for slug, page in self.pages.items():
            words = [t.value for t in page.title] + [h.value for h in page.header] + [h.value for h in page.subheader] + [x.label for x in page.expander]
            self.assertEqual([w for w in words if MONEY_OR_SHARE.search(w)], [], slug)

    def test_every_chart_comes_with_a_dated_source(self):
        page = self.pages["GLW"]
        heads = [h for h in body_of(page) if 'class="d-fig d-chart-head"' in h]
        charts = page.get("vega_lite_chart")
        self.assertGreater(len(charts), 8)
        self.assertEqual(len(heads), len(charts))
        for head in heads:
            self.assertTrue(dated_source(parse(head)), head[:160])

    def test_no_table_widget_can_slip_past_the_check(self):
        for slug, page in self.pages.items():
            self.assertEqual(len(page.dataframe), 0, slug)
            self.assertEqual(len(page.markdown), 0, slug)
            self.assertEqual(len(page.metric), 0, slug)

    def test_broken_copies_fail(self):
        """Take the source off each kind of figure on Corning's real page. Each must fail, or the check is worth nothing."""
        model = data.company_view(data.find_company("GLW", data.company_list()), NOW.date())
        pages = view.company_pages(data.company_list())
        run = model["value"]["run"]
        self.assertEqual(bare_figures(view.value_layers(run), strict=True), [])
        no_caption = re.sub(r'<caption class="d-src">.*?</caption>', "", view.value_layers(run))
        self.assertIn("$14.06", " ".join(bare_figures(no_caption)))
        undated = re.sub(r'(<caption class="d-src">).*?(</caption>)', r"\1a file\2", view.value_layers(run))
        self.assertTrue(any(f.startswith("caption with no date") for f in bare_figures(undated)))
        self.assertEqual(bare_figures(view.value_table(run), strict=True), [])
        self.assertTrue(bare_figures(re.sub(r'<td class="d-muted d-src">.*?</td>', "<td></td>", view.value_table(run))))
        self.assertEqual(bare_figures(view.price_zones(run, model["close"]), strict=True), [])
        self.assertTrue(bare_figures(re.sub(r'<small class="d-src".*?</small>', "", view.price_zones(run, model["close"]))))
        self.assertEqual(bare_figures(view.catalysts_table(model), strict=True), [])
        self.assertEqual(bare_figures(view.links_table(model, pages), strict=True), [])
        unsourced = dict(model["links"]["rows"][0], source="A release", size="More than $3B")
        broken = view.links_table({**model, "links": {"rows": [unsourced], "only_there": [], "problems": []}}, pages)
        self.assertEqual(bare_figures(broken, strict=True), [])  # the page says so itself
        self.assertIn(view.NO_SOURCE, plain(broken))
        self.assertTrue(bare_figures(broken.replace(view.NO_SOURCE, "").replace('class="d-nosrc"', ""), strict=True))
        self.assertTrue(bare_figures('<p class="d-text">Base value is $21.73.</p>'))  # every screen now runs the Company page's rule
        self.assertEqual(bare_figures('<p class="d-text">Read Nov. 3, 2026.</p>', strict=True), [])
        self.assertTrue(bare_figures('<table class="d-table"><tr><td>$1.00</td><td class="d-src">a file</td></tr></table>'))
        self.assertEqual(bare_figures('<table class="d-table"><tr><td>$1.00</td><td class="d-src">a file, Nov. 3, 2026</td></tr></table>'), [])

    def test_a_copied_line_with_a_figure_and_no_source_says_so(self):
        for line, flagged in (("- Sales were $5M.", True), ("- Sales were $5M ([10-K, filed Feb. 12, 2026][k]).", False), ("- A share of 10% (calc.).", False),
                              ("- Sales were $5M (`value-tests.html`, Nov. 3, 2026).", False), ("- Filed in 2026, with no amount.", False), ("- Sales were $5M ([a page](https://www.sec.gov/x)).", True)):
            markup = view.note_words(line, {"k": "https://www.sec.gov/k"})
            self.assertEqual(view.NO_SOURCE in plain(markup), flagged, line)
            self.assertEqual(bare_figures(markup, strict=True), [], line)

    def test_what_the_page_calls_copied_really_is_in_the_vault(self):
        """So a sentence of the page's own cannot hide from the word tests or the figure test by being marked copied."""
        vault = source_words(" ".join(p.read_text() for folder in ("Companies", "Research", "Catalysts") for p in (ROOT / folder).glob("*.md")))
        for slug, page in self.pages.items():
            for piece in body_of(page):
                for node in inside(parse(piece), lambda n: "d-copied" in n["classes"]):
                    words = source_words(html.unescape(" ".join(flat(node).split())))
                    if words:
                        self.assertIn(words, vault, slug)

    def test_the_word_rules_hold_on_every_page(self):
        for slug, page in self.pages.items():
            text = plain(" ".join(own_words(h) for h in body_of(page)))
            for line in NO_VIEW_LINES:
                text = text.replace(line, "")
            text = LINE_NAMES.sub("", text.replace(view.ZONE_LINE, "").replace("Rules/when-to-buy.md", ""))  # the rule's file name, not a view
            for note in data.read_inbox():  # a filing's reason says "may sell up to $2B", as on Ideas and alerts
                text = text.replace(" ".join(note["reason"].split()), "")
            run = data.company_run(data.find_company(slug, data.company_list())["name"], data.find_company(slug, data.company_list())["ticker"])["run"]
            for words in sorted(valuation_data_text(run), key=len, reverse=True):
                text = text.replace(" ".join(words.split()), "")
            self.assertIsNone(VIEW_WORDS.search(text), (slug, VIEW_WORDS.search(text)))
            self.assertIsNone(ALERT_WORDS.search(text), (slug, ALERT_WORDS.search(text)))


class CompanyAddress(unittest.TestCase):
    def setUp(self):
        self.rows = data.company_list()

    def test_every_address_is_unique_and_finds_its_own_note(self):
        slugs = [data.company_slug(r).lower() for r in self.rows]
        self.assertEqual(len(slugs), len(set(slugs)))
        for row in self.rows:
            self.assertEqual(data.find_company(data.company_slug(row), self.rows)["name"], row["name"])
            self.assertEqual(data.find_company(row["name"].lower(), self.rows)["name"], row["name"])

    def test_an_address_with_an_odd_character_is_escaped(self):
        self.assertEqual(view.company_href({"ticker": "", "name": "AT&T"}), "/company?company=AT%26T")
        self.assertEqual(view.company_href({"ticker": "", "name": "Furukawa Electric"}), "/company?company=Furukawa%20Electric")
        self.assertEqual(view.company_href({"ticker": "GLW", "name": "Corning"}), "/company?company=GLW")

    def test_an_address_cannot_reach_a_file_outside_the_list(self):
        for wanted in ("../Rules/my-rules", "../../etc/passwd", "README", "NOPE", "", None, "   "):
            self.assertIsNone(data.find_company(wanted, self.rows))

    def test_an_unknown_address_shows_no_company_and_no_figure(self):
        text = plain(" ".join(body_of(company_screen("NOPE"))))
        self.assertIn("No note in Companies/ has the name or ticker NOPE", text)
        self.assertNotIn("Thesis status", text)
        self.assertNotIn("$14.06", text)

    def test_with_no_address_the_list_shows_and_no_company_is_assumed(self):
        from streamlit.testing.v1 import AppTest

        page = AppTest.from_file(str(HERE / "app.py"), default_timeout=60).run()
        page.switch_page("screens/company.py")
        page.run()
        markup = " ".join(body_of(page))
        self.assertIn('href="/company?company=GLW"', markup)
        self.assertIn('href="/company?company=T"', markup)
        self.assertNotIn("Thesis status", [h.value for h in page.header])
        self.assertEqual([b for h in body_of(page) for b in bare_figures(h, strict=True)], [])

    def test_a_ticker_and_a_name_reach_the_same_page(self):
        self.assertEqual(plain(" ".join(body_of(company_screen("t")))), plain(" ".join(body_of(company_screen("AT&T")))))


class CompanyPageCorning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = data.find_company("GLW", data.company_list())
        cls.model = data.company_view(cls.row, NOW.date())
        cls.page = company_screen("GLW")
        cls.text = plain(" ".join(body_of(cls.page)))

    def test_the_draft_label_is_on_the_page_above_the_drafts(self):
        self.assertIn(view.DRAFT_LABEL, self.text)
        self.assertLess(self.text.index(view.DRAFT_LABEL), self.text.index("Drafts on file"))
        self.assertLess(self.text.rindex(view.DRAFT_LABEL), self.text.index("Kill lines"))
        for words in ("draft, not approved", "draft, not merged", "Not written yet."):
            self.assertIn(words, self.text)

    def test_a_thesis_recorded_in_the_note_does_not_sit_under_the_label(self):
        recorded = {**self.model, "thesis_section": "A real thesis, recorded by me."}
        text = plain(view.thesis_block(recorded, {}))
        self.assertLess(text.index("A real thesis"), text.index(view.DRAFT_LABEL))

    def test_the_label_cannot_be_turned_off(self):
        for fn in (view.thesis_block, view.kill_block):
            self.assertIn(view.DRAFT_LABEL, plain(fn(self.model, {})))
            self.assertEqual(fn.__code__.co_argcount, 2)
        approved = {**self.model, "thesis": {**self.model["thesis"], "drafts": [{**d, "status": "approved"} for d in self.model["thesis"]["drafts"]]}}
        self.assertIn(view.DRAFT_LABEL, plain(view.thesis_block(approved, {})))

    def test_the_thesis_section_is_word_for_word(self):
        section = data._section(data.split_note((ROOT / "Companies/Corning.md").read_text()), "Thesis")
        self.assertIn(source_words(section), self.text)

    def test_claims_and_nine_lines_as_written(self):
        t = self.model["thesis"]
        self.assertEqual([r[0] for r in t["claims"]["rows"]], [f"C{i}" for i in range(1, 9)])
        self.assertEqual([r[0] for r in t["lines"]["rows"]], [f"**K{i}**" for i in range(1, 10)])
        self.assertEqual(len(t["calendar"][0]["rows"]), 9)
        for words in ("Fiber stays short through 2028.", "At or below $2,379M.", "Column dates are my estimates.", "Q4 2026 (Jan. 2027)", "C4's figures are targets"):
            self.assertIn(words, self.text)

    def test_two_layers_stay_apart_and_each_figure_shows(self):
        text = plain(view.value_layers(self.model["value"]["run"]))
        self.assertLess(text.index("Layer one, base value"), text.index("Layer two, strategic value"))
        for figure in ("$14.06", "$21.73", "$30.03", "$14.33", "Signed fiber deals ship", "70%", "worked out Nov. 3, 2026"):
            self.assertIn(figure, text)
        self.assertIn("never counts toward coverage", text)
        self.assertIn("Forecasts, not results", text)

    def test_each_close_keeps_its_own_date_and_neither_stands_in(self):
        text = plain(view.price_zones(self.model["value"]["run"], self.model["close"]))
        for words in ("$126.14", "Last saved close, Nov. 3, 2026", "sensors/prices/cache/GLW/2026-11-03.csv", "$123.20", "The close the run used: close of Nov. 2, 2026", "Under $28.97", "$28.97 to $36.06", "Above $36.06"):
            self.assertIn(words, text)
        missing = plain(view.price_zones(self.model["value"]["run"], None))
        self.assertIn("Last saved close: not on file", missing)
        self.assertNotIn("$126.14", missing)
        self.assertIn("$123.20", missing)  # only as what the run used

    def test_the_zones_never_say_where_the_newest_close_sits(self):
        """The board compares no close to a line (PLAN.md). The zone block reads the same, tag for tag and word for word apart from the close, at any close."""
        run, close = self.model["value"]["run"], self.model["close"]
        one, other = view.price_zones(run, {**close, "close": 1.0}), view.price_zones(run, {**close, "close": 500.0})
        self.assertEqual(tags_only(one), tags_only(other))
        self.assertEqual(plain(one).replace("$1.00", "X"), plain(other).replace("$500.00", "X"))
        self.assertEqual(one.replace("$1.00", "X"), other.replace("$500.00", "X"))

    def test_zones_when_the_lines_cross(self):
        run = valuation_fixture()
        crossed = {**run, "buy_below": 40.0, "trim_above": 30.0}
        text = plain(view.price_zones(crossed, None))
        self.assertIn(view.ZONE_WORDS["under_and_above"], text)
        self.assertIn("$30.00 to $40.00", text)

    def test_catalysts_all_with_a_source_and_a_date(self):
        rows = self.model["catalysts"]
        self.assertEqual(len(rows), data.latest_radar()["dates"]["total"])
        starts = [r["start"] for r in rows if r["start"]]
        self.assertEqual(starts, sorted(starts))
        self.assertFalse(any(r["start"] for r in rows[len(starts):]))
        self.assertEqual(bare_figures(view.catalysts_table(self.model), strict=True), [])
        self.assertIn("Nov. 27, 2026", self.text)

    def test_every_neighbor_says_how_it_is_linked(self):
        rows = self.model["links"]["rows"]
        self.assertGreater(len(rows), 20)
        for words in ("Corning supplies AT&T", "Corning partners with NVIDIA", "Corning competes with Prysmian", "Read together", "Conditional", "My reading", "Optiemus (no note)"):
            self.assertIn(words, self.text)
        markup = view.links_table(self.model, view.company_pages(data.company_list()))
        self.assertIn('href="/company?company=T"', markup)
        self.assertIn('href="/company?company=Prysmian"', markup)
        self.assertNotIn("company=Optiemus", markup)

    def test_a_link_only_the_other_note_holds_is_shown_and_labelled(self):
        with tempfile.TemporaryDirectory() as folder:
            head = "---\nticker: A\n---\n\n## Typed links\n\n| Link | Company | Chain | What | Size | Evidence | Source |\n|---|---|---|---|---|---|---|\n"
            (Path(folder) / "One.md").write_text(head + "| supplies | [[Two]] | fiber | Fiber | $1B | Stated | [10-K, Feb. 1, 2026](https://www.sec.gov/x) |\n\n## End\n")
            (Path(folder) / "Two.md").write_text("---\nticker: B\n---\n\n## Typed links\n\nNone.\n\n## End\n")
            found = data.company_links("Two", folder)
            self.assertEqual(found["rows"], [])
            self.assertEqual(found["only_there"][0]["written_in"], "One")
            markup = view.links_table({"note": {"name": "Two"}, "links": found}, {})
            self.assertIn("Written only in One's note", plain(markup))
            self.assertEqual(bare_figures(markup, strict=True), [])

    def test_a_run_for_one_company_never_shows_under_another(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "2026-12-01-01.json").write_text(json.dumps(valuation_fixture(company="Other", ticker="OTH")))
            (Path(folder) / "2026-11-01-01.json").write_text(json.dumps(valuation_fixture()))
            self.assertEqual(data.company_run("Corning", "GLW", folder)["run"]["company"], "Corning")
            self.assertEqual(data.company_run("Other", "OTH", folder)["run"]["company"], "Other")
            self.assertIsNone(data.company_run("Fujikura", "", folder)["run"])

    def test_a_run_that_disagrees_with_itself_shows_a_problem_and_no_older_run_stands_in(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "2026-11-01-01.json").write_text(json.dumps(valuation_fixture()))
            (Path(folder) / "2026-12-01-01.json").write_text(json.dumps(valuation_fixture(buy_below=1.0)))
            found = data.company_run("Corning", "GLW", folder)
            self.assertIsNone(found["run"])
            self.assertIn("does not agree with itself", found["problems"][0])

    def test_a_note_cannot_make_the_browser_fetch(self):
        evil = "![a](http://evil.example/x.png) <img src=x> [b](javascript:alert(1)) <script>1</script> [c][r] ![[d]] `<iframe>`"
        for markup in (view.note_inline(evil, {"r": "http://evil.example/y"}), view.note_words(f"- {evil}\n\n| a |\n|---|\n| {evil} |")):
            self.assertEqual(inside(parse(markup), lambda n: n["tag"] in ("img", "iframe", "script")), [])
            self.assertNotIn('href="http://', markup)
            self.assertNotIn('href="javascript', markup)

    def test_no_grade_score_size_or_action_is_read(self):
        for name in ("company_view", "company_thesis", "company_history"):
            source = ast.get_source_segment((HERE / "data.py").read_text(), next(n for n in ast.parse((HERE / "data.py").read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name))
            self.assertNotIn("pm.py", source)
            self.assertNotIn("sizing", source)
        decision = (ROOT / "Journal/decisions/2026-11-03 Corning.md").read_text()
        self.assertIn("## ", decision)
        self.assertEqual(self.model["history"]["decisions"], [{"date": "2026-11-03", "stage": "compared", "file": "Journal/decisions/2026-11-03 Corning.md"}])


class CompanyPageNotValued(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = data.find_company("Fujikura", data.company_list())
        cls.model = data.company_view(cls.row, NOW.date())
        cls.page = company_screen("Fujikura")
        cls.text = plain(" ".join(body_of(cls.page)))

    def test_it_says_plainly_what_is_missing(self):
        for words in ("Not on file.", "Base value, strategic value, buy-below and trim-above", "The note says base value: not defined yet", "check that the method fits", "A thesis draft", "Claims and kill lines", "A recorded thesis", "The note gives no ticker"):
            self.assertIn(words, self.text)

    def test_what_is_missing_comes_before_what_is_on_file(self):
        self.assertLess(self.text.index("Base value, strategic value, buy-below and trim-above"), self.text.index("The note's sections"))

    def test_it_shows_what_is_on_file(self):
        self.assertIn("What it is", [x.label for x in self.page.expander])
        self.assertIn("Fujikura competes with Corning", self.text)
        self.assertIn("Graph neighbors", [h.value for h in self.page.header])
        self.assertEqual(self.model["value"]["run"], None)
        self.assertIsNone(self.model["close"])

    def test_no_figure_of_another_company_is_borrowed(self):
        for figure in ("$14.06", "$21.73", "$28.97", "$36.06", "$126.14", "$123.20", "DRAFT"):
            self.assertNotIn(figure, self.text)
        self.assertEqual(len(self.page.get("vega_lite_chart")), 0)
        self.assertNotIn("Corning financial health", [h.value for h in self.page.header])

    def test_every_other_note_says_the_same_kind_of_thing(self):
        for row in data.company_list():
            if row["ticker"] != "GLW":
                model = data.company_view(row, NOW.date())
                self.assertIsNone(model["value"]["run"], row["name"])
                self.assertTrue(any(a.startswith("Base value") for a, _ in model["missing"]), row["name"])

    def test_a_ticker_with_no_saved_close_says_so(self):
        model = data.company_view(data.find_company("LUMN", data.company_list()), NOW.date())
        self.assertIsNone(model["close"])
        self.assertTrue(any(a == "Last close" and "sensors/prices/cache/LUMN/" in b for a, b in model["missing"]))

    def test_a_file_that_cannot_be_read_is_a_problem_and_the_rest_still_draws(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "Broken.md").write_text("---\nno colon here\n---\n\n## What it is\n\nWords.\n")
            row = data.company_list(folder)[0]
            self.assertTrue(row["problem"])


class ComingUp(unittest.TestCase):
    def setUp(self):
        self.temp, self.folder, self.paths = home_copy()
        self.addCleanup(self.temp.cleanup)

    def write_note(self, name="2026-11-03 Corning kill criteria.md", grid="| Line | Q4 2026 (Jan. 2027) | Q1 2027 (Apr. 2027) |\n|---|---|---|\n| K1 One | r | T |\n| K2 Two | T | T |\n"):
        (self.folder / "Research" / name).write_text(f"---\nticker: GLW\n---\n\n## Calendar of checks\n\nColumn dates are my estimates.\n\n{grid}\n| When | What | Kind |\n|---|---|---|\n| x | y | z |\n\n## How far to trust this\n\nx\n")

    def test_the_next_report_is_read_from_the_grid(self):
        self.write_note()
        row = data.next_kill_checks(dt.date(2026, 11, 4), self.folder / "Research")["rows"][0]
        self.assertEqual((row["company"], row["report"], row["month"], row["lines"]), ("Corning", "Q4 2026", "Jan. 2027", ["K2"]))
        self.assertEqual(data.next_kill_checks(dt.date(2027, 1, 31), self.folder / "Research")["rows"][0]["report"], "Q4 2026")
        self.assertEqual(data.next_kill_checks(dt.date(2027, 2, 1), self.folder / "Research")["rows"][0]["lines"], ["K1", "K2"])

    def test_a_calendar_that_ran_out_or_is_missing_is_a_problem(self):
        self.write_note()
        self.assertIn("no report after", data.next_kill_checks(dt.date(2027, 5, 1), self.folder / "Research")["problems"][0])
        (self.folder / "Research" / "2026-11-03 Other kill criteria.md").write_text("# no calendar\n")
        self.assertIn("could not be read", " ".join(data.next_kill_checks(dt.date(2026, 11, 4), self.folder / "Research")["problems"]))

    def test_the_newest_note_for_a_company_wins(self):
        self.write_note()
        self.write_note("2026-12-01 Corning kill criteria.md", "| Line | Q4 2026 (Jan. 2027) |\n|---|---|\n| K5 New | T |\n")
        self.assertEqual([r["lines"] for r in data.next_kill_checks(dt.date(2026, 11, 4), self.folder / "Research")["rows"]], [["K5"]])

    def test_the_real_note_gives_the_real_lines(self):
        row = data.next_kill_checks(dt.date(2026, 11, 4))["rows"][0]
        self.assertEqual((row["company"], row["report"], row["month"], row["lines"]), ("Corning", "Q4 2026", "Jan. 2027", ["K2", "K6", "K7"]))

    def test_nearest_first_together_and_a_passed_date_leaves(self):
        date = lambda title, start, end: {"title": title, "file": "Catalysts/x.md", "date_start": start, "date_end": end, "date_quote": start, "date_kind": "stated", "source": None}  # noqa: E731
        run = {"run_date": "2026-11-03", "dates": {"soon": [date("Later", "2026-12-20", "2026-12-20"), date("Gone", "2026-11-01", "2026-11-03"), date("Open now", "2026-07-01", "2026-12-31"), date("Jan one", "2027-01-01", "2027-01-31")]}}
        checks = {"rows": [{"company": "Corning", "report": "Q4 2026", "month": "Jan. 2027", "start": dt.date(2027, 1, 1), "lines": ["K2"], "file": "Research/x.md", "written": "2026-11-03"}], "problems": []}
        rows = data.coming_up(run, checks, dt.date(2026, 11, 4))
        self.assertEqual([r["title"][:7] for r in rows], ["Open no", "Later", "Corning", "Jan one"])

    def test_a_kill_row_is_labelled_an_estimate(self):
        checks = {"rows": [{"company": "Corning", "report": "Q4 2026", "month": "Jan. 2027", "start": dt.date(2027, 1, 1), "lines": ["K2", "K6"], "file": "Research/x.md", "written": "2026-11-03"}], "problems": []}
        text = plain(view._coming_figure(data.coming_up(None, checks, dt.date(2026, 11, 4))[0]))
        self.assertEqual(text, "about Jan. 2027 my estimate Corning: K2, K6 can fire on the Q4 2026 report Nov. 3, 2026, Research/x.md")

    def test_no_kill_row_when_no_line_can_fire(self):
        checks = {"rows": [{"company": "Corning", "report": "Q4 2026", "month": "Jan. 2027", "start": dt.date(2027, 1, 1), "lines": [], "file": "Research/x.md", "written": "2026-11-03"}], "problems": []}
        self.assertEqual(data.coming_up(None, checks, dt.date(2026, 11, 4)), [])


class WhereThingsStand(unittest.TestCase):
    def setUp(self):
        self.temp, self.folder, self.paths = home_copy()
        self.addCleanup(self.temp.cleanup)

    def note(self, name, kind, cash, rows):
        table = "\n".join(f"| {t} | {s} | 2026-11-01 | $10.00 | x |" for t, s in rows)
        marked = f"kind: {kind}\n" if kind else ""
        (self.folder / "notes" / name).write_text(f'---\n{marked}cash: {cash}\nas of: "2026-11-01"\nlast checked: "2026-11-01"\n---\n\n## Positions\n\n| Ticker | Shares | Bought on | Cost a share | Thesis note |\n|---|---|---|---|---|\n{table}\n')

    def test_real_and_paper_stay_apart_and_real_comes_first(self):
        self.note("A.md", "paper", 100, [])
        self.note("B.md", "real", 50, [])
        books = data.position_notes(self.folder / "notes", self.folder / "cache")
        self.assertEqual(([n["cash"] for n in books["real"]], [n["cash"] for n in books["paper"]]), ([50.0], [100.0]))
        text = plain(view._home_stands(home_model(books=books)))
        self.assertLess(text.index("Real"), text.index("Paper, made-up money"))

    def test_a_note_marked_neither_is_a_problem_and_counts_as_neither(self):
        self.note("A.md", None, 100, [])
        self.note("B.md", "both", 100, [])
        books = data.position_notes(self.folder / "notes", self.folder / "cache")
        self.assertEqual((books["real"], books["paper"], len(books["problems"])), ([], [], 2))
        self.assertIn("not marked real or paper", books["problems"][0])

    def test_shares_use_todays_close_as_the_cash_rule_says(self):
        write_prices(self.folder / "cache", close="100.00")  # GLW at $100, bought at $10 in the note
        self.note("A.md", "paper", 1000, [("GLW", "90")])
        note = data.position_notes(self.folder / "notes", self.folder / "cache")["paper"][0]
        self.assertAlmostEqual(note["share"], 1000 / 10000)
        self.assertEqual(note["level"], "Normal")

    def test_no_close_means_unknown_with_no_fallback_to_cost(self):
        self.note("A.md", "paper", 1000, [("NONE", "90")])
        note = data.position_notes(self.folder / "notes", self.folder / "cache")["paper"][0]
        self.assertIsNone(note["share"])
        self.assertIn("Share Unknown: no saved close for NONE", plain(view._book_row("Paper", note)))

    def test_no_real_note_says_so(self):
        self.assertIn("No real holdings or cash on file.", plain(view._home_stands(home_model())))

    def test_the_real_vault_has_only_a_paper_note(self):
        books = data.position_notes()
        self.assertEqual((books["real"], books["problems"], len(books["paper"])), ([], [], 1))

    def test_the_real_row_shows_the_saved_close_not_the_runs_price(self):
        row = data.where_it_stands(data.latest_valuation())
        self.assertEqual(row["price"], data.last_price("GLW"))
        self.assertNotEqual(row["price"]["date"], data.latest_valuation()["price"]["date"])

    def test_a_company_with_no_saved_close_shows_none_and_no_fallback(self):
        run = {**data.latest_valuation(), "ticker": "NONE"}
        row = data.where_it_stands(run, self.folder / "cache")
        self.assertIsNone(row["price"])
        self.assertIn("Close not on file.", plain(view._stand_row(row)))
        self.assertNotIn("$123.20", plain(view._stand_row(row)))

    def test_a_run_that_disagrees_with_itself_is_a_problem_not_a_row(self):
        run = data.latest_valuation()
        (self.folder / "values" / "2026-11-03-01.json").write_text(json.dumps({**run, "buy_below": 1.0}))
        out = data.latest_valuations(self.folder / "values")
        self.assertEqual(out["rows"], [])
        self.assertIn("does not agree with itself", out["problems"][0])

    def test_one_broken_block_leaves_the_others(self):
        (self.folder / "runs" / "2026-11-03-01.json").write_text("{not json")
        (self.folder / "Journal" / "2026-11-05.md").write_text("# 2026-11-05\n\n### Orange\n\n- [8-K, Nov. 5, 2026](https://www.sec.gov/x), O2: a fact.\n")
        model = data.home_view(**self.paths)
        self.assertTrue(model["coming_problems"])
        text = plain(view.home(model, NOW))
        self.assertIn("Waiting for me: 0 Red, 1 Orange.", text)
        self.assertIn("No real holdings", text)


class BusyTestCopy(unittest.TestCase):
    """The made-up day: a real copy, read by the real readers, and it can never land in the vault."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(HERE / "tools"))
        import busy_copy

        cls.tool = busy_copy
        cls.temp = tempfile.TemporaryDirectory()
        cls.copy = Path(cls.temp.name) / "copy"
        before = sys.argv
        sys.argv = ["busy_copy.py", str(cls.copy)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                busy_copy.main()
        finally:
            sys.argv = before
        cls.model = data.home_view(journal=cls.copy / "Journal", research=cls.copy / "Research", radar_runs=cls.copy / "sensors/radar/runs",
                                   valuation_runs=cls.copy / "sensors/valuation/runs", notes=cls.copy / "Portfolio", cache=cls.copy / "sensors/prices/cache")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_it_refuses_the_vault_and_an_existing_folder(self):
        for target in (ROOT, ROOT / "dashboard" / "busy", self.copy):
            before = sys.argv
            sys.argv = ["busy_copy.py", str(target)]
            try:
                with self.assertRaises(SystemExit) as stop:
                    self.tool.main()
                self.assertIn("Refused", str(stop.exception))
            finally:
                sys.argv = before

    def test_it_carries_the_label(self):
        self.assertIn("TEST COPY", data.test_copy_label(self.copy / "TEST_COPY.txt"))
        self.assertIn("TEST COPY", view.test_copy_banner(data.test_copy_label(self.copy / "TEST_COPY.txt")))

    def test_the_counts_on_home_match_what_was_made_up(self):
        waiting = self.model["waiting"]
        made_up = [r for r in waiting["rows"] if "ade-up" in r["text"] or "MADE-UP" in r["text"]]
        self.assertEqual(view.home_counts(waiting), (4, 8))
        self.assertEqual(len(made_up), 12)
        self.assertEqual(len(waiting["closed"]), 2)
        self.assertEqual(sum("matches no alert" in p for p in waiting["problems"]), 1)
        self.assertIn("And 7 more: 0 Red, 7 Orange", plain(view.home(self.model, NOW)))

    def test_it_has_every_kind_of_row_past_its_limit(self):
        self.assertGreater(len(self.model["coming"]), view.COMING_ROWS)
        self.assertGreater(len(self.model["brief"]["info"]), view.INFO_ROWS)
        self.assertTrue(self.model["coming_problems"])
        self.assertTrue(self.model["books"]["problems"])
        self.assertFalse([r for r in self.model["coming"] if "passed before today" in r["title"]])

    def test_nothing_on_it_is_a_bare_figure(self):
        self.assertEqual(bare_figures(view.home(self.model, NOW)), [])

    def test_ideas_on_it_reach_every_early_stage(self):
        c = self.copy
        model = data.ideas_view(journal=c / "Journal", research=c / "Research", inbox=c / "Inbox", radar_runs=c / "sensors/radar/runs", companies=c / "Companies", settings=c / "sensors/hunt/settings.toml")
        self.assertEqual([i["ticker"] for i in model["stages"]["idea"]], ["TSTI"])
        self.assertEqual([i["ticker"] for i in model["stages"]["tested"]], ["TSTP"])
        self.assertEqual(model["problems"], [])
        self.assertEqual(len(model["reports"]), 1)


def ideas_folder(root, log=None, reports=(), ideas=(), decisions=(), journal=()):
    """A small made-up vault for the Ideas readers. Files are written the way the routines and the coach write them."""
    root = Path(root)
    for sub in ("Research", "Inbox", "Journal/decisions", "Companies", "runs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    head = "| Date | Company | Gate | Reason | Look again |\n|---|---|---|---|---|\n"
    (root / "Research/Rejection log.md").write_text("---\ntrack: rejection log\nwritten: 2026-11-03\n---\n\n# Rejection log\n\n*Leads, never picks.*\n\n" + head + "\n".join(log or []) + "\n")
    for name, text in reports:
        (root / "Research" / name).write_text(text)
    for name, text in ideas:
        (root / "Inbox" / name).write_text(text)
    for name, text in decisions:
        (root / "Journal/decisions" / name).write_text(text)
    for name, text in journal:
        (root / "Journal" / name).write_text(text)
    (root / "Companies/Made Up.md").write_text('---\nticker: MADE\nstatus: researching\nlast checked: "2026-11-03"\n---\n\n# Made Up\n')
    (root / "settings.toml").write_text("")
    return root


def view_of(root):
    root = Path(root)
    return data.ideas_view(journal=root / "Journal", research=root / "Research", inbox=root / "Inbox", radar_runs=root / "runs", companies=root / "Companies", settings=root / "settings.toml")


def log_line(company="Made Co (MCO)", day="Nov. 3, 2026", look="After the 10-K, about Feb. 2027 (my estimate).", gate="Gate 1", reason="Debt was $5.0B (calc., [10-K, filed Feb. 2, 2026](https://www.sec.gov/x))."):
    return f"| {day} | {company} | {gate} | {reason} | {look} |"


def idea_file(ticker="MCO", day="2026-12-15"):
    return (f'---\nform: "idea"\ncompany: "Made Co"\nticker: "{ticker}"\nsurfaced: "{day}"\nfiled: "{day}"\nattention: "unknown"\nreason: "A lead to read, never a pick."\nsources:\n  - "https://www.sec.gov/x"\n---\n\n'
            f"# Idea to read: Made Co\n\n*A lead to read, never a pick.*\n\n## Why it surfaced\n\nRemaining obligations went from $1.0M to $9.0M (calc., [frame, retrieved Dec. 15, 2026](https://data.sec.gov/x)).\n\n## How far it got\n\nGate 2: pass.\n")


SYSTEM_SECRET = "SYSTEM-VIEW-SECRET Strong grade, 20% cap, size $7,100"


def coach_file(company="Made Co", ticker="MCO", day="2026-11-03", decided="Not said yet. Only my own words go here. A recommendation is not my decision."):
    return (f'---\ncompany: {company}\nticker: {ticker}\ndate: "{day}"\nstage: compared\n---\n\n# {company}: decision\n\n## My view\n\nWritten before anything was shown.\n\n- **Action:** No position\n- **Size:** zero dollars\n- **One main reason:** Not my kind of business.\n\n'
            f"## The system's view\n\n{SYSTEM_SECRET}\n\n## Where we differ, and why\n\n{SYSTEM_SECRET}\n\n## The one question\n\nWould I?\n\n## What I then decided\n\n{decided}\n\n## What this log does not say\n\nNo trade.\n")


def lead_row(name="Made Co", ticker="MCO", on_map=None):
    line = {"label": "Contract liabilities", "earlier": 1e6, "later": 9e6, "end_earlier": "2026-03-31", "end_later": "2026-06-30", "rise_pct": 800.0, "year_ago_pct": None, "accession_earlier": "a", "accession_later": "b",
            "filing_later": "https://www.sec.gov/x", "frame_url_later": "https://data.sec.gov/y", "frame_later": "CY2026Q2I"}
    return {"cik": 1, "name": name, "ticker": ticker, "on_map": on_map, "lines": [line]}


class IdeasStages(unittest.TestCase):
    """Each company or lead sits at one stage, from what the files say, and the words around it give no view."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def stage_of(self, model, ticker):
        return [stage for stage, rows in model["stages"].items() if any(item["ticker"] == ticker for item in rows)]

    def test_the_real_vault_puts_each_company_at_one_stage(self):
        model = data.ideas_view()
        keys = [item["key"] for rows in model["stages"].values() for item in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(self.stage_of(model, "GLW"), ["decision"])
        self.assertEqual(self.stage_of(model, "MU"), ["watchlist"])
        self.assertEqual(self.stage_of(model, "ORCL"), ["rejected"])
        self.assertEqual(self.stage_of(model, "NVDA"), ["map"])
        self.assertEqual(len(model["stages"]["map"]) + 1, len(data.company_list()), "every note but Corning's is on the map")

    def test_the_real_screen_rows_add_up(self):
        model = data.ideas_view()
        here = sum(len(lead["lines"]) for part in model["steps"] for lead in part["leads"] + part["hidden"])
        self.assertGreater(here, 100)
        self.assertEqual(here + model["rows_elsewhere"], model["screen_rows"])
        self.assertEqual(model["screen_rows"], sum(len(lead["lines"]) for step in model["radar"]["screen"]["steps"] for lead in step["leads"] + step.get("hidden_leads", [])))

    def test_the_watchlist_says_what_gate_3_found(self):
        micron = data.ideas_view()["stages"]["watchlist"][0]
        self.assertIn("No edge", micron["at"]["words"][0])
        self.assertIn("look", micron["at"]["says"])

    def test_corning_shows_everything_on_file_beside_its_stage(self):
        corning = next(item for item in data.ideas_view()["stages"]["decision"] if item["ticker"] == "GLW")
        self.assertEqual([ev["stage"] for ev in corning["also"]][:3], ["skeptic", "thesis", "rejected"])
        self.assertIn("did not survive", corning["also"][0]["words"][0])

    def test_the_newest_step_wins_and_the_furthest_on_a_tie(self):
        root = ideas_folder(self.root, log=[log_line(day="Nov. 3, 2026")])
        self.assertEqual(self.stage_of(view_of(root), "MCO"), ["rejected"])
        (root / "Inbox/2026-12-15 MCO idea.md").write_text(idea_file())
        self.assertEqual(self.stage_of(view_of(root), "MCO"), ["idea"], "a look-again brought it back")
        (root / "Inbox/2026-12-15 MCO idea.md").unlink()
        (root / "Journal/decisions/2026-11-03 Made Co.md").write_text(coach_file())
        self.assertEqual(self.stage_of(view_of(root), "MCO"), ["decision"], "same day")
        (root / "Research/Rejection log.md").write_text((root / "Research/Rejection log.md").read_text() + log_line(day="Dec. 1, 2026") + "\n")
        self.assertEqual(self.stage_of(view_of(root), "MCO"), ["rejected"], "a newer rejection")

    def test_a_screen_row_never_outranks_a_file_of_ours(self):
        root = ideas_folder(self.root, log=[log_line()])
        (root / "runs/2026-12-20-01.json").write_text(json.dumps(radar_fixture(screen={"status": "ok", "lead_count": 2, "steps": [{**radar_fixture()["screen"]["steps"][0], "leads": [lead_row(), lead_row("Made Up Inc", "MADE", "Made Up"), lead_row("New Co", "NEW")]}]})))
        model = view_of(root)
        self.assertEqual(self.stage_of(model, "MCO"), ["rejected"])
        self.assertEqual(self.stage_of(model, "MADE"), ["map"])
        self.assertEqual(self.stage_of(model, "NEW"), ["lead"])
        self.assertEqual([lead["ticker"] for lead in model["steps"][0]["leads"]], ["NEW"])
        self.assertEqual(model["rows_elsewhere"], 2)
        self.assertEqual(next(item["name"] for item in model["stages"]["rejected"]), "Made Co", "our own name, not SEC's")

    def test_every_lead_row_says_what_it_is(self):
        def count(markup):
            return plain(markup).count(view.LEAD_LABEL)

        leads = [lead_row(), lead_row("Other", "OTH")]
        table = view.radar_leads_table(leads, "Nov. 3, 2026")
        self.assertEqual(count(table), 2)
        self.assertEqual(table.count("<tr>") - 1, 2)
        model = data.ideas_view()
        pages = view.company_pages(model["pages"])
        for stage in ("map", "watchlist", "rejected"):
            rows = model["stages"][stage]
            self.assertEqual(count(view.stage_table(rows, stage, pages, "Nov. 4, 2026")), len(rows), stage)
        log = model["log"]["rows"]
        self.assertEqual(count(view.rejection_table(log, "x, 2026")), len(log))
        self.assertEqual(view.LEAD_LABEL, "A lead to read, never a pick")

    def test_the_real_screen_labels_every_lead(self):
        html_body = plain(" ".join(run_screens()["screens/ideas.py"]["html"]))
        model = data.ideas_view()
        shown = sum(len(lead["lines"]) for part in model["steps"] for lead in part["leads"] + part["hidden"])
        rows = sum(len(model["stages"][s]) for s in data.STAGES if s not in ("lead", "decision")) + len(model["log"]["rows"])
        self.assertEqual(html_body.count(view.LEAD_LABEL), shown + rows + 1, "one for each row, and the line at the top")

    def test_a_coach_file_shows_only_my_words(self):
        root = ideas_folder(self.root, decisions=[("2026-11-03 Made Co.md", coach_file(decided='"Yes, no position."'))])
        model = view_of(root)
        item = model["stages"]["decision"][0]
        self.assertEqual(item["at"]["words"], ["**Action:** No position", "**Size:** zero dollars", "**One main reason:** Not my kind of business.", '"Yes, no position."'])
        markup = view.stage_table(model["stages"]["decision"], "decision", {}, "Nov. 4, 2026")
        self.assertNotIn("SYSTEM-VIEW", markup)
        self.assertIn("then what I decided", plain(markup))
        self.assertIn(view.MY_WORDS_LABEL, plain(markup))

    def test_a_paper_coach_file_carries_its_label_and_a_real_one_does_not(self):
        model = data.ideas_view()
        markup = view.stage_table(model["stages"]["decision"], "decision", view.company_pages(model["pages"]), "Nov. 4, 2026")
        self.assertEqual(plain(markup).count("Paper, a lesson"), 1)
        self.assertLess(plain(markup).index("Paper, a lesson"), plain(markup).index("Buy what passes"))

    def test_a_coach_file_with_no_decision_says_so(self):
        model = view_of(ideas_folder(self.root, decisions=[("2026-11-03 Made Co.md", coach_file())]))
        item = model["stages"]["decision"][0]
        self.assertEqual(len(item["at"]["words"]), 3)
        self.assertIn("no decision of mine in it yet", item["at"]["says"])

    def test_the_real_screen_has_no_grade_score_or_system_view(self):
        text = plain(" ".join(run_screens()["screens/ideas.py"]["html"]))
        for words in ("The system's view:", "pm.py", "Thin", "Strong", "Value if wrong", "Loss if wrong", "$14.33"):
            self.assertNotIn(words, text)
        self.assertIn("No position", text)

    def test_a_skeptic_ruling_must_be_mine(self):
        root = ideas_folder(self.root, journal=[("2026-11-03.md", "# 2026-11-03\n\n## Session\n\n### What we did\n\n- The idea did not survive the skeptic's review. My decision.\n\n### What we decided\n\n- Made Up: Claude thinks it survived the skeptic.\n- **The idea did not survive the skeptic's review, for now. Made Up stays no buy. My decision.**\n")])
        rulings = data.skeptic_rulings(root / "Journal")
        self.assertEqual(len(rulings), 1)
        self.assertIn("for now", rulings[0]["line"])
        model = view_of(root)
        self.assertEqual(self.stage_of(model, "MADE"), ["skeptic"])

    def test_real_rulings_are_the_ones_i_made(self):
        self.assertEqual([r["day"] for r in data.skeptic_rulings()], ["2026-11-03"])

    def test_empty_stages_say_what_would_fill_them(self):
        for stage in view.STAGE_ORDER:
            self.assertTrue(view.STAGE_WORDS[stage][2])
        self.assertEqual(set(view.STAGE_WORDS), {*data.STAGES, data.OFF_RAMP})

    def test_nothing_on_file_still_draws(self):
        root = self.root / "nothing"
        for sub in ("Research", "Inbox", "Journal", "Companies", "runs"):
            (root / sub).mkdir(parents=True)
        model = data.ideas_view(journal=root / "Journal", research=root / "Research", inbox=root / "Inbox", radar_runs=root / "runs", companies=root / "Companies", settings=root / "none.toml")
        self.assertIsNone(model["log"])
        self.assertIsNone(model["radar"])
        self.assertEqual(sum(len(rows) for rows in model["stages"].values()), 0)
        self.assertEqual(model["problems"], [])

    def test_a_file_that_cannot_be_read_is_a_problem_and_the_rest_still_show(self):
        root = ideas_folder(self.root, log=[log_line()], ideas=[("2026-12-15 BAD idea.md", "no front matter")])
        model = view_of(root)
        self.assertTrue([p for p in model["problems"] if "BAD idea" in p])
        self.assertEqual(self.stage_of(model, "MCO"), ["rejected"])
        (root / "runs/2026-12-20-01.json").write_text("{broken")
        self.assertTrue([p for p in view_of(root)["problems"] if "radar" in p])

    def test_the_own_words_give_no_view_and_no_price_move(self):
        root = ideas_folder(self.root, log=[log_line()], ideas=[("2026-12-15 NEW idea.md", idea_file("NEW"))], decisions=[("2026-11-03 Made Up.md", coach_file("Made Up", "MADE", decided='"I will buy and hold."'))])
        model = view_of(root)
        pages = view.company_pages(model["pages"])
        parts = [view.stage_strip(model, "Nov. 4, 2026"), view.jump_line(3, "Nov. 4, 2026"), view.rejection_counts(model), view.rejection_table(model["log"]["rows"], "x, 2026")]
        parts += [view.stage_table(rows, stage, pages, "Nov. 4, 2026") for stage, rows in model["stages"].items()]
        parts += [f"<p>{w[1]} {w[0]}</p>" for w in view.STAGE_WORDS.values()]
        text = plain(own_words("".join(parts))).replace("Alerts", "")
        self.assertIsNone(VIEW_WORDS.search(text), VIEW_WORDS.search(text))
        self.assertIsNone(ALERT_WORDS.search(text), ALERT_WORDS.search(text))

    def test_copied_text_cannot_reach_the_browser_raw(self):
        evil = '<img src=x onerror=alert(1)> [click](javascript:alert(1)) ![pic](https://evil.example/x.png)'
        root = ideas_folder(self.root, log=[log_line(company="<b>Bad</b> (BAD)", reason=evil, look=evil)])
        model = view_of(root)
        markup = view.rejection_table(model["log"]["rows"], "x, 2026") + view.stage_table(model["stages"]["rejected"], "rejected", {}, "Nov. 4, 2026")
        self.assertNotIn("<img", markup)
        self.assertNotIn("<b>Bad", markup)
        self.assertNotIn('href="javascript', markup)


class RejectionLogTable(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = ideas_folder(self.temp.name, log=[log_line("Later (LAT)", look="About mid 2028, by hand."), log_line("Soon (SON)", look="After the 10-K, about Dec. 2026 (my estimate)."), log_line("Year (YR)", look="After its first 10-K, about early 2027 (my estimate)."), log_line("No Date (NOD)", look="When I ask.")])

    def tearDown(self):
        self.temp.cleanup()

    def test_rows_come_nearest_month_first_and_no_month_last(self):
        rows = data.rejection_log(self.root / "Research/Rejection log.md")["rows"]
        self.assertEqual([r["ticker"] for r in rows], ["SON", "YR", "LAT", "NOD"])
        self.assertEqual([r["month_shown"] for r in rows], ["Dec. 2026", "2027", "None named", "None named"])

    def test_a_row_that_cannot_be_read_is_named_and_not_dropped(self):
        path = self.root / "Research/Rejection log.md"
        path.write_text(path.read_text() + "| Nov. 3, 2026 | Short (SHO) | Gate 1 |\n")
        log = data.rejection_log(path)
        self.assertEqual(len(log["rows"]), 4)
        self.assertTrue([p for p in log["problems"] if "Nov. 3, 2026" in p and "Short" in p])

    def test_the_real_log_has_every_row_and_why_and_when(self):
        log = data.rejection_log()
        written = [line for line in (ROOT / "Research/Rejection log.md").read_text().splitlines() if re.match(r"\| [A-Z][a-z]+\.? \d", line)]
        self.assertEqual(len(log["rows"]), len(written))
        self.assertEqual(log["problems"], [])
        text = plain(view.rejection_table(log["rows"], "x, 2026", sits_at=False))
        for row in log["rows"]:
            self.assertTrue(row["reason"] and row["look"] and row["date"], row["company"])
            self.assertIn(row["company"], text)
        self.assertIn("Why it was rejected", text)
        self.assertIn("When to look again", text)

    def test_month_reading_agrees_with_the_hunt(self):
        """In a separate process, because the hunt imports what the board may not."""
        code = ("import sys, json; sys.path.insert(0, 'sensors/hunt'); import hunt; "
                "print(json.dumps({w: hunt.look_month(w) for w in json.load(sys.stdin)}))")
        rows = data.rejection_log()["rows"]
        words = [r["look"] for r in rows] + ["about Sept. 2027", "about early 2027", "When I ask.", "about late Jan. 2027"]
        out = subprocess.run([sys.executable, "-c", code], input=json.dumps(words), capture_output=True, text=True, cwd=ROOT, check=True)
        self.assertEqual(json.loads(out.stdout), {w: data.look_again_month(w) for w in words})

    def test_no_look_again_row_looks_different_for_its_month(self):
        rows = data.rejection_log(self.root / "Research/Rejection log.md")["rows"]
        soon, later = view.rejection_table(rows[:1], "x, 2026", sits_at=False), view.rejection_table(rows[2:3], "x, 2026", sits_at=False)
        self.assertEqual(tags_only(soon).replace(" ", ""), tags_only(later).replace(" ", ""))


class HuntReports(unittest.TestCase):
    """The real shape: hunt.py's own saved sample, and the file name it writes."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        sample = (ROOT / "sensors/hunt/samples/hunt-report.md").read_text()
        self.root = ideas_folder(self.temp.name, reports=[("2026-11-04 Monthly hunt.md", sample)])
        self.model = view_of(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_it_reads_the_funnel_the_tested_and_the_proposed(self):
        report = self.model["reports"][0]
        self.assertEqual(report["day"], "2026-11-04")
        self.assertEqual(report["funnel"]["headers"], ["Step", "Count (calc.)", "Who"])
        self.assertEqual(len(report["tested"]["rows"]), 5)
        self.assertEqual([r["ticker"] for r in report["proposed"]], ["AKAM", "CTMX", "CCCC", "CRWV", "AROC"])

    def test_a_proposal_sits_at_tested_and_is_not_in_the_log(self):
        self.assertEqual(len(self.model["stages"]["tested"]), 5)
        self.assertEqual(self.model["stages"]["rejected"], [])
        self.assertIn("not in the log unless I add it", self.model["stages"]["tested"][0]["at"]["says"])

    def test_it_draws_with_every_figure_sourced(self):
        report = self.model["reports"][0]
        for markup in (view.hunt_block(report), view.rejection_table(report["proposed"], "x, 2026", sits_at=False), view.stage_table(self.model["stages"]["tested"], "tested", {}, "Nov. 4, 2026")):
            self.assertEqual(bare_figures(markup, strict=True), [])

    def test_an_idea_note_is_read_and_is_no_8k(self):
        (self.root / "Inbox/2026-12-15 NEW idea.md").write_text(idea_file("NEW"))
        model = view_of(self.root)
        item = model["stages"]["idea"][0]
        self.assertEqual((item["ticker"], item["at"]["day"]), ("NEW", "2026-12-15"))
        self.assertIn("Remaining obligations", item["at"]["words"][0])
        self.assertEqual(data.read_inbox(self.root / "Inbox"), [])
        markup = view.stage_table(model["stages"]["idea"], "idea", {}, "Nov. 4, 2026")
        self.assertEqual(bare_figures(markup, strict=True), [])
        self.assertIn(view.LEAD_LABEL, plain(markup))


class AlertStates(unittest.TestCase):
    """Whether I have ruled, from the same reading as Home's waiting list."""

    def book(self):
        return {"alerts": [alert("2026-11-05", "Info", "I3"), alert("2026-11-04", "Orange", "O2", "First O2."), alert("2026-11-04", "Orange", "O2", "Second O2."), alert("2026-11-03", "Red", "R1"), alert("2026-11-01", "Red", "R3"), alert("2026-11-04", "Orange", "O3")],
                "rulings": [ruled("2026-11-04", "O2", words="The first holds."), ruled("2026-11-03", "R1", words="Still holds."), ruled("2026-01-01", "R9", words="Matches nothing.")], "last_run": {}, "days_read": 3}

    def test_each_line_has_its_state_and_my_words(self):
        rows = data.alert_rows(self.book(), TODAY)["rows"]
        got = [(r["level"], r["rule"], r["state"], r["ruled"]) for r in rows]
        self.assertEqual(got, [("Red", "R3", "Waiting", None), ("Red", "R1", "Ruled", "Still holds."), ("Orange", "O2", "Waiting", None), ("Orange", "O3", "Waiting", None), ("Orange", "O2", "Ruled", "The first holds."), ("Info", "I3", "No ruling asked", None)])
        self.assertEqual(next(r for r in rows if r["rule"] == "O2" and r["state"] == "Ruled")["text"], "First O2.")
        self.assertEqual(next(r for r in rows if r["rule"] == "O2" and r["state"] == "Waiting")["text"], "Second O2.")
        self.assertEqual(rows[0]["days"], 4)

    def test_it_agrees_with_home(self):
        book = self.book()
        rows = data.alert_rows(book, TODAY)
        home = data.waiting_list(book, TODAY)
        self.assertEqual(sorted(r["text"] for r in rows["rows"] if r["state"] == "Waiting"), sorted(r["text"] for r in home["rows"]))
        self.assertEqual(rows["problems"], home["problems"])
        self.assertTrue([p for p in rows["problems"] if "matches no alert" in p])

    def test_the_table_shows_the_whole_line_with_its_source_and_state(self):
        long = "x" * 900
        rows = data.alert_rows({"alerts": [alert("2026-11-04", "Red", "R1", f"[8-K, filed Nov. 4, 2026](https://www.sec.gov/x), R1: {long}"), alert("2026-11-05", "Info", "I3", "no source, I3.")], "rulings": [], "last_run": {}, "days_read": 1}, TODAY)["rows"]
        table = view.alerts_table(rows)
        text = plain(table)
        self.assertIn(long, text)
        self.assertNotIn("**", plain(view.alerts_table(data.alert_rows({"alerts": [alert("2026-11-04", "Red", "R1", "**Made Co, R1.** A line.")], "rulings": [], "last_run": {}, "days_read": 1}, TODAY)["rows"])))
        self.assertIn("Waiting", text)
        self.assertIn("1 day since its Journal day (calc.)", text)
        self.assertIn("No ruling asked", text)
        self.assertIn("The line names no source", text)
        self.assertIn("Journal/2026-11-04.md", text)
        self.assertEqual(bare_figures(table, strict=True), [])

    def test_a_ruled_line_carries_my_words_and_where(self):
        rows = data.alert_rows({"alerts": [alert("2026-11-03", "Red", "R1")], "rulings": [ruled("2026-11-03", "R1", words="Still holds, $5.")], "last_run": {}, "days_read": 1}, TODAY)["rows"]
        table = view.alerts_table(rows)
        self.assertIn("Still holds, $5.", plain(table))
        self.assertIn("Journal/2026-11-05.md", plain(table))
        self.assertEqual(bare_figures(table, strict=True), [])

    def test_each_filter_works_alone_and_together(self):
        rows = data.alert_rows(self.book(), TODAY)["rows"]
        pick = lambda **kw: [(r["rule"], r["state"]) for r in data.filter_alerts(rows, **kw)]  # noqa: E731
        self.assertEqual(len(pick()), 6)
        self.assertEqual({r for r, _ in pick(levels=["Red"])}, {"R1", "R3"})
        self.assertEqual(pick(rules=["O3"]), [("O3", "Waiting")])
        self.assertEqual(len(pick(routines=["Daily run"])), 6)
        self.assertEqual(pick(routines=["Event run"]), [])
        self.assertEqual({r for r, s in pick(states=["Ruled"])}, {"R1", "O2"})
        self.assertEqual(pick(states=["No ruling asked"]), [("I3", "No ruling asked")])
        self.assertEqual(pick(first=dt.date(2026, 11, 5)), [("I3", "No ruling asked")])
        self.assertEqual(pick(last=dt.date(2026, 11, 1)), [("R3", "Waiting")])
        self.assertEqual(pick(levels=["Orange"], states=["Ruled"], first=dt.date(2026, 11, 4), last=dt.date(2026, 11, 4)), [("O2", "Ruled")])

    def test_a_filter_never_hides_a_waiting_red_silently(self):
        rows = data.alert_rows(self.book(), TODAY)["rows"]
        line = plain(view.alert_filter_line(data.filter_alerts(rows, levels=["Info"]), rows))
        self.assertEqual(line, "Showing 1 of 6 lines. These filters leave out 1 Red and 2 Oranges still waiting.")
        self.assertEqual(plain(view.alert_filter_line(rows, rows)), "Showing 6 of 6 lines.")

    def test_the_own_words_give_no_view(self):
        rows = data.alert_rows(self.book(), TODAY)["rows"]
        text = plain(own_words(view.alerts_table(rows) + view.alert_filter_line(rows[:1], rows))) + " ".join(data.ALERT_STATES)
        self.assertIsNone(VIEW_WORDS.search(text), VIEW_WORDS.search(text))
        self.assertIsNone(ALERT_WORDS.search(text), ALERT_WORDS.search(text))

    def test_the_guard_table_is_whole(self):
        rows = [{"when": "2026-11-05T08:00:00+00:00", "rule": "W1", "how": "before the call", "tool": "Edit", "target": f"file {i}"} for i in range(40)]
        text = plain(view.guard_table(rows, view.src_markup("x, Nov. 5, 2026")))
        self.assertIn("file 39", text)


def ideas_screen(book=None, levels=None, states=None):
    """The real Ideas screen through the real app. A book stands in for the Journal, so the filters can be driven on lines the real Journal does not have yet."""
    from streamlit.testing.v1 import AppTest

    page = AppTest.from_file(str(HERE / "app.py"), default_timeout=60).run()
    page.switch_page("screens/ideas.py")
    if book is None:
        page.run()
    else:
        with mock.patch.object(data, "journal_alerts", lambda: book):
            page.run()
            if levels:
                page.multiselect[0].set_value(levels).run()
            if states:
                page.multiselect[3].set_value(states).run()
    assert not page.exception, list(page.exception)
    return page


class IdeasScreenThroughTheApp(unittest.TestCase):
    def test_the_real_screen_has_no_bare_figure(self):
        page = ideas_screen()
        self.assertEqual([b for h in body_of(page) for b in bare_figures(h, strict=True)], [])

    def test_a_broken_copy_fails_the_check(self):
        good = view.alerts_summary([], 3, "Nov. 4, 2026")
        self.assertEqual(bare_figures(good, strict=True), [])
        self.assertTrue(bare_figures(good.replace("Nov. 4, 2026", "today"), strict=True))
        self.assertTrue(bare_figures(view.stage_strip({"stages": {s: [] for s in view.STAGE_ORDER}}, "Nov. 4, 2026").replace("Nov. 4, 2026", "today"), strict=True))
        stripped = view.rejection_table(data.rejection_log()["rows"], "", sits_at=False)
        self.assertTrue(bare_figures(re.sub(r"<cite>.*?</cite>", "", stripped), strict=True))

    def test_the_order_is_ideas_then_the_log_then_alerts(self):
        page = ideas_screen()
        heads = [h.value for h in page.header]
        self.assertLess(heads.index("Ideas, from the first lead to a decision"), heads.index("Rejection log"))
        self.assertLess(heads.index("Rejection log"), heads.index("Alerts"))
        self.assertEqual([h.value.split(":")[0] for h in page.subheader][:9], [view.STAGE_WORDS[s][0] for s in data.STAGES])

    def test_filters_change_only_the_table_through_the_app(self):
        book = {"alerts": [alert("2026-11-03", "Red", "R1", "The red line."), alert("2026-11-02", "Orange", "O2", "The orange line.")], "rulings": [ruled("2026-11-03", "R1", words="My ruling words.")], "last_run": {}, "days_read": 2}
        text = plain(" ".join(body_of(ideas_screen(book))))
        self.assertIn("The red line.", text)
        self.assertIn("The orange line.", text)
        self.assertIn("My ruling words.", text)
        self.assertIn("Showing 2 of 2 lines.", text)
        text = plain(" ".join(body_of(ideas_screen(book, levels=["Red"]))))
        self.assertIn("The red line.", text)
        self.assertNotIn("The orange line.", text)
        self.assertIn("Showing 1 of 2 lines. These filters leave out 1 Orange still waiting.", text)
        text = plain(" ".join(body_of(ideas_screen(book, levels=["Red"], states=["Waiting"]))))
        self.assertIn("No line fits these filters.", text)

    def test_the_date_filters_work_through_the_app(self):
        from streamlit.testing.v1 import AppTest

        book = {"alerts": [alert("2026-11-03", "Red", "R1", "The red line."), alert("2026-11-02", "Orange", "O2", "The orange line.")], "rulings": [], "last_run": {}, "days_read": 2}
        page = AppTest.from_file(str(HERE / "app.py"), default_timeout=60).run()
        page.switch_page("screens/ideas.py")
        with mock.patch.object(data, "journal_alerts", lambda: book):
            page.run()
            page.date_input[0].set_value(dt.date(2026, 11, 3)).run()
            self.assertNotIn("The orange line.", plain(" ".join(body_of(page))))
            page.date_input[0].set_value(None).run()
            page.date_input[1].set_value(dt.date(2026, 11, 2)).run()
            text = plain(" ".join(body_of(page)))
        self.assertIn("The orange line.", text)
        self.assertNotIn("The red line.", text)
        self.assertIn("leave out 1 Red still waiting", text)

    def test_copied_words_are_really_in_the_vault(self):
        files = [p for folder in ("Research", "Journal", "Journal/decisions", "Companies", "Inbox") for p in (ROOT / folder).glob("*.md")]
        source = source_words(" ".join(p.read_text() for p in files)) + " " + source_words(" ".join(json.dumps(data.latest_radar()["leads_line"]).split()))
        missing = []
        for markup in body_of(ideas_screen()):
            for node in inside(parse(markup), lambda n: "d-copied" in n["classes"]):
                words = " ".join(flat(node).split())
                if words and words not in source:
                    missing.append(words[:120])
        self.assertEqual(missing, [])


class JournalReaders(unittest.TestCase):
    DAY = """# 2026-11-05

**We decided not to buy [[Made Co]] today.**

## Why

- A reason.

---

## Session: first

### What we did

- Did a thing.

### What we decided

- Kept it, for $5.00 ([10-Q, filed Oct. 1, 2026](https://www.sec.gov/x)).
  - A nested reason.

### What we left open

- **For me:** one question.
- For me to approve: another.
- Claude's choices, for me to correct: not mine to ask.
Also open:
- nothing

---

Correction to the session above: a note, not an open item.

---

## Session: second

### What we did

- Nothing new.

### What we decided

- Nothing.

### What we left open

- Nothing new.
"""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.journal, self.lessons = self.root / "Journal", self.root / "Lessons"
        (self.journal / "decisions").mkdir(parents=True)
        self.lessons.mkdir()
        (self.journal / "2026-11-05.md").write_text(self.DAY)
        (self.journal / "README.md").write_text("Not a day.")
        self.model = data.journal_view(self.journal)

    def test_a_day_is_split_as_written_with_nothing_dropped(self):
        day = self.model["days"][0]
        self.assertEqual([s["heading"] for s in day["sessions"]], ["Why", "Session: first", "Session: second"])
        self.assertEqual(day["top"], "**We decided not to buy [[Made Co]] today.**")
        self.assertIn("Correction to the session above", day["sessions"][1]["text"])
        self.assertNotIn("---", day["sessions"][1]["text"])
        self.assertEqual(len(self.model["days"]), 1)

    def test_the_first_decision_counts_though_no_heading_names_it(self):
        self.assertIn("**We decided not to buy [[Made Co]] today.**", [i["text"] for i in self.model["decided"]])

    def test_a_nested_line_stays_with_its_parent_and_a_lone_nothing_is_counted_not_shown(self):
        kept = next(i for i in self.model["decided"] if i["text"].startswith("Kept it"))
        self.assertEqual(kept["text"].split("\n")[1], "- A nested reason.")
        self.assertEqual(self.model["quiet"], {"decided": 1, "left_open": 2})

    def test_a_note_after_the_rule_is_not_an_open_item(self):
        words = [i["text"] for i in self.model["left_open"]]
        self.assertFalse([w for w in words if "Correction" in w])
        (self.journal / "2026-11-05.md").write_text("# 2026-11-05\n\n## Session: x\n\n### What we left open\n\n- Real item.\nCorrection to the session above: a note.\n- Update to the session above: another.\n")
        self.assertEqual([i["text"] for i in data.journal_view(self.journal)["left_open"]], ["Real item."])
        self.assertIn("Also open:", words)

    def test_for_me_means_the_line_starts_with_it(self):
        self.assertEqual([i["text"][:20] for i in self.model["left_open"] if i["for_me"]], ["**For me:** one ques", "For me to approve: a"])

    def test_the_newest_session_comes_first(self):
        markup = view.journal_day_blocks(self.model["days"][0])
        self.assertLess(markup.index("Session: second"), markup.index("Session: first"))
        self.assertIn("Top of the day", markup[markup.index("Why"):])

    def test_a_file_that_cannot_be_read_is_named_and_the_rest_still_shows(self):
        (self.journal / "2026-11-06.md").write_bytes(b"\xff\xfe\xff")
        model = data.journal_view(self.journal)
        self.assertEqual([d["day"] for d in model["days"]], ["2026-11-05"])
        self.assertIn("2026-11-06.md could not be read", model["problems"][0])
        self.assertIn("would fill", model["problems"][0])
        self.assertIn("2026-11-06.md", data.search_journal("kept", self.journal, self.lessons)["problems"][0])

    def test_no_journal_reads_as_empty_not_as_a_crash(self):
        model = data.journal_view(self.root / "None")
        self.assertEqual((model["days"], model["decided"], model["left_open"]), ([], [], []))

    def test_nothing_from_a_file_reaches_the_browser_raw(self):
        bad = """# 2026-11-05

## Session: <script>alert(1)</script>

### What we left open

- <img src=https://evil.example/x.png> ![a](https://evil.example/y.png) [b](javascript:alert(2))
"""
        (self.journal / "2026-11-05.md").write_text(bad)
        model = data.journal_view(self.journal)
        for markup in (view.journal_day_blocks(model["days"][0]), view.journal_items_table(model["left_open"]), view.search_table(data.search_journal("evil", self.journal, self.lessons)["rows"], TODAY)):
            self.assertNotIn("<script", markup)
            self.assertNotIn("<img", markup)
            self.assertNotIn('href="javascript', markup)
        self.assertNotIn("<script", view.journal_day_blocks(model["days"][0]).replace("&lt;script", ""))

    def test_search_is_plain_text_in_any_case(self):
        (self.lessons / "A lesson.md").write_text('---\nstatus: researching\nlast checked: "2026-11-03"\n---\n\n# A lesson\n\n*Written 2026-11-04.*\n\nKept (it) [x].\n')
        find = lambda w: data.search_journal(w, self.journal, self.lessons)["rows"]  # noqa: E731
        self.assertEqual(find("   "), [])
        self.assertEqual([r["file"] for r in find("KEPT")], ["Journal/2026-11-05.md", "Lessons/A lesson.md"])
        self.assertEqual(find("(it) [x]")[0]["day"], "2026-11-04")
        self.assertEqual(find("k.pt"), [])  # no pattern: not one line holds these four characters
        self.assertEqual(len(find("[x]")), 1)
        self.assertEqual(find("researching"), [])  # a field block is not a lesson's words
        row = find("one question")[0]
        self.assertEqual((row["where"], row["line"], row["text"]), ("Session: first", self.DAY.splitlines().index("- **For me:** one question.") + 1, "**For me:** one question."))
        self.assertEqual(find("kept   for"), [])
        self.assertEqual(len(find("kept it, for $5")), 1)

    def test_search_never_reads_a_coach_file(self):
        (self.journal / "decisions" / "2026-11-03 Made Co.md").write_text(coach_file())
        self.assertEqual(data.search_journal("SYSTEM-VIEW-SECRET", self.journal, self.lessons)["rows"], [])

    def test_decisions_show_my_words_and_never_the_systems_view(self):
        (self.journal / "decisions" / "2026-11-03 Made Co.md").write_text(coach_file())
        files = data.decision_files(self.journal)
        self.assertEqual(files[0]["stage"], "compared")
        markup = view.decisions_table(files)
        self.assertNotIn("SYSTEM-VIEW-SECRET", markup)
        self.assertIn("Not said yet", markup)
        self.assertIn("would fill", markup)
        self.assertEqual(bare_figures(markup), [])

    def test_a_lesson_with_no_date_says_so_and_never_lends_one(self):
        (self.lessons / "No date.md").write_text("# No date\n\nSome words.\n")
        (self.lessons / "Dated.md").write_text('---\nlast checked: "2026-11-03"\n---\n\n# Dated\n\nSome 2020 words, $5.00.\n')
        rows = data.lesson_files(self.lessons)["lessons"]
        self.assertEqual([(r["title"], r["day"]) for r in rows], [("Dated", "2026-11-03"), ("No date", None)])
        markup = view.lesson_blocks(rows, TODAY)
        self.assertIn("undated, retrieved Nov. 5, 2026", plain(markup))
        self.assertEqual(bare_figures(markup), [])

    def test_a_figure_with_no_source_fails_on_a_broken_copy(self):
        good = view.journal_day_blocks(self.model["days"][0])
        self.assertEqual(bare_figures(good), [])
        self.assertTrue(bare_figures(re.sub(r'<small class="d-src".*?</small>', "", good)))

    def test_the_version_is_one_and_unknown_stays_unknown(self):
        self.assertEqual(data.board_version(), "1")
        self.assertIn("board v{VERSION}", (HERE / "app.py").read_text())
        self.assertIsNone(data.board_version(self.root / "None"))


class JournalScreen(unittest.TestCase):
    """The real Journal screen through the real app, on the real files, in every part and on every day."""

    @classmethod
    def setUpClass(cls):
        from streamlit.testing.v1 import AppTest

        cls.pages = {}
        page = AppTest.from_file(str(HERE / "app.py"), default_timeout=120).run()
        page.switch_page("screens/journal.py").run()
        cls.first = list(page.radio[0].options)
        for part in view.JOURNAL_PARTS:
            page.radio[0].set_value(part).run()
            if part == "Search":
                page.text_input[0].set_value("Corning").run()
            assert not page.exception, (part, list(page.exception))
            cls.pages[part] = (body_of(page), bare_labels(page))
        page.radio[0].set_value("By day").run()
        for day in [d["day"] for d in data.journal_view()["days"]]:
            page.selectbox[0].set_value(day).run()
            assert page.selectbox[0].value == day
            assert not page.exception, (day, list(page.exception))
            cls.pages[f"By day {day}"] = (body_of(page), bare_labels(page))
        page.radio[0].set_value("What we left open").run()
        page.checkbox[0].set_value(True).run()
        cls.pages["For me"] = (body_of(page), bare_labels(page))

    def test_the_parts_are_the_plans(self):
        self.assertEqual(self.first, ["By day", "What we decided", "What we left open", "Decisions", "Lessons", "Search"])
        self.assertGreaterEqual(len(self.pages), 10)

    def test_every_figure_has_a_source_and_every_gap_says_what_fills_it(self):
        for name, (bodies, labels) in self.pages.items():
            markup = "".join(bodies)
            self.assertEqual(bare_figures(markup), [], name)
            self.assertEqual(missing_with_no_fill(markup), [], name)
            self.assertEqual(labels, [], name)

    def test_its_own_words_give_no_view_and_raise_nothing(self):
        for name, (bodies, _) in self.pages.items():
            text = html.unescape(plain(own_words("".join(bodies))))
            self.assertIsNone(VIEW_WORDS.search(text), (name, VIEW_WORDS.search(text)))
            self.assertIsNone(ALERT_WORDS.search(text), (name, ALERT_WORDS.search(text)))

    def test_copied_words_are_really_in_the_files(self):
        files = [p for folder in ("Journal", "Journal/decisions", "Lessons") for p in (ROOT / folder).glob("*.md")]
        source = source_words(" ".join(p.read_text() for p in files))
        for name, (bodies, _) in self.pages.items():
            for markup in bodies:
                for node in inside(parse(markup), lambda n: "d-copied" in n["classes"]):
                    words = " ".join(flat(node).replace("*", "").split())  # source_words takes every star out, and a cron line in the Journal keeps its own
                    self.assertTrue(not words or words in source, (name, words[:120]))

    def test_no_line_carries_a_tag_it_could_never_lose(self):
        for name, (bodies, _) in self.pages.items():
            self.assertNotIn('class="d-nosrc"', "".join(bodies), name)

    def test_the_real_systems_view_is_on_no_part(self):
        text = (ROOT / "Journal/decisions/2026-11-03 Corning.md").read_text()
        secret = re.search(r"\*\*Corning: no position\. Size: \$0, 0% of the portfolio\.\*\*", text)
        self.assertTrue(secret)
        words = plain("".join(self.pages["Decisions"][0]))
        self.assertNotIn("The system's view", words.replace("A decision file's system view", ""))
        self.assertNotIn("Size: $0, 0% of the portfolio", words)
        self.assertIn("No position", words)
        self.assertIn("Yes, I would still want no position.", words)
        rows = inside(parse("".join(self.pages["Decisions"][0])), lambda n: n["tag"] == "tr")
        marked = {"Demo portfolio" in flat(r): "Paper, made-up money" in flat(r) for r in rows if "Journal/decisions" in flat(r)}
        self.assertEqual(marked, {True: True, False: False})

    def test_the_for_me_filter_narrows_the_list(self):
        all_rows = "".join(self.pages["What we left open"][0]).count("<tr>")
        mine = "".join(self.pages["For me"][0]).count("<tr>")
        self.assertLess(mine, all_rows)
        self.assertEqual(mine - 1, sum(i["for_me"] for i in data.journal_view()["left_open"]))
        self.assertIn("no closed mark", plain("".join(self.pages["For me"][0])))

    def test_every_session_of_the_longest_day_is_folded_under_its_heading(self):
        day = next(d for d in data.journal_view()["days"] if d["day"] == "2026-11-03")
        markup = "".join(self.pages["By day 2026-11-03"][0])
        self.assertEqual(markup.count("<details"), len(day["sessions"]) + bool(day["top"]))
        self.assertIn(f'{len(day["sessions"]) + bool(day["top"])} blocks on this day', plain(markup))
        self.assertEqual(markup.count("<details class=\"j-fold d-fig\" open"), bool(day["top"]))  # only the lines above the first heading stand open

    def test_search_counts_what_it_does_not_show(self):
        total = len(data.search_journal("Corning")["rows"])
        self.assertGreater(total, view.SEARCH_ROWS)
        markup = "".join(self.pages["Search"][0])
        self.assertIn(f"Showing {view.SEARCH_ROWS} of {total} lines", plain(markup))
        self.assertEqual(markup.count("<tr>") - 1, view.SEARCH_ROWS)

    def test_an_address_picks_the_day_and_a_wrong_one_says_so(self):
        from streamlit.testing.v1 import AppTest

        page = AppTest.from_file(str(HERE / "app.py"), default_timeout=60).run()
        page.switch_page("screens/journal.py")
        page.query_params["day"] = "2026-11-02"
        page.run()
        self.assertEqual(page.selectbox[0].value, "2026-11-02")
        self.assertIn("/journal?day=2026-11-02", view.journal_items_table([{"day": "2026-11-02", "file": "Journal/2026-11-02.md", "session": "S", "text": "T", "refs": {}, "for_me": False}]))
        page.query_params["day"] = "<script>"
        page.run()
        self.assertEqual(page.selectbox[0].value, data.journal_view()["days"][0]["day"])
        self.assertIn("names no day", plain(" ".join(body_of(page))))
        self.assertNotIn("<script>", " ".join(body_of(page)))


if __name__ == "__main__":
    unittest.main(verbosity=1)
