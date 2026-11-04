"""Checks parts.html without using model.py or draw.py. Inputs come from the saved filings and typed sums. No network.

    .venv/bin/python sensors/parts/test_parts.py
"""

import html
import re
import statistics as st
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "sensors/edgar/cache/CIK0000024741/documents"
PAGE = (ROOT / "parts.html").read_text()
TEXT = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", PAGE.split("<script>")[0])))


def flat(name):
    t = re.sub(r"<[^>]+>", " ", (DOCS / name).read_text(errors="ignore"))
    t = re.sub(r"[\s$|]+", " ", html.unescape(t).replace("\xa0", " "))
    return re.sub(r"\( ?([\d,.]+) ?\)", r"(\1)", t).replace(" %", "%")


class Filings(unittest.TestCase):
    """The typed inputs appear in the printed filings."""

    def test_q10(self):
        t = flat("glw-20260930.htm")
        for s in ["Segment net sales 6,297 4,389 1,378 1,244 13,308 856 14,164",
                  "Segment net income (loss) 1,357 1,006 219 (7) 2,575 (73) 2,502",
                  "Operating income 911 589 2,248 1,607", "Income before income taxes 968 550 2,146 1,374",
                  "Net income attributable to non-controlling interest (66) (40) (153) (99)"]:
            self.assertTrue(s in t, s)

    def test_k25(self):
        t = flat("glw-20251231.htm")
        for s in ["Segment net income (loss) 1,048 993 367 278 61 (26) 2,721", "Income tax provision (4) 304 259 98 74 16 7 758",
                  "Operating income 2,279 1,135 890", "Impact of constant-currency reporting (665) (989) (744)",
                  "Net income attributable to non-controlling interest (146) (86) (67)", "Other corporate items (175) (272) (140)"]:
            self.assertTrue(s in t, s)
        self.assertTrue("carrying value of precious metals was 2.8 billion" in t)
        self.assertTrue("NGK Insulators, Ltd., Ibiden Co., Ltd., AGC Inc. and LENS" in t)

    def test_q1_release_q4_column(self):
        t = flat("0000024741-26-000198-glw-20260328xex991xq12026.htm")
        for s in ["Net Income 387 305 201", "Net Income 324 356 317", "Net Income 70 63 68", "Net Income 7 30 27"]:
            self.assertTrue(s in t, s)


class Sum(unittest.TestCase):
    """Recomputes the result by hand."""

    @classmethod
    def setUpClass(cls):
        old = {p["name"]: p for p in tomllib.loads((ROOT / "sensors/multiples/peers.toml").read_text())["peer"]}
        new = {p["name"]: p for p in tomllib.loads((ROOT / "sensors/parts/peers.toml").read_text())["peer"]}
        opt = st.median(old[n]["ev_ebit"] for n in ["Amphenol", "Fujikura", "Prysmian", "Furukawa Electric", "YOFC (Hong Kong shares)", "STL"])
        cls.optm = opt
        pre = dict(o=1357 + 392 + 305 + 89, g=1006 + 265 + 356 + 93, a=219 + 58 + 63 + 17)
        cls.pre = pre
        v = dict(o=pre["o"] * opt, g=pre["g"] * 13.27, a=pre["a"] * 12.42)
        blended = sum(v.values()) / sum(pre.values())
        cls.blended = blended
        gross = sum(v.values()) + 1719 * 1.46 + 1153 * 2.08
        cls.gross = gross
        corp, yen = (159 + 95 + 169) * blended, (773 - 299) * 13.27
        cls.biz = gross - corp - yen
        cls.eq = cls.biz - 8200 + 2537 - 200 * blended
        # low and high
        lo = pre["o"] * 18.77 + pre["g"] * 12.42 + pre["a"] * 11.95
        bl = lo / sum(pre.values())
        cls.eq_low = lo + 1719 * .81 + 26.11 * 77 - 634 * bl - 474 * 12.42 - 8200 + 2537 - 200 * bl
        hi = pre["o"] * 33.39 + pre["g"] * 18.54 + pre["a"] * 13.20
        bh = hi / sum(pre.values())
        cls.eq_high = hi + 1719 * 3.64 + 1153 * 6.09 - 423 * bh - 474 * 18.54 - 8200 + 2537 - 200 * bh
        cls.need = (112405 - (cls.biz - pre["o"] * opt)) / pre["o"]

    def seen(self, x, what):
        self.assertIn(what.format(x), TEXT)

    def test_words(self):
        self.seen(self.eq_low / 1000, "${:.1f}B to")
        self.seen(self.eq_high / 1000, "to ${:.1f}B for the shares")
        self.seen(self.eq / 1000, "${:.1f}B in the middle")
        self.seen(self.biz / 1000, "${:.1f}B")
        self.seen(self.blended, "blended {:.1f}x")
        self.seen(self.need, "{:.1f}x of its twelve-month profit")

    def test_whole_range_below_market(self):
        self.assertLess(self.eq_high, 106125)

    def test_optical_share_and_width(self):
        self.assertIn(f"Optical is {self.pre['o'] * self.optm / self.gross * 100:.0f}% of the parts", TEXT)
        width = self.pre["o"] * (33.39 - 18.77)
        self.assertIn(f"${width / 1000:.1f}B, is about the same", TEXT)
        rest = self.gross - self.pre["o"] * self.optm
        self.assertIn(f"(${rest / 1000:.1f}B)", TEXT)
        self.assertLess(abs(width - rest) / rest, .05)

    def test_counts(self):
        self.assertEqual(len(tomllib.loads((ROOT / "sensors/parts/peers.toml").read_text())["peer"]), 14)
        self.assertIn("14 more outside pages", TEXT)

    def test_named_figures(self):
        avg = (351 + 469 + 592 + 489 + 366 + 553 + 661 + 478 + 612 + 1048) / 10
        self.assertIn(f"{(1357 + 305) / avg:.1f} times its FY2016 to FY2025 average of ${round(avg)}M", TEXT)
        glass = [953 + 228, 888 + 301, 835 + 313, 786 + 302, 717 + 423, 960 + 371, 769 + 340, 842 + 202, 1006 + 260, 993 + 367]
        self.assertGreater(1362, max(glass))
        self.assertEqual(max(glass), 1360)
        self.assertIn(f"{(532 / 295 - 1) * 100:.0f}% in a year", TEXT)
        for a, b, w in ((153.96, 2160, "AGC 7.1%"), (25.24, 311.77, "Nippon Electric Glass 8.1%"), (137.72, 1050, "Jenoptik 13.1%")):
            self.assertEqual(f"{a / b * 100:.1f}%", w.split()[-1])
            self.assertIn(w, TEXT)
        self.assertEqual(round(77.4 / 484.72 * 100), 16)
        self.assertIn("${:,}M".format(474), TEXT)
        self.assertIn(f"{474 / 1720 * 100:.0f}% of Glass's profit", TEXT)
        self.assertIn(f"{1720 / 5888 * 100:.1f}% for Glass", TEXT)

    def test_ties(self):
        self.assertEqual(18576 - 857, 15629 - 11414 + 13504)
        self.assertEqual(4152 - 773 + 299 + 15 - 5 - 159 - 95 - 235 - 206 - 169, 2052 - 1374 + 2146)


if __name__ == "__main__":
    unittest.main()
