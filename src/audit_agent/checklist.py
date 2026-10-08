from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from .storage import read_json


TERMINAL_STATUSES = {"completed", "inconclusive", "blocked", "failed"}


def load_checklist(path: Path) -> dict[str, Any]:
    checklist = read_json(path)
    if not isinstance(checklist, dict) or not isinstance(checklist.get("tasks"), list):
        raise ValueError(f"{path} is not a checklist JSON object with a tasks array")
    return checklist


def validate_checklist(checklist: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tasks = checklist["tasks"]
    ids = [task.get("id") for task in tasks]
    counts = Counter(ids)
    duplicates = sorted(str(task_id) for task_id, count in counts.items() if count > 1)
    if duplicates:
        errors.append(f"duplicate task IDs: {', '.join(duplicates)}")
    known = set(ids)
    for task in tasks:
        task_id = task.get("id", "<missing>")
        if not isinstance(task_id, str) or not task_id:
            errors.append("task has a missing or invalid id")
        for prerequisite in task.get("prerequisites", []):
            if prerequisite != "NONE" and prerequisite not in known:
                errors.append(f"{task_id} references unknown prerequisite {prerequisite}")

    ordered = [
        task_id
        for phase in checklist.get("execution_order", [])
        for task_id in phase.get("task_ids", [])
    ]
    ordered_counts = Counter(ordered)
    missing = sorted(known - set(ordered))
    extra = sorted(set(ordered) - known)
    repeated = sorted(task_id for task_id, count in ordered_counts.items() if count > 1)
    if missing:
        errors.append(f"tasks missing from execution_order: {', '.join(missing)}")
    if extra:
        errors.append(f"unknown tasks in execution_order: {', '.join(extra)}")
    if repeated:
        errors.append(f"tasks repeated in execution_order: {', '.join(repeated)}")

    for statement in checklist.get("final_completeness_checks", []):
        match = re.search(r"contains\s+(\d+)\s+bounded tasks", str(statement), re.I)
        if match and int(match.group(1)) != len(tasks):
            errors.append(
                f"declared task count {match.group(1)} does not match actual count {len(tasks)}"
            )
    return errors


def task_map(checklist: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in checklist["tasks"]}


def execution_ids(checklist: dict[str, Any]) -> list[str]:
    ordered = [
        task_id
        for phase in checklist.get("execution_order", [])
        for task_id in phase.get("task_ids", [])
    ]
    if ordered:
        return ordered
    return [task["id"] for task in checklist["tasks"]]


def next_ready_task(
    checklist: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any] | None:
    tasks = task_map(checklist)
    statuses = state["tasks"]
    for task_id in execution_ids(checklist):
        record = statuses[task_id]
        if record["status"] not in {"pending", "retry"}:
            continue
        prerequisites = [p for p in tasks[task_id].get("prerequisites", []) if p != "NONE"]
        # A limitation in one audit must not deadlock every dependent check. The
        # downstream finder receives the terminal prerequisite summary and can
        # account for the missing evidence explicitly.
        if all(statuses[p]["status"] in TERMINAL_STATUSES for p in prerequisites):
            return tasks[task_id]
    return None
