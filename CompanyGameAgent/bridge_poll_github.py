"""Poll a GitHub-backed task queue and execute CompanyGameAgent tasks locally.

The local machine must have GitHub CLI authenticated (`gh auth status`).
ChatGPT can enqueue JSON task files in agent-bridge/inbox on the configured
branch, while this process executes them locally and writes results to outbox.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from pathlib import Path

from src.cline_runner import ClineRunner
from src.task import Task

DEFAULT_REPO = "whatchamacallit0129-del/CompanyGameV2"
DEFAULT_BRANCH = "agent/cline-bridge-impl12"
ROOT = Path(__file__).resolve().parent
WORK_DIR = ROOT / ".bridge"


def gh(*args: str) -> str:
    p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f"gh exited {p.returncode}")
    return p.stdout


def git_ref(repo: str, branch: str) -> str:
    return gh("api", f"repos/{repo}/git/ref/heads/{branch}").strip()


def list_inbox(repo: str, branch: str) -> list[dict]:
    out = gh("api", f"repos/{repo}/contents/agent-bridge/inbox?ref={branch}")
    data = json.loads(out)
    return [x for x in data if x.get("type") == "file" and x.get("name", "").endswith(".json")]


def read_file(repo: str, path: str, branch: str) -> dict:
    out = gh("api", f"repos/{repo}/contents/{path}?ref={branch}")
    data = json.loads(out)
    import base64
    return json.loads(base64.b64decode(data["content"]).decode("utf-8"))


def commit_file(repo: str, branch: str, path: str, content: str, message: str) -> None:
    import base64
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    # GitHub contents API creates the file and commits it to the branch.
    gh("api", "--method", "PUT", f"repos/{repo}/contents/{path}", "-f", f"message={message}", "-f", f"content={encoded}", "-f", f"branch={branch}")


def delete_file(repo: str, branch: str, path: str, message: str) -> None:
    data = json.loads(gh("api", f"repos/{repo}/contents/{path}?ref={branch}"))
    gh("api", "--method", "DELETE", f"repos/{repo}/contents/{path}", "-f", f"message={message}", "-f", f"sha={data['sha']}", "-f", f"branch={branch}")


def run_task(payload: dict) -> dict:
    task = Task.from_dict(payload)
    project = Path(task.project_path).resolve()
    # Only execute tasks against the configured Unity project.
    allowed = Path(payload.get("allowed_project", "D:/CompanyGameV2Unity")).resolve()
    if project != allowed:
        raise ValueError(f"project_path must be {allowed}, got {project}")
    runner = ClineRunner(
        executable="cline.cmd",
        cwd=project,
        timeout_seconds=int(payload.get("timeout", 0)),
        thinking=str(payload.get("thinking", "high")),
        auto_approve=bool(payload.get("auto_approve", True)),
        retries=int(payload.get("retries", 3)),
        model=payload.get("model"),
        provider=payload.get("provider"),
    )
    result = runner.run(task.prompt())
    return {
        "status": "completed",
        "success": result.success,
        "returncode": result.returncode,
        "output": result.output,
        "stderr": result.stderr,
        "events": len(result.events),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    print(f"[GitHubBridge] polling {args.repo}@{args.branch}", flush=True)
    gh("auth", "status")
    while True:
        try:
            for item in list_inbox(args.repo, args.branch):
                path = item["path"]
                job_id = Path(path).stem
                print(f"[GitHubBridge] executing {job_id}", flush=True)
                try:
                    result = run_task(read_file(args.repo, path, args.branch))
                except Exception as exc:
                    result = {"status": "failed", "success": False, "error": str(exc)}
                out_path = f"agent-bridge/outbox/{job_id}.json"
                commit_file(args.repo, args.branch, out_path, json.dumps(result, ensure_ascii=False, indent=2), f"agent bridge: result {job_id}")
                delete_file(args.repo, args.branch, path, f"agent bridge: consume {job_id}")
                print(f"[GitHubBridge] result written to {out_path}", flush=True)
        except Exception as exc:
            print(f"[GitHubBridge] {type(exc).__name__}: {exc}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
