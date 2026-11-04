"""Look at a broken_copy.py folder in real headless Chrome. For checks by hand. The app never imports this.

    .venv/bin/python dashboard/tools/look_broken.py <the copy> <folder for screenshots>

It starts a fresh board inside the copy on a spare port, and stops it after. It reports, for each screen: the words of the banner and the failed-sensor lines, any error, sideways scroll,
and any host other than this computer asked for. Home must still fit one laptop screen.
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

SCREENS = (("home", "/"), ("company-list", "/company"), ("company-corning", "/company?company=GLW"), ("portfolio", "/portfolio"), ("ideas", "/ideas"), ("journal", "/journal"))
METRICS = """JSON.stringify((() => { const m = document.querySelector('[data-testid=stMain]'); return {
  banner: [...document.querySelectorAll('.d-testcopy')].map(x => x.textContent.slice(0, 60)), lines: [...document.querySelectorAll('.d-run')].map(x => x.textContent),
  ages: document.querySelectorAll('.d-age').length, exceptions: document.querySelectorAll('[data-testid=stException]').length, problems: [...document.querySelectorAll('.d-problem')].map(x => x.textContent.slice(0, 160)),
  scrollsAcross: m.scrollWidth > m.clientWidth, box: [m.scrollHeight, m.clientHeight]}; })())"""


async def main(base, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    async with Chrome(port=9337) as chrome:
        await chrome.size(1366, 768)
        for name, path in SCREENS:
            await chrome.go(base + path, "document.querySelector('.d-testcopy') && document.querySelector('[data-testid=stMain]') && !document.querySelector('[data-testid=stSkeleton]')", 60)
            await asyncio.sleep(1.5)
            report[name] = json.loads(await chrome.js(METRICS))
            await chrome.shot(folder / f"{name}.png")
        report["other hosts asked for"] = sorted({u.split("/")[2] for u in chrome.requests if u.startswith("http") and not u.split("/")[2].startswith("127.0.0.1")})
    print(json.dumps(report, indent=1, ensure_ascii=False))


def start_board(copy, port=8505):
    python = Path(__file__).resolve().parents[2] / ".venv/bin/python"
    board = subprocess.Popen([str(python), "-m", "streamlit", "run", "app.py", "--server.port", str(port)], cwd=Path(copy) / "dashboard",
                             env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(Path(copy) / ".empty-home")}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(150):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1)
            return board, f"http://127.0.0.1:{port}"
        except OSError:
            time.sleep(.2)
    board.terminate()
    raise RuntimeError("The board did not start.")


if __name__ == "__main__":
    process, url = start_board(sys.argv[1])
    try:
        asyncio.run(main(url, sys.argv[2]))
    finally:
        process.terminate()
        process.wait(timeout=10)
