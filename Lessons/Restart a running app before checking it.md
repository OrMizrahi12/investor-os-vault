# Restart a running app before checking it

*Written 2026-11-04.*

## What happened

Claude caught both of these while checking the Company page in Chrome. No wrong result reached the owner.

- **Old code on screen.** Claude changed `dashboard/view.py`, reran the browser check on a board it had already started, and the check passed. The screenshots still showed the old wording. A running Streamlit reads each screen file again, but keeps the `data.py` and `view.py` it first imported. So a pass on that board said nothing about the new code. Only opening a screenshot showed it.
- **A wrong address.** Claude measured Home at `/home`. That is not a page: Home lives at `/`. A "Page not found" box covered the page, and `measure_home.py` reported every heading as covered. It looked like a fault in the new code until the screenshot showed the box.

## What changed

- `dashboard/tools/look_company.py` starts its own board and stops it after, so it cannot check old code.
- `dashboard/README.md` says new code needs a restart.

## What it does not say

That the board the owner keeps open is up to date. One left running shows old code until it is restarted.
