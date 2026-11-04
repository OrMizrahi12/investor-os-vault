"""Check the coach's guard by calling it the way Claude Code does.

    .venv/bin/python -I sensors/coach/test_guard.py

Works in a temporary copy of the guard, so it touches no real decision file.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL = Path(__file__).resolve().parents[2] / ".claude/hooks/coach-guard.py"
tmp = Path(tempfile.mkdtemp())
(tmp / ".claude/hooks").mkdir(parents=True)
shutil.copy(REAL, tmp / ".claude/hooks/coach-guard.py")
(tmp / "Journal").mkdir()
D = tmp / "Journal/decisions"
SCRATCH = "/tmp/claude-1000/-x/abc/scratchpad/in.json"
fails = 0


def call(tool, **tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": str(tmp)}
    return subprocess.run([sys.executable, str(tmp / ".claude/hooks/coach-guard.py")], input=json.dumps(payload), text=True, capture_output=True).returncode


def check(name, want, got):
    global fails
    ok = (want == "allow") == (got == 0) and got in (0, 2)
    fails += not ok
    print(("ok  " if ok else "FAIL"), want.ljust(5), name)


VIEW = "---\ncompany: X\nstage: view written\n---\n\n# X\n\n## My view\n\nWritten before anything was shown.\n\n- **Action:** buy\n"
name = "Journal/decisions/2026-11-03 X.md"

# Before any view is on file: the gate is shut.
check("read before the view", "block", call("Read", file_path="Companies/Corning.md"))
check("grep before the view", "block", call("Bash", command="grep -i buy Rules/sizing.md"))
check("skill before the view", "block", call("Skill", skill="portfolio-manager"))
check("edit before the view", "block", call("Edit", file_path=name, old_string="a", new_string="b"))
check("scratch JSON before the view", "block", call("Write", file_path=SCRATCH, content="{}"))
check("first write with the system's view in it", "block", call("Write", file_path=name, content=VIEW + "\n## The system's view\nno position\n"))
check("first write with no stage", "block", call("Write", file_path=name, content="## My view\nbuy\n"))
check("first write with no view", "block", call("Write", file_path=name, content="---\nstage: view written\n---\n"))
check("write to the wrong folder", "block", call("Write", file_path="Portfolio/Paper portfolio.md", content=VIEW))
check("write to a company note", "block", call("Write", file_path="Companies/Corning.md", content=VIEW))
check("write with a bad name", "block", call("Write", file_path="Journal/decisions/x.md", content=VIEW))
check("write climbing out", "block", call("Write", file_path="Journal/decisions/../2026-11-03 X.md", content=VIEW))
check("the first write itself", "allow", call("Write", file_path=name, content=VIEW))

# Create what the allowed write would create; the guard itself writes nothing.
D.mkdir()
(tmp / name).write_text(VIEW)

check("read after the view", "allow", call("Read", file_path="Companies/Corning.md"))
check("the skill", "allow", call("Skill", skill="portfolio-manager"))
check("another skill", "block", call("Skill", skill="valuation"))
check("scratch JSON after the view", "allow", call("Write", file_path=SCRATCH, content="{}"))
check("scratch file that is not JSON", "block", call("Write", file_path=SCRATCH.replace(".json", ".md"), content="x"))
check("overwrite the decision file", "block", call("Write", file_path=name, content=VIEW))
check("second decision on the same day", "allow", call("Write", file_path="Journal/decisions/2026-11-03 X 2.md", content=VIEW))
check("edit the owner's words", "block", call("Edit", file_path=name, old_string="- **Action:** buy", new_string="- **Action:** hold"))
check("edit the view's heading", "block", call("Edit", file_path=name, old_string="## My view", new_string="## Our view"))
check("edit across into the view", "block", call("Edit", file_path=name, old_string="# X\n\n## My view", new_string="# X\n"))
check("replace_all", "block", call("Edit", file_path=name, old_string="view written", new_string="compared", replace_all=True))
check("add a second view", "block", call("Edit", file_path=name, old_string="stage: view written", new_string="stage: compared\n\n## My view\nhold"))
check("stage change", "allow", call("Edit", file_path=name, old_string="stage: view written", new_string="stage: compared\nnote: x"))
check("edit a company note", "block", call("Edit", file_path="Companies/Corning.md", old_string="a", new_string="b"))
check("edit the portfolio", "block", call("Edit", file_path="Portfolio/Paper portfolio.md", old_string="a", new_string="b"))
check("grep inside", "allow", call("Bash", command='grep -n "Corning" Journal/README.md'))
check("grep outside", "block", call("Bash", command="grep root /etc/passwd"))
check("ls inside", "allow", call("Bash", command="ls Lessons"))
check("date", "allow", call("Bash", command="date +%F"))
check("date setting the clock", "block", call("Bash", command="date -s 2020-01-01"))
check("jq", "allow", call("Bash", command="jq .x sensors/a.json"))
check("pm on scratch", "allow", call("Bash", command=f'.venv/bin/python -I {".claude/skills/portfolio-manager/scripts/pm.py"} {SCRATCH} --portfolio "Portfolio/Paper portfolio.md"'))
check("pm on asset", "allow", call("Bash", command=".venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py .claude/skills/portfolio-manager/assets/corning-2026-11-03.json"))
check("pm with a what-if", "allow", call("Bash", command=f".venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py {SCRATCH} --what-if-size 5000"))
check("pm, unknown option", "block", call("Bash", command=f".venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py {SCRATCH} --save x"))
check("other python", "block", call("Bash", command=".venv/bin/python -I sensors/prices/prices.py"))
check("redirect", "block", call("Bash", command="ls > x"))
check("chain", "block", call("Bash", command="ls; rm -rf ."))
check("rm", "block", call("Bash", command="rm x"))
check("web tool", "block", call("WebFetch", url="https://example.com"))
check("bad input", "block", call("Write", nothing="here"))

# Once compared, the gate shuts again.
(tmp / name).write_text(VIEW.replace("stage: view written", "stage: compared"))
check("read after the file is closed", "block", call("Read", file_path="Companies/Corning.md"))

# A whole run in order, as the coach makes it. Each stage must reach the next, and
# changing the stage line early must not lock the coach out of its own file.
run = "Journal/decisions/2026-11-04 Y.md"
check("run: read before the view", "block", call("Read", file_path="Rules/sizing.md"))
check("run: writes the view", "allow", call("Write", file_path=run, content=VIEW))
(tmp / run).write_text(VIEW)
check("run: reads the vault", "allow", call("Read", file_path="Rules/sizing.md"))
check("run: runs the skill", "allow", call("Skill", skill="portfolio-manager"))
check("run: saves inputs", "allow", call("Write", file_path=SCRATCH, content="{}"))
check("run: runs pm.py", "allow", call("Bash", command=f".venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py {SCRATCH}"))
check("run: closes the stage early", "allow", call("Edit", file_path=run, old_string="stage: view written", new_string="stage: compared"))
(tmp / run).write_text(VIEW.replace("stage: view written", "stage: compared"))
check("run: still adds its sections", "allow", call("Edit", file_path=run, old_string="- **Action:** buy\n", new_string="- **Action:** buy\n\n## The system's view\n"))
check("run: still cannot touch the view", "block", call("Edit", file_path=run, old_string="- **Action:** buy", new_string="- **Action:** hold"))
check("run: adds plain text inside the view", "block", call("Edit", file_path=run, old_string="- **Action:** buy\n", new_string="- **Action:** buy\n- **Size:** more\n"))
check("run: adds a section from mid-view", "block", call("Edit", file_path=run, old_string="Written before anything was shown.", new_string="Written before anything was shown.\n\n## Other\n"))
check("run: edit of a file that does not exist", "block", call("Edit", file_path="Journal/decisions/2026-11-04 Z.md", old_string="a", new_string="b"))

shutil.rmtree(tmp)
print(f"{fails} failed")
sys.exit(1 if fails else 0)
