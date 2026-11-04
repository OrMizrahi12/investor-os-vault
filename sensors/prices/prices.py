"""Prices sensor: Corning's daily prices from Yahoo, through yfinance. For my personal use only.

Run from the project root:
    uv run python sensors/prices/prices.py

It asks Yahoo at most once per UTC day. A failed try counts, and there is no override.
Each fetch is one dated file: sensors/prices/cache/GLW/YYYY-MM-DD.csv. manifest.json logs every try.
No email or other personal detail is sent. SEC and FRED stay our backbone, so nothing should treat
this as a source of company facts, and nothing built from it should be published.

Yahoo's terms bar automated collection without its permission, and it has not given any. Keeping this
sensor is my decision of Nov. 3, 2026. See Journal/2026-11-03.md.
"""

import csv
import datetime as dt
import hashlib
import json
import logging
import sys
import warnings
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
TICKER = "GLW"
START = "2010-01-01"  # enough for the 15-year page
COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume", "dividends", "stock_splits"]
NEW_YORK = ZoneInfo("America/New_York")
SESSION_DONE = dt.time(16, 15)  # before this, today's row is not a final close


class PriceError(Exception):
    """Something the owner should see. The script stops instead of writing doubtful data."""


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def _write_atomic(path, data):
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(data)
    temp.replace(path)


def load_manifest(folder):
    path = Path(folder) / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {"ticker": TICKER, "attempts": []}


def save_manifest(folder, manifest):
    _write_atomic(Path(folder) / "manifest.json", json.dumps(manifest, indent=1).encode())


def tried_today(manifest, now):
    return any(a["started_utc"][:10] == now.date().isoformat() for a in manifest["attempts"])


def latest_good(manifest):
    good = [a for a in manifest["attempts"] if a["status"] == "ok"]
    return good[-1] if good else None


def to_rows(frame, now):
    """Turn yfinance's table into plain rows. Drop today's row if the session has not closed."""
    needed = {"Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"}
    # Close and Adj Close both matter. Adj Close lowers old prices for dividends, which would
    # overstate an old earnings yield. With auto_adjust on, the real Close would be gone.
    missing = needed - set(frame.columns)
    if missing:
        raise PriceError(f"Yahoo's table has no {sorted(missing)}.")
    local = now.astimezone(NEW_YORK)
    rows = []
    for stamp, r in frame.iterrows():
        day = stamp.date()
        if day == local.date() and local.time() < SESSION_DONE:
            continue
        if day > local.date():
            raise PriceError(f"Yahoo's table has a future date: {day}.")
        if not r["Close"] > 0:
            raise PriceError(f"Close on {day} is {r['Close']}.")
        rows.append({"date": day.isoformat(), "open": r["Open"], "high": r["High"], "low": r["Low"],
                     "close": r["Close"], "adj_close": r["Adj Close"], "volume": int(r["Volume"]),
                     "dividends": r["Dividends"], "stock_splits": r["Stock Splits"]})
    dates = [r["date"] for r in rows]
    if not rows or dates != sorted(set(dates)):
        raise PriceError("Yahoo's dates are empty, out of order or repeated.")
    return rows


def rows_to_csv(rows):
    lines = [",".join(COLUMNS)] + [",".join(str(r[c]) for c in COLUMNS) for r in rows]
    return ("\n".join(lines) + "\n").encode()


def download(ticker):
    """The only code that talks to Yahoo. One history call, no retries. Returns (table, data requests logged).

    yfinance presents itself to Yahoo as a Chrome browser, and may also fetch a cookie and crumb,
    which its log does not count.
    """
    import yfinance as yf

    seen = []

    class Count(logging.Handler):
        def emit(self, record):
            if "url=" in record.getMessage():
                seen.append(1)

    yf.config.network.retries = 0
    yf.config.debug.hide_exceptions = False
    logger = logging.getLogger("yfinance")
    handler = Count(level=logging.DEBUG)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # yfinance's own pandas deprecation notices
            frame = yf.Ticker(ticker).history(start=START, interval="1d", auto_adjust=False, actions=True, repair=False)
    finally:
        logger.removeHandler(handler)
    return frame, len(seen)


def fetch(folder=None, ticker=TICKER, downloader=download, clock=now_utc):
    """Fetch once if today's try is unused. The try is logged before the request, so a crash still counts."""
    folder = Path(folder or CACHE / ticker)
    folder.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(folder)
    now = clock()
    if tried_today(manifest, now):
        return manifest, False
    attempt = {"started_utc": now.isoformat(timespec="seconds"), "status": "started"}
    manifest["attempts"].append(attempt)
    save_manifest(folder, manifest)
    try:
        frame, sent = downloader(ticker)
        rows = to_rows(frame, now)
        body = rows_to_csv(rows)
        name = f"{now.date().isoformat()}.csv"
        _write_atomic(folder / name, body)
        attempt.update(status="ok", file=name, requests_logged=sent, rows=len(rows), bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest(), first=rows[0]["date"], last=rows[-1]["date"],
                       source=f"Yahoo Finance through yfinance, ticker {ticker}, auto_adjust off")
    except Exception as e:
        attempt.update(status="failed", error=f"{type(e).__name__}: {e}"[:400])
        save_manifest(folder, manifest)
        raise PriceError(f"Fetch failed and today's try is used. Next try is tomorrow UTC. {attempt['error']}") from e
    save_manifest(folder, manifest)
    return manifest, True


def read_latest(folder=None, ticker=TICKER):
    """The newest good fetch: (rows with numbers, its manifest entry). No network."""
    folder = Path(folder or CACHE / ticker)
    entry = latest_good(load_manifest(folder))
    if not entry:
        raise PriceError(f"No good price fetch in {folder}. Run prices.py.")
    body = (folder / entry["file"]).read_bytes()
    if hashlib.sha256(body).hexdigest() != entry["sha256"]:
        raise PriceError(f"{entry['file']} does not match its manifest entry.")
    rows = list(csv.DictReader(body.decode().splitlines()))
    for r in rows:
        for key in COLUMNS[1:]:
            r[key] = float(r[key])
    return rows, entry


def main():
    try:
        manifest, fetched = fetch()
    except PriceError as e:
        sys.exit(f"Stopped: {e}")
    entry = latest_good(manifest)
    print("Fetched from Yahoo." if fetched else "Already tried today (UTC). No request sent.")
    if entry:
        print(f"Newest good file: {entry['file']}, {entry['rows']} rows, {entry['first']} to {entry['last']}.")
        if fetched:
            print(f"Requests logged by yfinance: {entry['requests_logged']}.")
    else:
        print("No good fetch on file yet.")


if __name__ == "__main__":
    main()
