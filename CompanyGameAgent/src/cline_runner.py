"""Cline CLI process adapter for CompanyGameAgent."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ClineResult:
    returncode: int
    output: str
    stderr: str
    events: tuple[dict, ...]
    command: tuple[str, ...]

    @property
    def success(self) -> bool:
        return self.returncode == 0


class ClineRunner:
    """Run Cline CLI and optionally give it a pseudo-terminal on Windows."""

    def __init__(
        self,
        executable: str = "cline.cmd" if os.name == "nt" else "cline",
        cwd: Optional[Path] = None,
        timeout_seconds: int = 0,
        thinking: str = "high",
        auto_approve: bool = False,
        retries: int = 3,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        use_pty: bool = False,
    ) -> None:
        self.executable = executable
        self.cwd = Path(cwd) if cwd else None
        self.timeout_seconds = timeout_seconds
        self.thinking = thinking
        self.auto_approve = auto_approve
        self.retries = retries
        self.model = model
        self.provider = provider
        self.use_pty = use_pty

    def build_command(self, prompt: str) -> list[str]:
        command = [
            self.executable,
            "--json",
            "--auto-approve",
            "true" if self.auto_approve else "false",
            "--thinking",
            self.thinking,
            "--retries",
            str(self.retries),
        ]
        if self.timeout_seconds > 0:
            command += ["--timeout", str(self.timeout_seconds)]
        if self.model:
            command += ["--model", self.model]
        if self.provider:
            command += ["--provider", self.provider]
        command.append(prompt)
        return command

    def run(self, prompt: str) -> ClineResult:
        command = tuple(self.build_command(prompt))
        if self.use_pty and os.name == "nt":
            return self._run_windows_pty(command)
        return self._run_subprocess(command)

    def _run_subprocess(self, command: tuple[str, ...]) -> ClineResult:
        try:
            completed = subprocess.run(
                list(command),
                cwd=str(self.cwd) if self.cwd else None,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds if self.timeout_seconds > 0 else None,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ClineResult(-2, self._as_text(exc.stdout), self._as_text(exc.stderr) + "\nCline process timed out.", (), command)
        except OSError as exc:
            return ClineResult(-1, "", f"Could not start Cline: {exc}", (), command)
        return self._result(completed.returncode, completed.stdout, completed.stderr, command)

    def _run_windows_pty(self, command: tuple[str, ...]) -> ClineResult:
        """Use Windows ConPTY through pywinpty when installed.

        This is opt-in because normal pipe capture is preferable for pure JSON
        output. The PTY path exists for Cline tools that explicitly require a TTY.
        """
        try:
            from winpty import PtyProcess  # type: ignore
        except ImportError:
            return ClineResult(-3, "", "PTY mode requires the 'pywinpty' package. Install it with: python -m pip install pywinpty", (), command)

        try:
            command_line = subprocess.list2cmdline(list(command))
            proc = PtyProcess.spawn(command_line, cwd=str(self.cwd) if self.cwd else None)
            chunks: list[str] = []
            while proc.isalive():
                try:
                    chunks.append(proc.read(4096))
                except EOFError:
                    break
            try:
                chunks.append(proc.read(4096))
            except EOFError:
                pass
            output = "".join(chunks)
            return self._result(proc.exitstatus if proc.exitstatus is not None else 0, output, "", command)
        except Exception as exc:
            return ClineResult(-1, "", f"Could not start Cline PTY: {exc}", (), command)

    def _result(self, returncode: int, stdout: str, stderr: str, command: tuple[str, ...]) -> ClineResult:
        events = []
        for line in stdout.splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    events.append(value)
            except json.JSONDecodeError:
                continue
        return ClineResult(returncode, stdout, stderr, tuple(events), command)

    @staticmethod
    def _as_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)
