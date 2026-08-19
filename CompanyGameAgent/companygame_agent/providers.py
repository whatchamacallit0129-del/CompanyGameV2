from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .models import ExecutionResult, TaskDefinition, ValidationResult


class AgentProvider(ABC):
    @abstractmethod
    def execute(self, task: TaskDefinition, working_directory: Path) -> ExecutionResult:
        raise NotImplementedError


class ClineProvider(AgentProvider):
    """Cline CLI adapter. The core engine does not depend on Cline-specific APIs."""

    def __init__(self, executable: str = "cline", auto_approve: bool = False, timeout_seconds: int = 1800):
        self.executable = executable
        self.auto_approve = auto_approve
        self.timeout_seconds = timeout_seconds

    def execute(self, task: TaskDefinition, working_directory: Path) -> ExecutionResult:
        prompt = self._build_prompt(task)
        args = [self.executable]
        if self.auto_approve:
            args.append("--yolo")
        args.extend(["--json", prompt])
        try:
            completed = subprocess.run(
                args,
                cwd=working_directory,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            return ExecutionResult(False, -1, "", f"Cline executable not found: {self.executable}. {exc}")
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(False, -1, exc.stdout or "", f"Cline timed out after {self.timeout_seconds}s")
        return ExecutionResult(
            success=completed.returncode == 0,
            exit_code=completed.returncode,
            output=completed.stdout,
            error=completed.stderr,
        )

    @staticmethod
    def _build_prompt(task: TaskDefinition) -> str:
        requirements = "\n".join(f"- {item}" for item in task.requirements) or "- Follow repository architecture."
        validations = "\n".join(f"- {item.name}: {' '.join(item.command)}" for item in task.validations) or "- No external validation command supplied."
        return (
            f"TASK ID: {task.id}\n\n"
            f"OBJECTIVE:\n{task.objective}\n\n"
            f"REQUIREMENTS:\n{requirements}\n\n"
            f"VALIDATION EXPECTATIONS:\n{validations}\n\n"
            "Work directly in the current repository. Inspect existing code before changing it. "
            "Prefer extensible, data-driven designs and avoid hard-coded gameplay values. "
            "Do not claim success without actually validating the result."
        )


class ValidationProvider(ABC):
    @abstractmethod
    def validate(self, task: TaskDefinition, working_directory: Path) -> list[ValidationResult]:
        raise NotImplementedError


class CommandValidationProvider(ValidationProvider):
    def validate(self, task: TaskDefinition, working_directory: Path) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for spec in task.validations:
            try:
                completed = subprocess.run(
                    spec.command,
                    cwd=working_directory,
                    text=True,
                    capture_output=True,
                    timeout=spec.timeout_seconds,
                    check=False,
                )
                results.append(ValidationResult(
                    success=completed.returncode == 0,
                    name=spec.name,
                    exit_code=completed.returncode,
                    output=completed.stdout,
                    error=completed.stderr,
                ))
            except FileNotFoundError as exc:
                results.append(ValidationResult(False, spec.name, -1, "", f"Command not found: {spec.command[0]}: {exc}"))
            except subprocess.TimeoutExpired as exc:
                results.append(ValidationResult(False, spec.name, -1, exc.stdout or "", f"Validation timed out after {spec.timeout_seconds}s"))
        return results
