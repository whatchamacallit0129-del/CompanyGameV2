"""Poll a GitHub-backed task queue and run Cline locally.

The watcher is the only long-running local process required. ChatGPT (or another
GitHub client) creates JSON files under agent-queue/pending on the configured
branch. This process pulls them, claims each task, runs Cline against the task's
Unity project, and commits the result under agent-results.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from src.cline_runner import ClineRunner
from src.task import Task

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BRANCH = os.environ.get("AGENT_BRANCH", "agent/cline-bridge-impl12")
POLL_SECONDS = int(os.environ.get("AGENT_POLL_SECONDS", "5"))
PENDING = REPO / "agent-queue" / "pending"
PROCESSING = REPO / "agent-queue" / "processing"
RESULTS = REPO / "agent-results"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO, text=True, capture_output=True,
        encoding="utf-8", errors="replace", check=check,
    )


def sync() -> None:
    result = git("status", "--porcelain")
    if result.stdout.strip():
        raise RuntimeError("Local checkout has uncommitted changes; watcher refuses to overwrite them.")
    git("pull", "--ff-only", "origin", BRANCH)


def publish(message: str) -> None:
    git("add", "agent-queue", "agent-results")
    status = git("status", "--porcelain")
    if not status.stdout.strip():
        return
    git("commit", "-m", message)
    pushed = git("push", "origin", BRANCH, check=False)
    if pushed.returncode != 0:
        git("pull", "--rebase", "origin", BRANCH)
        git("push", "origin", BRANCH)


def claim(path: Path) -> Path:
    target = PROCESSING / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    path.rename(target)
    publish(f"Claim task {path.stem}")
    return target


def run_task(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    task = Task.from_dict(payload)
    runner = ClineRunner(
        executable=payload.get("cline", "cline.cmd"),
        cwd=Path(task.project_path),
        timeout_seconds=int(payload.get("timeout", 0)),
        thinking=str(payload.get("thinking", "high")),
        auto_approve=bool(payload.get("auto_approve", True)),
        retries=int(payload.get("retries", 3)),
        model=payload.get("model"),
        provider=payload.get("provider"),
        use_pty=bool(payload.get("pty", False)),
    )
    result = runner.run(task.prompt())
    return {
        "id": task.id,
        "status": "completed" if result.success else "failed",
        "success": result.success,
        "returncode": result.returncode,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "output": result.output,
        "stderr": result.stderr,
        "events": len(result.events),
    }


def main() -> int:
    for directory in (PENDING, PROCESSING, RESULTS):
        directory.mkdir(parents=True, exist_ok=True)
    print(f"[Watcher] Branch: {BRANCH}")
    print(f"[Watcher] Watching: {PENDING}")
    while True:
        try:
            sync()
            tasks = sorted(PENDING.glob("*.json"))
            for pending in tasks:
                processing = claim(pending)
                try:
                    result = run_task(processing)
                except Exception as exc:
                    result = {
                        "id": processing.stem,
                        "status": "failed",
                        "success": False,
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "error": str(exc),
                    }
                (RESULTS / f"{processing.stem}.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                processing.unlink(missing_ok=True)
                publish(f"Complete task {processing.stem}")
                print(f"[Watcher] {result['status']}: {processing.name}", flush=True)
        except KeyboardInterrupt:
            print("[Watcher] Stopped.")
            return 0
        except Exception as exc:
            print(f"[Watcher] {type(exc).__name__}: {exc}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
