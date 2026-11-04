"""Measure Home in real headless Chrome on a running board. For checks by hand. The app never imports this.

    .venv/bin/python dashboard/tools/measure_home.py <url> <folder for screenshots> <name>

Streamlit scrolls an inner box, so the document's height always equals the window, and measuring that would always pass.
This measures the box that scrolls (stMain), and it also fails on a block whose rows spill out or a figure that is cut.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome import Chrome  # noqa: E402

READY = "document.querySelector('.h-grid')"
METRICS = """JSON.stringify((() => {
  const m = document.querySelector('[data-testid=stMain]');
  const grid = document.querySelector('.h-grid');
  const bottom = Math.max(...[...grid.querySelectorAll('section')].map(s => s.getBoundingClientRect().bottom));
  const bar = document.querySelector('[data-testid=stHeader]').getBoundingClientRect().bottom;
  const covered = [...document.querySelectorAll('.h-top, .h-block h2')].filter(el => {
    const r = el.getBoundingClientRect(); const hit = document.elementFromPoint(r.left + 5, r.top + r.height / 2);
    if (r.top >= innerHeight) return false;  // further down the page, not covered
    return r.top < bar || !hit || !(el === hit || el.contains(hit));
  }).map(el => el.textContent.slice(0, 40));
  const cut = [...document.querySelectorAll('.h-grid .d-val, .h-grid .h-tag')].filter(el => {
    const r = el.getBoundingClientRect(); const row = el.closest('.h-row, section').getBoundingClientRect();
    return el.scrollWidth > el.clientWidth + 1 || r.right > row.right + 1;
  }).map(el => el.textContent.slice(0, 60));
  return {viewport: [innerWidth, innerHeight], scrollBox: [m.scrollHeight, m.clientHeight], scrollsDown: m.scrollHeight > m.clientHeight,
          scrollsAcross: m.scrollWidth > m.clientWidth || document.documentElement.scrollWidth > innerWidth,
          contentBottom: Math.round(bottom), coveredByTheBar: covered, cutFigures: cut, stacked: getComputedStyle(grid).gridTemplateColumns.split(' ').length === 1,
          order: [...grid.querySelectorAll('section')].map(s => s.dataset.block),
          rows: Object.fromEntries([...grid.querySelectorAll('section')].map(s => [s.dataset.block, s.querySelectorAll('.h-row').length]))};
})())"""


async def smallest_height(chrome, width, top=800, low=300):
    """The shortest window that does not scroll."""
    while top - low > 1:
        mid = (top + low) // 2
        await chrome.size(width, mid)
        await asyncio.sleep(.35)
        over = await chrome.js("(m => m.scrollHeight > m.clientHeight)(document.querySelector('[data-testid=stMain]'))")
        low, top = (mid, top) if over else (low, mid)
    return top


async def main(url, folder, name):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    async with Chrome() as chrome:
        await chrome.size(1366, 650)
        await chrome.go(url, READY)
        for label, width, height, dark in (("1366x650", 1366, 650, False), ("1366x768", 1366, 768, False), ("1920x970", 1920, 970, False), ("1024x650", 1024, 650, False),
                                           ("1366x650 dark", 1366, 650, True), ("900x650", 900, 650, False), ("420x800", 420, 800, False)):
            await chrome.size(width, height, dark)
            await asyncio.sleep(.8)
            report[label] = json.loads(await chrome.js(METRICS))
            await chrome.shot(folder / f'{name}-{label.replace(" ", "-")}.png')
        report["smallest height with no scroll, 1366 wide"] = await smallest_height(chrome, 1366)
        report["smallest height with no scroll, 1280 wide"] = await smallest_height(chrome, 1280)
        report["other hosts asked for"] = sorted({u.split("/")[2] for u in chrome.requests if u.startswith("http") and not u.split("/")[2].startswith("127.0.0.1")})
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:4]))
