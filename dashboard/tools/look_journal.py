"""Look at the Journal screen in real headless Chrome. For checks by hand. The app never imports this.

    .venv/bin/python dashboard/tools/look_journal.py <folder for screenshots>

It starts a fresh board on a spare port and stops it after. It reports what a test cannot see: whether a fold really opens with no call to the server, whether each part draws, what scrolls sideways, whether a day link lands on its day, and any host other than this computer asked for.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome import Chrome  # noqa: E402
from look_ideas import start_board  # noqa: E402

PARTS = ("By day", "What we decided", "What we left open", "Decisions", "Lessons", "Search")
METRICS = """JSON.stringify((() => { const main = document.querySelector('[data-testid=stMain]');
  return {head: (document.querySelector('h2') || {}).textContent, folds: document.querySelectorAll('details.j-fold').length, open: document.querySelectorAll('details.j-fold[open]').length, rows: document.querySelectorAll('table.d-table tbody tr').length,
          exceptions: document.querySelectorAll('[data-testid=stException]').length, problems: [...document.querySelectorAll('.d-problem')].map(p => p.textContent.slice(0, 140)),
          scrollsAcross: main.scrollWidth > main.clientWidth || document.documentElement.scrollWidth > innerWidth, height: main.scrollHeight}; })())"""


async def click(chrome, spot):
    for kind in ("mousePressed", "mouseReleased"):
        await chrome.send("Input.dispatchMouseEvent", type=kind, x=spot[0], y=spot[1], button="left", clickCount=1)


async def spot_of(chrome, expression):
    return await chrome.js(f"(() => {{ const el = {expression}; el.scrollIntoView({{block: 'center'}}); const r = el.getBoundingClientRect(); return [r.left + 12, r.top + r.height / 2]; }})()")


async def main(base, folder):
    report = {}
    async with Chrome(port=9336) as chrome:
        for width in (1366, 600):
            await chrome.size(width, 768)
            await chrome.go(base + "/journal", "document.querySelector('h1') && document.querySelector('[role=radiogroup]')")
            for part in PARTS:
                label = f"[...document.querySelectorAll('[role=radiogroup] label')].find(l => l.textContent.trim() === {json.dumps(part)})"
                await click(chrome, await spot_of(chrome, label))
                await chrome.wait(f"[...document.querySelectorAll('h2')].some(h => h.textContent.trim() === {json.dumps(part)})")
                if part == "Search":
                    box = await spot_of(chrome, "document.querySelector('[data-testid=stTextInput] input')")
                    await click(chrome, box)
                    await chrome.send("Input.insertText", text="Corning")
                    await chrome.send("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter", windowsVirtualKeyCode=13, text="\r")
                    await chrome.send("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter", windowsVirtualKeyCode=13)
                    await chrome.wait("document.querySelectorAll('table.d-table tbody tr').length > 0")
                await asyncio.sleep(.5)
                report[f"{width} {part}"] = json.loads(await chrome.js(METRICS))
                await chrome.shot(str(Path(folder) / f"journal-{width}-{part.replace(' ', '-').lower()}.png"))
        await chrome.size(1366, 768)
        await chrome.go(base + "/journal?day=2026-11-03", "document.querySelector('details.j-fold')")
        report["address picks the day"] = await chrome.js("document.querySelector('[data-testid=stSelectbox]').textContent")
        report["blocks on that day"] = await chrome.js("document.querySelectorAll('details.j-fold').length")
        await chrome.js("window.__sent = 0")
        before = len(chrome.requests)
        summary = "document.querySelectorAll('details.j-fold')[1].querySelector('summary')"
        await click(chrome, await spot_of(chrome, summary))
        await asyncio.sleep(.5)
        report["fold opens on a click"] = await chrome.js("document.querySelectorAll('details.j-fold')[1].open")
        report["fold has words"] = await chrome.js("document.querySelectorAll('details.j-fold')[1].querySelectorAll('.d-note').length")
        report["asked the server when opened"] = len(chrome.requests) - before
        await chrome.shot(str(Path(folder) / "journal-fold-open.png"))
        report["other hosts asked for"] = sorted({u.split("/")[2] for u in chrome.requests if u.startswith("http") and not u.split("/")[2].startswith("127.0.0.1")})
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    board, address = start_board(Path(__file__).resolve().parents[1], 8531)
    try:
        asyncio.run(main(address, out))
    finally:
        board.terminate()
        board.wait(timeout=10)
