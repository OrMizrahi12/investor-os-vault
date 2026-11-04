"""EDGAR sensor: pull one company's filing list and financial facts from SEC, and cache them.

Run from the project root:
    uv run python sensors/edgar/edgar.py GLW
    uv run python sensors/edgar/edgar.py GLW --refresh
    uv run python sensors/edgar/edgar.py GLW --document 0000024741-26-000124

Writes to sensors/edgar/cache/CIK##########/:
    submissions*.json, companyfacts.json   SEC's files, unchanged
    filings.jsonl                          every filing, one per line
    facts.jsonl                            every number, with its form, filing date and accession
    manifest.json                          where each file came from and when
"""

import argparse
import datetime as dt
import gzip
import hashlib
import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETTINGS = HERE / "settings.toml"
CACHE = HERE / "cache"
SEC_HOSTS = {"www.sec.gov", "data.sec.gov"}  # my email goes to these hosts and nowhere else
MAX_AGE_HOURS = 24
RETRIES = 4


class EdgarError(Exception):
    """Something the owner should see. The script stops instead of writing doubtful data."""


def load_settings(path=SETTINGS):
    try:
        sec = tomllib.loads(Path(path).read_text())["sec"]
        name, email, rate = sec["name"], sec["email"], sec["requests_per_second"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as e:
        raise EdgarError(f"Cannot read {path}: {e!r}") from e
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise EdgarError(f"{path}: 'email' is not an email address.")
    if not 0 < rate < 10:
        raise EdgarError(f"{path}: 'requests_per_second' must be above 0 and below 10.")
    return {"user_agent": f"{name} {email}", "rate": rate}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect would be an extra request the limiter never saw, possibly to another host."""

    def redirect_request(self, *args, **kwargs):
        return None


class SecClient:
    """Every SEC request goes through get(), which declares us and spaces the requests."""

    def __init__(self, user_agent, rate, opener=None, clock=time.monotonic, sleep=time.sleep):
        self.user_agent = user_agent
        self.interval = 1.0 / rate
        self.opener = opener or urllib.request.build_opener(_NoRedirect)
        self.clock, self.sleep = clock, sleep
        self.sent = []  # the clock time of every request sent

    def _wait_turn(self):
        if self.sent:
            wait = self.sent[-1] + self.interval - self.clock()
            if wait > 0:
                self.sleep(wait)
        self.sent.append(self.clock())

    def get(self, url):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in SEC_HOSTS:
            raise EdgarError(f"Refusing to send the User-Agent to a non-SEC address: {url}")
        request = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        })
        for attempt in range(RETRIES + 1):
            self._wait_turn()
            try:
                with self.opener.open(request, timeout=60) as response:
                    return _decode(response.read(), response.headers.get("Content-Encoding"))
            except urllib.error.HTTPError as e:
                # 403 is how SEC answers a blocked tool. Retrying would only make that worse.
                if e.code not in (429, 500, 502, 503, 504) or attempt == RETRIES:
                    raise EdgarError(f"SEC answered {e.code} for {url}") from e
                self.sleep(_retry_seconds(e.headers.get("Retry-After"), attempt))
            except urllib.error.URLError as e:
                if attempt == RETRIES:
                    raise EdgarError(f"Could not reach {url}: {e.reason}") from e
                self.sleep(_retry_seconds(None, attempt))
        raise AssertionError("unreachable")

    def busiest_second(self):
        """The most requests that started inside any one-second window."""
        return max((sum(1 for t in self.sent if s <= t < s + 1) for s in self.sent), default=0)


def _decode(body, encoding):
    if encoding == "gzip":
        return gzip.decompress(body)
    if encoding == "deflate":
        return zlib.decompress(body)
    return body


def _retry_seconds(retry_after, attempt):
    try:
        return max(float(retry_after), 1.0)
    except (TypeError, ValueError):
        return 2.0 ** (attempt + 1)


class Cache:
    """One folder per company. A file younger than max_age_hours is reused without a request."""

    def __init__(self, folder, client_factory, max_age_hours):
        self.folder = Path(folder)
        self.client_factory = client_factory
        self.max_age = dt.timedelta(hours=max_age_hours)
        self.manifest_path = self.folder / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text()) if self.manifest_path.exists() else {}

    def fetch(self, name, url):
        path = self.folder / name
        entry = self.manifest.get(name)
        if path.exists() and entry and entry["url"] == url:
            age = now_utc() - dt.datetime.fromisoformat(entry["retrieved_utc"])
            if age < self.max_age:
                return path.read_bytes()
        body = self.client_factory().get(url)
        self.folder.mkdir(parents=True, exist_ok=True)
        _write_atomic(path, body)
        self.manifest[name] = {
            "url": url,
            "retrieved_utc": now_utc().isoformat(timespec="seconds"),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        _write_atomic(self.manifest_path, json.dumps(self.manifest, indent=1).encode())
        return body


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def _write_atomic(path, data):
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(data)
    temp.replace(path)


def find_cik(identifier, client_factory):
    """A plain number is a CIK. Anything else is a ticker, looked up in SEC's own list."""
    if identifier.isdigit():
        return int(identifier)
    tickers = Cache(CACHE, client_factory, 24 * 7).fetch(
        "company_tickers.json", "https://www.sec.gov/files/company_tickers.json")
    for row in json.loads(tickers).values():
        if row["ticker"].upper() == identifier.upper():
            return int(row["cik_str"])
    raise EdgarError(f"SEC's ticker list has no {identifier}.")


def filing_url(cik, accession, primary_document):
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{primary_document}"


def flatten_filings(cik, submissions, older_pages):
    """Join the recent list and the older pages into one list, newest first."""
    columns = [submissions["filings"]["recent"]] + older_pages
    filings = {}
    for column in columns:
        for i, accession in enumerate(column["accessionNumber"]):
            document = column["primaryDocument"][i]
            filings[accession] = {
                "accession": accession,
                "form": column["form"][i],
                "filed": column["filingDate"][i],
                "report_date": column["reportDate"][i],
                "items": column["items"][i],
                "primary_document": document,
                "description": column["primaryDocDescription"][i],
                "url": filing_url(cik, accession, document) if document else None,
            }
    return sorted(filings.values(), key=lambda f: (f["filed"], f["accession"]), reverse=True)


def flatten_facts(companyfacts, filings):
    """Turn SEC's nested facts into flat rows. A number with no provenance stops the run."""
    urls = {f["accession"]: f["url"] for f in filings}
    rows = []
    for taxonomy, concepts in companyfacts["facts"].items():
        for concept, body in concepts.items():
            for unit, entries in body["units"].items():
                for e in entries:
                    missing = [k for k in ("form", "filed", "accn", "end", "val") if e.get(k) in (None, "")]
                    if missing:
                        raise EdgarError(f"{taxonomy}:{concept} ({unit}) has a number with no {missing}: {e}")
                    rows.append({
                        "taxonomy": taxonomy,
                        "concept": concept,
                        "label": body.get("label"),
                        "unit": unit,
                        "value": e["val"],
                        "start": e.get("start"),
                        "end": e["end"],
                        "form": e["form"],
                        "filed": e["filed"],
                        "accession": e["accn"],
                        "filing_url": urls.get(e["accn"]),
                        "fy": e.get("fy"),
                        "fp": e.get("fp"),
                        "frame": e.get("frame"),
                    })
    return rows


def write_jsonl(path, rows):
    _write_atomic(path, "".join(json.dumps(r) + "\n" for r in rows).encode())


def pull(identifier, refresh=False, document=None, settings_path=SETTINGS):
    settings = load_settings(settings_path)
    clients = []

    def client_factory():
        if not clients:
            clients.append(SecClient(settings["user_agent"], settings["rate"]))
        return clients[0]

    cik = find_cik(identifier, client_factory)
    tag = f"CIK{cik:010d}"
    cache = Cache(CACHE / tag, client_factory, 0 if refresh else MAX_AGE_HOURS)

    submissions = json.loads(cache.fetch("submissions.json", f"https://data.sec.gov/submissions/{tag}.json"))
    # The main file holds only the latest filings. Older ones sit in extra pages.
    older = [json.loads(cache.fetch(p["name"], f"https://data.sec.gov/submissions/{p['name']}"))
             for p in submissions["filings"]["files"]]
    companyfacts = json.loads(cache.fetch("companyfacts.json", f"https://data.sec.gov/api/xbrl/companyfacts/{tag}.json"))

    filings = flatten_filings(cik, submissions, older)
    facts = flatten_facts(companyfacts, filings)
    write_jsonl(cache.folder / "filings.jsonl", filings)
    write_jsonl(cache.folder / "facts.jsonl", facts)

    print(f"{submissions['name']} ({tag}): {len(filings)} filings, {len(facts)} numbers")
    print(f"Newest filing: {filings[0]['form']}, filed {filings[0]['filed']}")
    print(f"Numbers whose filing is not in the filing list: {sum(1 for f in facts if not f['filing_url'])}")

    if document:
        match = next((f for f in filings if f["accession"] == document), None)
        if not match or not match["url"]:
            raise EdgarError(f"{document} is not in {submissions['name']}'s filing list.")
        (cache.folder / "documents").mkdir(exist_ok=True)
        cache.fetch(f"documents/{match['primary_document']}", match["url"])
        print(f"Saved {match['form']} filed {match['filed']}: documents/{match['primary_document']}")

    client = clients[0] if clients else None
    print(f"Requests to SEC: {len(client.sent) if client else 0}. "
          f"Busiest second: {client.busiest_second() if client else 0}.")
    return cache.folder


def main():
    parser = argparse.ArgumentParser(description="Pull a company's filings and facts from SEC, and cache them.")
    parser.add_argument("company", help="ticker (GLW) or CIK (24741)")
    parser.add_argument("--refresh", action="store_true", help="ignore the cache and ask SEC again")
    parser.add_argument("--document", metavar="ACCESSION", help="also save this filing's main document")
    args = parser.parse_args()
    try:
        pull(args.company, args.refresh, args.document)
    except EdgarError as e:
        sys.exit(f"Stopped: {e}")


if __name__ == "__main__":
    main()
