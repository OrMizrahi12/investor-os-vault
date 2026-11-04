"""Make a test copy of the vault with a busy made-up day, so Home can be seen and measured when things happen.

    .venv/bin/python dashboard/tools/busy_copy.py <new folder outside the vault>
    cd <that folder>/dashboard && <vault>/.venv/bin/python -m streamlit run app.py --server.port 8502

The real vault is only read. The app is copied as it is and reads the copy's files, so there is no switch in the app that could
show made-up data on the real board. Every made-up line says so, and TEST_COPY.txt puts a banner on every screen. Lines use the exact
forms the routines write (sensors/daily/publish.py, sensors/hunt/events.py) and hold hostile lengths on purpose. No routine, sensor or
phone step runs here. The app never imports this file.
"""

import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
COPIED = ("dashboard", "sensors", "Companies", "Research", "Inbox", "Journal", "Catalysts", "Lessons", "Rules", "Portfolio")
BANNER = "TEST COPY. Everything on this board is made up or copied for a test. It is not my vault, and nothing here happened."
LONG = " The made-up line runs on and on, so that a long line in a real brief cannot push this page past one screen, whatever a routine writes in it."


def nice(day):
    return f'{ {1: "Jan.", 2: "Feb.", 3: "Mar.", 4: "Apr.", 5: "May", 6: "June", 7: "July", 8: "Aug.", 9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Dec."}[day.month]} {day.day}, {day.year}'


def journal_days(today):
    """Nine Reds and Oranges waiting past the row limit, two closed by a ruling, one ruling that matches nothing, and one failed run."""
    d = lambda n: today - dt.timedelta(days=n)  # noqa: E731
    link = lambda name, n: f"[MADE-UP {name}, filed {nice(d(n))}](https://example.com/made-up-{name.replace(' ', '-').lower()})"  # noqa: E731
    return {
        d(9): f"""# {d(9)}

## Session: weekly thesis check, Made-up A

### What we did

- Checked one thesis.

**Orange**

- {link("Q3 call", 9)}, O2: made-up fact on claim C3, older than a week.{LONG}
- {link("Q3 release", 9)}, O13: a made-up catalyst date passed with no Outcome written.

### What we decided

- Nothing.
""",
        d(6): f"""# {d(6)}

## Session: event run

### What we did

- Read 2.

**Red**

- **Made-up A, R1.** {link("8-K", 6)}: made-up customer ended a deal, line K2 crossed.{LONG}
- **Made-up B, R2.** {link("8-K", 6)}: made-up dated fact appears to contradict claim C2.

**Orange**

- **Made-up B, O3.** {link("424B5", 6)}: made-up new shares become possible.

### What we decided

- Nothing.
""",
        d(3): f"""# {d(3)}

## Session: my ruling on the event run

### What we did

- Read the source myself.

### What we decided

- Ruled: {d(6)} R1. Made up: the claim still holds, on this made-up reading.
- Ruled: {d(9)} O13. Made up: read it, no claim went either way.
- Ruled: {d(3)} O9. Made up: this ruling matches no alert, so Home must say so.
""",
        d(1): f"""# {d(1)}

## Daily brief, {nice(d(1))}, 08:01

**Since the brief of {nice(d(3))}:** 3 new items.

### Red

- {link("8-K item 2.06", 1)}, R3: made-up impairment, presumed Red until read.

### Orange

- {link("8-K item 5.02", 1)}, O11: made-up CFO leaves.

### Info

- Nothing.

## Session: daily run, 08:01

### What we did

- Ran the daily run.
""",
        today: f"""# {today}

## Daily brief, {nice(today)}, 08:03

**Since the brief of {nice(d(1))}:** 2 Red, 3 Orange and 6 Info lines are new today, all of them made up for this test copy, and this sentence is long on purpose to show how the brief's own opening line is cut when it runs past what this block has room for, because a brief has no limit on how long this one sentence may be, and the page must still fit on one screen no matter how long it gets on a very busy day.

### Red

- {link("8-K item 4.02", 0)}, R3: made-up restatement, presumed Red until read.{LONG}
- {link("8-K item 1.02", 0)}, R3: made-up deal ended with no new one.

### Orange

- {link("8-K item 3.02", 0)}, O3: made-up new shares.
- {link("SEC staff letter", 0)}, O10: made-up letter opens a thread.
- {link("Schedule 13D", 0)}, O12: a made-up holder files.

### Info

- {link("10-Q", 0)}, I3: the made-up filing came, and its refresh is due.{LONG}
- {link("Form 4", 0)}, I4: 11 made-up forms, 3 sales.
- {link("8-K item 7.01", 0)}, I2: a made-up conference notice.
- {link("Radar", 0)}, I7: 117 made-up leads.
- {link("Catalyst note", 0)}, I6: a made-up date enters the horizon.
- {link("Close", 0)}, I9: where a made-up price stands.

## Session: daily run, 08:03

### What we did

- Ran the daily run.

## Session: event run

### What we did

- Read 1.

**Orange**

- **Made-up C, O2.** {link("8-K", 0)}: a made-up deal could change claim C1.

### What we decided

- Nothing.

Monthly hunt FAILED at step 2: made-up failure, the saved screen could not be read.
""",
    }


def add_radar_dates(copy, today):
    path = sorted((copy / "sensors/radar/runs").glob("*.json"))[-1]
    run = json.loads(path.read_text())
    day = lambda n: (today + dt.timedelta(days=n)).isoformat()  # noqa: E731
    row = lambda title, n, kind: {"title": f"MADE-UP {title}", "file": f"Catalysts/Made-up {title}.md", "ticker": "TSTA", "window": "made up", "date_start": day(n), "date_end": day(n),  # noqa: E731
                                  "date_quote": nice(today + dt.timedelta(days=n)), "date_kind": kind, "source": {"label": f"Made-up source, {nice(today)}", "url": "https://example.com/made-up"},
                                  "outcome_written": False, "companies": ["Made-up A"], "problem": None, "days_to_start": n, "days_to_end": n}
    run["dates"]["soon"] += [row("tariff decision, with a title long enough that it must be cut with an ellipsis on the row", 0, "stated"), row("plant opening", 1, "stated"),
                             row("deal start", 2, "forecast"), row("court date", 5, "stated"), row("date that passed before today and must leave the list", -3, "stated")]
    path.write_text(json.dumps(run))


def add_value_runs(copy, today):
    """Three made-up companies' runs, dated before the real one so the Company screen still opens on Corning. Each agrees with itself."""
    runs = copy / "sensors/valuation/runs"
    real = json.loads(sorted(runs.glob("*.json"))[-1].read_text())
    for i, (ticker, name, mid, close) in enumerate((("TSTA", "Made-up A", 40.0, 50.0), ("TSTB", "Made-up B", 38.0, 40.0), ("TSTC", "Made-up C", 10.0, 80.0))):
        run = json.loads(json.dumps(real))
        run.update(ticker=ticker, company=name, run_file=f"sensors/valuation/runs/2020-01-0{i + 1}-01.json")
        run["base"].update(low=mid * .5, mid=mid, high=mid * 1.5)
        run["strategic"] = 5.0
        run["buy_below"], run["trim_above"] = mid / .75, mid + 5.0
        run["price"].update(close=close, date=today.isoformat())
        run["series"] = [[today.isoformat(), close]]
        run["coverage"]["mid"] = mid / close
        under, above = mid / close >= .75, close > mid + 5.0
        run["zone"] = "under_and_above" if under and above else "under" if under else "above" if above else "between"
        (runs / f"2020-01-0{i + 1}-01.json").write_text(json.dumps(run))


def add_close(copy, ticker, close, today):
    folder = copy / "sensors/prices/cache" / ticker
    folder.mkdir(parents=True)
    columns = (copy / "sensors/prices/cache/GLW").glob("*.csv")
    header = next(iter(sorted(columns))).read_text().splitlines()[0]
    body = (header + "\n" + f"{today},1,1,1,{close},{close},1,0,0\n").encode()
    (folder / f"{today}.csv").write_bytes(body)
    (folder / "manifest.json").write_text(json.dumps({"attempts": [{"started_utc": f"{today}T07:00:00+00:00", "status": "ok", "file": f"{today}.csv", "rows": 1,
                                                                    "sha256": hashlib.sha256(body).hexdigest(), "first": str(today), "last": str(today), "source": "MADE-UP price file"}]}))


NOTE = """---
kind: {kind}
cash: {cash}
currency: USD
as of: "{today}"
last checked: "{today}"
---

# Made up for a test copy

## Positions

| Ticker | Shares | Bought on | Cost a share | Thesis note |
|---|---|---|---|---|
{rows}

## Changes

| Date | Change | Cash after | My yes |
|---|---|---|---|
| {today} | Made up | ${cash} | Made up |
"""


def add_notes(copy, today):
    """A paper note with positions that all have closes, a real one where a position has none, and a note marked neither."""
    folder = copy / "Portfolio"
    position = lambda ticker, shares: f"| {ticker} | {shares} | {today} | $10.00 | Made-up note |"  # noqa: E731
    (folder / "Paper portfolio.md").write_text(NOTE.format(kind="paper", cash=9000, today=today, rows="\n".join((position("TSTA", 1000), position("TSTB", 500)))))
    (folder / "Real holdings.md").write_text(NOTE.format(kind="real", cash=4000, today=today, rows="\n".join((position("TSTA", 100), position("TSTX", 100)))))
    (folder / "Unmarked.md").write_text("---\ncash: 5\n---\n\n# Made up, and marked neither real nor paper\n")


def add_kill_note(copy, today):
    """A second company's calendar, whose next report is this month, and a third with no calendar at all."""
    month = today.strftime("%b")
    (copy / "Research" / f"{today} Made-up A kill criteria.md").write_text(
        f"# Made up\n\n## Calendar of checks\n\nMade up.\n\n| Line | Q3 ({month}. {today.year}) |\n|---|---|\n| K1 A line | T |\n| K2 A reading | r |\n| K3 Another line | T |\n\n## How far to trust this\n\nNot at all.\n")
    (copy / "Research" / f"{today} Made-up B kill criteria.md").write_text("# Made up, with no calendar, so Home must show one problem line\n")


def add_hunt(copy, today):
    """One made-up idea note and one made-up hunt report, in the forms sensors/hunt/hunt.py writes, so the early stages of the pipeline show."""
    (copy / "Inbox" / f"{today} TSTI idea.md").write_text(f"""---
form: "idea"
company: "MADE-UP Idea Co"
ticker: "TSTI"
surfaced: "{today}"
filed: "{today}"
attention: "unknown"
reason: "A lead to read, never a pick."
sources:
  - "https://example.com/made-up-filing"
---

# Idea to read: MADE-UP Idea Co (TSTI), {nice(today)}

*A lead to read, never a pick.*

## Why it surfaced

Made-up remaining obligations went from $1.0M to $9.0M (calc., [MADE-UP frame, retrieved {nice(today)}](https://example.com/made-up-frame)).

## How far it got

| Test | State | What it read |
|---|---|---|
| Made up | pass | Made up. |
""")
    (copy / "Research" / f"{today} Monthly hunt.md").write_text(f"""---
track: monthly hunt
written: {today}
---

# Monthly hunt, {nice(today)}

*MADE-UP for this test copy. Leads, never picks.*

**2 rows, 2 tested, 1 written to Inbox (calc.).**

## The funnel

| Step | Count (calc.) | Who |
|---|---|---|
| Rows on the screen, retrieved {nice(today)} | 2 | Made up |
| Tested | 2 | Made up |

## The tested companies

| Rank | Company | Rise ÷ revenue (calc.) | Gate 1 | Gate 2 | Sorted |
|---|---|---|---|---|---|
| 1 | MADE-UP Idea Co (TSTI) | 0.90 | pass. | pass. | Idea in Inbox |
| 2 | MADE-UP Passed Over Co (TSTP) | 0.50 | fail. Debt is 9.0× cash. | not run. | Not worth reading now |

Sources: TSTI: [MADE-UP frame, retrieved {nice(today)}](https://example.com/made-up-frame)

## Proposed lines for the Rejection log

*Nothing was added. These go in only if I say so.*

| {nice(today)} | MADE-UP Passed Over Co (TSTP) | Gate 1 | Debt is 9.0× a year's operating cash (calc., [MADE-UP facts, retrieved {nice(today)}](https://example.com/made-up-facts)) | After the next 10-K, about Dec. {today.year} (made up). |

## Not done

- Made up.
""")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    copy = Path(sys.argv[1]).resolve()
    if copy == VAULT or VAULT in copy.parents:
        sys.exit("Refused: the test copy must be outside the vault.")
    if copy.exists():
        sys.exit(f"Refused: {copy} already exists.")
    today = dt.date.today()
    copy.mkdir(parents=True)
    # SEC's saved filings are large and the app only reads them, so the copy links to them.
    for name in COPIED:
        shutil.copytree(VAULT / name, copy / name, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "edgar"))
    (copy / "sensors/edgar").symlink_to(VAULT / "sensors/edgar")
    (copy / "TEST_COPY.txt").write_text(BANNER + "\n")
    for day, text in journal_days(today).items():
        path = copy / "Journal" / f"{day}.md"
        path.write_text(text + ("\n" + path.read_text() if path.exists() else ""))
    add_radar_dates(copy, today)
    add_value_runs(copy, today)
    add_close(copy, "TSTA", 50.0, today)
    add_close(copy, "TSTB", 40.0, today)
    add_notes(copy, today)
    add_kill_note(copy, today)
    add_hunt(copy, today)
    print(copy)


if __name__ == "__main__":
    main()
