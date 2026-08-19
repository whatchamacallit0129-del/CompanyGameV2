from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class GitProvider(ABC):
    @abstractmethod
    def status(self, working_directory: Path) -> str:
        raise NotImplementedError

    @abstractmethod
    def commit(self, working_directory: Path, message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def push(self, working_directory: Path, remote: str = "origin", branch: str | None = None) -> str:
        raise NotImplementedError


class LocalGitProvider(GitProvider):
    """Thin Git CLI adapter. No GitHub credentials are stored by the agent."""

    def _run(self, cwd: Path, *args: str) -> str:
        completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
        return completed.stdout.strip()

    def status(self, working_directory: Path) -> str:
        return self._run(working_directory, "status", "--short")

    def commit(self, working_directory: Path, message: str) -> str:
        self._run(working_directory, "add", "-A")
        self._run(working_directory, "commit", "-m", message)
        return self._run(working_directory, "rev-parse", "HEAD")

    def push(self, working_directory: Path, remote: str = "origin", branch: str | None = None) -> str:
        if branch:
            return self._run(working_directory, "push", remote, branch)
        return self._run(working_directory, "push")
