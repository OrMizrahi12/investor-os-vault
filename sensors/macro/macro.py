"""Macro sensor: read the three FRED files I download by hand. This script makes no network requests.

FRED's terms bar scripts from collecting its data and bar storing a cache without written consent,
and they allow me to download a copy for personal use. So I download, and this script only reads.
Terms: https://fred.stlouisfed.org/legal/ (undated, retrieved Nov. 2, 2026)

To refresh: open each series page, choose the longest range, then Download, CSV (data). Save the file
as sensors/macro/downloads/<ID>.csv, replacing the old one.

Run from the project root:
    uv run python sensors/macro/macro.py

The file's modified time is taken as the date downloaded. Each new file is logged in downloads/manifest.json.
"""

import csv
import datetime as dt
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOWNLOADS = HERE / "downloads"
YEARS = 15
OLD_AFTER_DAYS = 45

SERIES = {
    "DGS10": {"title": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis",
              "owner": "Board of Governors of the Federal Reserve System (US)", "frequency": "daily",
              "low": -1, "high": 25, "extra_months": 0},
    "AAA": {"title": "Moody's Seasoned Aaa Corporate Bond Yield", "owner": "Moody's", "frequency": "monthly",
            "low": 0, "high": 25, "extra_months": 0},
    # CPI is an index, so a yearly change needs 12 months before the window opens.
    "CPIAUCSL": {"title": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
                 "owner": "U.S. Bureau of Labor Statistics", "frequency": "monthly",
                 "low": 15, "high": 1000, "extra_months": 12},
}


class MacroError(Exception):
    """Something the owner should see. The script stops instead of using doubtful data."""


def page_url(series_id):
    return f"https://fred.stlouisfed.org/series/{series_id}"


def window_start(today, years=YEARS):
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # Feb. 29
        return today.replace(year=today.year - years, day=28)


def months_before(day, months):
    index = day.year * 12 + day.month - 1 - months
    return dt.date(index // 12, index % 12 + 1, 1)


def read_series(series_id, folder=DOWNLOADS, today=None):
    """Read and check one file. Returns None if it is not there yet. A missing value stays None."""
    spec = SERIES[series_id]
    today = today or dt.datetime.now(dt.timezone.utc).date()
    path = Path(folder) / f"{series_id}.csv"
    if not path.exists():
        return None
    body = path.read_bytes()
    rows = list(csv.reader(body.decode("utf-8-sig").splitlines()))
    if len(rows) < 2 or len(rows[0]) != 2 or rows[0][1] != series_id or rows[0][0] not in ("observation_date", "DATE"):
        raise MacroError(f"{path.name}: the header is {rows[0] if rows else 'empty'}, not a date and {series_id}. "
                         "Is it the right file?")
    data = []
    for row in rows[1:]:
        if len(row) != 2:
            raise MacroError(f"{path.name}: bad row {row}.")
        try:
            day = dt.date.fromisoformat(row[0])
            value = None if row[1].strip() in ("", ".") else float(row[1])
        except ValueError as e:
            raise MacroError(f"{path.name}: bad row {row}.") from e
        if value is not None and not spec["low"] <= value <= spec["high"]:
            raise MacroError(f"{path.name}: {value} on {day} is outside {spec['low']} to {spec['high']}. "
                             "The units may have been changed before downloading.")
        data.append((day, value))
    days = [d for d, _ in data]
    if days != sorted(set(days)):
        raise MacroError(f"{path.name}: dates are out of order or repeated.")
    _check_frequency(path.name, days, spec["frequency"])
    need = months_before(window_start(today).replace(day=1), spec["extra_months"])
    if days[0] > need:
        raise MacroError(f"{path.name} starts on {days[0]}, and the page needs {need}. "
                         f"Choose the longest range on {page_url(series_id)} before downloading.")
    known = [d for d, v in data if v is not None]
    if not known:
        raise MacroError(f"{path.name} has no values.")
    downloaded = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
    return {"id": series_id, "rows": data, "downloaded_utc": downloaded.isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "first": days[0].isoformat(),
            "last_value_date": known[-1].isoformat(), "missing": sum(v is None for _, v in data),
            "old": (today - downloaded.date()).days > OLD_AFTER_DAYS, **spec}


def _check_frequency(name, days, frequency):
    if len(days) < 24:
        raise MacroError(f"{name} has only {len(days)} rows.")
    if frequency == "daily" and statistics.median((b - a).days for a, b in zip(days, days[1:])) > 3:
        raise MacroError(f"{name} is not daily. Set the frequency back to daily before downloading.")
    if frequency == "monthly":
        steps = {(b.year * 12 + b.month) - (a.year * 12 + a.month) for a, b in zip(days, days[1:])}
        if steps != {1} or {d.day for d in days} != {1}:
            raise MacroError(f"{name} is not monthly with one row a month.")


def read_all(folder=DOWNLOADS, today=None):
    return {series_id: read_series(series_id, folder, today) for series_id in SERIES}


def update_manifest(found, folder=DOWNLOADS, now=None):
    """Log a file the first time its contents are seen. It keeps no copy of the data."""
    path = Path(folder) / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {}
    stamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    for series_id, s in found.items():
        if s is None:
            continue
        log = manifest.setdefault(series_id, [])
        if not log or log[-1]["sha256"] != s["sha256"]:
            log.append({"first_read_utc": stamp, "downloaded_utc": s["downloaded_utc"], "sha256": s["sha256"],
                        "bytes": s["bytes"], "rows": len(s["rows"]), "first": s["first"],
                        "last_value_date": s["last_value_date"], "missing": s["missing"], "source": page_url(series_id)})
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(manifest, indent=1))
    temp.replace(path)
    return manifest


def main():
    try:
        found = read_all()
    except MacroError as e:
        sys.exit(f"Stopped: {e}")
    update_manifest(found)
    for series_id, s in found.items():
        if s is None:
            print(f"{series_id}: not downloaded yet. Save it as sensors/macro/downloads/{series_id}.csv from {page_url(series_id)}")
            continue
        note = f"  OLD: older than {OLD_AFTER_DAYS} days" if s["old"] else ""
        print(f"{series_id}: downloaded {s['downloaded_utc'][:10]}, {len(s['rows'])} rows, latest value {s['last_value_date']}, "
              f"{s['missing']} missing{note}")


if __name__ == "__main__":
    main()
