"""Break one sensor on a labelled test copy, as if it failed overnight, and save what each screen then says. For checks by hand. The app never imports this.

    .venv/bin/python dashboard/tools/broken_copy.py <new folder outside the vault>

The real vault is only read. The copy gets a TEST_COPY.txt, so every screen carries the banner, and its own full copy of sensors/edgar, because a run writes there.
Three guards hold for each command it runs in the copy: the network goes to a dead port, HOME is an empty folder so no bot token can be found, and its working folder is the copy.
So nothing can reach SEC, Yahoo or my phone, and the real Journal, Inbox and sensors are not touched.

What it does, in the copy:
  1. Breaks the 8-K watcher: watch.py exits with a made-up SEC failure, the way the real one stops on an error (sys.exit("Stopped: ...")).
  2. Runs the real sensors/daily/collect.py, which runs that watcher and the radar and writes the digest.
  3. Saves what each screen says at this point: "died", as if the Desktop run died before it wrote a brief.
  4. Writes the brief from the digest's items, in the form step 4 of Playbooks/Daily run.md asks, then runs the real sensors/daily/publish.py. This stands in for the model's reading. It is the one step a real run does differently.
  5. Saves what each screen says again: "briefed".
  6. Saves a third reading with the clock moved 8 days, to show the words of my age limits on real screens. No file changes for this: read_screens.py moves it in its own process.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
COPIED = ("dashboard", "sensors", "Companies", "Research", "Inbox", "Journal", "Catalysts", "Lessons", "Rules", "Portfolio")
BANNER = "TEST COPY. The 8-K watcher was broken on purpose in this copy, as if it failed overnight. It is not my vault, and nothing here happened."
BREAK = 'import sys\nsys.exit("Stopped: TEST COPY BREAK, made up: SEC did not answer the filing list request.")\n'


def run(copy, *args):
    home = copy / ".empty-home"
    home.mkdir(exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "",
           "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9", "http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9", "NO_PROXY": ""}
    done = subprocess.run([sys.executable, *args], cwd=copy, env=env, capture_output=True, text=True, timeout=590)
    print(f"--- {' '.join(args)}: exit {done.returncode}")
    print((done.stdout + done.stderr)[-1500:])
    return done


def write_brief(copy):
    """Step 4's form, from the digest's own items. No model read them, so each line says so."""
    path = sorted((copy / "sensors/daily/runs").glob("*.json"))[-1]
    d = json.loads(path.read_text())
    parts = {"Red": [], "Orange": [], "Info": []}
    for item in d["items"]:
        day = item["filed"] or d["today"]
        web = str(item["url"]).startswith("http")
        source = f'[{item["form"]}, {day}]({item["url"]})' if web else f'`sensors/daily/runs/{d["stem"]}.json`, {day}'
        parts[item["level"]].append(f'- {source}, {item["rule"]}: {item["summary"][:220]} {item.get("token", "")}. Not read: this copy has no model.'.replace("\n", " "))
    body = "\n\n".join(f'### {level}\n\n' + ("\n".join(lines) or "- Nothing.") for level, lines in parts.items())
    (copy / d["brief_path"]).write_text(f'**Since {d["since_text"]}:** {len(d["items"])} items, written by the test tool.\n\n{body}\n')
    return d


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    copy = Path(sys.argv[1]).resolve()
    if copy == VAULT or VAULT in copy.parents:
        sys.exit("Refused: the test copy must be outside the vault.")
    if copy.exists():
        sys.exit(f"Refused: {copy} already exists.")
    copy.mkdir(parents=True)
    for name in COPIED:
        shutil.copytree(VAULT / name, copy / name, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
    (copy / ".claude/guardrails").mkdir(parents=True)
    shutil.copy2(VAULT / ".claude/guardrails/blocked.jsonl", copy / ".claude/guardrails/blocked.jsonl")
    (copy / "TEST_COPY.txt").write_text(BANNER + "\n")

    watch = copy / "sensors/8k-watch/watch.py"
    watch.write_text(BREAK + watch.read_text())

    out = copy / "screens-said"
    reader = str(copy / "dashboard/tools/read_screens.py")
    run(copy, reader, str(out / "before"))
    collected = run(copy, "sensors/daily/collect.py")
    if collected.returncode:
        sys.exit("collect.py itself stopped, which is a finding: see above.")
    run(copy, reader, str(out / "died"))
    d = write_brief(copy)
    run(copy, "sensors/daily/publish.py")
    run(copy, reader, str(out / "briefed"))
    run(copy, reader, str(out / "briefed-8-days-later"), "8")
    print(json.dumps({"copy": str(copy), "sensors": [{k: r[k] for k in ("name", "ok")} for r in d["sensors"]], "items": [(i["level"], i["rule"], i["summary"][:90]) for i in d["items"]]}, indent=1))


if __name__ == "__main__":
    main()
