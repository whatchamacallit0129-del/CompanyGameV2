"""Task model shared by orchestration adapters."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Task:
    id: str
    goal: str
    project_path: str
    validation: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Task":
        return cls(
            id=str(value["id"]),
            goal=str(value["goal"]),
            project_path=str(value["project_path"]),
            validation=tuple(str(item) for item in value.get("validation", [])),
            metadata=dict(value.get("metadata", {})),
        )

    def prompt(self) -> str:
        checks = "\n".join(f"- {item}" for item in self.validation) or "- No explicit checks supplied."
        return (
            "You are operating CompanyGameV2.\n"
            "Complete the requested task in the configured project.\n"
            "Do not claim success without actually verifying the result.\n\n"
            f"Task ID: {self.id}\n"
            f"Goal: {self.goal}\n\n"
            "Validation requirements:\n"
            f"{checks}\n\n"
            "When finished, report what you changed and what you actually verified."
        )
