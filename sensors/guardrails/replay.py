"""Every tool call in this project's past sessions, put through the hook's check. Nothing runs. It answers: what would the guardrails have stopped?
It saves counts only, no command text. Run: python3 sensors/guardrails/replay.py     writes sensors/guardrails/runs/replay-<date>.json
"""
import collections
import datetime as dt
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("guardrails", ROOT / ".claude/hooks/guardrails.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
HISTORY = Path.home() / ".claude/projects" / ("-" + str(ROOT).strip("/").replace("/", "-"))


def main():
    calls, stopped, errors = collections.Counter(), collections.Counter(), 0
    for path in HISTORY.rglob("*.jsonl"):
        for line in path.read_text(errors="replace").splitlines():
            if '"tool_use"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            message = row.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls[block["name"]] += 1
                    try:
                        guard.check_call(block["name"], block["input"], row.get("cwd") or str(ROOT))
                    except guard.Blocked as stop:
                        stopped[f'{block["name"]} {stop.rule}'] += 1
                    except Exception:
                        errors += 1
    out = {"date": dt.date.today().isoformat(), "calls": sum(calls.values()), "by_tool": dict(calls.most_common()), "stopped": dict(sorted(stopped.items())), "stopped_total": sum(stopped.values()), "errors": errors}
    (HERE / "runs" / f'replay-{out["date"]}.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out)[:600])


if __name__ == "__main__":
    main()
