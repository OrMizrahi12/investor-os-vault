"""Checks multiples.html's numbers without using draw.py's sums. No network.

    .venv/bin/python sensors/multiples/test_multiples.py
"""

import html
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import multiples as m

NOTE = (m.ROOT / "Companies/Corning.md").read_text()
PAGE = (m.ROOT / "multiples.html").read_text()
TEXT = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", PAGE.split("<script>")[0])))


def money(text):
    text = text.replace("−", "-").replace("$", "").replace("M", "").replace(",", "")
    return float(text)


class Corning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = m.build()

    def test_year_tables_tie_to_the_note(self):
        rows = {}
        for line in NOTE[NOTE.index("## Cash flow"):NOTE.index("### Capex")].splitlines():
            hit = re.match(r"\| FY(\d{4}) \| (\S+) \| (\S+) \| (\S+) \| (\S+) \|", line)
            if hit:
                rows[int(hit[1])] = [money(x) for x in hit.groups()[1:]]
        self.assertEqual(len(rows), 10)
        for p in self.d["year"]:
            _, ocf, capex, fcf = rows[int(p["date"][:4])]
            self.assertEqual(p["ocf"] / 1e6, ocf, p["date"])
            self.assertEqual(p["capex"] / 1e6, capex, p["date"])
            self.assertEqual(p["fcf"] / 1e6, fcf, p["date"])

    def test_now_ties_by_hand(self):
        t = self.d["today"]
        # Figures typed from the printed 10-K and 10-Q, as in the note, not from SEC's data.
        self.assertAlmostEqual(t["eps"], 1.83 + 1.85 - 1.21)
        self.assertEqual(t["ebit"] / 1e6, 2279 + 2248 - 1607)
        self.assertEqual(t["fcf"] / 1e6, 2461)
        self.assertEqual(t["cash"] / 1e6, 2537)
        self.assertEqual(t["debt"] / 1e6, 8200)
        self.assertEqual(t["nci"] / 1e6, 617)
        self.assertEqual(t["price"], 123.19999694824219)
        cap = 861.401106 * t["price"]
        self.assertAlmostEqual(t["cap"] / 1e6, cap, 2)
        self.assertAlmostEqual(t["ev"] / 1e6, cap + 8200 + 617 - 2537, 2)
        self.assertAlmostEqual(t["ev_ebit"], (cap + 8200 + 617 - 2537) / 2920, 6)
        self.assertAlmostEqual(t["fcfy"], 2461 / cap * 100, 6)

    def test_eps_matches_the_earnings_yield_rule(self):
        mod = m.earnings_module()
        steps = mod.eps_steps(m.load_facts(m.GLW))
        points = self.d["known"] + [self.d["today"]]
        self.assertEqual(len(points), 11)
        for p in points:
            step = [s for s in steps if s["filed"] <= p["date"]][-1]
            self.assertAlmostEqual(step["eps"], p["eps"], 6, p["date"])
            self.assertEqual(step["accession"], p["accession"])

    def test_ten_year_ends(self):
        self.assertEqual([p["date"][:4] for p in self.d["known"]], [str(y) for y in range(2016, 2026)])
        self.assertEqual(self.d["today"]["date"], "2026-11-02")

    def test_loss_is_not_a_multiple(self):
        p = self.d["known"][2]
        self.assertLess(p["eps"], 0)
        self.assertIsNone(p["pe"])
        self.assertEqual(self.d["stats"]["pe"]["n"], 9)
        self.assertEqual(self.d["stats"]["ey"]["n"], 10)

    def test_note_figures_used_in_draw(self):
        for needle in ["$1,505M", "about $1,256M", "about $971M", "Share-based compensation $368M", "finance lease principal $428M",
                       "operating leases of $971M", "pension liabilities of $625M", "contract liabilities of $2,701M", "$442M"]:
            self.assertIn(needle, NOTE, needle)


class Amphenol(unittest.TestCase):
    def test_split_is_handled(self):
        a = m.amphenol(82.28)
        self.assertAlmostEqual(a["eps"], 3.34 / 2 + 1.84 - 1.21)
        self.assertAlmostEqual(a["straight_sum"], 3.97)
        self.assertAlmostEqual(a["pe"], 35.78, 0)  # the outside page's own figure
        self.assertAlmostEqual(a["fcf"] / 1e9, 5.12, 2)
        self.assertAlmostEqual(a["debt"] / 1e9, 17.87, 2)
        self.assertAlmostEqual(a["cash"] / 1e9, 5.30, 2)


class Page(unittest.TestCase):
    def test_words(self):
        # Recomputed here from typed inputs, so a slip in draw.py's sums shows.
        cap = 861.401106 * 123.19999694824219
        for needle in ["49.9x earnings", "38.5x EBIT", "2.32% free cash flow yield", f"{1505 / cap * 100:.2f}% without the filed deposits line",
                       "2.00% earnings yield", "6.12% on Moody's Aaa", "4.94% on the 10-year Treasury",
                       f"{(2.47 / 123.2) * 100:.2f}%", f"{abs(2.0048 - 6.12):.2f} points to Aaa", f"{abs(2.0048 - 4.94):.2f} to the Treasury",
                       f"{123.2 / 3.11:.1f}x", f"{123.2 / 1.77:.1f}x", f"{123.2 / 1.10:.1f}x",
                       f"${861.401106 * 123.2 + 8200 + 617 - 2537:,.0f}M", f"{163.47 / 7.57:.1f}x", f"{2250 / 80.87:.1f}x"]:
            self.assertIn(needle, TEXT, needle)

    def test_no_view(self):
        self.assertIn("No buy or sell view", TEXT)
        self.assertIn("Base value is not defined yet", TEXT)
        self.assertIn("Keep this page on this computer", TEXT)
        for word in ["cheap", "expensive", "overvalued", "undervalued", "bargain", "we recommend"]:
            self.assertNotIn(word, TEXT.lower(), word)

    def test_no_outside_requests(self):
        self.assertEqual(re.findall(r'(?:src|href)="https?://[^"]+\.(?:js|css)', PAGE), [])
        self.assertNotIn("<script src", PAGE)


if __name__ == "__main__":
    unittest.main()
