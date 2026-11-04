"""Tests for the launcher. Run from the project root:
    .venv/bin/python dashboard/launch/test_board.py

The first class starts and stops the real board on the real app, on Linux. Its browser is a small script that writes down the address. Its record lives in a throwaway folder, so a board you have open is never touched.
The Mac and Windows branches run here only with the system calls stood in for. A real Mac or Windows has not run them, and these tests cannot say they work there.
"""

import ast
import configparser
import contextlib
import hashlib
import http.server
import io
import json
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import board  # noqa: E402

NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class RealBoard(unittest.TestCase):
    """The whole path, through the wrapper a double-click runs."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.opened = self.temp / "opened.txt"
        browser = self.temp / "browser.sh"
        browser.write_text(f'#!/bin/sh\necho "$1" >> "{self.opened}"\n')
        browser.chmod(0o755)
        self.env = {**os.environ, "INVESTOR_BOARD_HOME": str(self.temp / "state"), "BROWSER": f"{browser} %s", "PYTHONDONTWRITEBYTECODE": "1"}
        self.state_path = self.temp / "state" / hashlib.sha256(str(ROOT).encode()).hexdigest()[:12] / "board.json"
        self.addCleanup(self.run_launcher, "stop")

    def run_launcher(self, action):
        return subprocess.run(["sh", str(HERE / "launch.sh"), action], env=self.env, capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL)

    def state(self):
        return json.loads(self.state_path.read_text())

    def urls(self):
        return self.opened.read_text().split() if self.opened.exists() else []

    def wait_for_urls(self, count):
        deadline = time.monotonic() + 10  # the browser stub runs on its own
        while len(self.urls()) < count and time.monotonic() < deadline:
            time.sleep(.05)
        return self.urls()

    def alive(self, pid):
        return bool(board.process_words(pid))

    def test_start_reuse_restart_and_stop(self):
        out = self.run_launcher("start")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        first = self.state()
        self.assertTrue(board.healthy(first["port"]))
        self.assertEqual(self.wait_for_urls(1), [f"http://127.0.0.1:{first['port']}/"])
        with NO_PROXY.open(f"http://127.0.0.1:{first['port']}/", timeout=10) as page:
            self.assertEqual(page.status, 200)
        self.assertIn("streamlit", board.process_words(first["pid"]))  # it outlives the launcher that started it
        self.assertIn("version 1", out.stdout)

        again = self.run_launcher("start")
        self.assertEqual(again.returncode, 0, again.stdout)
        self.assertIn("reused", again.stdout)
        self.assertEqual(self.state()["pid"], first["pid"])
        self.assertEqual(len(self.wait_for_urls(2)), 2)

        status = self.run_launcher("status")
        self.assertIn(f"http://127.0.0.1:{first['port']}/", status.stdout)
        self.assertIn(str(first["pid"]), status.stdout)

        # A board on older code would show old screens, so it is not reused.
        self.state_path.write_text(json.dumps({**first, "code": "older"}))
        changed = self.run_launcher("start")
        self.assertEqual(changed.returncode, 0, changed.stdout)
        self.assertIn("code changed", changed.stdout)
        second = self.state()
        self.assertNotEqual(second["pid"], first["pid"])
        self.assertFalse(self.alive(first["pid"]))
        self.assertTrue(board.healthy(second["port"]))

        stopped = self.run_launcher("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stdout)
        self.assertIn("has stopped", stopped.stdout)
        self.assertFalse(board.healthy(second["port"]))
        self.assertFalse(self.alive(second["pid"]))
        self.assertFalse(self.state_path.exists())

        twice = self.run_launcher("stop")
        self.assertEqual(twice.returncode, 0)
        self.assertIn("No board started by this launcher", twice.stdout)

    def test_a_stale_record_never_harms_the_process_that_now_has_its_number(self):
        other = subprocess.Popen(["sleep", "300"])
        self.addCleanup(other.wait)
        self.addCleanup(other.kill)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps({"pid": other.pid, "port": board.LAST_PORT, "root": str(ROOT), "code": "x"}))
        self.assertIn("No board started", self.run_launcher("stop").stdout)
        self.assertIsNone(other.poll())
        self.state_path.write_text(json.dumps({"pid": other.pid, "port": board.LAST_PORT, "root": str(ROOT), "code": "x"}))
        self.assertEqual(self.run_launcher("start").returncode, 0)
        self.assertNotEqual(self.state()["pid"], other.pid)
        self.assertIsNone(other.poll())
        self.assertEqual(self.run_launcher("stop").returncode, 0)
        self.assertIsNone(other.poll())

    def test_a_board_from_another_vault_is_left_alone(self):
        other = subprocess.Popen(["sleep", "300"])
        self.addCleanup(other.wait)
        self.addCleanup(other.kill)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps({"pid": other.pid, "port": board.LAST_PORT, "root": "/another/vault", "code": "x"}))
        with mock.patch.dict(os.environ, self.env):
            self.assertIsNone(board.ours())
        self.assertEqual(self.run_launcher("stop").returncode, 0)
        self.assertIsNone(other.poll())

    def test_something_else_on_the_port_is_left_alone(self):
        with mock.patch.dict(os.environ, self.env):
            port = board.free_port()

        class Quiet(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"not a board")

            def log_message(self, *_):
                pass

        other = http.server.ThreadingHTTPServer(("127.0.0.1", port), Quiet)
        threading.Thread(target=other.serve_forever, daemon=True).start()
        self.addCleanup(other.server_close)
        self.addCleanup(other.shutdown)
        out = self.run_launcher("start")
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertGreater(self.state()["port"], port)
        self.assertEqual(self.wait_for_urls(1), [f"http://127.0.0.1:{self.state()['port']}/"])
        self.assertEqual(self.run_launcher("stop").returncode, 0)
        with NO_PROXY.open(f"http://127.0.0.1:{port}/", timeout=5) as page:
            self.assertEqual(page.read(), b"not a board")

    def test_two_quick_double_clicks_make_one_board(self):
        runs = [subprocess.Popen(["sh", str(HERE / "launch.sh"), "start"], env=self.env, stdout=subprocess.PIPE, text=True, stdin=subprocess.DEVNULL) for _ in range(3)]
        outs = [r.communicate(timeout=180)[0] for r in runs]
        self.assertEqual([r.returncode for r in runs], [0, 0, 0], outs)
        self.assertEqual(sum("Starting the board" in o for o in outs), 1, outs)
        self.assertEqual(sum("reused" in o for o in outs), 2, outs)
        self.assertEqual(len(set(self.wait_for_urls(3))), 1)


class Quiet(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        patch = mock.patch.dict(os.environ, {"INVESTOR_BOARD_HOME": str(self.temp / "state"), "INVESTOR_BOARD_DESKTOP": str(self.temp)})
        patch.start()
        self.addCleanup(patch.stop)

    def quiet(self, call, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = call(*args)
        return result, out.getvalue()


class Basics(Quiet):
    def test_home_is_the_root_because_home_is_not_a_page(self):
        self.assertEqual(board.home_url(8501), "http://127.0.0.1:8501/")

    def test_the_only_address_off_this_computer_is_one_it_prints(self):
        text = (HERE / "board.py").read_text()
        hosts = {found.rstrip(":") for found in re.findall(r"https?://([^/\s\"'{]+)", text)}
        self.assertEqual(hosts - {"127.0.0.1", "www.python.org"}, set())
        self.assertNotIn("0.0.0.0", text)

    def test_it_runs_on_the_standard_library_alone(self):
        for node in ast.walk(ast.parse((HERE / "board.py").read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                self.assertIn(name.split(".")[0], sys.stdlib_module_names)

    def test_an_old_python_is_told_what_to_do_and_nothing_is_run(self):
        with mock.patch.object(board.sys, "version_info", (3, 9, 0)), mock.patch.object(board.subprocess, "run") as run:
            with self.assertRaises(SystemExit) as stopped:
                board.set_up()
        self.assertIn("python.org", str(stopped.exception.code))
        run.assert_not_called()

    def test_setup_prefers_the_lock_file_through_uv(self):
        with mock.patch.object(board.shutil, "which", return_value="/x/uv"), mock.patch.object(board.subprocess, "run") as run, mock.patch.object(board, "has_streamlit", return_value=True):
            run.return_value.returncode = 0
            _, said = self.quiet(board.set_up)
        self.assertEqual(run.call_args_list[0].args[0], ["/x/uv", "sync", "--frozen"])
        self.assertIn("PyPI", said)

    def test_setup_with_no_uv_pins_what_the_lock_file_says(self):
        with mock.patch.object(board.shutil, "which", return_value=None), mock.patch.object(board.subprocess, "run") as run, mock.patch.object(board, "has_streamlit", return_value=True):
            run.return_value.returncode = 0
            self.quiet(board.set_up)
        install = run.call_args_list[1].args[0]
        self.assertEqual(install[1:4], ["-m", "pip", "install"])
        self.assertTrue(any(re.fullmatch(r"streamlit==\d+\.\d+\.\d+", word) for word in install))

    def test_a_failed_setup_says_so(self):
        with mock.patch.object(board.shutil, "which", return_value="/x/uv"), mock.patch.object(board.subprocess, "run") as run:
            run.return_value.returncode = 1
            with self.assertRaises(SystemExit) as stopped:
                self.quiet(board.set_up)
        self.assertIn("internet", stopped.exception.code)

    def test_a_board_that_will_not_start_shows_its_log_and_records_nothing(self):
        process = mock.Mock()
        process.poll.return_value = 1
        with mock.patch.object(board, "has_streamlit", return_value=True), mock.patch.object(board, "launch", return_value=process), mock.patch.object(board, "healthy", return_value=False), mock.patch.object(board, "open_home") as opened:
            board.log_file().write_text("the line that explains it\n")
            with self.assertRaises(SystemExit) as stopped:
                self.quiet(board.start)
        self.assertIn("the line that explains it", stopped.exception.code)
        self.assertFalse(board.state_file().exists())
        opened.assert_not_called()

    def test_no_browser_still_gives_the_address(self):
        with mock.patch.object(board.webbrowser, "open", return_value=False):
            _, said = self.quiet(board.open_home, 8503)
        self.assertIn("http://127.0.0.1:8503/", said)

    def test_the_record_is_outside_the_vault(self):
        with mock.patch.dict(os.environ, {"INVESTOR_BOARD_HOME": ""}):
            with mock.patch.object(board.Path, "mkdir"):
                self.assertNotIn(ROOT, board.state_file().parents)

    def test_a_dead_launchers_lock_does_not_block_for_ever(self):
        path = board.state_dir() / "lock"
        path.write_text("")
        old = time.time() - board.LOCK_SECONDS - 5
        os.utime(path, (old, old))
        with board.Lock():
            self.assertTrue(path.exists())
        self.assertFalse(path.exists())

    def test_the_code_stamp_sees_a_changed_screen_and_not_a_changed_test(self):
        self.assertEqual(board.code_stamp(), board.code_stamp())
        names = []
        real = board.Path.stat

        def spy(path, *args, **kwargs):
            names.append(path.name)
            return real(path, *args, **kwargs)

        with mock.patch.object(board.Path, "stat", spy):
            board.code_stamp()
        for name in ("app.py", "data.py", "view.py", "journal.py", "VERSION", "config.toml", "prices.py"):
            self.assertIn(name, names)
        self.assertFalse([n for n in names if n.startswith("test_")])


class OtherSystems(Quiet):
    """Stand-ins for the system calls. These check what would be asked of Windows and a Mac. They do not show that it works there."""

    def test_windows_never_checks_a_process_with_os_kill(self):
        """There, os.kill(pid, 0) ends the process."""
        with mock.patch.object(board, "WINDOWS", True), mock.patch.object(board.os, "kill", side_effect=AssertionError("os.kill on Windows")), mock.patch.object(board.subprocess, "run") as run:
            run.return_value.stdout = '"python.exe","4242","Console","1","99,000 K"'
            self.assertTrue(board.is_our_process(4242))
            self.assertEqual(run.call_args.args[0][0], "tasklist")
            run.return_value.stdout = "INFO: No tasks are running which match the specified criteria."
            self.assertFalse(board.is_our_process(4242))
            board.end_process(4242)
            self.assertEqual(run.call_args.args[0], ["taskkill", "/PID", "4242", "/T", "/F"])

    def test_windows_detaches_the_board_and_uses_its_python(self):
        flags = {"DETACHED_PROCESS": 8, "CREATE_NEW_PROCESS_GROUP": 512, "CREATE_NO_WINDOW": 134217728}
        with mock.patch.object(board, "WINDOWS", True), mock.patch.multiple(board.subprocess, create=True, **flags), mock.patch.object(board.subprocess, "Popen") as popen:
            board.launch(8501)
        args, kwargs = popen.call_args
        self.assertTrue(args[0][0].endswith(str(Path("Scripts/python.exe"))))
        self.assertEqual(kwargs["creationflags"], 8 | 512 | 134217728)
        self.assertNotIn("start_new_session", kwargs)
        self.assertEqual(kwargs["cwd"], board.DASHBOARD)
        self.assertEqual(args[0][1:6], ["-m", "streamlit", "run", "app.py", "--server.port"])

    def test_the_windows_desktop_files_call_the_ones_in_the_vault(self):
        with mock.patch.object(board, "WINDOWS", True):
            files = board.launcher_files()
        self.assertEqual(set(files), {"Start board.bat", "Stop board.bat"})
        for name, words in files.items():
            self.assertIn(f'{board.HERE}\\{name}"', words)
            self.assertIn(board.MARK, words)
            self.assertEqual(words.count("\n"), words.count("\r\n"))

    def test_the_mac_desktop_files_name_the_whole_path_safely(self):
        with mock.patch.object(board, "WINDOWS", False), mock.patch.object(board, "MAC", True):
            files = board.launcher_files()
        self.assertEqual(set(files), {"Start board.command", "Stop board.command"})
        self.assertIn(f"sh '{board.HERE}/launch.sh' start", files["Start board.command"])
        self.assertIn(f"sh '{board.HERE}/launch.sh' stop", files["Stop board.command"])
        self.assertEqual(board.shell_quote("/a b/it's"), "'/a b/it'\\''s'")

    def test_the_files_in_the_folder_call_the_right_action(self):
        for title, action in (("Start board", "start"), ("Stop board", "stop"), ("Put on Desktop", "desktop")):
            bat = (HERE / f"{title}.bat").read_bytes()
            self.assertEqual(bat.count(b"\n"), bat.count(b"\r\n"), title)  # cmd.exe mishandles labels in a file with bare line ends
            self.assertEqual(set(re.findall(rb'board\.py" (\w+)', bat)), {action.encode()})
            self.assertIn(b"pause", bat)
            command = HERE / f"{title}.command"
            self.assertTrue(command.stat().st_mode & stat.S_IXUSR, title)
            self.assertEqual(subprocess.run(["sh", "-n", str(command)]).returncode, 0)
            self.assertTrue(command.read_text().rstrip().endswith(f"launch.sh\" {action}"))
        self.assertEqual(subprocess.run(["sh", "-n", str(HERE / "launch.sh")]).returncode, 0)


class Desktop(Quiet):
    def test_linux_entries_can_be_read_and_keep_the_window_for_a_problem(self):
        with mock.patch.object(board, "WINDOWS", False), mock.patch.object(board, "MAC", False):
            files = board.launcher_files()
        self.assertEqual(set(files), {"Start board.desktop", "Stop board.desktop"})
        for name, action in (("Start board.desktop", "start"), ("Stop board.desktop", "stop")):
            entry = configparser.RawConfigParser(strict=True)
            entry.optionxform = str
            entry.read_string(files[name])
            section = entry["Desktop Entry"]
            self.assertEqual(section["Type"], "Application")
            self.assertEqual(section["Terminal"], "true")
            self.assertTrue(section["Exec"].endswith(f'launch.sh" {action}'))
            self.assertIn(str(board.HERE), section["Exec"])

    def test_a_path_with_odd_characters_is_quoted_as_the_spec_says(self):
        self.assertEqual(board.desktop_quote("/a b/c"), '"/a b/c"')
        self.assertEqual(board.desktop_quote("/a$b"), '"/a\\\\$b"')
        self.assertEqual(board.desktop_quote("/100%"), '"/100%%"')

    def test_it_writes_runnable_files_and_replaces_only_its_own(self):
        with mock.patch.object(board, "WINDOWS", False), mock.patch.object(board, "MAC", False), mock.patch.object(board, "trust") as trust:
            self.quiet(board.put_on_desktop)
            start = self.temp / "Start board.desktop"
            self.assertTrue(start.stat().st_mode & stat.S_IXUSR)
            self.assertEqual(trust.call_count, 2)
            self.quiet(board.put_on_desktop)  # ours, so it may be written again
            (self.temp / "Stop board.desktop").write_text("Someone else's launcher\n")
            with self.assertRaises(SystemExit) as stopped:
                self.quiet(board.put_on_desktop)
            self.assertIn("did not write it", stopped.exception.code)
            self.assertEqual((self.temp / "Stop board.desktop").read_text(), "Someone else's launcher\n")

    def test_no_desktop_folder_writes_nothing(self):
        with mock.patch.dict(os.environ, {"INVESTOR_BOARD_DESKTOP": str(self.temp / "None")}):
            with self.assertRaises(SystemExit) as stopped:
                self.quiet(board.put_on_desktop)
        self.assertIn("work from where they are", stopped.exception.code)


class TheBoardDoesNotDependOnIt(unittest.TestCase):
    def test_the_port_it_starts_from_is_the_one_in_the_settings(self):
        import tomllib

        self.assertEqual(tomllib.loads((board.DASHBOARD / ".streamlit/config.toml").read_text())["server"]["port"], board.FIRST_PORT)

    def test_python_is_new_enough_for_the_project(self):
        import tomllib

        wanted = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["requires-python"]
        self.assertEqual(wanted, f">={board.MIN_PYTHON[0]}.{board.MIN_PYTHON[1]}")

    def test_no_board_port_is_taken_by_the_probe(self):
        with mock.patch.object(board, "FIRST_PORT", 8521), mock.patch.object(board, "LAST_PORT", 8530):
            port = board.free_port()
        with socket.socket() as again:
            again.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            again.bind(("127.0.0.1", port))


if __name__ == "__main__":
    unittest.main(verbosity=1)
