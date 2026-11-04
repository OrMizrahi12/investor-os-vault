"""Cash lesson, step 1: turn the saved downloads into one monthly file. No network.

    uv run --no-project --with xlrd python -I sensors/cash/prepare.py

Reads sensors/cash/downloads/. Writes sensors/cash/cache/monthly.csv and annual.csv.
Stops if the files look wrong. See "cash" in sensors/README.md for the sources and their terms.
"""
import csv
import datetime as dt
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import xlrd

HERE = Path(__file__).resolve().parent
DL = HERE / "downloads"
CACHE = HERE / "cache"
SOURCES = {
    "ie_data.xls": ("https://shillerdata.com/", "Shiller, U.S. Stock Markets 1871-Present and CAPE Ratio"),
    "histretSP.xls": ("https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html", "Damodaran, Historical Returns"),
    "bills_2002_2023.csv": ("https://home.treasury.gov/interest-rates-data-csv-archive", "Treasury daily bill rates archive"),
    "bills_2024.csv": ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value=2024", "Treasury daily bill rates 2024"),
    "bills_2025.csv": ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value=2025", "Treasury daily bill rates 2025"),
    "bills_2026.csv": ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value=2026", "Treasury daily bill rates 2026"),
}


def read_shiller():
    sheet = xlrd.open_workbook(DL / "ie_data.xls").sheet_by_name("Data")
    head = [" ".join(str(sheet.cell_value(r, c)).split()) for c in range(13) for r in [7]]
    assert head[0] == "Date" and head[1] == "P" and head[4] == "CPI" and head[9] == "Price" and head[12] == "CAPE", head
    rows = {}
    for r in range(8, sheet.nrows):
        raw = sheet.cell_value(r, 0)
        if not isinstance(raw, float):
            continue
        year = int(raw)
        month = round((raw - year) * 100)
        assert 1 <= month <= 12, raw
        cape = sheet.cell_value(r, 12)
        rows[(year, month)] = {
            "price": sheet.cell_value(r, 1), "cpi": sheet.cell_value(r, 4), "real_tr": sheet.cell_value(r, 9),
            "cape": cape if isinstance(cape, float) else None,
        }
    keys = sorted(rows)
    assert [k[0] * 12 + k[1] for k in keys] == list(range(keys[0][0] * 12 + keys[0][1], keys[-1][0] * 12 + keys[-1][1] + 1))
    last_cpi = rows[keys[-1]]["cpi"]
    for v in rows.values():  # his real series is scaled to the last CPI, so this undoes it
        v["tr"] = v["real_tr"] * v["cpi"] / last_cpi
    return rows


def read_bill_months():
    """Average each month's daily 13-week coupon-equivalent rate."""
    days = defaultdict(list)
    for name in ("bills_2002_2023.csv", "bills_2024.csv", "bills_2025.csv", "bills_2026.csv"):
        with open(DL / name, newline="") as f:
            reader = csv.reader(f)
            head = [h.strip().lower() for h in next(reader)]
            col = head.index("13 weeks coupon equivalent")
            for row in reader:
                day = dt.datetime.strptime(row[0], "%m/%d/%Y").date()
                if row[col].strip() not in ("", "N/A"):
                    value = float(row[col])
                    assert -1 < value < 12, (day, value)
                    days[(day.year, day.month)].append(value)
    return {k: sum(v) / len(v) for k, v in days.items()}, sum(len(v) for v in days.values())


def read_damodaran():
    sheet = xlrd.open_workbook(DL / "histretSP.xls").sheet_by_name("Returns by year")
    assert sheet.cell_value(19, 1).startswith("S&P 500 (includes dividends)") and sheet.cell_value(19, 3) == "3-month T.Bill"
    out = {}
    for r in range(20, sheet.nrows):
        y = sheet.cell_value(r, 0)
        if isinstance(y, float) and 1900 < y < 2100:
            out[int(y)] = (sheet.cell_value(r, 1), sheet.cell_value(r, 3))
    assert min(out) == 1928 and max(out) >= 2025
    return out


def main():
    shiller = read_shiller()
    bills, n_days = read_bill_months()
    damo = read_damodaran()
    CACHE.mkdir(exist_ok=True)
    with open(CACHE / "annual.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "sp500_tr", "tbill"])
        for y in sorted(damo):
            w.writerow([y, f"{damo[y][0]:.8f}", f"{damo[y][1]:.8f}"])
    with open(CACHE / "monthly.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "price", "cpi", "tr", "cape", "bill_pct", "bill_source"])
        for (y, m), v in sorted(shiller.items()):
            if (y, m) in bills:
                rate, src = bills[(y, m)], "treasury"
            elif y in damo:
                rate, src = damo[y][1] * 100, "damodaran_year"  # before Jan. 2002 only: the year's average
            else:
                rate, src = None, ""
            w.writerow([y, m, f"{v['price']:.4f}", f"{v['cpi']:.4f}", f"{v['tr']:.6f}", "" if v["cape"] is None else f"{v['cape']:.4f}",
                        "" if rate is None else f"{rate:.5f}", src])
    log = {n: {"url": u, "what": w, "bytes": (DL / n).stat().st_size, "sha256": hashlib.sha256((DL / n).read_bytes()).hexdigest(),
               "downloaded_utc": dt.datetime.fromtimestamp((DL / n).stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")}
           for n, (u, w) in SOURCES.items()}
    log["bill_days_read"] = n_days
    (CACHE / "manifest.json").write_text(json.dumps(log, indent=1))
    print("months", len(shiller), "bill months", len(bills), "bill days", n_days, "damodaran years", min(damo), max(damo))


if __name__ == "__main__":
    main()
