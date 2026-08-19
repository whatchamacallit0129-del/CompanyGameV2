"""Cline CLI process adapter for CompanyGameAgent.

The core agent can invoke this adapter without depending on Cline internals.
"""
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
    """Run Cline CLI in headless mode with project-local configuration."""

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
    ) -> None:
        self.executable = executable
        self.cwd = Path(cwd) if cwd else None
        self.timeout_seconds = timeout_seconds
        self.thinking = thinking
        self.auto_approve = auto_approve
        self.retries = retries
        self.model = model
        self.provider = provider

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
        command += [prompt]
        return command

    def run(self, prompt: str) -> ClineResult:
        command = tuple(self.build_command(prompt))
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
            stdout = self._as_text(exc.stdout)
            stderr = self._as_text(exc.stderr)
            return ClineResult(-2, stdout, stderr + "\nCline process timed out.", (), command)
        except OSError as exc:
            return ClineResult(-1, "", f"Could not start Cline: {exc}", (), command)

        events = []
        for line in completed.stdout.splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    events.append(value)
            except json.JSONDecodeError:
                continue

        return ClineResult(
            completed.returncode,
            completed.stdout,
            completed.stderr,
            tuple(events),
            command,
        )

    @staticmethod
    def _as_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)
