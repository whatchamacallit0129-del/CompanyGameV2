"""Local entry point: task JSON -> Cline CLI -> diagnostic JSON result."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.cline_runner import ClineRunner
from src.task import Task


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a CompanyGameAgent task through Cline CLI")
    parser.add_argument("task", type=Path)
    parser.add_argument("--cline", default="cline.cmd" if os.name == "nt" else "cline")
    parser.add_argument("--auto-approve", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--thinking", choices=("none", "low", "medium", "high", "xhigh"), default="high")
    parser.add_argument("--timeout", type=int, default=0)
    parser.add_argument("--pty", action="store_true", help="Run Cline inside a Windows pseudo-terminal")
    args = parser.parse_args()

    task = Task.from_dict(json.loads(args.task.read_text(encoding="utf-8")))
    print(f"[Agent] Task: {task.id}", flush=True)
    print(f"[Agent] Project: {task.project_path}", flush=True)
    print(f"[Agent] PTY: {args.pty}", flush=True)

    runner = ClineRunner(
        executable=args.cline,
        cwd=Path(task.project_path),
        timeout_seconds=args.timeout,
        thinking=args.thinking,
        auto_approve=args.auto_approve,
        use_pty=args.pty,
    )
    print("[Agent] Starting Cline...", flush=True)
    result = runner.run(task.prompt())
    print(f"[Agent] Cline exit code: {result.returncode}", flush=True)
    if result.output:
        print("[Cline output]", flush=True)
        print(result.output, flush=True)
    if result.stderr:
        print("[Cline stderr]", flush=True)
        print(result.stderr, flush=True)
    print("[Agent] Finished.", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
