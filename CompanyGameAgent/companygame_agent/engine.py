from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .models import TaskDefinition, TaskResult, TaskStatus
from .providers import AgentProvider, ValidationProvider


class TaskEngine:
    def __init__(self, agent: AgentProvider, validator: ValidationProvider, state_dir: Path | None = None):
        self.agent = agent
        self.validator = validator
        self.state_dir = state_dir or Path(".agent-state")

    def run(self, task: TaskDefinition, working_directory: Path, on_event: Callable[[str], None] | None = None) -> TaskResult:
        emit = on_event or (lambda _: None)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        result = TaskResult(task_id=task.id, status=TaskStatus.RUNNING)

        for attempt in range(task.max_repair_attempts + 1):
            result.repair_attempts = attempt
            emit(f"execute attempt={attempt}")
            result.execution = self.agent.execute(task, working_directory)
            if not result.execution.success:
                result.status = TaskStatus.FAILED
                result.message = "Agent execution failed."
                self._persist(result)
                return result

            result.status = TaskStatus.VALIDATING
            emit("validation started")
            result.validations = self.validator.validate(task, working_directory)
            if all(item.success for item in result.validations):
                result.status = TaskStatus.COMPLETED
                result.message = "All configured validations passed."
                self._persist(result)
                emit("completed")
                return result

            if attempt < task.max_repair_attempts:
                result.status = TaskStatus.REPAIRING
                emit(f"validation failed; repair cycle {attempt + 1}")
                task = self._augment_with_failure(task, result)
            else:
                result.status = TaskStatus.FAILED
                result.message = "Validation failed after the configured repair attempts."
                self._persist(result)
                emit("failed")
                return result

        result.status = TaskStatus.FAILED
        result.message = "Unexpected engine termination."
        self._persist(result)
        return result

    def _augment_with_failure(self, task: TaskDefinition, result: TaskResult) -> TaskDefinition:
        failures = [
            f"{item.name}: exit={item.exit_code}\nstdout:\n{item.output}\nstderr:\n{item.error}"
            for item in result.validations if not item.success
        ]
        return TaskDefinition(
            id=task.id,
            objective=task.objective + "\n\nRepair the failures from the previous validation run.",
            requirements=task.requirements + ["Previous validation failures:\n" + "\n\n".join(failures)],
            validations=task.validations,
            max_repair_attempts=task.max_repair_attempts,
            metadata=task.metadata,
        )

    def _persist(self, result: TaskResult) -> None:
        path = self.state_dir / f"{result.task_id}.json"
        path.write_text(json.dumps({
            "task_id": result.task_id,
            "status": result.status.value,
            "repair_attempts": result.repair_attempts,
            "message": result.message,
            "execution": None if result.execution is None else {
                "success": result.execution.success,
                "exit_code": result.execution.exit_code,
                "output": result.execution.output,
                "error": result.execution.error,
            },
            "validations": [item.__dict__ for item in result.validations],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
