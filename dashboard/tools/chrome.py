"""Drive headless Chrome over its debugging port, with no extra package: Streamlit already brings websockets.

For checks by hand only. The app never imports this. It starts Chrome and writes a throwaway profile.
"""

import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
import urllib.request

from websockets.asyncio.client import connect


class Chrome:
    def __init__(self, port=9333, binary="google-chrome"):
        self.port, self.binary = port, binary
        self.seq, self.requests = 0, []

    async def __aenter__(self):
        self.profile = tempfile.mkdtemp(prefix="board-chrome-")
        self.proc = subprocess.Popen([self.binary, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run", "--disable-dev-shm-usage",
                                      "--disable-background-networking", "--disable-component-update", "--disable-sync",
                                      f"--remote-debugging-port={self.port}", f"--user-data-dir={self.profile}", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                pages = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json"))
                target = next(p for p in pages if p["type"] == "page")
                break
            except (OSError, StopIteration):
                await asyncio.sleep(.1)
        else:
            raise RuntimeError("Chrome did not open its debugging port.")
        self.ws = await connect(target["webSocketDebuggerUrl"], max_size=200_000_000, proxy=None)
        await self.send("Page.enable")
        await self.send("Runtime.enable")
        await self.send("Network.enable")
        return self

    async def __aexit__(self, *_):
        await self.ws.close()
        self.proc.terminate()
        self.proc.wait(timeout=10)
        shutil.rmtree(self.profile, ignore_errors=True)

    async def send(self, method, **params):
        self.seq += 1
        await self.ws.send(json.dumps({"id": self.seq, "method": method, "params": params}))
        while True:
            message = json.loads(await asyncio.wait_for(self.ws.recv(), 60))
            if message.get("method") == "Network.requestWillBeSent":
                self.requests.append(message["params"]["request"]["url"])
            if message.get("id") == self.seq:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    async def size(self, width, height, dark=False):
        await self.send("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
        await self.send("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "dark" if dark else "light"}])

    async def js(self, expression):
        out = await self.send("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in out:
            raise RuntimeError(json.dumps(out["exceptionDetails"])[:500])
        return out["result"].get("value")

    async def go(self, url, ready, seconds=40):
        """Load a page and wait until `ready`, a JS expression, is true and Streamlit has stopped running."""
        await self.send("Page.navigate", url=url)
        await self.wait(ready, seconds)

    async def wait(self, ready, seconds=40):
        check = f"!!({ready}) && !document.querySelector('[data-testid=stStatusWidget]')"
        for _ in range(seconds * 5):
            if await self.js(check):
                await asyncio.sleep(.5)
                return
            await asyncio.sleep(.2)
        raise TimeoutError(f"Not ready after {seconds}s: {ready}")

    async def shot(self, path):
        out = await self.send("Page.captureScreenshot", format="png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(out["data"]))
