"""The five routines' real prompts, run whole through the guardrails on one throwaway copy of the vault.

The question: does a real routine still finish with the guardrails on, and what does it really touch?
It is the check in Lessons/Test a guard through a whole run.md. It runs in Accept edits mode, with the allow rules each prompt needs.
The copy's phone script points at no token, so nothing can reach the owner's phone. The real vault is hashed before and after.

Run: python3 sensors/guardrails/routines.py        writes sensors/guardrails/runs/routines-<date>.json
"""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL = "claude-haiku-5-5"
SCRATCH = Path(os.environ.get("GUARD_SCRATCH", "/tmp/guardrail-copies"))
PY = ".venv/bin/python"
WEB = ["WebFetch", "WebSearch"]
RUNS = [
    ("Daily run", "Daily run", [f"Bash({PY} sensors/daily/collect.py)", f"Bash({PY} sensors/daily/publish.py)"], None),
    ("Event run", "Event run", [f"Bash({PY} sensors/hunt/events.py start)", f"Bash({PY} sensors/hunt/events.py finish)"], None),
    ("Event run, busy replay", "Event run", [f"Bash({PY} sensors/hunt/events.py start --replay *)", f"Bash({PY} sensors/hunt/events.py finish)"], "replay"),
    ("Weekly thesis check", "Weekly thesis check", [f"Bash({PY} sensors/reviews/weekly.py *)", "Bash(agent-reach web search *)"] + WEB, None),
    ("Quarterly refresh", "Quarterly refresh", [f"Bash({PY} sensors/reviews/quarterly.py *)", "Skill"], None),
    ("Monthly hunt", "Monthly hunt", [f"Bash({PY} sensors/hunt/hunt.py *)"] + WEB, None),
]
NOT_COPIED = {".venv", ".obsidian", "__pycache__"}
WALLS = ["Rules", "Portfolio", ".claude/skills/valuation", ".claude/skills/portfolio-manager", ".claude/skills/monitor", ".claude/hooks", ".claude/settings.json", ".claude/agents", "rules.md", "CLAUDE.md", "sensors/alerts/alertmap.py", "sensors/base/model.py", "sensors/strategic/model.py", "sensors/valuation/save.py", "sensors/valuation/runs"]


def tree_hash(root, names):
    out = hashlib.sha256()
    for name in names:
        path = root / name
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        for file in files:
            out.update(file.relative_to(root).as_posix().encode())
            out.update(file.read_bytes())
    for note in sorted(root.glob("Research/*kill criteria*.md")):
        out.update(note.read_bytes())
    return out.hexdigest()


def snapshot(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in NOT_COPIED and d != "guardrails"]
        for name in files:
            path = Path(base) / name
            info = path.stat()
            out[path.relative_to(root).as_posix()] = (info.st_size, info.st_mtime_ns)
    return out


def changed_areas(before, after):
    paths = [p for p, v in after.items() if before.get(p) != v] + [p for p in before if p not in after]
    areas = {}
    for path in paths:
        parts = path.split("/")
        area = "/".join(parts[:2]) if parts[0] in ("sensors", ".claude") and len(parts) > 2 else parts[0]
        areas[area] = areas.get(area, 0) + 1
    return dict(sorted(areas.items()))


def build():
    folder = SCRATCH / "routines"
    if folder.exists():
        shutil.rmtree(folder)
    shutil.copytree(ROOT, folder, ignore=lambda where, names: [n for n in names if n in NOT_COPIED], symlinks=True)
    os.symlink(ROOT / ".venv", folder / ".venv")
    shutil.copy(HERE / "settings.proposed.json", folder / ".claude/settings.json")
    phone = folder / "sensors/phone/phone.py"
    text, count = re.subn(r"^SECRET = .*$", 'SECRET = Path("/nonexistent/no-token")', phone.read_text(), flags=re.M)
    assert count == 1
    phone.write_text(text)
    return folder


def prompt_of(playbook, mode):
    text = (ROOT / "Playbooks" / f"{playbook}.md").read_text()
    prompt = re.search(r"## The prompt\s+```text\n(.*?)\n```", text, re.S).group(1)
    if mode == "replay":
        meta = json.loads((ROOT / "sensors/hunt/samples/replay-1/meta.json").read_text())
        accession = meta.get("accession") or meta.get("accessions", [None])[0]
        if not accession:
            order = json.loads((ROOT / "sensors/hunt/samples/replay-1/order.json").read_text())
            accession = order["events"][0]["accession"]
        prompt = prompt.replace("sensors/hunt/events.py start", f"sensors/hunt/events.py start --replay {accession}")
    return prompt


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    real_before = tree_hash(ROOT, WALLS)
    folder = build()
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_") and k not in ("CLAUDECODE", "CLAUDE_PROJECT_DIR")}
    rows = []
    for name, playbook, allowed, mode in RUNS:
        log = folder / ".claude/guardrails/blocked.jsonl"
        log_before = log.read_text().count("\n") if log.exists() else 0
        walls_before, files_before = tree_hash(folder, WALLS), snapshot(folder)
        started = time.time()
        command = ["claude", "-p", prompt_of(playbook, mode), "--model", MODEL, "--output-format", "json", "--permission-mode", "acceptEdits", "--setting-sources", "project", "--allowedTools", ",".join(allowed)]
        try:
            out = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=1500, env=env, stdin=subprocess.DEVNULL)
            result = json.loads(out.stdout) if out.stdout.strip().startswith("{") else {"result": out.stdout[-400:] + out.stderr[-300:]}
        except subprocess.TimeoutExpired:
            result = {"result": "timed out after 25 minutes"}
        lines = log.read_text().splitlines()[log_before:] if log.exists() else []
        rows.append({"routine": name, "reply": str(result.get("result", ""))[:600], "cost": result.get("total_cost_usd", 0), "turns": result.get("num_turns"), "denials": result.get("permission_denials", []),
                     "seconds": round(time.time() - started), "walls_unchanged": walls_before == tree_hash(folder, WALLS), "blocks": [json.loads(x) for x in lines], "changed": changed_areas(files_before, snapshot(folder))})
        print(json.dumps({k: rows[-1][k] for k in ("routine", "seconds", "cost", "walls_unchanged", "changed")})[:400], len(rows[-1]["blocks"]), "blocks", len(rows[-1]["denials"]), "denials", flush=True)
    report = {"date": dt.date.today().isoformat(), "model": MODEL, "real_walls_unchanged": real_before == tree_hash(ROOT, WALLS), "rows": rows}
    (HERE / "runs" / f"routines-{report['date']}.json").write_text(json.dumps(report, indent=1))
    print("real walls unchanged:", report["real_walls_unchanged"])


if __name__ == "__main__":
    sys.exit(main())
