"""Minimal local entry point: task JSON -> Cline CLI -> JSON result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.cline_runner import ClineRunner
from src.task import Task


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a CompanyGameAgent task through Cline CLI")
    parser.add_argument("task", type=Path, help="Path to a task JSON file")
    parser.add_argument("--cline", default="cline.cmd" if __import__("os").name == "nt" else "cline")
    parser.add_argument("--auto-approve", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--thinking", choices=("none", "low", "medium", "high", "xhigh"), default="high")
    parser.add_argument("--timeout", type=int, default=0)
    args = parser.parse_args()

    task = Task.from_dict(json.loads(args.task.read_text(encoding="utf-8")))
    runner = ClineRunner(
        executable=args.cline,
        cwd=Path(task.project_path),
        timeout_seconds=args.timeout,
        thinking=args.thinking,
        auto_approve=args.auto_approve,
    )
    result = runner.run(task.prompt())
    print(json.dumps({
        "task_id": task.id,
        "success": result.success,
        "returncode": result.returncode,
        "output": result.output,
        "events": list(result.events),
    }, ensure_ascii=False, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
