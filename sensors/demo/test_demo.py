"""Checks demo.html against the saved files, sharing no code with draw.py. Run: .venv/bin/python -I sensors/demo/test_demo.py"""
import html, json, re, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "demo.html").read_text()
TEXT = " ".join(html.unescape(re.sub(r"<style.*?</style>|<[^>]+>", " ", PAGE, flags=re.S)).split())
LOG = (ROOT / "Research/Rejection log.md").read_text()
INP = json.loads((ROOT / "sensors/demo/powell-2026-11-03.json").read_text())["inputs"]


class Demo(unittest.TestCase):
    def test_powell_sums_by_hand(self):
        s, a = 36.604, .0612
        e, c, g = 180.75, 243.96 - (466.36 - 299.5), .03
        mid = .4 * (e / s / .09) + .4 * (c / s * (1 + g) / (.09 - g)) + .2 * (e / s / a)
        self.assertEqual(f"{mid:.2f}", "52.55")
        self.assertEqual(f"{mid / 163.34:.1%}", "32.2%")
        self.assertEqual(f"{mid / .75:.2f}", "70.06")
        self.assertEqual(INP["cash_m"]["mid"]["v"], round(c, 2))

    def test_kodiak_debt_by_hand(self):
        ocf = 599.74 + 170.65 - 291.50
        self.assertEqual(f"{2725.3 / ocf:.1f}", "5.7")
        self.assertEqual(f"{2725.3 / 599.74:.1f}", "4.5")

    def test_every_candidate_is_on_the_page_and_in_the_log(self):
        for name, t in (("Axe Compute", "AGPU"), ("Backblaze", "BLZE"), ("Kodiak Gas Services", "KGS"), ("Kopin", "KOPN"), ("Powell Industries", "POWL")):
            self.assertIn(f"{name} {t}", TEXT)
            self.assertIn(f"{name} ({t})", LOG)

    def test_no_position_on_paper_note(self):
        note = (ROOT / "Portfolio/Paper portfolio.md").read_text()
        self.assertRegex(note, r"(?m)^cash: 100000$")
        rows = note.split("## Positions")[1].split("## Changes")[0]
        self.assertEqual(sum(l.startswith("|") for l in rows.splitlines()), 2)
        self.assertIn("100%", TEXT)

    def test_page_says_lesson_and_loads_nothing_outside(self):
        self.assertIn("not advice", TEXT)
        self.assertNotRegex(PAGE, r"<script|<img|src=|<link")


if __name__ == "__main__":
    unittest.main()
