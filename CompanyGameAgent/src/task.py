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
        write_task = self.metadata.get("type") == "write-smoke-test"
        execution = (
            "This is an EXECUTION task, not a planning or exploration task. "
            "You must perform the requested change now. Do not stop after inspecting the project "
            "and do not ask the user what to build. Use the Unity MCP tools available to you. "
            "After making the change, use Unity MCP again to verify it."
            if write_task
            else
            "Perform the task now. Use the available Unity MCP tools when the task requires Unity state."
        )
        return (
            "You are an autonomous Unity development agent operating CompanyGameV2.\n"
            "The user has already authorized this task.\n"
            f"{execution}\n"
            "Do not merely describe commands or provide instructions for the user to run.\n"
            "Do not claim success without actually verifying the result.\n\n"
            f"Task ID: {self.id}\n"
            f"Goal: {self.goal}\n\n"
            "Validation requirements:\n"
            f"{checks}\n\n"
            "When finished, report exactly what you changed and what you actually verified."
        )
