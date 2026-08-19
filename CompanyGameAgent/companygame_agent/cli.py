from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import TaskEngine
from .models import TaskDefinition, ValidationSpec
from .providers import ClineProvider, CommandValidationProvider


def load_task(path: Path) -> TaskDefinition:
    raw = json.loads(path.read_text(encoding="utf-8"))
    validations = [ValidationSpec(**item) for item in raw.get("validations", [])]
    return TaskDefinition(
        id=raw["id"],
        objective=raw["objective"],
        requirements=raw.get("requirements", []),
        validations=validations,
        max_repair_attempts=raw.get("max_repair_attempts", 2),
        metadata=raw.get("metadata", {}),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CompanyGameV2 local development orchestrator")
    parser.add_argument("task", type=Path, help="Path to a task JSON file")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Working repository/project directory")
    parser.add_argument("--cline", default="cline", help="Cline executable")
    parser.add_argument("--auto-approve", action="store_true", help="Allow Cline autonomous approval mode")
    parser.add_argument("--dry-run", action="store_true", help="Print the task without executing an agent")
    args = parser.parse_args()

    task = load_task(args.task)
    if args.dry_run:
        print(json.dumps({
            "task_id": task.id,
            "objective": task.objective,
            "requirements": task.requirements,
            "validations": [item.__dict__ for item in task.validations],
            "max_repair_attempts": task.max_repair_attempts,
        }, ensure_ascii=False, indent=2))
        return 0

    engine = TaskEngine(
        agent=ClineProvider(executable=args.cline, auto_approve=args.auto_approve),
        validator=CommandValidationProvider(),
    )
    result = engine.run(task, args.project, on_event=lambda message: print(f"[agent] {message}"))
    print(json.dumps({
        "task_id": result.task_id,
        "status": result.status.value,
        "repair_attempts": result.repair_attempts,
        "message": result.message,
    }, ensure_ascii=False, indent=2))
    return 0 if result.status.value == "completed" else 1


if __name__ == "__main__":
    main()
