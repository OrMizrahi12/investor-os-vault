"""Start, reuse and stop the board with one double-click. The wrappers beside this file call it. Standard library only, so it runs before anything is installed.

    python board.py start     start the board, or reuse the one running, and open Home
    python board.py stop      stop the board this launcher started
    python board.py status    say whether it is running
    python board.py desktop   put Start and Stop launchers on the desktop

It only ever talks to 127.0.0.1, with one exception that says so first: when the .venv is missing, it installs the locked packages. The board stays read-only and local (dashboard/app.py refuses otherwise).

It reuses or stops only a board it started itself and recorded. Anything else on the port is left alone, and the board takes the next free port.
"""

import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHBOARD = HERE.parent
ROOT = DASHBOARD.parent
WINDOWS = os.name == "nt"
MAC = sys.platform == "darwin"
FIRST_PORT, LAST_PORT = 8501, 8520  # 8501 is what dashboard/.streamlit/config.toml names
START_SECONDS = 90
STOP_SECONDS = 10
LOCK_SECONDS = 180  # a lock older than the longest start belongs to a launcher that died
MARK = "investor-os board launcher"  # in every file put on a desktop, so only ours is ever replaced
MIN_PYTHON = (3, 12)  # pyproject.toml
# No proxy for this computer, whatever the environment says.
LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def say(words):
    print(words, flush=True)


def state_dir():
    """Outside the vault, because the tests compare the vault's files before and after a page load, and a running board writes its log here."""
    base = Path(os.environ.get("INVESTOR_BOARD_HOME") or Path.home() / ".investor-os-board")
    folder = base / hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]  # one per copy of the vault
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def state_file():
    return state_dir() / "board.json"


def log_file():
    return state_dir() / "board.log"


def read_state():
    try:
        state = json.loads(state_file().read_text())
        return state if isinstance(state.get("pid"), int) and isinstance(state.get("port"), int) else None
    except (OSError, ValueError, AttributeError):
        return None


def forget():
    try:
        state_file().unlink()
    except OSError:
        pass


def healthy(port, timeout=1.0):
    """Streamlit's own health address, on this computer."""
    try:
        with LOCAL.open(f"http://127.0.0.1:{port}/_stcore/health", timeout=timeout) as reply:
            return reply.status == 200 and reply.read().strip() == b"ok"
    except (OSError, urllib.error.URLError, ValueError):
        return False


def process_words(pid):
    """What the system says this process is, or "" if there is none. Never os.kill(pid, 0) on Windows: there it ends the process."""
    try:
        if WINDOWS:
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=10).stdout
            return out if str(pid) in out else ""
        return subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def is_our_process(pid):
    words = process_words(pid).lower()
    return "python" in words if WINDOWS else "streamlit" in words


def ours():
    """The recorded board, only if all of it still stands: this vault, a Streamlit process with that number, answering on that port."""
    state = read_state()
    if state and state.get("root") == str(ROOT) and is_our_process(state["pid"]) and healthy(state["port"]):
        return state
    return None


def code_stamp():
    """A running board keeps the code it first imported, so a board on older code must not be reused. Size and time of everything it runs."""
    files = [p for folder, pattern in ((DASHBOARD, "*.py"), (DASHBOARD / "screens", "*.py"), (ROOT / "sensors", "*/*.py")) for p in folder.glob(pattern) if not p.name.startswith("test_")]
    files += [DASHBOARD / "VERSION", DASHBOARD / ".streamlit" / "config.toml"]
    digest = hashlib.sha256()
    for path in sorted(files):
        try:
            stat = path.stat()
            digest.update(f"{path}:{stat.st_size}:{stat.st_mtime_ns}\n".encode())
        except OSError:
            digest.update(f"{path}:gone\n".encode())
    return digest.hexdigest()


def venv_python():
    return ROOT / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")


def has_streamlit(python):
    try:
        return subprocess.run([str(python), "-c", "import streamlit"], capture_output=True, timeout=120).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def locked_versions(names=("streamlit", "yfinance")):
    """The versions in uv.lock, so a pip install gets what the tests ran on."""
    import tomllib  # 3.11 and up. By here the Python's age has been checked.

    packages = tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    return [f'{p["name"]}=={p["version"]}' for p in packages if p["name"] in names]


def set_up():
    """First time only: make the .venv from the lock file. It goes to the internet, and says so first. A failure says what to do."""
    if sys.version_info < MIN_PYTHON:
        raise SystemExit(f"The board needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer, and this is {sys.version.split()[0]}. Install one from https://www.python.org/downloads/ and start again.")
    say("First time on this computer: the board's packages are not installed.")
    say("This one time, it downloads them from the Python package site (PyPI). After this, starting the board uses no internet.")
    uv = shutil.which("uv")
    steps = [[uv, "sync", "--frozen"]] if uv else [[sys.executable, "-m", "venv", str(ROOT / ".venv")], [str(venv_python()), "-m", "pip", "install", *locked_versions()]]
    for step in steps:
        if subprocess.run(step, cwd=ROOT).returncode != 0:
            raise SystemExit("Setup did not finish. Check the internet connection and start again. Nothing else was changed.")
    if not has_streamlit(venv_python()):
        raise SystemExit("Setup finished, and the board's Python still cannot load Streamlit. Delete the .venv folder and start again.")


def free_port():
    for port in range(FIRST_PORT, LAST_PORT + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if not WINDOWS:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # a board that just stopped leaves the port waiting a moment
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit(f"Every port from {FIRST_PORT} to {LAST_PORT} is in use on this computer. Close something and start again.")


def launch(port):
    """The board, detached, so closing this window leaves it running. It runs from dashboard/ so its local-only config is read, as run.sh does."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    args = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if WINDOWS else {"start_new_session": True}
    with open(log_file(), "w") as log:
        return subprocess.Popen([str(venv_python()), "-m", "streamlit", "run", "app.py", "--server.port", str(port)], cwd=DASHBOARD, env=env,
                                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **args)


def wait_until_up(process, port):
    deadline = time.monotonic() + START_SECONDS
    while time.monotonic() < deadline:
        if healthy(port):
            return True
        if process.poll() is not None:
            return False
        time.sleep(.25)
    return False


def log_tail(lines=15):
    try:
        return "\n".join(log_file().read_text(errors="replace").splitlines()[-lines:])
    except OSError:
        return "(no log)"


def home_url(port):
    return f"http://127.0.0.1:{port}/"  # Home is at the root. /home is not a page.


def open_home(port):
    url = home_url(port)
    try:
        opened = webbrowser.open(url)
    except webbrowser.Error:
        opened = False
    say(f"Home is at {url}" if opened else f"The browser did not open by itself. Open this address: {url}")


def version():
    try:
        return (DASHBOARD / "VERSION").read_text().strip()
    except OSError:
        return "unknown"


class Lock:
    """Two quick double-clicks must not start two boards. The second waits, then finds the first one's board."""

    def __enter__(self):
        path = state_dir() / "lock"
        deadline = time.monotonic() + LOCK_SECONDS
        while True:
            try:
                os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                self.path = path
                return self
            except FileExistsError:
                try:
                    if time.time() - path.stat().st_mtime > LOCK_SECONDS:
                        path.unlink()
                        continue
                except OSError:
                    continue
                if time.monotonic() > deadline:
                    raise SystemExit(f"Another start is still working. If it is stuck, delete {path} and start again.")
                time.sleep(.25)

    def __exit__(self, *_):
        try:
            self.path.unlink()
        except OSError:
            pass


def end_process(pid):
    if WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30)
        return
    try:
        os.killpg(pid, signal.SIGTERM)  # the launcher made it its own group, so this reaches only the board
    except OSError:
        return
    deadline = time.monotonic() + STOP_SECONDS
    while time.monotonic() < deadline and process_words(pid):
        time.sleep(.2)
    if process_words(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass


def stop_board(state):
    end_process(state["pid"])
    deadline = time.monotonic() + STOP_SECONDS
    while time.monotonic() < deadline and healthy(state["port"], .5):
        time.sleep(.2)
    still = healthy(state["port"], .5)
    if not still:
        forget()
    return not still


def start():
    with Lock():
        stamp = code_stamp()
        state = ours()
        if state and state.get("code") == stamp:
            say(f"The board is already running (version {version()}), so it is reused.")
            open_home(state["port"])
            return 0
        if state:
            say("The board's code changed since it started, so it restarts.")
            if not stop_board(state):
                raise SystemExit(f"The old board on port {state['port']} did not stop, so no new one was started.")
        forget()  # a record with no board behind it, say after a restart of the computer
        if not has_streamlit(venv_python()):
            set_up()
        port = free_port()
        if port != FIRST_PORT:
            say(f"Port {FIRST_PORT} is taken by something this launcher did not start. It is left alone, and the board uses {port}.")
        say(f"Starting the board (version {version()}). This takes a few seconds.")
        process = launch(port)
        if not wait_until_up(process, port):
            if process.poll() is None:
                end_process(process.pid)
            raise SystemExit(f"The board did not start. The end of its log, {log_file()}:\n{log_tail()}")
        state_file().write_text(json.dumps({"pid": process.pid, "port": port, "root": str(ROOT), "code": stamp, "started": time.strftime("%Y-%m-%d %H:%M:%S")}))
        open_home(port)
    return 0


def stop():
    with Lock():
        state = ours()
        if not state:
            forget()
            say("No board started by this launcher is running. A board started by hand with run.sh stops with Ctrl+C in its own window.")
            return 0
        if stop_board(state):
            say(f"The board on port {state['port']} has stopped.")
            return 0
        raise SystemExit(f"The board on port {state['port']} did not stop. Its process number is {state['pid']}.")


def status():
    state = ours()
    say(f"The board is running at {home_url(state['port'])} (version {version()}, started {state.get('started')}, process {state['pid']})." if state else "No board started by this launcher is running.")
    return 0


# ---- The launchers on the desktop ----

def desktop_folder():
    """Where the desktop really is. It can be moved or renamed on Linux and Windows, and Windows may keep it in OneDrive."""
    wanted = os.environ.get("INVESTOR_BOARD_DESKTOP")
    if wanted:
        return Path(wanted)
    if WINDOWS:
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"], capture_output=True, text=True, timeout=30).stdout.strip()
            if out:
                return Path(out)
        except (OSError, subprocess.SubprocessError):
            pass
    elif not MAC:
        try:
            out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=10).stdout.strip()
            if out and out != str(Path.home()):
                return Path(out)
        except (OSError, subprocess.SubprocessError):
            pass
    return Path.home() / "Desktop"


def desktop_quote(path):
    """Quoting inside a .desktop file's Exec line. The spec escapes twice: these characters inside a quoted word, then every backslash as a string value. A percent is doubled."""
    text = str(path)
    for ch in ("\\", '"', "`", "$"):
        text = text.replace(ch, "\\" + ch)
    return '"' + text.replace("\\", "\\\\").replace("%", "%%") + '"'


def shell_quote(path):
    return "'" + str(path).replace("'", "'\\''") + "'"


def launcher_files():
    """Each file to put on the desktop: its name and its words, with this vault's whole path, since a launcher on a desktop cannot find its folder by itself."""
    if WINDOWS:
        return {f"{title}.bat": f'@echo off\r\nrem {MARK}\r\ncall "{str(HERE).replace("%", "%%")}\\{title}.bat"\r\n' for title in ("Start board", "Stop board")}
    if MAC:
        return {f"{title}.command": f'#!/bin/sh\n# {MARK}\nexec sh {shell_quote(HERE / "launch.sh")} {action}\n' for title, action in (("Start board", "start"), ("Stop board", "stop"))}
    entry = "[Desktop Entry]\nVersion=1.0\nType=Application\nName={name}\nComment={comment}. {mark}\nExec=sh {script} {action}\nIcon={icon}\nTerminal=true\nCategories=Office;\n"
    script = desktop_quote(HERE / "launch.sh")
    return {"Start board.desktop": entry.format(name="Start board", comment="Start the investing board and open Home", mark=MARK, script=script, action="start", icon="utilities-system-monitor"),
            "Stop board.desktop": entry.format(name="Stop board", comment="Stop the investing board", mark=MARK, script=script, action="stop", icon="process-stop")}


def trust(path):
    """Linux desktops refuse an unknown launcher until it is marked as trusted. Both marks are the file's own settings, and neither changes what it does. A desktop with neither just asks once."""
    gio = shutil.which("gio")
    if not gio:
        return
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    for args in (["-t", "string", str(path), "metadata::xfce-exe-checksum", checksum], ["-t", "string", str(path), "metadata::trusted", "true"]):
        subprocess.run([gio, "set", *args], capture_output=True, timeout=10)


def put_on_desktop():
    folder = desktop_folder()
    if not folder.is_dir():
        raise SystemExit(f"There is no desktop folder at {folder}. Nothing was written. The Start and Stop files in {HERE} work from where they are.")
    files = launcher_files()
    for name in files:
        target = folder / name
        if target.exists() and MARK not in target.read_text(errors="replace"):
            raise SystemExit(f"{target} is already there, and this launcher did not write it. Nothing was changed. Move that file and try again.")
    for name, words in files.items():
        target = folder / name
        with open(target, "w", newline="") as out:  # as written: a .bat keeps its CRLF
            out.write(words)
        if not WINDOWS:
            target.chmod(0o755)
        if not WINDOWS and not MAC:
            trust(target)
        say(f"Written: {target}")
    say("If this folder ever moves, run this again, because these files name its whole path.")
    return 0


COMMANDS = {"start": start, "stop": stop, "status": status, "desktop": put_on_desktop}


def main(argv):
    if len(argv) != 2 or argv[1] not in COMMANDS:
        say(__doc__)
        return 2
    try:
        return COMMANDS[argv[1]]()
    except SystemExit as stopped:
        if isinstance(stopped.code, str):
            say(stopped.code)
            return 1
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv))
