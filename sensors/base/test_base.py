"""Checks base.html without using model.py or draw.py. Inputs come from the saved filings and typed sums. No network.

    .venv/bin/python sensors/base/test_base.py
"""

import csv
import html
import re
import statistics as st
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "sensors/edgar/cache/CIK0000024741/documents"
PAGE = (ROOT / "base.html").read_text()
BODY = PAGE.split("</style>")[1].split("<script>")[0]
TEXT = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", BODY)))

SH, PX, R, AAA = 871, 123.20, .09, .0612
NI = [1323, 1496, 1270, 783, 133, 1519, 1097, 543, 577, 1543]
EPS = [1.16, 1.47, 1.35, .87, .05, 1.74, 1.28, .63, .66, 1.77]
SALES = [9390, 10116, 11290, 11503, 11303, 14082, 14189, 12588, 13118, 15629]
E_LOW, E_MID = sum(NI) / 10 / SH, 1543 / SH
TTM_NI = 1596 + 1610 - 1056 + (40 - 50 + 0) + (-111 + 47 - 41) + (18 - 11 + 22 - 1 - 12)
E_HIGH = TTM_NI / SH
G_NI = (1543 / 1323) ** (1 / 9) - 1
RD = [971 / SH / R, 1256 / SH * (1 + G_NI) / (R - G_NI), 1505 / SH * 1.03 / (R - .03)]
EARN = [E_LOW / R, E_MID / R, E_HIGH / R]
BOND = [E_LOW / AAA, E_MID / AAA, E_HIGH / AAA]
BASE = [.4 * a + .4 * b + .2 * c for a, b, c in zip(EARN, RD, BOND)]
BUY = BASE[1] / .75
BUY23 = BASE[1] / (2 / 3)


def worth(c, g, r=R, t=.03):
    return sum(c * (1 + g) ** i / (1 + r) ** i for i in range(1, 11)) + c * (1 + g) ** 10 * (1 + t) / (r - t) / (1 + r) ** 10


def need(p, c):
    lo, hi = -.5, 1
    for _ in range(80):
        x = (lo + hi) / 2
        lo, hi = (x, hi) if worth(c, x) < p else (lo, x)
    return lo


def flat(name):
    t = re.sub(r"<[^>]+>", " ", (DOCS / name).read_text(errors="ignore"))
    t = re.sub(r"[\s$|]+", " ", html.unescape(t).replace("\xa0", " "))
    return re.sub(r"\( ?([\d,.]+) ?\)", r"(\1)", t)


def closes():
    with open(ROOT / "sensors/prices/cache/GLW/2026-11-02.csv") as f:
        return [(r["date"], float(r["close"])) for r in csv.DictReader(f)]


class Filings(unittest.TestCase):
    def test_q10_hedges(self):
        t = flat("glw-20260930.htm")
        self.assertIn("Unrealized gain, net 55 41 61 47", t)

    def test_k25_hedges(self):
        t = flat("glw-20251231.htm")
        self.assertIn("Unrealized gain (loss), net 146 111", t)

    def test_release_items(self):
        t = flat("0000024741-26-000273-glw-20261027xex99xq32026.htm")
        for s in ["Translation gain on foreign denominated debt, net (2) (1) 0.00", "Translation loss on foreign denominated debt, net (2) 66 50",
                  "Gain on sale of business (10) (2) (1)", "Gain on sale of assets (11) (16) (12)", "Loss on sale of business (10) 11 7", "Loss on sale of assets (11) 5 4"]:
            self.assertIn(s, t)

    def test_year_end_closes_and_price(self):
        c = dict(closes())
        self.assertAlmostEqual(c["2026-11-02"], PX, places=2)
        self.assertAlmostEqual(c["2025-12-31"], 87.56, places=1)
        self.assertAlmostEqual(c["2016-12-30"], 24.27, places=1)

    def test_aaa(self):
        with open(ROOT / "sensors/macro/downloads/AAA.csv") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(float(rows[-1]["AAA"]), 6.12)


class Words(unittest.TestCase):
    def has(self, s):
        self.assertIn(s, TEXT)

    def test_base(self):
        self.has(f"${BASE[0]:.2f} to ${BASE[2]:.2f}, middle ${BASE[1]:.2f}")
        self.has(f"${round(BASE[0])} to ${round(BASE[2])} a share, ${round(BASE[1])} in the middle")
        self.has(f"it covers {BASE[1] / PX * 100:.0f}% of the price")
        self.has(f"buy-below price ${BUY:.2f}")

    def test_anchors(self):
        self.assertEqual(TTM_NI, 2051)
        self.has(f"{TTM_NI:,} ${E_HIGH:.2f} High")
        self.has(f"${E_LOW:.2f} Low")
        m = sum(NI) / sum(SALES)
        self.has(f"{m * 100:.1f}% on twelve-month sales of $17,719M gives ${m * 17719 / SH:.2f}")
        self.has(f"Owner cash gives ${(4192 - 956 - 965 - 368 - 428 - 165) / SH:.2f}")

    def test_margin(self):
        self.has(f"gap is −{(PX - BASE[1]) / BASE[1] * 100:.0f}%")
        self.has(f"{PX / BASE[1]:.1f} times the base middle")
        self.has(f"fall {(1 - BASE[1] / PX) * 100:.0f}% to reach it")
        self.has(f"still −{(BUY - BASE[1]) / BASE[1] * 100:.0f}%")
        self.has(f"it +{(BASE[2] - BUY) / BASE[2] * 100:.1f}%")
        self.has(f"{(1 - BASE[1] / BUY) * 100:.0f}% to the base middle and {(1 - BASE[0] / BUY) * 100:.0f}% to the low")

    def test_past_tags(self):
        c = [24.27, 31.99, 30.21, 29.11, 36.00, 37.23, 31.94, 30.45, 47.52, 87.56]
        t = [a / b for a, b in zip(c, EPS)]
        self.has(f"{min(t):.1f}x at the lowest, {st.median(t):.1f}x at the median")

    def test_growth(self):
        self.has(f"{need(BUY, 1505 / SH) * 100:.1f}%, under the 3.1%")
        self.has(f"From $1.44 it needs {need(BUY, 1256 / SH) * 100:.1f}%, which only sales reached, at 5.8%")
        self.has(f"Two thirds needs {need(BUY23, 1505 / SH) * 100:.1f}% and {need(BUY23, 1256 / SH) * 100:.1f}%")
        self.has(f"needs {need(PX, 1505 / SH) * 100:.1f}% from $1.73")

    def test_dates(self):
        rows = closes()
        last = [d for d, x in rows if x < BUY][-1]
        self.assertEqual(last, "2023-12-06")
        self.has("last closed under it on Dec. 6, 2023")
        since = [x for d, x in rows if d >= "2016-01-01"]
        self.has(f"spent {sum(x < BUY for x in since) / len(since) * 100:.0f}% of days since 2016")
        self.assertEqual([d for d, x in rows if x < BASE[1]][-1], "2020-05-22")

    def test_peak(self):
        day, top = max(closes(), key=lambda r: r[1])
        self.assertEqual(day, "2026-06-29")
        self.has(f"fallen {(1 - PX / top) * 100:.0f}% from its ${top:.2f} close on June 29, 2026")

    def test_comparisons(self):
        self.assertLess(BUY, BASE[2])
        self.assertGreater(BUY23, BASE[2])
        self.assertLess(need(BUY, 1505 / SH), .031)
        self.assertLess(need(BUY, 1256 / SH), .058)
        self.assertGreater(need(BUY, 1256 / SH), .031)
        self.assertGreater(need(BUY23, 1256 / SH), .058)
        self.assertLess(sum(NI) / sum(SALES) * 17719 / SH, E_MID)
        self.assertLess((4192 - 956 - 965 - 368 - 428 - 165) / SH, E_MID)
        self.assertEqual(max(EPS), 1.77)
        self.assertLess(8928 / 10 / SH, 971 / SH)
        self.assertLess(abs(E_MID / BUY - AAA), .001)
        # All five equal stays under a third of the price, as the footnote says.
        self.assertIn("covers under a third", TEXT)

    def test_rule_saved(self):
        rule = (ROOT / "Rules/when-to-buy.md").read_text()
        self.assertIn("covers at least 75% of the price", rule)
        self.assertNotIn("not defined yet", rule)
        self.assertIn("Strategic value is worked out this way", (ROOT / "Rules/when-to-trim.md").read_text())
        self.assertIn(f"middle ${BASE[1]:.2f}, buy below ${BUY:.2f}", (ROOT / "Companies/Corning.md").read_text())


if __name__ == "__main__":
    unittest.main()
