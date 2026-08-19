"""Persistent local HTTP bridge for CompanyGameAgent.

Keeps the Agent process alive and accepts task JSON over localhost. Each task is
written to a temporary task file and executed through the existing ClineRunner.
This bridge does not expose the service outside localhost.
"""
from __future__ import annotations

import argparse
import json
import queue
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.cline_runner import ClineRunner
from src.task import Task

ROOT = Path(__file__).resolve().parent
TASK_DIR = ROOT / "tasks"
HOST = "127.0.0.1"
DEFAULT_PORT = 18765
_jobs: queue.Queue[tuple[str, dict]] = queue.Queue()
_results: dict[str, dict] = {}
_lock = threading.Lock()


def run_job(job_id: str, payload: dict) -> None:
    try:
        task = Task.from_dict(payload)
        runner = ClineRunner(
            executable="cline.cmd",
            cwd=Path(task.project_path),
            timeout_seconds=int(payload.get("timeout", 0)),
            thinking=str(payload.get("thinking", "high")),
            auto_approve=bool(payload.get("auto_approve", True)),
            retries=int(payload.get("retries", 3)),
            model=payload.get("model"),
            provider=payload.get("provider"),
        )
        result = runner.run(task.prompt())
        with _lock:
            _results[job_id] = {
                "status": "completed",
                "success": result.success,
                "returncode": result.returncode,
                "output": result.output,
                "stderr": result.stderr,
                "events": len(result.events),
            }
    except Exception as exc:
        with _lock:
            _results[job_id] = {"status": "failed", "success": False, "error": str(exc)}


def worker() -> None:
    while True:
        job_id, payload = _jobs.get()
        with _lock:
            _results[job_id] = {"status": "running"}
        run_job(job_id, payload)
        _jobs.task_done()


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, value: dict) -> None:
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "CompanyGameAgent", "queued": _jobs.qsize()})
            return
        if self.path.startswith("/jobs/"):
            job_id = self.path.rsplit("/", 1)[-1]
            with _lock:
                result = _results.get(job_id)
            self._json(200 if result else 404, result or {"error": "unknown job"})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/tasks":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            Task.from_dict(payload)  # validate before enqueueing
        except Exception as exc:
            self._json(400, {"error": f"invalid task: {exc}"})
            return
        job_id = uuid.uuid4().hex
        _jobs.put((job_id, payload))
        self._json(202, {"job_id": job_id, "status": "queued"})

    def log_message(self, format: str, *args: object) -> None:
        print(f"[Bridge] {format % args}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Persistent local CompanyGameAgent bridge")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    threading.Thread(target=worker, daemon=True, name="agent-worker").start()
    server = ThreadingHTTPServer((HOST, args.port), Handler)
    print(f"[Bridge] Listening on http://{HOST}:{args.port}", flush=True)
    print("[Bridge] Waiting for tasks...", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[Bridge] Stopped.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
