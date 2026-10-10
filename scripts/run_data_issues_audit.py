#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


from audit_agent.checklist import load_checklist, validate_checklist
from audit_agent.dashboard import build_snapshot, render_dashboard, watch_dashboard
from audit_agent.escalation import DEFAULT_MODELS, OpenCodeEscalator
from audit_agent.issues import render_markdown
from audit_agent.local_model import OpenAICompatibleClient
from audit_agent.runner import AuditRunner
from audit_agent.storage import read_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run the bounded agentic data audit.")
    result.add_argument(
        "command",
        choices=("init", "validate", "status", "watch", "run", "render", "retry", "escalate"),
    )
    result.add_argument("--root", type=Path, default=Path.cwd())
    result.add_argument("--checklist", type=Path, default=Path("meta/audits/data_issues/checklist.json"))
    result.add_argument("--audit-dir", type=Path, default=Path("audit"))
    result.add_argument("--output", type=Path, default=Path("audit/issues.md"))
    result.add_argument("--endpoint", default="http://localhost:8000/v1/chat/completions")
    result.add_argument("--model", default="mlx-community/Qwen3.5-4B-MLX-4bit")
    result.add_argument(
        "--local-max-tokens",
        type=int,
        default=1024,
        help="Maximum Qwen output tokens per investigation turn",
    )
    result.add_argument("--local-final-max-tokens", type=int, default=8192)
    result.add_argument(
        "--local-max-prompt-chars",
        type=int,
        default=280_000,
        help="Compact local-model history above this character budget",
    )
    result.add_argument(
        "--local-tool-result-chars",
        type=int,
        default=8_000,
        help="Maximum serialized characters retained from each local tool result",
    )
    result.add_argument("--max-tasks", type=int, default=1)
    result.add_argument("--max-tool-steps", type=int, default=20)
    result.add_argument("--timeout", type=int, default=300)
    result.add_argument("--task-id", help="Task to reset with the retry command")
    result.add_argument(
        "--retry-status",
        choices=("retry", "pending"),
        default="retry",
        help="Schedulable state to restore with the retry command",
    )
    result.add_argument(
        "--undo-attempt",
        action="store_true",
        help="Subtract one attempt when rolling back an infrastructure-only run",
    )
    result.add_argument("--json", action="store_true", help="Emit machine-readable status")
    result.add_argument(
        "--watch-interval",
        type=float,
        default=2.0,
        help="Seconds between live dashboard refreshes",
    )
    result.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    result.add_argument(
        "--with-opencode",
        action="store_true",
        help="Use OpenCode as the primary finder; local Qwen remains the fallback",
    )
    result.add_argument(
        "--finder-backend",
        choices=("qwen", "opencode"),
        help="Primary issue finder; --with-opencode selects opencode when omitted",
    )
    result.add_argument(
        "--no-local-fallback",
        "--no-gemma-fallback",
        dest="no_local_fallback",
        action="store_true",
        help="Do not fall back to local Qwen when every OpenCode model fails",
    )
    result.add_argument(
        "--escalation-model",
        action="append",
        help="OpenCode model in fallback order; may be supplied more than once",
    )
    result.add_argument("--escalation-timeout", type=int, default=1800)
    result.add_argument(
        "--escalation-stall-timeout",
        type=int,
        default=600,
        help="Stop an OpenCode model after this many seconds without a new unique completed tool call or verdict",
    )
    result.add_argument(
        "--escalation-max-tool-calls",
        type=int,
        default=30,
        help="Stop an OpenCode model after this many completed tool calls",
    )
    result.add_argument(
        "--escalation-max-repeat",
        type=int,
        default=3,
        help="Stop after this many consecutive repeats of the same completed tool call",
    )
    result.add_argument(
        "--opencode-pure",
        action="store_true",
        default=True,
        help="Disable external OpenCode plugins (default)",
    )
    result.add_argument(
        "--opencode-with-plugins",
        action="store_false",
        dest="opencode_pure",
        help="Allow external OpenCode plugins; increases initial context",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    root = args.root.resolve()
    checklist_path = (root / args.checklist).resolve() if not args.checklist.is_absolute() else args.checklist
    audit_dir = (root / args.audit_dir).resolve() if not args.audit_dir.is_absolute() else args.audit_dir
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output
    client = OpenAICompatibleClient(
        args.endpoint,
        args.model,
        args.timeout,
        max_tokens=args.local_max_tokens,
        max_prompt_chars=args.local_max_prompt_chars,
    )
    finder_backend = args.finder_backend or (
        "opencode" if args.with_opencode else "qwen"
    )
    use_escalation = (
        args.with_opencode
        or finder_backend == "opencode"
        or args.command == "escalate"
    )
    escalator = None
    if use_escalation:
        escalator = OpenCodeEscalator(
            root=root,
            output_dir=audit_dir / "escalations",
            models=args.escalation_model or list(DEFAULT_MODELS),
            timeout_seconds=args.escalation_timeout,
            stall_timeout_seconds=args.escalation_stall_timeout,
            max_tool_calls=args.escalation_max_tool_calls,
            max_consecutive_repeats=args.escalation_max_repeat,
            pure=args.opencode_pure,
            adaptive_ordering=not bool(args.escalation_model),
        )
    runner = AuditRunner(
        root,
        checklist_path,
        audit_dir,
        output,
        client,
        max_tool_steps=args.max_tool_steps,
        escalator=escalator,
        finder_backend=finder_backend,
        local_fallback=not args.no_local_fallback,
        local_final_max_tokens=args.local_final_max_tokens,
        local_tool_result_chars=args.local_tool_result_chars,
    )

    if args.command == "validate":
        checklist = load_checklist(checklist_path)
        warnings = validate_checklist(checklist)
        print(json.dumps({"tasks": len(checklist["tasks"]), "warnings": warnings}, indent=2))
        return 1 if warnings else 0
    if args.command == "init":
        state = runner.initialize()
        print(json.dumps({"tasks": len(state["tasks"]), "warnings": state["validation_warnings"]}, indent=2))
        return 0
    if args.command == "status":
        snapshot = build_snapshot(runner.state_path, audit_dir, checklist_path)
        if args.json:
            print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        else:
            print(render_dashboard(snapshot, color=sys.stdout.isatty() and not args.no_color))
        return 0
    if args.command == "watch":
        watch_dashboard(
            runner.state_path,
            audit_dir,
            checklist_path,
            interval=args.watch_interval,
            json_output=args.json,
            color=not args.no_color,
        )
        return 0
    if args.command == "render":
        runner.initialize()
        render_markdown(read_json(runner.issues_path, default=[]), output)
        print(output)
        return 0
    if args.command == "retry":
        runner.initialize()
        if not args.task_id:
            raise SystemExit("retry requires --task-id")
        state = read_json(runner.state_path)
        if args.task_id not in state["tasks"]:
            raise SystemExit(f"unknown task ID: {args.task_id}")
        record = state["tasks"][args.task_id]
        record.update(
            {
                "status": args.retry_status,
                "started_at": None,
                "completed_at": None,
                "last_error": None,
                "escalation": None,
                "finder_backend": None,
                "controller_pid": None,
            }
        )
        if args.undo_attempt:
            record["attempts"] = max(0, int(record.get("attempts", 0)) - 1)
        from audit_agent.storage import atomic_write_json

        atomic_write_json(runner.state_path, state)
        print(
            json.dumps(
                {
                    "task_id": args.task_id,
                    "status": args.retry_status,
                    "attempts": record.get("attempts", 0),
                },
                indent=2,
            )
        )
        return 0
    if args.command == "escalate":
        processed = runner.escalate_existing(
            max_tasks=args.max_tasks if args.max_tasks > 0 else None,
            task_id=args.task_id,
        )
        print(json.dumps({"escalations_processed": processed}, indent=2))
        return 0
    completed = runner.run(max_tasks=args.max_tasks if args.max_tasks > 0 else None)
    print(json.dumps({"tasks_processed": completed, "state": str(runner.state_path), "issues": str(runner.issues_path), "markdown": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
