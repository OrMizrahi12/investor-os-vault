"""Look at the Company page in real headless Chrome on a running board. For checks by hand. The app never imports this.

    .venv/bin/python dashboard/tools/look_company.py <folder for screenshots>

It starts its own board on a spare port and stops it after, because a running Streamlit keeps the data.py and view.py it first imported, so a board left
running would show old code. It loads each address, opens every fold, and takes screenshots. It reports what a test cannot see: which address came up, what scrolls sideways,
whether the picker and a neighbor link really go where they say, and any host other than this computer asked for.
"""

import asyncio
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome import Chrome  # noqa: E402

READY = "[...document.querySelectorAll('h1')].some(h => h.textContent.includes('Company')) && document.querySelector('[data-testid=stSelectbox]')"
METRICS = """JSON.stringify((() => {
  const main = document.querySelector('[data-testid=stMain]');
  const heads = [...document.querySelectorAll('h2')].map(h => h.textContent.trim());
  const wide = [...document.querySelectorAll('.stHtml, [data-testid=stHtml]')].filter(el => el.scrollWidth > el.clientWidth + 1 && !el.querySelector('.d-wrap')).length;
  return {url: location.pathname + location.search, picked: (document.querySelector('[data-testid=stSelectbox] input') || {}).value || (document.querySelector('[data-testid=stSelectbox]').textContent || '').trim(),
          headers: heads, scrollsAcross: main.scrollWidth > main.clientWidth || document.documentElement.scrollWidth > innerWidth, widePieces: wide,
          tables: document.querySelectorAll('table.d-table').length, charts: document.querySelectorAll('[data-testid=stVegaLiteChart] canvas, [data-testid=stVegaLiteChart] svg.marks, .vega-embed canvas, .vega-embed svg').length,
          draftLabels: [...document.querySelectorAll('.c-draft')].length, noSource: document.querySelectorAll('.d-nosrc').length, exceptions: document.querySelectorAll('[data-testid=stException]').length,
          problems: [...document.querySelectorAll('.d-problem')].map(p => p.textContent.slice(0, 120)), imgs: document.querySelectorAll('[data-testid=stMain] img').length, height: main.scrollHeight};
})())"""
OPEN_FOLDS = "(() => { const shut = [...document.querySelectorAll('[data-testid=stExpander] details:not([open]) summary')]; shut.forEach(s => s.click()); return shut.length; })()"


async def go(chrome, url):
    await chrome.go(url, READY)
    await asyncio.sleep(1.5)


async def main(base, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    async with Chrome(port=9334) as chrome:

        await chrome.size(1366, 768)
        for label, address in (("corning", "/company?company=GLW"), ("fujikura", "/company?company=Fujikura"), ("att", "/company?company=AT%26T"), ("t-ticker", "/company?company=T"), ("t1", "/company?company=TE"),
                               ("unknown", "/company?company=NOPE"), ("escape", "/company?company=../Rules/my-rules"), ("list", "/company")):
            await go(chrome, base + address)
            report[label] = json.loads(await chrome.js(METRICS))
            await chrome.shot(folder / f"{label}-top.png")

        await go(chrome, base + "/company?company=GLW")
        opened = await chrome.js(OPEN_FOLDS)
        await asyncio.sleep(2)
        report["corning folds opened"] = opened
        report["corning, folds open"] = json.loads(await chrome.js(METRICS))
        for section, name in (("Thesis status", "thesis"), ("Price against value", "value"), ("Price zones and the last close", "zones"), ("Catalysts", "catalysts"), ("Graph neighbors", "neighbors"), ("Corning financial health", "health"), ("History", "history")):
            await chrome.js(f"[...document.querySelectorAll('h2,h3')].find(h => h.textContent.trim().startsWith({json.dumps(section)})).scrollIntoView()")
            await asyncio.sleep(1)
            await chrome.shot(folder / f"corning-{name}.png")

        # A click on a neighbor: does it go to that page's own address?
        await go(chrome, base + "/company?company=GLW")
        await chrome.js("[...document.querySelectorAll('a')].find(a => a.getAttribute('href') === '/company?company=Prysmian').click()")
        await chrome.wait("location.search === '?company=Prysmian' && [...document.querySelectorAll('.c-name')].some(x => x.textContent === 'Prysmian')")
        report["neighbor click"] = json.loads(await chrome.js(METRICS))

        # The picker: does choosing change the address and the page?
        await asyncio.sleep(.6)
        box = await chrome.js("(() => { const r = document.querySelector('[data-testid=stSelectbox] input').getBoundingClientRect(); return [r.left + 40, r.top + r.height / 2]; })()")
        for kind in ("mousePressed", "mouseReleased"):
            await chrome.send("Input.dispatchMouseEvent", type=kind, x=box[0], y=box[1], button="left", clickCount=1)
        await asyncio.sleep(.8)
        await chrome.send("Input.insertText", text="Verizon")
        await asyncio.sleep(.6)
        await chrome.send("Input.dispatchKeyEvent", type="rawKeyDown", key="Enter", code="Enter", windowsVirtualKeyCode=13)
        await chrome.send("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter", windowsVirtualKeyCode=13)
        await chrome.wait("location.search === '?company=VZ' && [...document.querySelectorAll('.c-name')].some(x => x.textContent === 'Verizon')")
        report["picker"] = json.loads(await chrome.js(METRICS))
        await chrome.send("Page.reload")
        await chrome.wait(READY + " && [...document.querySelectorAll('.c-name')].some(x => x.textContent === 'Verizon')")
        report["picker, after reload"] = json.loads(await chrome.js(METRICS))["url"]

        for label, width, height, dark in (("corning-420", 420, 800, False), ("corning-dark", 1366, 768, True), ("fujikura-420", 420, 800, False), ("fujikura-dark", 1366, 768, True)):
            await chrome.size(width, height, dark)
            await go(chrome, base + ("/company?company=GLW" if label.startswith("corning") else "/company?company=Fujikura"))
            report[label] = json.loads(await chrome.js(METRICS))
            await chrome.shot(folder / f"{label}.png")
        await chrome.size(1366, 768)

        # Home still fits, since the shared CSS changed.
        await chrome.go(base + "/", "document.querySelector('.h-grid')")
        await asyncio.sleep(1)
        report["home"] = json.loads(await chrome.js("JSON.stringify((m => ({box: [m.scrollHeight, m.clientHeight], scrolls: m.scrollHeight > m.clientHeight}))(document.querySelector('[data-testid=stMain]')))"))
        report["other hosts asked for"] = sorted({u.split("/")[2] for u in chrome.requests if u.startswith("http") and not u.split("/")[2].startswith("127.0.0.1")})
    print(json.dumps(report, indent=1))


def start_board(port=8503):
    here = Path(__file__).resolve().parents[1]
    board = subprocess.Popen([str(here.parent / ".venv/bin/python"), "-m", "streamlit", "run", "app.py", "--server.port", str(port)], cwd=here,
                             env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1)
            return board, f"http://127.0.0.1:{port}"
        except OSError:
            time.sleep(.2)
    board.terminate()
    raise RuntimeError("The board did not start.")


if __name__ == "__main__":
    process, url = start_board()
    try:
        asyncio.run(main(url, sys.argv[1]))
    finally:
        process.terminate()
        process.wait(timeout=10)
