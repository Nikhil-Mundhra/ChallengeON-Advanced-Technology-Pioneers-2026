from __future__ import annotations

import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import read_json


STATUS_ORDER = (
    "completed",
    "blocked",
    "inconclusive",
    "failed",
    "running",
    "retry",
    "pending",
)
TERMINAL = {"completed", "blocked", "inconclusive", "failed"}
STATUS_LABELS = {
    "completed": ("✓", "completed", "32"),
    "blocked": ("!", "blocked", "33"),
    "inconclusive": ("?", "inconclusive", "33"),
    "failed": ("×", "failed", "31"),
    "running": ("▶", "running", "36"),
    "retry": ("↻", "retry", "35"),
    "pending": ("○", "pending", "90"),
}


def build_snapshot(
    state_path: Path,
    audit_dir: Path,
    checklist_path: Path,
) -> dict[str, Any]:
    state = read_json(state_path)
    if not isinstance(state, dict):
        raise FileNotFoundError(f"audit state not found: {state_path}")
    checklist = read_json(checklist_path, default={})
    titles = {
        task.get("id"): task.get("title", "")
        for task in checklist.get("tasks", [])
        if isinstance(task, dict)
    }
    records = state.get("tasks", {})
    statuses = Counter(record.get("status", "unknown") for record in records.values())
    total = len(records)
    terminal = sum(statuses.get(status, 0) for status in TERMINAL)
    active_tasks = [
        {
            "task_id": task_id,
            "title": titles.get(task_id, ""),
            **record,
        }
        for task_id, record in records.items()
        if record.get("status") == "running"
    ]
    progress_by_task: dict[str, dict[str, Any]] = {}
    for progress_path in sorted((audit_dir / "escalations").glob("*/progress.json")):
        progress = read_json(progress_path, default={})
        task_id = progress.get("task_id")
        if task_id and progress.get("status") in {"running", "stopping"}:
            progress_by_task[str(task_id)] = progress
    for task in active_tasks:
        task["progress"] = progress_by_task.get(task["task_id"])

    issues = read_json(audit_dir / "issues.json", default=[])
    warnings = state.get("validation_warnings", [])
    return {
        "total": total,
        "terminal": terminal,
        "percent_complete": round(100 * terminal / total, 1) if total else 100.0,
        "statuses": {status: statuses.get(status, 0) for status in STATUS_ORDER},
        "open_issues": sum(
            item.get("status", "open") == "open"
            for item in issues
            if isinstance(item, dict)
        ),
        "active_tasks": active_tasks,
        "orphan_escalations": [
            progress
            for task_id, progress in progress_by_task.items()
            if task_id not in {task["task_id"] for task in active_tasks}
        ],
        "warnings": warnings,
        "state_updated_at": state.get("updated_at"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def render_dashboard(
    snapshot: dict[str, Any], *, color: bool = True, live: bool = False
) -> str:
    color = color and "NO_COLOR" not in os.environ

    def paint(value: str, code: str) -> str:
        return f"\033[{code}m{value}\033[0m" if color else value

    total = snapshot["total"]
    terminal = snapshot["terminal"]
    percent = snapshot["percent_complete"]
    bar_width = 34
    filled = round(bar_width * terminal / total) if total else bar_width
    bar = paint("█" * filled, "32") + paint("░" * (bar_width - filled), "90")
    lines = [
        paint("DATA ISSUES AUDIT", "1;36")
        + paint("  LIVE" if live else "  SNAPSHOT", "1;32" if live else "1;90"),
        paint("━" * 66, "90"),
        f"Overall  [{bar}]  {percent:5.1f}%  ({terminal}/{total} terminal)",
        "",
    ]

    status_parts = []
    for status in STATUS_ORDER:
        icon, label, code = STATUS_LABELS[status]
        status_parts.append(
            paint(f"{icon} {snapshot['statuses'].get(status, 0):>2} {label}", code)
        )
    lines.extend(
        [
            "  ".join(status_parts[:4]),
            "  ".join(status_parts[4:]),
            f"Open issues: {snapshot['open_issues']}",
        ]
    )

    active_tasks = snapshot.get("active_tasks", [])
    if active_tasks:
        for task in active_tasks:
            lines.extend(["", paint("CURRENT TASK", "1"), _render_task(task, paint)])
    else:
        lines.extend(["", paint("CURRENT TASK", "1"), "No task is currently running."])

    for progress in snapshot.get("orphan_escalations", []):
        age = _age_seconds(progress.get("updated_at"))
        stale = age is None or age >= 30
        label = "stale artifact" if stale else "live without matching task state"
        lines.extend(
            [
                "",
                paint("ORPHAN ESCALATION", "1;33"),
                (
                    f"{progress.get('task_id')} · {progress.get('model')} · {label} · "
                    f"last heartbeat {_duration(age)} ago"
                ),
            ]
        )

    warnings = snapshot.get("warnings", [])
    if warnings:
        lines.extend(["", paint("WARNINGS", "1;33")])
        lines.extend(f"• {warning}" for warning in warnings)

    captured = _format_timestamp(snapshot.get("captured_at"))
    lines.extend(["", paint("━" * 66, "90"), f"Updated {captured}"])
    return "\n".join(lines)


def watch_dashboard(
    state_path: Path,
    audit_dir: Path,
    checklist_path: Path,
    *,
    interval: float = 2.0,
    json_output: bool = False,
    color: bool = True,
) -> None:
    if interval <= 0:
        raise ValueError("watch interval must be positive")
    interactive = sys.stdout.isatty() and not json_output
    use_color = interactive and color
    try:
        while True:
            snapshot = build_snapshot(state_path, audit_dir, checklist_path)
            if json_output:
                import json

                print(json.dumps(snapshot, ensure_ascii=False), flush=True)
            else:
                if interactive:
                    print("\033[2J\033[H", end="")
                print(render_dashboard(snapshot, color=use_color, live=True), flush=True)
                if not interactive:
                    print()
            if snapshot["terminal"] >= snapshot["total"] and not snapshot["active_tasks"]:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        if interactive:
            print("\nStopped watching; the audit continues in the background.")


def _render_task(task: dict[str, Any], paint: Any) -> str:
    task_id = task.get("task_id", "unknown")
    title = task.get("title", "")
    progress = task.get("progress")
    backend = task.get("finder_backend") or ("opencode" if progress else "starting")
    lines = [paint(f"{task_id}  {title}", "1;36"), f"Backend: {backend}"]
    if not progress:
        lines.append("Waiting for finder telemetry…")
        return "\n".join(lines)

    meaningful = progress.get("meaningful_progress", {})
    token_usage = progress.get("token_usage", {})
    initial_tokens = token_usage.get("initial_input_tokens")
    heartbeat_age = _age_seconds(progress.get("updated_at"))
    health = "healthy" if heartbeat_age is not None and heartbeat_age < 15 else "stale"
    health_color = "32" if health == "healthy" else "33"
    lines.extend(
        [
            f"Model:   {progress.get('model', 'unknown')}",
            (
                f"Elapsed: {_duration(progress.get('elapsed_seconds'))}  ·  "
                f"meaningful progress {_duration(progress.get('seconds_since_meaningful_progress'))} ago  ·  "
                + paint(f"heartbeat {health}", health_color)
            ),
            (
                f"Tools:   {meaningful.get('unique_completed_tool_calls', 0)} unique / "
                f"{meaningful.get('completed_tool_calls', 0)} completed  ·  "
                f"repeats {meaningful.get('consecutive_repeated_tool_calls', 0)}"
            ),
            (
                f"Context: {_integer(initial_tokens)} initial tokens  ·  "
                f"text {_integer(meaningful.get('assistant_text_chars', 0))} chars  ·  "
                f"verdict {'ready' if meaningful.get('has_verdict_candidate') else 'pending'}"
            ),
            f"Latest:  {progress.get('last_action', 'waiting')}",
        ]
    )
    if progress.get("stop_reason"):
        lines.append(paint(f"Stop reason: {progress['stop_reason']}", "31"))
    return "\n".join(lines)


def _duration(value: Any) -> str:
    if value is None:
        return "—"
    seconds = max(0, int(float(value)))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:d}:{seconds:02d}"


def _integer(value: Any) -> str:
    return "—" if value is None else f"{int(value):,}"


def _age_seconds(value: Any) -> float | None:
    if not value:
        return None
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds()


def _format_timestamp(value: Any) -> str:
    if not value:
        return "unknown"
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    return timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
