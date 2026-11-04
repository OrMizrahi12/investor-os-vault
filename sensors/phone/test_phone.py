"""Tests for the phone sender. A fake Telegram on this computer, so nothing leaves it. Run: .venv/bin/python sensors/phone/test_phone.py"""
import contextlib
import http.server
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "sensors/daily"), str(ROOT / "sensors/hunt"), str(ROOT / "sensors/radar"), str(ROOT / "sensors/edgar"), str(ROOT / "sensors/prices")]
import phone  # noqa: E402

TOKEN = "123456" + "789:" + ("FAKEtokenFORtestsONLY" * 2)[:35]  # built in parts, so this file never looks like it holds a token
A1, A2 = "0000024741-26-000999", "0001730168-25-005318"


class Fake(http.server.BaseHTTPRequestHandler):
    sent, fail = [], None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(length).decode())
        if Fake.fail:
            self.send_response(Fake.fail)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "description": f"bad url /bot{TOKEN}/x"}).encode())
            return
        Fake.sent.append(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "result": {"message_id": 1}}).encode())

    def log_message(self, *args):
        pass


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.api = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Fake.sent, Fake.fail = [], None
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "vault"
        (self.root / "sensors/daily/runs").mkdir(parents=True)
        (self.root / "sensors/hunt/runs").mkdir(parents=True)
        (self.root / "Journal").mkdir()
        self.secret = Path(self.tmp.name) / "home/telegram.env"
        phone.write_secret(TOKEN, 42, self.secret, self.root)

    def daily(self, brief, briefed=True, items=(), stem="2026-11-04-01"):
        runs = self.root / "sensors/daily/runs"
        (runs / f"{stem}.brief.md").write_text(brief)
        (runs / f"{stem}.json").write_text(json.dumps({"today": "2026-11-04", "briefed": briefed, "brief_path": f"sensors/daily/runs/{stem}.brief.md", "items": list(items)}))

    def event(self, report, replay=False, name="events-2026-11-04"):
        run = self.root / "sensors/hunt/runs" / name
        run.mkdir()
        (run / "report.md").write_text(report)
        (run / "order.json").write_text(json.dumps({"replay": replay}))

    def go(self, **kw):
        return phone.send_pass(self.root, self.secret, self.api, **kw)

    def texts(self):
        return [m["text"][0] for m in Fake.sent]


BRIEF = f"### Red\n\n- Corning, R3, {A1}, [8-K, filed Nov. 4, 2026](https://sec.gov/x).\n\n### Orange\n\n- Orange line, 0000024741-26-000111.\n\n### Info\n\n- Info line.\n"
REPORT = f'# Event run\n\n## Red\n\n- **Corning, R3.** A credit agreement ended. "..." ([8-K, filed Nov. 4, 2026](https://sec.gov/y), {A2}; link: x)\n- **Meta, R3.** The same filing reaches Meta. ([8-K](https://sec.gov/y), {A2})\n\n## Orange\n\n- **Corning, O2.** An Orange. (0001111111-26-000001)\n\n## Info\n\n- Nothing.\n\n## Who was checked\n\n- Problem: none\n'


class RedOnly(Base):
    def test_red_goes_and_nothing_else(self):
        self.daily(BRIEF)
        self.assertEqual(self.go()["sent"], 1)
        text = self.texts()[0]
        self.assertTrue(text.startswith("RED ALERT"))
        self.assertIn(A1, text)
        self.assertNotIn("Orange", text)
        self.assertNotIn("Info line", text)

    def test_only_nothing_sends_nothing_and_touches_no_network(self):
        self.daily("### Red\n\n- Nothing.\n\n### Orange\n\n- O, 0000024741-26-000111.\n\n### Info\n\n- I.\n")
        with mock.patch.object(phone, "call", side_effect=AssertionError("network")), mock.patch.object(phone, "read_secret", side_effect=AssertionError("secret")):
            self.assertEqual(self.go(), {"sent": 0, "waiting": 0, "error": None})

    def test_event_report_red_only_one_alert_for_one_filing(self):
        self.event(REPORT)
        self.assertEqual(self.go()["sent"], 1)
        text = self.texts()[0]
        self.assertIn("Corning, R3", text)
        self.assertIn("Meta, R3", text)
        self.assertNotIn("O2", text)
        self.assertNotIn("Problem", text)

    def test_replay_never_goes(self):
        self.event(REPORT, replay=True)
        self.assertEqual(self.go()["sent"], 0)
        self.assertEqual(Fake.sent, [])

    def test_alert_text_has_no_markdown(self):
        self.daily(BRIEF)
        self.go()
        self.assertIn("8-K, filed Nov. 4, 2026: https://sec.gov/x", self.texts()[0])

    def test_long_line_is_cut_under_telegrams_limit(self):
        self.daily(f"### Red\n\n- {'long words ' * 900} {A1}\n\n### Orange\n\n### Info\n")
        self.go()
        self.assertLess(len(self.texts()[0]), 4096)


class RealFormats(Base):
    """The lines the runs really write, from their saved samples."""

    def test_saved_event_report_gives_its_reds_and_no_orange(self):
        report = (ROOT / "sensors/hunt/samples/replay-3/report.md").read_text()
        reds = phone.red_lines(report)
        filings = {k for x in reds for k in phone.keys_of(x)}
        self.assertEqual(len(filings), 3)  # the three 1.02s of Rules/alerts.md, decision 2 of Nov. 4, 2026
        self.event(report)
        self.assertEqual(self.go()["sent"], 3)
        self.assertEqual(self.go()["sent"], 0)
        self.assertFalse(any("O2" in t or "I8" in t for t in self.texts()))

    def test_saved_event_report_with_no_red_sends_nothing(self):
        self.event((ROOT / "sensors/hunt/samples/replay-1/report.md").read_text())
        self.assertEqual(self.go()["sent"], 0)

    def test_saved_daily_samples_with_no_red_send_nothing(self):
        self.daily((ROOT / "sensors/daily/samples/busy.md").read_text())
        self.assertEqual(self.go()["sent"], 0)

    def test_a_quartr_address_is_not_taken_for_a_token(self):
        self.assertFalse(phone.TOKEN_SHAPE.search(b"news/urn:live_audio:quartr.com:" + b"123456:" + b"a" * 40))


class EachOnce(Base):
    def test_second_pass_sends_nothing(self):
        self.daily(BRIEF)
        self.assertEqual(self.go()["sent"], 1)
        self.assertEqual(self.go()["sent"], 0)
        self.assertEqual(len(Fake.sent), 1)

    def test_same_filing_in_both_runs_is_one_alert(self):
        self.daily(BRIEF)
        self.event(f"## Red\n\n- **Corning, R3.** Again. ([8-K](https://sec.gov/x), {A1})\n\n## Orange\n\n- Nothing.\n")
        self.assertEqual(self.go()["sent"], 1)

    def test_dashed_and_plain_accession_are_one(self):
        self.daily(BRIEF)
        self.go()
        self.event(f'## Red\n\n- **Corning, R3.** ([8-K](https://sec.gov/{A1.replace("-", "")}/d.htm))\n\n## Orange\n\n- Nothing.\n')
        self.assertEqual(self.go()["sent"], 0)

    def test_new_filing_still_goes_after_an_old_one(self):
        self.daily(BRIEF)
        self.go()
        self.event(REPORT)
        self.assertEqual(self.go()["sent"], 1)
        self.assertEqual(len(Fake.sent), 2)


class Failing(Base):
    def test_failed_send_is_kept_retried_once_and_written_down(self):
        self.daily(BRIEF)
        Fake.fail = 500
        out = self.go()
        self.assertEqual((out["sent"], out["waiting"]), (0, 1))
        self.assertIn("Phone send FAILED, O16", next((self.root / "Journal").glob("*.md")).read_text())
        self.go()
        self.assertEqual(next((self.root / "Journal").glob("*.md")).read_text().count("Phone send FAILED"), 1)
        Fake.fail = None
        self.assertEqual(self.go()["sent"], 1)
        self.assertEqual(self.go()["sent"], 0)

    def test_no_token_file_keeps_the_red_waiting(self):
        self.daily(BRIEF)
        self.secret.unlink()
        out = self.go()
        self.assertEqual((out["sent"], out["waiting"]), (0, 1))
        self.assertIn("No bot set up", out["error"])

    def test_scratch_copy_never_reaches_the_phone(self):
        copy = Path(self.tmp.name) / "scratch"
        (copy / "sensors/daily/runs").mkdir(parents=True)
        runs = copy / "sensors/daily/runs"
        (runs / "x.brief.md").write_text(BRIEF)
        (runs / "x.json").write_text(json.dumps({"today": "2026-11-04", "briefed": True, "brief_path": "sensors/daily/runs/x.brief.md", "items": []}))
        out = phone.send_pass(copy, self.secret, self.api)
        self.assertEqual(Fake.sent, [])
        self.assertIn("not the vault", out["error"])

    def test_dead_run_sends_presumed_red_only_after_the_wait(self):
        item = {"id": A1, "level": "Red", "rule": "R3", "form": "8-K", "filed": "2026-11-04", "url": "https://sec.gov/z", "company": "Corning", "items": ["1.03"]}
        orange = {"id": "0000024741-26-000222", "level": "Orange", "rule": "O3", "items": ["3.02"]}
        self.daily("", briefed=False, items=[item, orange])
        path = self.root / "sensors/daily/runs/2026-11-04-01.json"
        self.assertEqual(self.go(now=path.stat().st_mtime + 60)["sent"], 0)
        self.assertEqual(self.go(now=path.stat().st_mtime + 3 * 3600)["sent"], 1)
        self.assertIn("not read", self.texts()[0])
        self.assertNotIn("000222", self.texts()[0])


class TokenStaysOut(Base):
    def captured(self, fn):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            fn()
        return out.getvalue()

    def test_an_error_echoing_the_token_is_scrubbed_everywhere(self):
        self.daily(BRIEF)
        Fake.fail = 401
        text = self.captured(lambda: phone.after_run(self.root, self.secret, self.api))
        self.assertIn("401", text)
        self.assertNotIn(TOKEN, text)
        self.assertNotIn(TOKEN, next((self.root / "Journal").glob("*.md")).read_text())

    def test_nothing_written_holds_it(self):
        self.daily(BRIEF)
        self.captured(lambda: phone.after_run(self.root, self.secret, self.api))
        self.assertEqual(phone.scan_vault(self.root, self.secret), [])

    def test_a_line_holding_a_token_shape_is_cut_from_the_message(self):
        self.daily(f"### Red\n\n- A filing, {A1}, odd text {TOKEN}.\n\n### Orange\n\n### Info\n")
        self.go()
        self.assertNotIn(TOKEN, self.texts()[0])

    def test_token_file_is_private_and_refused_inside_the_vault(self):
        self.assertEqual(self.secret.stat().st_mode & 0o077, 0)
        with self.assertRaises(phone.PhoneError):
            phone.write_secret(TOKEN, 42, self.root / "Journal/telegram.env", self.root)

    def test_loose_file_is_refused(self):
        os.chmod(self.secret, 0o644)
        with self.assertRaises(phone.PhoneError) as caught:
            phone.read_secret(self.secret, self.root)
        self.assertNotIn(TOKEN, str(caught.exception))

    def test_check_finds_a_planted_token_and_names_only_the_file(self):
        (self.root / "Journal/leak.md").write_text(f"oops {TOKEN}\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = phone.check(self.root, self.secret, outside=[])
        self.assertEqual(code, 1)
        self.assertIn("leak.md", out.getvalue())
        self.assertNotIn(TOKEN, out.getvalue())

    def test_check_finds_it_in_a_transcript_too(self):
        place = Path(self.tmp.name) / "projects"
        place.mkdir()
        (place / "t.jsonl").write_text(f'{{"text": "{TOKEN}"}}\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(phone.check(self.root, self.secret, outside=[place]), 1)

    def test_setup_refuses_without_a_terminal(self):
        with mock.patch.object(sys.stdin, "isatty", return_value=False), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(phone.setup(self.secret), 2)

    def test_the_real_vault_has_no_token_shape_and_the_token_file_is_outside(self):
        self.assertEqual(phone.scan_vault(ROOT, phone.SECRET), [])
        self.assertFalse(phone.SECRET.is_relative_to(ROOT))


class MadeUpRed(Base):
    def test_the_made_up_red_is_marked_goes_once_and_leaves_no_trace(self):
        journal_before = sorted(p.name for p in (ROOT / "Journal").glob("*.md"))
        sent_before = phone.load_sent(ROOT)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(phone.run_test(self.secret, self.api), 0)
        self.assertEqual(len(Fake.sent), 1)
        text = self.texts()[0]
        self.assertIn("TEST ONLY. NOT A REAL ALERT", text)
        self.assertNotIn("must not be sent", text)
        self.assertEqual(sent_before, phone.load_sent(ROOT))
        self.assertEqual(journal_before, sorted(p.name for p in (ROOT / "Journal").glob("*.md")))


class Page(unittest.TestCase):
    """Works the counts out again from the saved files, sharing no code with draw.py."""

    def test_counts(self):
        page = (ROOT / "phone.html").read_text()
        y2 = json.loads((ROOT / "sensors/hunt/samples/two-years-102.json").read_text())
        y1 = json.loads((ROOT / "sensors/hunt/samples/two-years.json").read_text())
        red = sum(1 for r in y2 if r["alone"] and r["company"] != "Corning")
        event = sum(1 for r in y1 if r["company"] not in ("Corning", "Linde"))
        self.assertEqual((red, event), (3, 52))
        total = 27 + 401 + red + event
        self.assertEqual(total, 483)
        self.assertIn(f"{red / 24:.3f}", page)
        self.assertIn(f"{total / 24:.1f}", page)
        self.assertEqual(page.count("<circle"), red + total)
        self.assertNotRegex(page, r"<script[^>]+src=")
        self.assertFalse(phone.TOKEN_SHAPE.search(page.encode()))


class Wiring(unittest.TestCase):
    """The two runs call the sender at their end, and a phone failure cannot stop them."""

    def test_publish_main_calls_it(self):
        import publish
        with mock.patch.object(publish, "publish", return_value={"journal": "J", "line": None, "filed": []}), mock.patch("phone.after_run") as after, contextlib.redirect_stdout(io.StringIO()):
            publish.main()
        after.assert_called_once()

    def test_events_finish_calls_it_only_when_finished(self):
        import events
        with mock.patch.object(events, "finish", return_value=0), mock.patch.object(sys, "argv", ["events.py", "finish"]), mock.patch("phone.after_run") as after:
            self.assertEqual(events.main(), 0)
        after.assert_called_once()
        with mock.patch.object(events, "finish", return_value=1), mock.patch.object(sys, "argv", ["events.py", "finish"]), mock.patch("phone.after_run") as after:
            self.assertEqual(events.main(), 1)
        after.assert_not_called()

    def test_a_broken_send_does_not_stop_a_run(self):
        with mock.patch.object(phone, "send_pass", side_effect=RuntimeError("boom " + TOKEN)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                phone.after_run()
        self.assertNotIn(TOKEN, out.getvalue())
        self.assertIn("RuntimeError", out.getvalue())

    def test_the_prompts_did_not_change_so_no_task_needs_pasting(self):
        for name in ("Daily run", "Event run"):
            text = (ROOT / "Playbooks" / f"{name}.md").read_text()
            prompt = re.search(r"```text\n(.*?)\n```", text, re.S).group(1)
            self.assertNotIn("phone", prompt.lower())


if __name__ == "__main__":
    unittest.main()
