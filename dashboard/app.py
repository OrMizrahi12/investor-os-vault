"""Local, read-only control board over what the sensors saved. Start it with dashboard/run.sh.

No orders, no broker and nothing sent anywhere. Loading a screen reads files and nothing else.
To get newer data, run a sensor by hand, then reload the page. The screens are in screens/. Plan: PLAN.md.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data  # noqa: E402
import view  # noqa: E402

LABEL = data.test_copy_label()
VERSION = data.board_version()
st.set_page_config(page_title="TEST COPY, made up" if LABEL else f"Investor OS, board v{VERSION}" if VERSION else "Investor OS", layout="wide")

# A run from the wrong folder misses config.toml and gets Streamlit's defaults. Refuse to show the data then.
if st.get_option("browser.gatherUsageStats") or st.get_option("server.address") not in ("127.0.0.1", "localhost"):
    st.html(view.problem("Stopped: Streamlit's local-only settings are not active, so no data is shown. Start it with dashboard/run.sh."))
    st.stop()

st.html(view.CSS)
if LABEL:
    st.html(view.test_copy_banner(LABEL))

# Every screen says it, because a failed sensor stops figures on all of them, and a run that died wrote no Journal line for the waiting list to show.
TROUBLE, UNREAD = data.run_trouble_or_problem()
if UNREAD:
    st.html(view.problem(f"The Daily run's newest digest could not be read: {UNREAD}. The next Daily run would write a new one."))
elif TROUBLE:
    st.html(view.run_trouble_lines(TROUBLE))

# Each screen is a file, because Streamlit's AppTest can only switch to a file-based page.
SCREENS = (("screens/home.py", "Home", "home"), ("screens/company.py", "Company", "company"), ("screens/portfolio.py", "Portfolio and cash", "portfolio"),
           ("screens/ideas.py", "Ideas and alerts", "ideas"), ("screens/journal.py", "Journal", "journal"))
st.navigation([st.Page(path, title=title, url_path=slug, default=slug == "home") for path, title, slug in SCREENS], position="top").run()
