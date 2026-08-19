from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    VALIDATING = "validating"
    REPAIRING = "repairing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ValidationSpec:
    command: list[str]
    name: str = "validation"
    timeout_seconds: int = 300


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    objective: str
    requirements: list[str] = field(default_factory=list)
    validations: list[ValidationSpec] = field(default_factory=list)
    max_repair_attempts: int = 2
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    success: bool
    exit_code: int
    output: str
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    success: bool
    name: str
    exit_code: int
    output: str
    error: str = ""


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    execution: ExecutionResult | None = None
    validations: list[ValidationResult] = field(default_factory=list)
    repair_attempts: int = 0
    message: str = ""
