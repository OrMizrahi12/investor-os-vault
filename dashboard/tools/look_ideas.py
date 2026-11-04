"""Look at Ideas and alerts in real headless Chrome. For checks by hand. The app never imports this.

    .venv/bin/python dashboard/tools/look_ideas.py <folder for screenshots>

It starts two fresh boards on spare ports: the real vault, and a labelled busy copy made by busy_copy.py in that folder, because the real Journal has no alert lines yet.
It stops both after. It reports what a test cannot see: whether the jump links scroll, whether each filter really narrows the table in the browser, what scrolls sideways,
whether the table's head stays on top of a scrolled box, and any host other than this computer asked for.
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

READY = "[...document.querySelectorAll('h2')].some(h => h.textContent.includes('How old each source is')) && document.querySelector('.i-flow')"
METRICS = """JSON.stringify((() => {
  const main = document.querySelector('[data-testid=stMain]');
  return {heads: [...document.querySelectorAll('h2')].map(h => h.textContent.trim()), tiles: [...document.querySelectorAll('.i-tile')].map(t => t.textContent.trim()),
          labels: [...document.querySelectorAll('.i-lead')].length, exceptions: document.querySelectorAll('[data-testid=stException]').length,
          problems: [...document.querySelectorAll('.d-problem')].map(p => p.textContent.slice(0, 140)), scrollsAcross: main.scrollWidth > main.clientWidth || document.documentElement.scrollWidth > innerWidth,
          filters: [...document.querySelectorAll('[data-testid=stMultiSelect]')].map(c => c.textContent.trim()), filterLine: ([...document.querySelectorAll('p.d-text b')].find(b => b.textContent.startsWith('Showing')) || {}).parentElement?.textContent, height: main.scrollHeight};
})())"""
ALERT_ROWS = "[...document.querySelectorAll('table.d-table')].filter(t => [...t.querySelectorAll('th')].some(th => th.textContent === 'Ruled or waiting')).flatMap(t => [...t.querySelectorAll('tbody tr')]).map(r => [r.cells[0].textContent.trim(), r.cells[1].textContent.trim(), r.cells[6].textContent.trim().slice(0, 40)])"


async def pick(chrome, index, option):
    """Choose an option in the nth multiselect by clicking it, the exact one. Typing, then Enter, would take Streamlit's "Select 2 matches" row: O2 also matches O12."""
    box = await chrome.js(f"(() => {{ const el = document.querySelectorAll('[data-testid=stMultiSelect] input')[{index}]; el.scrollIntoView({{block: 'center'}}); const r = el.getBoundingClientRect(); return [r.left + 10, r.top + r.height / 2]; }})()")
    for kind in ("mousePressed", "mouseReleased"):
        await chrome.send("Input.dispatchMouseEvent", type=kind, x=box[0], y=box[1], button="left", clickCount=1)
    await asyncio.sleep(.5)
    await chrome.send("Input.insertText", text=option)  # the list only draws the rows in view, so narrow it first
    await asyncio.sleep(.5)
    spot = await chrome.js(f"(() => {{ const o = [...document.querySelectorAll('[role=option]')].find(x => x.textContent.trim() === {json.dumps(option)}); o.scrollIntoView({{block: 'nearest'}}); const r = o.getBoundingClientRect(); return [r.left + 10, r.top + r.height / 2]; }})()")
    for kind in ("mousePressed", "mouseReleased"):
        await chrome.send("Input.dispatchMouseEvent", type=kind, x=spot[0], y=spot[1], button="left", clickCount=1)
    await asyncio.sleep(.3)
    await chrome.send("Input.dispatchKeyEvent", type="rawKeyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
    await asyncio.sleep(2.5)
    await chrome.wait(READY)


async def to(chrome, words):
    await chrome.js(f"[...document.querySelectorAll('h2,h3')].find(h => h.textContent.trim().startsWith({json.dumps(words)})).scrollIntoView()")
    await asyncio.sleep(.8)


async def main(real, busy, folder):
    report = {}
    async with Chrome(port=9335) as chrome:
        await chrome.size(1366, 768)
        await chrome.go(real + "/ideas", READY)
        await asyncio.sleep(1)
        report["real"] = json.loads(await chrome.js(METRICS))
        await chrome.shot(folder / "real-top.png")

        # A jump link: does the page really move to its section?
        before = await chrome.js("document.querySelector('[data-testid=stMain]').scrollTop")
        await chrome.js("[...document.querySelectorAll('.i-jump a')].find(a => a.getAttribute('href') === '#rejection-log').click()")
        await asyncio.sleep(1.5)
        report["jump link"] = {"before": before, "after": await chrome.js("document.querySelector('[data-testid=stMain]').scrollTop"),
                               "head in view": await chrome.js("(() => { const h = [...document.querySelectorAll('h2')].find(x => x.textContent.includes('Rejection log')).getBoundingClientRect(); return h.top >= 0 && h.top < innerHeight; })()")}
        await chrome.shot(folder / "real-log.png")
        await chrome.js("[...document.querySelectorAll('.i-tile')].find(a => a.getAttribute('href') === '#stage-decision').click()")
        await asyncio.sleep(1.5)
        await chrome.shot(folder / "real-decision.png")
        await to(chrome, "Lead on the screen")
        await chrome.js("document.querySelector('.i-box').scrollTop = 600")
        await asyncio.sleep(.5)
        report["sticky head"] = await chrome.js("(() => { const box = document.querySelector('.i-box'); const th = box.querySelector('th'); const a = th.getBoundingClientRect(), b = box.getBoundingClientRect(); return {offset: Math.round(a.top - b.top), background: getComputedStyle(th).backgroundColor}; })()")
        await chrome.shot(folder / "real-leads.png")
        await to(chrome, "Watchlist")
        await chrome.shot(folder / "real-watchlist.png")
        await to(chrome, "Alerts")
        await chrome.shot(folder / "real-alerts.png")
        for name, width, height, dark in (("real-420", 420, 800, False), ("real-dark", 1366, 768, True)):
            await chrome.size(width, height, dark)
            await chrome.go(real + "/ideas", READY)
            await asyncio.sleep(1)
            report[name] = json.loads(await chrome.js(METRICS))
            await chrome.shot(folder / f"{name}.png")
            await chrome.js("[...document.querySelectorAll('.i-jump a')].find(a => a.getAttribute('href') === '#rejection-log').click()")
            await asyncio.sleep(1.5)
            await chrome.shot(folder / f"{name}-log.png")
        await chrome.size(1366, 768)

        await chrome.go(busy + "/ideas", READY)
        await asyncio.sleep(1)
        report["busy"] = json.loads(await chrome.js(METRICS))
        report["busy, all lines"] = await chrome.js(ALERT_ROWS)
        await to(chrome, "Tested by the hunt")
        await chrome.shot(folder / "busy-tested.png")
        await to(chrome, "Alerts")
        await chrome.shot(folder / "busy-alerts.png")
        await pick(chrome, 0, "Red")
        report["busy, Level Red"] = {"line": json.loads(await chrome.js(METRICS))["filterLine"], "rows": await chrome.js(ALERT_ROWS)}
        await to(chrome, "Alerts")
        await chrome.shot(folder / "busy-red.png")
        await pick(chrome, 3, "Ruled")
        report["busy, Red and Ruled"] = {"line": json.loads(await chrome.js(METRICS))["filterLine"], "rows": await chrome.js(ALERT_ROWS)}
        await chrome.go(busy + "/ideas", READY)
        await asyncio.sleep(1)
        await pick(chrome, 1, "O2")
        report["busy, Rule O2"] = {"filters": json.loads(await chrome.js(METRICS))["filters"], "line": json.loads(await chrome.js(METRICS))["filterLine"], "rows": await chrome.js(ALERT_ROWS)}
        await chrome.go(busy + "/ideas", READY)
        await asyncio.sleep(1)
        await pick(chrome, 2, "Event run")
        report["busy, Routine Event run"] = {"line": json.loads(await chrome.js(METRICS))["filterLine"], "rows": len(await chrome.js(ALERT_ROWS))}

        # A date filter, typed the way a person types it.
        await chrome.go(busy + "/ideas", READY)
        await asyncio.sleep(1)
        await chrome.js("document.querySelector('[data-testid=stDateInput]').scrollIntoView({block: 'center'})")
        await asyncio.sleep(1)
        box = await chrome.js("(() => { const r = document.querySelector('[data-testid=stDateInput]').getBoundingClientRect(); return [r.left + 40, r.bottom - 18]; })()")
        for kind in ("mousePressed", "mouseReleased"):
            await chrome.send("Input.dispatchMouseEvent", type=kind, x=box[0], y=box[1], button="left", clickCount=1)
        await asyncio.sleep(.5)
        for digit in time.strftime("%Y%m%d"):  # the control has one field each for year, month and day
            await chrome.send("Input.dispatchKeyEvent", type="keyDown", text=digit, key=digit)
            await chrome.send("Input.dispatchKeyEvent", type="keyUp", key=digit)
            await asyncio.sleep(.08)
        await asyncio.sleep(.5)
        for kind in ("mousePressed", "mouseReleased"):  # the date only goes in when its calendar closes, so click away, as a person would
            await chrome.send("Input.dispatchMouseEvent", type=kind, x=30, y=500, button="left", clickCount=1)
        await asyncio.sleep(3)
        await chrome.wait(READY)
        await chrome.shot(folder / "busy-from-today.png")
        report["busy, From today"] = {"line": json.loads(await chrome.js(METRICS))["filterLine"], "rows": len(await chrome.js(ALERT_ROWS))}

        # Home still fits, since the shared CSS changed. Home's link still lands here.
        await chrome.go(real + "/", "document.querySelector('.h-grid')")
        await asyncio.sleep(1)
        report["home"] = json.loads(await chrome.js("JSON.stringify((m => ({box: [m.scrollHeight, m.clientHeight], scrolls: m.scrollHeight > m.clientHeight}))(document.querySelector('[data-testid=stMain]')))"))
        report["other hosts asked for"] = sorted({u.split("/")[2] for u in chrome.requests if u.startswith("http") and not u.split("/")[2].startswith("127.0.0.1")})
    print(json.dumps(report, indent=1))


def start_board(dashboard, port):
    python = Path(__file__).resolve().parents[2] / ".venv/bin/python"
    board = subprocess.Popen([str(python), "-m", "streamlit", "run", "app.py", "--server.port", str(port)], cwd=dashboard,
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
    folder = Path(sys.argv[1]).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    copy = folder / "busy"
    python = Path(__file__).resolve().parents[2] / ".venv/bin/python"
    subprocess.run([str(python), str(Path(__file__).with_name("busy_copy.py")), str(copy)], check=True, stdout=subprocess.DEVNULL)
    real, real_url = start_board(Path(__file__).resolve().parents[1], 8504)
    busy, busy_url = start_board(copy / "dashboard", 8505)
    try:
        asyncio.run(main(real_url, busy_url, folder))
    finally:
        for process in (real, busy):
            process.terminate()
            process.wait(timeout=10)
