"""Checks strategic.html without using model.py or draw.py for its sums. Inputs come from the saved filings and typed sums. No network.

    .venv/bin/python sensors/strategic/test_strategic.py
"""

import csv
import html
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "sensors/edgar/cache/CIK0000024741/documents"
PAGE = (ROOT / "strategic.html").read_text()
BODY = PAGE.split("</style>")[1].split("<script>")[0]
TEXT = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", BODY)))

SH, PX, R, AAA = 871, 123.20, .09, .0612
NI = [1323, 1496, 1270, 783, 133, 1519, 1097, 543, 577, 1543]
TTM = 2051
G = (1543 / 1323) ** (1 / 9) - 1
BASE = {}
for k, e, c in (("low", sum(NI) / 10 / SH, 971 / SH / R), ("mid", 1543 / SH, 1256 / SH * (1 + G) / (R - G)), ("high", TTM / SH, 1505 / SH * 1.03 / (R - .03))):
    BASE[k] = .4 * e / R + .4 * c + .2 * e / AAA
MULT = .4 / R + .4 * (1 + G) / (R - G) + .2 / AAA
MARGIN, LOW, ADDED = 532 / 2379, 305 / 1701, (532 - 295) / (2379 - 1652)
GROUP, TAX = 680 / 4855, 87 / (328 + 87)
K_OPT, K_SOL = 5039 / (6297 + 1701), 3166 / (1244 + 475)
RUN = 4 * 5081
SIGNED = (6000 + 12000 + 2000 + 2000 + 4000) / 6 * .75
SOLAR = 3000 - 4 * 436
DISPLAY = 3697 * .05
PLAN = 35000 - RUN - SIGNED - SOLAR - DISPLAY


def worth(ni, t, sales=0, k=0, extra=0, mult=MULT):
    return (ni * mult / (1 + R) ** t - (sales * k + extra) / (1 + R) ** (t / 2)) / SH


FULL = dict(signed=worth(SIGNED * MARGIN, 2.16, SIGNED, K_OPT), plan=worth(PLAN * MARGIN, 4.16, PLAN, K_OPT), scale=worth(5000 * MARGIN, 4.16, 5000, K_OPT),
            solar=worth(3000 * GROUP + 28, 3.16, SOLAR, K_SOL, 132), display=worth(DISPLAY * (1 - TAX), 1.16))
P = dict(signed=.7, plan=.4, scale=.2, solar=.35, display=.5)
EV = {k: FULL[k] * P[k] for k in FULL}
AT_RISK = .7 * SIGNED + .4 * PLAN + .2 * 5000
RIVAL_FULL = -(MARGIN - LOW) * AT_RISK * MULT / (1 + R) ** 3.16 / SH
STRAT = sum(EV.values()) + .4 * RIVAL_FULL
TRIM = BASE["mid"] + STRAT
ALL = BASE["mid"] + sum(FULL.values())


def flat(name):
    t = re.sub(r"<[^>]+>", " ", (DOCS / name).read_text(errors="ignore"))
    t = re.sub(r"[\s$|]+", " ", html.unescape(t).replace("\xa0", " "))
    return re.sub(r"\( ?([\d,.]+) ?\)", r"(\1)", t)


def closes():
    with open(ROOT / "sensors/prices/cache/GLW/2026-11-02.csv") as f:
        return [(r["date"], float(r["close"])) for r in csv.DictReader(f)]


def load_model():
    spec = importlib.util.spec_from_file_location("strategic_model", ROOT / "sensors/strategic/model.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Inputs(unittest.TestCase):
    def test_q10_segments(self):
        t = flat("glw-20260930.htm")
        self.assertIn("Segment net income (loss) 532 328 67 (7) 920 (28) 892", re.sub(r"\( (\d+) \)", r"(\1)", t))
        self.assertIn("Segment net sales 1,652 1,560 454 319 3,985 287 4,272", t)
        self.assertIn("Segment assets (1) 5,039 9,865 2,384 3,166", t)
        self.assertIn("exercise price of 180.00 per share", t)

    def test_k25_display(self):
        self.assertIn("Total Optical Communications 6,274 4,657 4,012 Display 3,697", flat("glw-20251231.htm"))

    def test_q3_release(self):
        t = flat("0000024741-26-000273-glw-20261027xex99xq32026.htm")
        self.assertIn("more than 3 billion Solar revenue stream", t)
        self.assertIn("Net Sales 1,506 1,463 1,560", t)

    def test_catalyst_map_is_whole(self):
        names = {p.stem for p in (ROOT / "Catalysts").glob("*.md") if p.name != "README.md"}
        self.assertEqual(names, set(load_model().MAP))
        self.assertEqual(len(names), 38)


class Counting(unittest.TestCase):
    def test_ladder_fills_gap_exactly(self):
        self.assertAlmostEqual(SIGNED + PLAN + 5000 + SOLAR + DISPLAY, 40000 - RUN)
        self.assertGreater(PLAN, 0)

    def test_scenarios_sit_above_base(self):
        self.assertLess(TTM, 4 * 680)
        self.assertLess(1256 * (1 + G) ** 4.16, 4 * 680)

    def test_chances_fall_up_the_ladder(self):
        self.assertGreaterEqual(P["signed"], P["plan"])
        self.assertGreaterEqual(P["plan"], P["scale"])

    def test_price_cannot_move_value(self):
        m = load_model()
        before = m.scenarios(), m.strategic(), m.trim_above()
        m.PRICE = m.base_model.PRICE = 999.0
        self.assertEqual(before, (m.scenarios(), m.strategic(), m.trim_above()))

    def test_model_agrees_with_this_file(self):
        m = load_model()
        self.assertAlmostEqual(m.strategic(), STRAT, places=6)
        self.assertAlmostEqual(m.trim_above(), TRIM, places=6)
        self.assertAlmostEqual(m.all_true(), ALL, places=6)

    def test_strategic_does_not_change_buy_below(self):
        self.assertIn(f"The buy-below stays ${BASE['mid'] / .75:.2f}", TEXT)


class Words(unittest.TestCase):
    def has(self, s):
        self.assertIn(s, TEXT)

    def test_lede(self):
        self.has(f"Trim above ${TRIM:.2f}, approved Nov. 3, 2026.")
        self.has(f"Base value of ${BASE['mid']:.2f} plus strategic value of ${STRAT:.2f} comes to ${TRIM:.2f}")
        self.has(f"close is {PX / TRIM:.1f} times that")
        self.has(f"the stack reaches ${ALL:.2f}")
        self.assertLess(TRIM, PX)
        self.assertLess(ALL, PX)

    def test_rows(self):
        for k in FULL:
            self.has(f"+${FULL[k]:.2f}")
            self.has(f"+${EV[k]:.2f}")
        self.has(f"−${-RIVAL_FULL:.2f}")
        self.has(f"−${-.4 * RIVAL_FULL:.2f}")

    def test_share_of_gap(self):
        self.has(f"the price pays ${PX - BASE['mid']:.2f} above base")
        self.has(f"or {STRAT / (PX - BASE['mid']) * 100:.0f}% of that")

    def test_meta_day_comparison(self):
        c = dict(closes())
        d = c["2026-01-27"] - c["2026-01-26"]
        self.assertGreater(d, STRAT)
        self.has(f"rise of ${d:.2f} is more than the whole strategic value")
        self.has(f"${c['2026-01-26']:.2f}, was already {c['2026-01-26'] / TRIM:.1f} times this value")

    def test_days_counts(self):
        s = [(d, x) for d, x in closes() if d >= "2016-01-01"]
        above = sum(x > TRIM for _, x in s)
        self.has(f"on {above:,} of {len(s):,} days, or {above / len(s) * 100:.0f}%")
        self.assertLess(above / len(s), .5)
        last = [d for d, x in s if x <= TRIM][-1]
        self.assertTrue(all(x > TRIM for d, x in s if d > last))
        self.assertLess(last, "2024-11-03")  # "over two years straight"
        self.has("for over two years straight")

    def test_peak_and_fall(self):
        pk = max(closes(), key=lambda r: r[1])
        self.assertEqual(pk[0], "2026-06-29")
        self.has(f"${pk[1]:.2f} on June 29, 2026")

    def test_sensitivity_never_reaches_price(self):
        m = load_model()
        _, rows = m.sensitivities()
        vals = [v for _, v in rows]
        self.assertLess(max(vals + [m.stretch()]), PX)
        self.has(f"Single changes run from ${min(vals):.2f} to ${max(vals):.2f}")
        self.has(f"It reaches ${m.stretch():.2f}")
        self.has(f"about {m.multiple_needed():.0f}x new profit, against {MULT:.1f}x")

    def test_gap_note(self):
        self.has(f"${BASE['high'] - BASE['mid']:.2f} a share (calc.)")
        self.has(f"${BASE['high'] + STRAT:.2f} is the same sum on the base's high")


class Saved(unittest.TestCase):
    def test_rule_and_note(self):
        rule = (ROOT / "Rules/when-to-trim.md").read_text()
        self.assertIn("If a rise takes the price above the trim-above price", rule)
        self.assertNotIn("not defined", rule)
        note = (ROOT / "Companies/Corning.md").read_text()
        self.assertIn(f'trim above: "${TRIM:.2f}', note)
        self.assertIn(f'strategic value: "${STRAT:.2f}', note)
        self.assertIn(f"trim-above of ${TRIM:.2f}", note)

    def test_what_if_stays_out(self):
        self.assertNotIn("80%", (ROOT / "Companies/Corning.md").read_text().split("**Strategic value (added")[1].split("## Rivals")[0])


if __name__ == "__main__":
    unittest.main()
