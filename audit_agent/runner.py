from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .checklist import load_checklist, next_ready_task, task_map, validate_checklist
from .escalation import OpenCodeEscalator
from .discovery import context_for_task, ensure_repository_map
from .issues import apply_decision, candidate_issues, render_markdown
from .local_model import OpenAICompatibleClient, parse_json_response
from .prompts import FINAL_REPORT_REQUEST, FINDER_SYSTEM, MANAGER_SYSTEM, finder_task_prompt, manager_prompt
from .storage import atomic_write_json, read_json
from .tools import ReadOnlyTools


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditRunner:
    def __init__(
        self,
        root: Path,
        checklist_path: Path,
        audit_dir: Path,
        output_path: Path,
        client: OpenAICompatibleClient,
        *,
        max_tool_steps: int = 20,
        max_attempts: int = 2,
        escalator: OpenCodeEscalator | None = None,
        finder_backend: str = "qwen",
        local_fallback: bool = True,
        local_final_max_tokens: int = 8192,
        local_tool_result_chars: int = 8_000,
    ):
        self.root = root.resolve()
        self.checklist_path = checklist_path.resolve()
        self.audit_dir = audit_dir.resolve()
        self.output_path = output_path.resolve()
        self.client = client
        self.max_tool_steps = max_tool_steps
        self.max_attempts = max_attempts
        self.escalator = escalator
        if finder_backend not in {"qwen", "opencode"}:
            raise ValueError("finder_backend must be qwen or opencode")
        if finder_backend == "opencode" and escalator is None:
            raise ValueError("OpenCode finder requires an OpenCodeEscalator")
        self.finder_backend = finder_backend
        self.local_fallback = local_fallback
        self.local_final_max_tokens = local_final_max_tokens
        self.local_tool_result_chars = local_tool_result_chars
        self.state_path = self.audit_dir / "run_state.json"
        self.issues_path = self.audit_dir / "issues.json"
        self.results_dir = self.audit_dir / "task_results"
        self.decisions_dir = self.audit_dir / "manager_decisions"
        self.logs_dir = self.audit_dir / "logs"
        self.tools = ReadOnlyTools(self.root)
        self.repository_map: dict[str, Any] = {}

    def initialize(self) -> dict[str, Any]:
        checklist = load_checklist(self.checklist_path)
        validation = validate_checklist(checklist)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        state = read_json(self.state_path)
        if state is None:
            state = {
                "checklist_version": checklist.get("checklist_version"),
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "validation_warnings": validation,
                "tasks": {
                    task["id"]: {
                        "status": "pending",
                        "attempts": 0,
                        "started_at": None,
                        "completed_at": None,
                        "last_error": None,
                        "accepted_issue_ids": [],
                        "escalation": None,
                        "finder_backend": None,
                    }
                    for task in checklist["tasks"]
                },
            }
        else:
            for task in checklist["tasks"]:
                state["tasks"].setdefault(
                    task["id"],
                    {
                        "status": "pending",
                        "attempts": 0,
                        "started_at": None,
                        "completed_at": None,
                        "last_error": None,
                        "accepted_issue_ids": [],
                        "escalation": None,
                        "finder_backend": None,
                    },
                )
            for record in state["tasks"].values():
                record.setdefault("escalation", None)
                record.setdefault("finder_backend", None)
                record.setdefault("controller_pid", None)
            state["validation_warnings"] = validation
            self._recover_interrupted_tasks(state)
            state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)
        issues = read_json(self.issues_path, default=[])
        if not isinstance(issues, list):
            raise ValueError("audit/issues.json must contain a JSON array")
        atomic_write_json(self.issues_path, issues)
        render_markdown(issues, self.output_path)
        self.repository_map = ensure_repository_map(self.root, self.audit_dir)
        return state

    def run(self, max_tasks: int | None = None) -> int:
        self.initialize()
        completed = 0
        while max_tasks is None or completed < max_tasks:
            checklist = load_checklist(self.checklist_path)
            state = read_json(self.state_path)
            task = next_ready_task(checklist, state)
            if task is None:
                break
            try:
                self._run_task(checklist, state, task)
            except KeyboardInterrupt:
                # SIGINT must not leave a durable phantom `running` task.
                latest = read_json(self.state_path)
                record = latest["tasks"][task["id"]]
                if record.get("status") == "running":
                    record.update(
                        {
                            "status": "retry",
                            "completed_at": utc_now(),
                            "last_error": "audit controller interrupted",
                            "controller_pid": None,
                        }
                    )
                    latest["updated_at"] = utc_now()
                    atomic_write_json(self.state_path, latest)
                raise
            completed += 1
        return completed

    def _recover_interrupted_tasks(self, state: dict[str, Any]) -> None:
        """Turn provably orphaned running records into schedulable retries."""
        for task_id, record in state.get("tasks", {}).items():
            if record.get("status") != "running":
                continue
            progress = read_json(
                self.audit_dir / "escalations" / task_id / "progress.json", default={}
            )
            progress_status = progress.get("status")
            controller_pid = record.get("controller_pid")
            dead_controller = bool(controller_pid) and not self._pid_is_alive(
                int(controller_pid)
            )
            if progress_status not in {"interrupted", "failed", "stopped"} and not dead_controller:
                continue
            reason = progress.get("stop_reason") or "controller process is no longer alive"
            record.update(
                {
                    "status": "retry",
                    "completed_at": utc_now(),
                    "last_error": f"recovered stale running state: {reason}",
                    "controller_pid": None,
                }
            )

    @staticmethod
    def _pid_is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except (OSError, ValueError):
            return False
        return True

    def escalate_existing(
        self, max_tasks: int | None = None, task_id: str | None = None
    ) -> int:
        """Escalate terminal local-model tasks after the main loop has stopped."""
        if self.escalator is None:
            raise ValueError("OpenCode escalation is not configured")
        self.initialize()
        checklist = load_checklist(self.checklist_path)
        tasks = task_map(checklist)
        state = read_json(self.state_path)
        running = [
            task_id
            for task_id, record in state["tasks"].items()
            if record["status"] == "running"
        ]
        if running:
            raise RuntimeError(
                "refusing concurrent state updates while audit tasks are running: "
                + ", ".join(running)
            )

        processed = 0
        for task in checklist["tasks"]:
            if task_id is not None and task["id"] != task_id:
                continue
            if max_tasks is not None and processed >= max_tasks:
                break
            task_id = task["id"]
            record = state["tasks"][task_id]
            if record["status"] not in {"blocked", "inconclusive", "failed"}:
                continue
            report = read_json(self.results_dir / f"{task_id}.json", default={})
            print(f"[{task_id}] OpenCode escalation started", flush=True)
            try:
                escalated, metadata = self.escalator.escalate(
                    tasks[task_id], report, record.get("last_error")
                )
                if report:
                    atomic_write_json(self.results_dir / f"{task_id}.qwen.json", report)
                atomic_write_json(self.results_dir / f"{task_id}.json", escalated)
                issue_ids = self._review_findings(task, escalated.get("findings", []))
                record.update(
                    {
                        "status": escalated.get("status", "blocked"),
                        "completed_at": utc_now(),
                        "accepted_issue_ids": sorted(
                            set(record.get("accepted_issue_ids", [])) | set(issue_ids)
                        ),
                        "escalation": metadata,
                    }
                )
                print(
                    f"[{task_id}] escalation {escalated.get('verdict')}; "
                    f"accepted issues: {issue_ids or 'none'}",
                    flush=True,
                )
            except Exception as exc:
                record["escalation"] = {
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(f"[{task_id}] escalation failed: {exc}", flush=True)
            state["updated_at"] = utc_now()
            atomic_write_json(self.state_path, state)
            processed += 1
        return processed

    def _run_task(
        self,
        checklist: dict[str, Any],
        state: dict[str, Any],
        task: dict[str, Any],
    ) -> None:
        task_id = task["id"]
        print(
            f"[{task_id}] {self.finder_backend} finder started: "
            f"{task.get('title', '')}",
            flush=True,
        )
        record = state["tasks"][task_id]
        record.update(
            {
                "status": "running",
                "attempts": record["attempts"] + 1,
                "started_at": utc_now(),
                "last_error": None,
                "finder_backend": self.finder_backend,
                "controller_pid": os.getpid(),
            }
        )
        state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)
        opencode_attempted = False
        escalation_metadata = None
        actual_backend = self.finder_backend
        try:
            prerequisites = self._prerequisite_summaries(checklist, task)
            repository_context = context_for_task(self.repository_map, task)
            if self.finder_backend == "opencode":
                try:
                    assert self.escalator is not None
                    opencode_attempted = True
                    report, escalation_metadata = self.escalator.investigate(
                        task, prerequisites, repository_context
                    )
                except Exception as exc:
                    if not self.local_fallback:
                        raise
                    print(
                        f"[{task_id}] OpenCode unavailable; falling back to Qwen: {exc}",
                        flush=True,
                    )
                    actual_backend = "qwen_fallback"
                    escalation_metadata = {
                        "status": "failed_with_qwen_fallback",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                    report = self._run_finder(task, prerequisites, repository_context)
            else:
                report = self._run_finder(task, prerequisites, repository_context)
                if (
                    self.escalator is not None
                    and report.get("status") in {"blocked", "inconclusive"}
                ):
                    atomic_write_json(self.results_dir / f"{task_id}.qwen.json", report)
                    print(f"[{task_id}] handing off to OpenCode escalation", flush=True)
                    try:
                        report, escalation_metadata = self.escalator.escalate(task, report)
                        actual_backend = "qwen_then_opencode"
                    except Exception as exc:
                        escalation_metadata = {
                            "status": "failed",
                            "error": f"{type(exc).__name__}: {exc}",
                        }
            atomic_write_json(self.results_dir / f"{task_id}.json", report)
            print(
                f"[{task_id}] finder finished with {len(report.get('findings', []))} finding(s)",
                flush=True,
            )
            issue_ids = self._review_findings(task, report.get("findings", []))
            status = report.get("status", "inconclusive")
            if status not in {"completed", "inconclusive", "blocked"}:
                status = "inconclusive"
            record.update(
                {
                    "status": status,
                    "completed_at": utc_now(),
                    "accepted_issue_ids": issue_ids,
                    "escalation": escalation_metadata,
                    "finder_backend": actual_backend,
                    "controller_pid": None,
                }
            )
            print(f"[{task_id}] {status}; accepted issues: {issue_ids or 'none'}", flush=True)
        except Exception as exc:
            record["last_error"] = f"{type(exc).__name__}: {exc}"
            # A complete OpenCode model cascade plus a Qwen fallback is already
            # one exhaustive attempt. Re-running the same cascade automatically
            # amplifies infrastructure failures without adding evidence.
            record["status"] = (
                "failed"
                if opencode_attempted
                else ("retry" if record["attempts"] < self.max_attempts else "failed")
            )
            record["completed_at"] = utc_now()
            if escalation_metadata is not None:
                record["escalation"] = escalation_metadata
            record["finder_backend"] = actual_backend
            record["controller_pid"] = None
            if (
                record["status"] == "failed"
                and self.escalator is not None
                and not opencode_attempted
            ):
                print(f"[{task_id}] terminal failure; handing off to OpenCode", flush=True)
                try:
                    escalated, metadata = self.escalator.escalate(
                        task, {}, record["last_error"]
                    )
                    atomic_write_json(self.results_dir / f"{task_id}.json", escalated)
                    issue_ids = self._review_findings(task, escalated.get("findings", []))
                    record.update(
                        {
                            "status": escalated.get("status", "blocked"),
                            "accepted_issue_ids": issue_ids,
                            "escalation": metadata,
                            "last_error": None,
                        }
                    )
                except Exception as escalation_exc:
                    record["escalation"] = {
                        "status": "failed",
                        "error": f"{type(escalation_exc).__name__}: {escalation_exc}",
                    }
            print(f"[{task_id}] {record['status']}: {record['last_error']}", flush=True)
        state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)

    def _run_finder(
        self, task: dict[str, Any], prerequisite_summaries: list[dict[str, Any]],
        repository_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": FINDER_SYSTEM},
            {"role": "user", "content": finder_task_prompt(task, prerequisite_summaries, repository_context)},
        ]
        transcript_path = self.logs_dir / f"{task['id']}.finder.json"
        atomic_write_json(transcript_path, messages)
        for _ in range(self.max_tool_steps):
            response_text = self.client.chat(messages)
            messages.append({"role": "assistant", "content": response_text})
            atomic_write_json(transcript_path, messages)
            try:
                response = parse_json_response(response_text)
            except ValueError as exc:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"FORMAT ERROR: {exc}. Return the same intended response again as one "
                            "valid JSON object with no prose or markdown fences."
                        ),
                    }
                )
                atomic_write_json(transcript_path, messages)
                continue
            if response.get("type") == "ready_to_finalize":
                messages.append({"role": "user", "content": FINAL_REPORT_REQUEST})
                response_text = self.client.chat(
                    messages,
                    max_tokens=self.local_final_max_tokens,
                    timeout_seconds=max(getattr(self.client, "timeout_seconds", 300), 900),
                )
                messages.append({"role": "assistant", "content": response_text})
                atomic_write_json(transcript_path, messages)
                response = parse_json_response(response_text)
            if response.get("type") == "final":
                report = response.get("report")
                if not isinstance(report, dict):
                    raise ValueError("finder final response has no report object")
                report["task_id"] = task["id"]
                report.setdefault("findings", [])
                report.setdefault("evidence", [])
                report.setdefault("checks_performed", [])
                report.setdefault("limitations", [])
                report.setdefault("criterion_results", [])
                return report
            if response.get("type") != "tool":
                raise ValueError("finder response type must be tool or final")
            tool_name = response.get("tool")
            args = response.get("args", {})
            if not isinstance(tool_name, str) or not isinstance(args, dict):
                raise ValueError("invalid tool request")
            print(f"[{task['id']}] tool: {tool_name}", flush=True)
            try:
                result = self.tools.execute(tool_name, args)
                tool_result = {"ok": True, "tool": tool_name, "result": result}
            # Data libraries expose their own exception hierarchies (for example,
            # DuckDB CatalogException). A failed read-only query is an agent-visible
            # tool result, not an orchestrator crash.
            except Exception as exc:
                tool_result = {"ok": False, "tool": tool_name, "error": str(exc)}
            serialized_result = json.dumps(tool_result, ensure_ascii=False)
            if len(serialized_result) > self.local_tool_result_chars:
                serialized_result = json.dumps(
                    {
                        "ok": tool_result["ok"],
                        "tool": tool_name,
                        "truncated": True,
                        "original_chars": len(serialized_result),
                        "result_preview": serialized_result[: self.local_tool_result_chars],
                        "guidance": "Run a narrower query/read if omitted evidence is needed.",
                    },
                    ensure_ascii=False,
                )
            messages.append(
                {
                    "role": "user",
                    "content": "TOOL RESULT:\n" + serialized_result,
                }
            )
            atomic_write_json(transcript_path, messages)
        raise RuntimeError(f"finder exceeded {self.max_tool_steps} tool steps")

    def _review_findings(
        self, task: dict[str, Any], findings: list[dict[str, Any]]
    ) -> list[str]:
        accepted: list[str] = []
        decisions: list[dict[str, Any]] = []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            issues = read_json(self.issues_path, default=[])
            candidates = candidate_issues(finding, issues)
            print(
                f"[{task['id']}] manager reviewing: {finding.get('title', 'untitled')}",
                flush=True,
            )
            manager_messages = [
                {"role": "system", "content": MANAGER_SYSTEM},
                {"role": "user", "content": manager_prompt(task, finding, candidates)},
            ]
            decision = None
            for _ in range(3):
                response = self.client.chat(manager_messages, max_tokens=2048)
                manager_messages.append({"role": "assistant", "content": response})
                try:
                    decision = parse_json_response(response)
                    break
                except ValueError as exc:
                    manager_messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"FORMAT ERROR: {exc}. Resend only one valid JSON decision object."
                            ),
                        }
                    )
            if decision is None:
                raise ValueError("manager failed to return valid JSON after three attempts")
            issue_id = apply_decision(issues, decision, finding, task["id"])
            decisions.append(
                {"finding": finding, "candidates": [i["id"] for i in candidates], "decision": decision}
            )
            atomic_write_json(self.issues_path, issues)
            render_markdown(issues, self.output_path)
            if issue_id:
                accepted.append(issue_id)
        atomic_write_json(self.decisions_dir / f"{task['id']}.json", decisions)
        return accepted

    def _prerequisite_summaries(
        self, checklist: dict[str, Any], task: dict[str, Any]
    ) -> list[dict[str, Any]]:
        summaries = []
        for task_id in task.get("prerequisites", []):
            if task_id == "NONE":
                continue
            report = read_json(self.results_dir / f"{task_id}.json", default={})
            summaries.append(
                {
                    "task_id": task_id,
                    "status": report.get("status"),
                    "summary": report.get("summary"),
                    "accepted_issue_ids": read_json(self.state_path)["tasks"][task_id].get(
                        "accepted_issue_ids", []
                    ),
                }
            )
        return summaries
