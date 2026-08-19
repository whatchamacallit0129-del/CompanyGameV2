"""Cline CLI process adapter for CompanyGameAgent.

The core agent can invoke this adapter without depending on Cline internals.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class ClineResult:
    returncode: int
    output: str
    events: tuple[dict, ...]

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
        auto_approve: bool = True,
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
        completed = subprocess.run(
            self.build_command(prompt),
            cwd=str(self.cwd) if self.cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_seconds if self.timeout_seconds > 0 else None,
            check=False,
        )
        events = []
        for line in completed.stdout.splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    events.append(value)
            except json.JSONDecodeError:
                continue
        output = completed.stdout
        if completed.stderr:
            output += "\n" + completed.stderr
        return ClineResult(completed.returncode, output, tuple(events))
