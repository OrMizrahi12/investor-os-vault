"""Corning's financial health: read the summary in the note, re-read the cached filings, tie one to the other.

Reads files only. No network and no writes. The filing number on the page is read from the saved filing
each time the page loads, so a wrong note shows up as a difference. The sensors saved these filings.
"""

import datetime as dt
import json
import re
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / "Companies" / "Corning.md"
SEC = ROOT / "sensors" / "edgar" / "cache" / "CIK0000024741"
VALUE_PAGE, FLAG_PAGE = ROOT / "value-tests.html", ROOT / "flags.html"
SUMMARY = "Financial health summary"
MATCH, DIFF, ABSENT, NO_FILING, UNREAD = "Match", "Difference", "Not in this 10-K", "No filing number", "Could not read"
APPROX = "Match, approximate"  # the arithmetic agrees, but one input is printed only as a rounded figure


# ---- The note ----

def _section(text, heading):
    found = re.search(rf"^(#+) {re.escape(heading)}\s*$", text, re.M)
    if not found:
        raise ValueError(f'The note has no "{heading}" section.')
    stop = re.compile(rf"^#{{1,{len(found[1])}}} ", re.M).search(text, found.end())
    return text[found.end():stop.start() if stop else len(text)]


def _tables(block):
    """Every markdown table in a block, as a list of {header: cell} rows."""
    tables, lines = [], []
    for line in block.splitlines() + [""]:
        if line.startswith("|"):
            lines.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif lines:
            # A repeated column name keeps its first column: the quarters table has "Core" for net income, then for EPS.
            tables.append([dict(reversed(list(zip(lines[0], row)))) for row in lines[2:]])
            lines = []
    return tables


def _links(cell, refs):
    """Reference and inline links in a cell, as (text, url). A link with no known target has no url."""
    out = []
    for text, inline, ref in re.findall(r"\[([^\]]+)\](?:\((https://[^)\s]+)\)|\[([^\]]+)\])", cell):
        out.append((text, inline or refs.get(ref)))
    return out


def _amount(text):
    """'$1,596M', '−$497M', '36.0%', '1.3x', 'about $1.0 billion' or '17' as (Decimal, decimals shown)."""
    found = re.search(r"([−-]?)\$?(\d[\d,]*(?:\.\d+)?)", text)
    if not found:
        raise ValueError(f"No number in {text!r}.")
    digits = found[2].replace(",", "")
    places = len(digits.partition(".")[2])
    value = Decimal(digits)
    return (-value if found[1] else value), places


def millions(text):
    """A figure as a plain number of millions, for drawing."""
    return float(_amount(text)[0]) * (1000 if "billion" in text else 1)


def _parts(figure):
    """'GAAP $1,596M; core $2,199M' as an ordered {label: text}. A lone figure gets the label ''."""
    out = {}
    for piece in figure.split(";"):
        piece = piece.replace("(calc.)", "").strip()
        found = re.fullmatch(r"(.*?)\s*((?:about )?[−-]?\$?\d[\d,]*(?:\.\d+)?(?: billion|[Mx%])?)", piece)
        if not found:
            raise ValueError(f"Cannot read the figure {piece!r}.")
        out[found[1]] = found[2]
    return out


def read_note(path=NOTE):
    """The summary and the tables the charts draw. Tables stay where they are in the note, so nothing is typed twice."""
    text = Path(path).read_text()
    refs = dict(re.findall(r"^\[([^\]]+)\]:\s*(https://\S+)\s*$", text, re.M))
    rows = []
    for row in _tables(_section(text, SUMMARY))[0]:
        rows.append({"measure": row["Measure"], "figure": row["Figure"], "parts": _parts(row["Figure"]),
                     "filings": _links(row["Filing"], refs), "filing_text": row["Filing"], "means": row["What it means"]})
    income = _tables(_section(text, "Income statement and core"))
    cash = _section(text, "Cash flow")
    years = []
    cash_rows = {r["Year"]: r for r in _tables(cash)[0]}
    for row in income[0]:
        c = cash_rows[row["Year"]]
        years.append({"year": int(row["Year"][2:]), "gross": row["Gross margin"], "operating": row["Operating margin"], "net": row["Net margin"],
                      "ocf": c["Operating cash flow"], "capex": c["Capex"], "fcf": c["Free cash flow"], "url": _links(row["Source"], refs)[0][1],
                      "filing": _links(row["Source"], refs)[0][0]})
    quarters = [{"quarter": r["Quarter"], "gaap": r["Net income GAAP"], "core": r["Core"], "gap": r["Gap (calc.)"],
                 "url": _links(r["Source"], refs)[0][1], "filing": _links(r["Source"], refs)[0][0]} for r in income[1]]
    watch = [{"period": r["Period"], "fcf": r["Free cash flow"], "deposits": r["Deposits stated"], "without": r["Without them (calc.)"],
              "url": _links(r["Source"], refs)[0][1], "filing": _links(r["Source"], refs)[0][0]}
             for r in _tables(_section(text, "Figures to watch"))[0]]
    line_label = "\"Customer deposits and government incentives\""
    watch_line = [{"period": r["Period"], "fcf": r["Free cash flow"], "line": r[line_label], "without": r["Without the line (calc.)"],
                   "url": _links(r["Source"], refs)[0][1], "filing": _links(r["Source"], refs)[0][0]}
                  for r in _tables(_section(text, "Figures to watch"))[1]]
    watch_estimate = [{"period": r["Period"], "fcf": r["Free cash flow"], "deposit": r["Deposit taken out"], "applied": r["Older deposits added back"],
                       "estimate": r["Estimate (calc.)"], "url": _links(r["Source"], refs)[0][1], "filing": _links(r["Source"], refs)[0][0]}
                      for r in _tables(_section(text, "Figures to watch"))[2]]
    ladder = [{"due": r["Due"], "amount": r["Amount"], "url": _links(r["Source"], refs)[0][1], "filing": _links(r["Source"], refs)[0][0]}
              for r in _tables(_section(text, "Debt ladder"))[0]]
    normal = _tables(_section(text, "Normal earnings"))
    normalized = [r for r in normal[0] if r[""].startswith("Normalized")][0]
    reported = [r for r in normal[1] if r["Item"] == "Reported diluted EPS"][0]
    last_checked = re.search(r'^last checked: "?([\d-]+)"?', text, re.M)
    return {"summary": rows, "years": years, "quarters": quarters, "watch": watch, "watch_line": watch_line, "watch_estimate": watch_estimate, "ladder": ladder, "refs": refs,
            "normalized": {y: normalized[str(y)] for y in range(2016, 2026)}, "reported": {y: reported[str(y)] for y in range(2016, 2026)},
            "last_checked": last_checked[1] if last_checked else None}


# ---- The saved filings ----

@lru_cache(maxsize=1)
def _filing_list(path=SEC / "filings.jsonl"):
    return tuple(json.loads(line) for line in Path(path).read_text().splitlines())


def latest_10k():
    """The newest 10-K in the saved SEC list. Dates are ISO, so the largest string is the newest."""
    return max((f for f in _filing_list() if f["form"] == "10-K"), key=lambda f: f["filed"])


def _accession(url):
    found = re.search(r"/(\d{18})/", url)
    return f"{found[1][:10]}-{found[1][10:12]}-{found[1][12:]}" if found else None


def _cached_path(url):
    name, accession, folder = url.rsplit("/", 1)[-1], _accession(url), SEC / "documents"
    for path in (folder / f"{accession}-{name}", folder / name):
        if path.exists():
            return path
    raise ValueError(f"{name} is not in the saved filings. This page does not fetch it.")


def _plain(markup):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", markup)).replace("\xa0", " ").split())


class Filing:
    """A saved filing as table rows and plain text."""

    def __init__(self, url):
        self.url = url
        markup = _cached_path(url).read_text(errors="replace")
        self.rows = []  # (table number, label, [numbers])
        self.tables = {}
        for number, table in enumerate(re.findall(r"<table\b.*?</table>", markup, re.S | re.I)):
            for tr in re.findall(r"<tr\b.*?</tr>", table, re.S | re.I):
                cells = [c for c in (_plain(x) for x in re.findall(r"<t[dh]\b.*?</t[dh]>", tr, re.S | re.I)) if c]
                if cells:
                    self.rows.append((number, cells[0], _numbers(cells[1:])))
                    self.tables.setdefault(number, []).append(cells[0])
        self.text = _plain(markup)
        match = next((f for f in _filing_list() if f["accession"] == _accession(url)), None)
        self.year = int(match["report_date"][:4]) if match and match["report_date"] else None

    def _table_with(self, anchors):
        for number, labels in self.tables.items():
            if all(any(re.fullmatch(a, label) for label in labels) for a in anchors):
                return number
        raise ValueError(f"No table with {anchors} in {self.url.rsplit('/', 1)[-1]}.")

    def number(self, label, col=0, anchors=None, nth=0, count=None):
        """A row's number by its exact label. `anchors` picks the table, `nth` a repeat, `count` how many numbers the row must hold."""
        table = self._table_with(anchors) if anchors else None
        found = [nums for number, text, nums in self.rows if re.fullmatch(label, text) and nums
                 and (table is None or number == table) and (count is None or len(nums) == count)]
        if len(found) <= nth:
            raise ValueError(f'No row "{label}" in {self.url.rsplit("/", 1)[-1]}.')
        return found[nth][col]

    def income(self, label, year):
        return self.number(label, self.year - year, INCOME, count=3)

    def cash(self, label, year):
        return abs(self.number(label, self.year - year, CASH, count=3))

    def prose(self, pattern):
        found = re.search(pattern, self.text)
        if not found:
            raise ValueError(f"No words matching {pattern!r} in {self.url.rsplit('/', 1)[-1]}.")
        return Decimal(found[1].replace(",", ""))


INCOME = (r"Cost of sales", r"Net income( \(loss\))? attributable to Corning Incorporated", r"Diluted.*")
CASH = (r"Net cash provided by operating activities", r"Capital expenditures", r"Depreciation")
NET_INCOME = r"Net income( \(loss\))? attributable to Corning Incorporated"


def _numbers(cells):
    """Numbers in the cells after a row's label. Brackets mean negative, even when the closing one sits in its own cell. Percent cells count as numbers."""
    out = []
    for token in re.findall(r"\(?\s*\$?\s*\(?\d[\d,]*(?:\.\d+)?", " ".join(cells)):
        value = Decimal(re.sub(r"[^\d.]", "", token))
        out.append(-value if "(" in token else value)
    return out


def filing(url):
    return _load(url, _cached_path(url).stat().st_mtime_ns)


@lru_cache(maxsize=32)
def _load(url, _changed):
    return Filing(url)


# ---- The check: our number, the filing's number, a match or the difference ----

def _rounded(value, places):
    return Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def _unit(text):
    """The note's way of writing a figure, so a filing number prints the same way."""
    return ("$" if "$" in text else "", " billion" if text.endswith("billion") else text[-1] if text[-1] in "Mx%" else "")


def show(value, like):
    dollar, tail = _unit(like)
    places = _amount(like)[1]
    number = f"{abs(_rounded(value, places)):,.{places}f}"
    return f"{'−' if value < 0 else ''}{dollar}{number}{tail}"


class Book:
    """Collects check rows. Every recipe runs inside a guard, so a filing we cannot read says so and never reads as a match."""

    def __init__(self, tenk_url):
        self.rows = []
        self.tenk = tenk_url

    def add(self, group, item, ours, read, source=None, how="", approx=False):
        """`read` returns the filing's number. With `source` set to (text, url) the number is not in the latest 10-K, so it is tied there."""
        row = {"group": group, "item": item, "ours": ours, "how": how, "tenk": None, "tenk_result": ABSENT, "other": None,
               "other_result": None, "source": source}
        try:
            value = read()
            places = _amount(ours)[1]
            shown = show(value, ours)
            same = _rounded(value, places) == _amount(ours)[0]
            gap = "" if same else f"{show(_amount(ours)[0] - _rounded(value, places), ours)}"
            agreed = APPROX if approx else MATCH
            if source:
                row.update(other=shown, other_result=agreed if same else DIFF, gap=gap)
            else:
                row.update(tenk=shown, tenk_result=agreed if same else DIFF, gap=gap)
        except (ValueError, KeyError, ArithmeticError, IndexError, OSError) as err:
            row.update({"other_result" if source else "tenk_result": UNREAD, "gap": str(err)})
        self.rows.append(row)

    def counted(self, group, item, ours, read, where):
        """A count of our own rows or cards. No filing prints it, so it is tied to the page that holds the rows."""
        row = {"group": group, "item": item, "ours": ours, "how": where, "tenk": None, "tenk_result": NO_FILING, "other": None,
               "other_result": None, "source": (where, None)}
        try:
            value = read()
            same = Decimal(value) == _amount(ours)[0]
            row.update(other=str(value), other_result=MATCH if same else DIFF, gap="" if same else str(_amount(ours)[0] - Decimal(value)))
        except (ValueError, KeyError, OSError) as err:
            row.update(other_result=UNREAD, gap=str(err))
        self.rows.append(row)

    def calc_only(self, group, item, ours, why):
        self.rows.append({"group": group, "item": item, "ours": ours, "how": why, "tenk": None, "tenk_result": NO_FILING, "other": None,
                          "other_result": None, "source": None})


def _margin(file, label, year):
    return file.income(label, year) / file.income("Net sales", year) * 100


def _fcf(file, year):
    return file.cash("Net cash provided by operating activities", year) - file.cash("Capital expenditures", year)


def _ebitda(tenk, q):
    """Trailing twelve months to Sept. 30, 2026: FY2025 + nine months of 2026 − nine months of 2025."""
    op = tenk.income("Operating income", 2025) + q.number("Operating income", 2, count=4) - q.number("Operating income", 3, count=4)
    fy = tenk.cash("Depreciation", 2025) + tenk.cash("Amortization of purchased intangibles", 2025)
    this = q.number("Depreciation", 0, count=2) + q.number("Amortization of purchased intangibles", 0, count=2)
    last = q.number("Depreciation", 1, count=2) + q.number("Amortization of purchased intangibles", 1, count=2)
    return op + fy + this - last


def _debt(q):
    return q.number(r"Current portion of long-term debt and short-term borrowings.*", 0) + q.number(r"Long-term debt \(Note \d+\)", 0)


def _schedule(file):
    """The maturity schedule: the row of six numbers right after the header naming 'Thereafter'."""
    found = re.search(r"2026\s+2027\s+2028\s+2029\s+2030\s+Thereafter\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)", file.text)
    if not found:
        raise ValueError("No maturity schedule found.")
    return [Decimal(x.replace(",", "")) for x in found.groups()]


def _core_eps(file, nth):
    return file.number(r"Core performance measures", -1, nth=nth)


# Which printed reconciliation table holds each year's core EPS. Same filings as the normal earnings section of the note.
CORE_EPS = {2016: ("k18", 2), 2017: ("k18", 1), 2018: ("k20", 2), 2019: ("k21", 2), 2020: ("k21", 1), 2021: ("k22", 1),
            2022: ("k23", 1), 2023: ("k24", 1), 2024: ("k", 1), 2025: ("k", 0)}


def _page_count(path, attribute, value, extra=""):
    return len(re.findall(rf'{attribute}="{value}"{extra}', Path(path).read_text()))


def _tie_summary(book, note, tenk, q):
    parts = {row["measure"]: row["parts"] for row in note["summary"]}
    refs = note["refs"]
    group = "Summary"
    q_label = ("10-Q, filed Oct. 29, 2026", q.url)
    def figure(measure, label=""):
        return parts[measure][label]

    book.add(group, "Sales, FY2025", figure("Sales, FY2025"), lambda: tenk.income("Net sales", 2025))
    m = "Sales, nine months of 2026"
    book.add(group, f"{m}: this year", figure(m, "this year"), lambda: q.number("Net sales", 2, count=4), q_label)
    book.add(group, f"{m}: a year earlier", figure(m, "a year earlier"), lambda: q.number("Net sales", 3, count=4), q_label)
    m = "Margins, FY2025"
    for label, line in (("gross", "Gross margin"), ("operating", "Operating income"), ("net", NET_INCOME)):
        book.add(group, f"{m}: {label}", figure(m, label), lambda line=line: _margin(tenk, line, 2025), how="calc. from 10-K lines ÷ net sales")
    m = "Net income, FY2025"
    book.add(group, f"{m}: GAAP", figure(m, "GAAP"), lambda: tenk.income(NET_INCOME, 2025))
    book.add(group, f"{m}: core", figure(m, "core"), lambda: tenk.number("Core net income", 0))
    book.add(group, f"{m}: gap", figure(m, "gap"), lambda: tenk.number("Core net income", 0) - tenk.income(NET_INCOME, 2025), how="calc. from the two 10-K lines")
    m = "Diluted EPS, FY2025"
    book.add(group, f"{m}: GAAP", figure(m, "GAAP"), lambda: tenk.income(r"Diluted.*", 2025))
    book.add(group, f"{m}: core", figure(m, "core"), lambda: tenk.number("Core earnings per share", 0))
    m = "GAAP to core, last 8 quarters"
    book.add(group, f"{m}: gap", figure(m, "gap"), lambda: sum(_release(x)[1] - _release(x)[0] for x in note["quarters"]),
             ("the 8 releases", None), how="calc. from each release")
    m = "Normal diluted EPS, FY2016 to FY2025"
    book.calc_only(group, f"{m}: normalized average", figure(m, "normalized average"), "Our own measure, from my confirmed adjustments. No filing prints it. Its ten years are averaged below.")
    book.add(group, f"{m}: reported average", figure(m, "reported average"), lambda: sum(filing(y["url"]).income(r"Diluted.*", y["year"]) for y in note["years"]) / 10,
             ("the 10-Ks filed Feb. 12, 2019 to Feb. 12, 2026", None), how="calc. from each filing's diluted EPS")
    book.add(group, f"{m}: core average", figure(m, "core average"), lambda: sum(_core_eps(filing(refs[k]), n) for k, n in CORE_EPS.values()) / 10,
             ("the 10-Ks filed Feb. 12, 2019 to Feb. 12, 2026", None), how="calc. from each filing's core line")
    book.add(group, f"{m}: normalized FY2025", figure(m, "normalized FY2025"),
             lambda: (tenk.income(NET_INCOME, 2025) + tenk.number(r"Translation loss on foreign denominated debt, net.*", 1)
                      - tenk.number(r"Unrealized gain \(loss\), net", 1) + tenk.number(r"Loss on investments.*", 1)
                      + tenk.number(r"Loss on sale of assets.*", 1) + tenk.number(r"Loss on sale of business.*", 1))
             / tenk.number(r"Weighted-average common shares outstanding - diluted", 0),
             how="calc.: net income with my confirmed FY2025 adjustments, ÷ diluted shares")
    m = "Free cash flow, FY2025"
    deposits = lambda: tenk.prose(r"received \$ ?([\d,]+) million relating to new customer contracts")  # noqa: E731
    book.add(group, f"{m}: with deposits", figure(m, "with deposits"), lambda: _fcf(tenk, 2025), how="calc.: operating cash flow − capex")
    book.add(group, f"{m}: deposits", figure(m, "deposits"), deposits)
    book.add(group, f"{m}: without", figure(m, "without"), lambda: _fcf(tenk, 2025) - deposits(), how="calc.")
    m = "Free cash flow, nine months of 2026"
    deposit = lambda: q.prose(r"\$ ?([\d.]+) billion customer deposit")  # noqa: E731
    fcf9 = lambda col: q.number("Net cash provided by operating activities", col, count=2) + q.number("Capital expenditures", col, count=2)  # noqa: E731
    book.add(group, f"{m}: with deposit", figure(m, "with deposit"), lambda: fcf9(0), q_label, how="calc.: operating cash flow − capex")
    book.add(group, f"{m}: deposit", figure(m, "deposit"), deposit, q_label, how="As printed. The filing gives no closer figure.")
    book.add(group, f"{m}: without", figure(m, "without"), lambda: fcf9(0) - deposit() * 1000, q_label, approx=True,
             how="calc. with the deposit taken as $1,000M. If it rounds from $950M to $1,049M, this is $792M to $891M.")
    book.add(group, f"{m}: a year earlier", figure(m, "a year earlier"), lambda: fcf9(1), q_label, how="calc.")
    m = "Free cash flow, ten years"
    book.add(group, f"{m}: free cash flow", figure(m, "free cash flow"), lambda: sum(_fcf(filing(y["url"]), y["year"]) for y in note["years"]),
             ("the 10-Ks filed Feb. 12, 2019 to Feb. 12, 2026", None), how="calc.: sum of ten years")
    book.add(group, f"{m}: net income", figure(m, "net income"), lambda: sum(filing(y["url"]).income(NET_INCOME, y["year"]) for y in note["years"]),
             ("the 10-Ks filed Feb. 12, 2019 to Feb. 12, 2026", None), how="calc.: sum of ten years")
    m = "Cash and debt, Sept. 30, 2026"
    book.add(group, f"{m}: cash", figure(m, "cash"), lambda: q.number("Cash and cash equivalents", 0), q_label)
    book.add(group, f"{m}: debt", figure(m, "debt"), lambda: _debt(q), q_label, how="calc.: current portion + long-term debt")
    book.add(group, f"{m}: due within a year", figure(m, "due within a year"), lambda: q.number(r"Current portion of long-term debt and short-term borrowings.*", 0), q_label)
    m = "Cash and debt, Dec. 31, 2025"
    book.add(group, f"{m}: cash", figure(m, "cash"), lambda: tenk.number("Cash and cash equivalents", 0))
    book.add(group, f"{m}: debt", figure(m, "debt"), lambda: tenk.number("Total debt", 0))
    book.add(group, f"{m}: due within a year", figure(m, "due within a year"), lambda: tenk.number(r"Current portion of long-term debt and short-term borrowings.*", 0))
    m = "Debt load, Sept. 30, 2026"
    net = lambda: _debt(q) - q.number("Cash and cash equivalents", 0)  # noqa: E731
    book.add(group, f"{m}: net debt", figure(m, "net debt"), net, q_label, how="calc.: debt − cash")
    book.add(group, f"{m}: net debt to trailing EBITDA", figure(m, "net debt to trailing EBITDA"), lambda: net() / _ebitda(tenk, q),
             ("10-K and 10-Q together", None), how="calc.: FY2025 + nine months of 2026 − nine months of 2025")
    m = "Debt ladder, Dec. 31, 2025"
    book.add(group, f"{m}: due after 2030", figure(m, "due after 2030"), lambda: _schedule(tenk)[5])
    book.add(group, f"{m}: schedule total", figure(m, "schedule total"), lambda: sum(_schedule(tenk)), how="calc.: sum of the schedule")
    book.add(group, f"{m}: share after 2030", figure(m, "share after 2030"), lambda: _schedule(tenk)[5] / sum(_schedule(tenk)) * 100, how="calc.")
    m = "Classic value tests"
    for label, value in (("pass", "pass"), ("fail", "fail"), ("not settled", "open")):
        book.counted(group, f"{m}: {label}", figure(m, label), lambda value=value: _page_count(VALUE_PAGE, "data-o", value), "Rows on value-tests.html")
    m = "Red flags"
    for label, value in (("concern", "concern"), ("watch", "watch"), ("clear", "clear")):
        book.counted(group, f"{m}: {label}", figure(m, label), lambda value=value: _page_count(FLAG_PAGE, "data-rate", value), "Cards on flags.html")
    book.counted(group, f"{m}: of watch, not tested", figure(m, "of watch, not tested"), lambda: _page_count(FLAG_PAGE, "data-rate", "watch", r' data-nt="1"'), "Cards on flags.html")


def _release(quarter):
    file = filing(quarter["url"])
    return file.number(r"As reported.*", 2, nth=0), file.number(r"Core performance measures", 2, nth=0)


def _source_for(row, tenk_url):
    return None if row["url"] == tenk_url else (row["filing"], row["url"])


def _tie_charts(book, note, tenk):
    for y in note["years"]:
        file_url, year = y["url"], y["year"]
        source = _source_for(y, tenk.url)
        for label, key, line in (("gross", "gross", "Gross margin"), ("operating", "operating", "Operating income"), ("net", "net", NET_INCOME)):
            book.add("Margins chart", f"FY{year} {label} margin", y[key], lambda line=line, u=file_url, yr=year: _margin(filing(u), line, yr), source, how="calc. from filing lines ÷ net sales")
    for y in note["years"]:
        file_url, year = y["url"], y["year"]
        source = _source_for(y, tenk.url)
        book.add("Free cash flow chart", f"FY{year} operating cash flow", y["ocf"], lambda u=file_url, yr=year: filing(u).cash("Net cash provided by operating activities", yr), source)
        book.add("Free cash flow chart", f"FY{year} capex", y["capex"], lambda u=file_url, yr=year: filing(u).cash("Capital expenditures", yr), source)
        book.add("Free cash flow chart", f"FY{year} free cash flow", y["fcf"], lambda u=file_url, yr=year: _fcf(filing(u), yr), source, how="calc.")
    q = filing(note["refs"]["q0930"])
    fcf9 = lambda col: q.number("Net cash provided by operating activities", col, count=2) + q.number("Capital expenditures", col, count=2)  # noqa: E731
    q_label = ("10-Q, filed Oct. 29, 2026", q.url)
    for w in note["watch"]:
        period = w["period"]
        if period == "FY2025":
            continue  # the same two figures are in the summary group
        if period == "FY2024":
            book.add("Free cash flow chart", "FY2024 without deposits", w["without"], lambda: _fcf(tenk, 2024), how='calc.: the 10-K calls the 2024 amounts "not material"')
        elif period == "Nine months 2025":
            book.add("Free cash flow chart", "Nine months 2025 without deposits", w["without"], lambda: fcf9(1), q_label, how="calc.: no deposit is stated for this period")
    filed_line = lambda col: q.number("Customer deposits and government incentives", col, count=2)  # noqa: E731
    for col, w in zip((0, 1), note["watch_line"]):
        book.add("Free cash flow chart", f'{w["period"]} filed deposits line', w["line"], lambda col=col: filed_line(col), q_label)
        book.add("Free cash flow chart", f'{w["period"]} without the filed line', w["without"], lambda col=col: fcf9(col) - filed_line(col), q_label, how="calc.: free cash flow minus the whole filed line")
    applied = lambda year: q.prose(rf"ended September 30, {year}, the Company applied \$ ?[\d,]+ million and \$ ?([\d,]+) million, respectively, of customer deposits")  # noqa: E731
    for col, year, w in zip((0, 1), (2026, 2025), note["watch_estimate"]):
        book.add("Free cash flow chart", f'{w["period"]} older deposits applied', w["applied"], lambda year=year: applied(year), q_label)
        taken_out = (lambda: q.prose(r"\$ ?([\d.]+) billion customer deposit") * 1000) if year == 2026 else (lambda: 0)
        book.add("Free cash flow chart", f'{w["period"]} estimate, both sides out', w["estimate"], lambda col=col, year=year, taken_out=taken_out: fcf9(col) - taken_out() + applied(year), q_label,
                 approx=year == 2026, how="An estimate. calc.: free cash flow minus the deposit plus older deposits applied. It assumes those repayments ran through the filed line.")
    for x in note["quarters"]:
        source = (x["filing"], x["url"])
        name = x["quarter"]
        book.add("GAAP vs core chart", f"{name} GAAP net income", x["gaap"], lambda x=x: _release(x)[0], source)
        book.add("GAAP vs core chart", f"{name} core net income", x["core"], lambda x=x: _release(x)[1], source)
    in_2025 = [x for x in note["quarters"] if x["quarter"].endswith("2025")]
    total = lambda key: sum(_amount(x[key])[0] for x in in_2025)  # noqa: E731
    book.add("GAAP vs core chart", "Four 2025 quarters added: GAAP", f"${total('gaap'):,}M", lambda: tenk.income(NET_INCOME, 2025), how="calc. on our side")
    book.add("GAAP vs core chart", "Four 2025 quarters added: core", f"${total('core'):,}M", lambda: tenk.number("Core net income", 0), how="calc. on our side")
    for i, rung in enumerate(note["ladder"]):
        book.add("Debt ladder chart", f'Due {rung["due"]}', rung["amount"], lambda i=i: _schedule(tenk)[i])
    ladder_total = sum(_amount(r["amount"])[0] for r in note["ladder"])
    book.add("Debt ladder chart", "Ladder added, against balance sheet total debt", f"${ladder_total:,}M", lambda: tenk.number("Total debt", 0),
             how="Two different lists. The 10-K says its schedule excludes bond discounts and deferred expenses and includes finance leases that have commenced.")
    for year, value in note["normalized"].items():
        book.calc_only("Normal earnings", f"FY{year} normalized EPS", value, "Our own measure. No filing prints it.")
    book.add("Normal earnings", "Ten-year average of the years above", _summary_part(note, "Normal diluted EPS, FY2016 to FY2025", "normalized average"),
             lambda: sum(_amount(v)[0] for v in note["normalized"].values()) / 10, ("the ten figures above", None), how="calc.")


def _summary_part(note, measure, label):
    return [r for r in note["summary"] if r["measure"] == measure][0]["parts"][label]


def checks(note=None):
    """Every number on the panel, tied to the latest 10-K where it reports it, and otherwise to the filing it came from."""
    note = note or read_note()
    newest = latest_10k()
    tenk = filing(newest["url"])
    q = filing(note["refs"]["q0930"])
    book = Book(tenk.url)
    _tie_summary(book, note, tenk, q)
    _tie_charts(book, note, tenk)
    tally = Counter(r["tenk_result"] for r in book.rows)
    other = Counter(r["other_result"] for r in book.rows if r["other_result"])
    return {"rows": book.rows, "tally": tally, "other": other, "tenk": newest}


def scoreboard(note):
    row = {r["measure"]: r["parts"] for r in note["summary"]}
    return {"tests": row["Classic value tests"], "flags": row["Red flags"]}


def file_time(path):
    return dt.datetime.fromtimestamp(Path(path).stat().st_mtime, dt.timezone.utc)
