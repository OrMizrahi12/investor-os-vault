"""Save what each screen says, as plain words, one file for each. For checks by hand, from inside a test copy. The app never imports this.

    python dashboard/tools/read_screens.py <folder> [days to move the clock]

It runs the app in this folder's copy through Streamlit's test tool. Moving the clock changes this process only: the app has no switch for it, and no file changes.
"""

import datetime as dt
import html
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
os.chdir(HERE)  # Streamlit reads .streamlit/config.toml from the working folder, and the app shows no data without it
sys.path.insert(0, str(HERE))
import data  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

SCREENS = (("home", "screens/home.py", None), ("company-list", "screens/company.py", None), ("company-corning", "screens/company.py", "GLW"), ("portfolio", "screens/portfolio.py", None),
           ("ideas", "screens/ideas.py", None), ("journal", "screens/journal.py", None))


def words(markup):
    text = re.sub(r"<style.*?</style>", " ", markup, flags=re.S)
    text = re.sub(r"</(?:div|p|tr|li|h\d|section|table)>", "\n", text)
    return "\n".join(line.strip() for line in html.unescape(re.sub(r"<[^>]+>", " ", text)).splitlines() if line.strip())


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    later = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    if later:
        real_now, real_today = data.now_utc, data.local_today
        data.now_utc = lambda: real_now() + dt.timedelta(days=later)
        data.local_today = lambda: real_today() + dt.timedelta(days=later)
    summary = {}
    for name, screen, company in SCREENS:
        page = AppTest.from_file(str(HERE / "app.py"), default_timeout=120).run()
        page.switch_page(screen)
        if company:
            page.query_params["company"] = company
        page.run()
        text = words("\n".join(h.proto.body for h in page.get("html")))
        (folder / f"{name}.txt").write_text(text + "\n")
        summary[name] = {"errors": [str(x.value)[:200] for x in page.exception], "lines": len(text.splitlines()),
                         "says": [line[:240] for line in text.splitlines() if re.search(r"failed|FAILED|past my|Past my|8-K watcher|TEST COPY", line)][:40]}
    (folder / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps({k: {"errors": v["errors"], "lines": v["lines"], "says": len(v["says"])} for k, v in summary.items()}))


if __name__ == "__main__":
    main()
