from __future__ import annotations

import atexit
import json
import os
import queue
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .local_model import parse_json_response
from .storage import atomic_write_json, atomic_write_text, read_json


DEFAULT_MODELS = [
    "opencode/longcat-2.5-preview-free",
    "opencode/big-pickle",
    "opencode/space-bunny-free",
    "opencode/nemotron-3-ultra-free",
]

DEFAULT_MODEL_VARIANTS = {
    "opencode/space-bunny-free": "medium",
}


@dataclass
class OpenCodeEscalator:
    root: Path
    output_dir: Path
    models: list[str] = field(default_factory=lambda: list(DEFAULT_MODELS))
    agent: str = "audit-escalation"
    timeout_seconds: int = 1800
    stall_timeout_seconds: int = 600
    max_tool_calls: int = 30
    max_consecutive_repeats: int = 3
    pure: bool = True
    isolated: bool = True
    adaptive_ordering: bool = True
    model_variants: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_MODEL_VARIANTS)
    )

    def escalate(
        self,
        task: dict[str, Any],
        primary_report: dict[str, Any],
        primary_error: str | None = None,
        *,
        primary_mode: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        task_id = task["id"]
        task_dir = self.output_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        request = self._request(
            task, primary_report, primary_error, primary_mode=primary_mode
        )
        atomic_write_text(task_dir / "request.txt", request)
        attempts = []
        ordered_models = self._ordered_models()
        if ordered_models != self.models:
            print(
                f"[{task_id}] adaptive model order: " + " -> ".join(ordered_models),
                flush=True,
            )
        for model in ordered_models:
            variant = self.model_variants.get(model)
            attempt_path = task_dir / f"{self._safe_model(model)}.json"
            attempt = self._recover_attempt(task_id, model, attempt_path)
            if attempt is None:
                print(
                    f"[{task_id}] OpenCode model {model}"
                    f"{f' ({variant})' if variant else ''} started; "
                    f"stall cutoff={self.stall_timeout_seconds}s, "
                    f"tool-call limit={self.max_tool_calls}",
                    flush=True,
                )
                attempt = self._invoke(task_id, model, request)
            else:
                print(
                    f"[{task_id}] recovered valid verdict from prior {model} output",
                    flush=True,
                )
            attempts.append(attempt)
            atomic_write_json(attempt_path, attempt)
            if attempt.get("report"):
                verdict = str(attempt["report"].get("verdict", "UNRESOLVED")).lower()
                summary = {
                    "status": verdict,
                    "selected_model": model,
                    "attempts": [self._attempt_summary(item) for item in attempts],
                }
                atomic_write_json(task_dir / "summary.json", summary)
                return attempt["report"], summary
        summary = {
            "status": "unavailable",
            "selected_model": None,
            "attempts": [self._attempt_summary(item) for item in attempts],
        }
        atomic_write_json(task_dir / "summary.json", summary)
        raise RuntimeError(
            "all OpenCode escalation models failed: "
            + "; ".join(f"{item['model']}: {item.get('error')}" for item in attempts)
        )

    def _ordered_models(self) -> list[str]:
        """Prefer models with the strongest observed verdict completion rate."""
        if not self.adaptive_ordering or len(self.models) < 2:
            return list(self.models)
        stats = {model: {"attempts": 0, "successes": 0} for model in self.models}
        for summary_path in self.output_dir.glob("*/summary.json"):
            summary = read_json(summary_path, default={})
            selected = summary.get("selected_model")
            for attempt in summary.get("attempts", []):
                model = attempt.get("model")
                if model not in stats:
                    continue
                stats[model]["attempts"] += 1
                if model == selected and not attempt.get("error"):
                    stats[model]["successes"] += 1

        base_position = {model: index for index, model in enumerate(self.models)}

        def rank(model: str) -> tuple[float, float, int, int]:
            attempts = stats[model]["attempts"]
            successes = stats[model]["successes"]
            return (
                1.0 if successes else 0.0,
                successes / attempts if attempts else 0.0,
                1 if attempts == 0 else 0,
                -base_position[model],
            )

        return sorted(self.models, key=rank, reverse=True)

    def investigate(
        self,
        task: dict[str, Any],
        prerequisite_summaries: list[dict[str, Any]],
        repository_context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Run OpenCode as the primary finder for one bounded checklist task."""
        context = {
            "status": "not_run",
            "summary": "OpenCode is the primary finder; there is no prior local-model report.",
            "prerequisite_summaries": prerequisite_summaries,
            "repository_map_context": repository_context or {},
        }
        return self.escalate(task, context, primary_mode=True)

    def _invoke(self, task_id: str, model: str, request: str) -> dict[str, Any]:
        command = [
            "opencode",
            "run",
            "--model",
            model,
            "--agent",
            self.agent,
            "--format",
            "json",
            "--title",
            f"data-audit-escalation-{task_id}",
            "--auto",
        ]
        if self.pure:
            command.append("--pure")
        variant = self.model_variants.get(model)
        if variant:
            command.extend(["--variant", variant])
        command.append(request)
        task_dir = self.output_dir / task_id
        safe_model = self._safe_model(model)
        event_path = task_dir / f"{safe_model}.events.jsonl"
        progress_path = task_dir / "progress.json"
        started_wall = self._now()
        started = time.monotonic()
        last_meaningful = started
        last_heartbeat = 0.0
        events: list[dict[str, Any]] = []
        texts: list[str] = []
        stderr_lines: list[str] = []
        event_counts: dict[str, int] = {}
        tool_signatures: set[str] = set()
        last_tool_signature: str | None = None
        consecutive_repeats = 0
        completed_tool_calls = 0
        session_id = None
        finish = None
        initial_input_tokens = None
        stop_reason = None
        last_action = "OpenCode process starting"

        isolated_workspace: tempfile.TemporaryDirectory[str] | None = None
        process_cwd = self.root
        process_env = {
            **os.environ,
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
        }
        if self.isolated:
            isolated_workspace = tempfile.TemporaryDirectory(
                prefix="data-audit-opencode-"
            )
            isolated_root = Path(isolated_workspace.name)
            process_cwd = isolated_root / "workspace"
            agent_dir = isolated_root / "xdg" / "opencode" / "agents"
            process_cwd.mkdir(parents=True)
            agent_dir.mkdir(parents=True)
            source = self.root / ".opencode" / "agents" / f"{self.agent}.md"
            agent_text = source.read_text(encoding="utf-8")
            external_rule = (
                "  external_directory:\n"
                '    "*": deny\n'
                f'    "{self.root}/**": allow'
            )
            agent_text = agent_text.replace(
                "  external_directory: deny", external_rule
            )
            atomic_write_text(agent_dir / f"{self.agent}.md", agent_text)
            process_env.update(
                {
                    "XDG_CONFIG_HOME": str(isolated_root / "xdg"),
                    "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
                }
            )

        try:
            process = subprocess.Popen(
                command,
                cwd=process_cwd,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True,
            )
        except OSError as exc:
            if isolated_workspace is not None:
                isolated_workspace.cleanup()
            return {"model": model, "error": f"{type(exc).__name__}: {exc}"}

        def stop_child_at_exit() -> None:
            if process.poll() is None:
                self._stop_process(process)
            progress = read_json(progress_path, default={})
            if progress.get("status") in {"running", "stopping"}:
                progress.update(
                    {
                        "status": "interrupted",
                        "updated_at": self._now(),
                        "last_action": "audit controller exited; child process stopped",
                        "stop_reason": "controller_interrupted",
                    }
                )
                atomic_write_json(progress_path, progress)
            if isolated_workspace is not None:
                isolated_workspace.cleanup()

        # The child owns a separate process group so an interactive Ctrl+C reaches
        # the controller first. Ensure that interruption cannot orphan OpenCode or
        # any command it spawned.
        atexit.register(stop_child_at_exit)

        streams: queue.Queue[tuple[str, str | None]] = queue.Queue()

        def pump(name: str, stream: Any) -> None:
            try:
                for line in iter(stream.readline, ""):
                    streams.put((name, line))
            finally:
                streams.put((name, None))

        assert process.stdout is not None and process.stderr is not None
        for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            threading.Thread(target=pump, args=(name, stream), daemon=True).start()

        ended: set[str] = set()
        event_path.parent.mkdir(parents=True, exist_ok=True)
        with event_path.open("w", encoding="utf-8") as event_log:
            while len(ended) < 2 or process.poll() is None:
                now = time.monotonic()
                try:
                    source, line = streams.get(timeout=1.0)
                except queue.Empty:
                    source, line = "", ""

                if line is None:
                    ended.add(source)
                elif line:
                    if source == "stderr":
                        stderr_lines.append(line)
                    else:
                        event_log.write(line)
                        event_log.flush()
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            event = None
                        if isinstance(event, dict):
                            events.append(event)
                            event_type = str(event.get("type", "unknown"))
                            event_counts[event_type] = event_counts.get(event_type, 0) + 1
                            session_id = session_id or event.get("sessionID")
                            part = event.get("part", {})
                            if event_type == "text":
                                text = part.get("text")
                                if isinstance(text, str):
                                    texts.append(text)
                                    last_action = f"assistant text (+{len(text):,} chars)"
                                    if self._extract_verdict_report([text]) is not None:
                                        last_meaningful = now
                            elif event_type == "tool_use":
                                state = part.get("state", {})
                                tool = str(part.get("tool", "unknown"))
                                status = str(state.get("status", "unknown"))
                                signature = self._tool_signature(tool, state.get("input"))
                                last_action = f"{tool} tool {status}: {self._input_preview(state.get('input'))}"
                                if status == "completed":
                                    completed_tool_calls += 1
                                    if signature == last_tool_signature:
                                        consecutive_repeats += 1
                                    else:
                                        consecutive_repeats = 0
                                    last_tool_signature = signature
                                    if signature not in tool_signatures:
                                        tool_signatures.add(signature)
                                        last_meaningful = now
                            elif event_type == "step_finish":
                                finish = part
                                if initial_input_tokens is None:
                                    initial_input_tokens = (
                                        part.get("tokens", {}).get("input")
                                    )
                                last_action = f"step finished: {part.get('reason', 'unknown')}"
                            elif event_type == "error":
                                last_action = "OpenCode emitted an error event"

                now = time.monotonic()
                if now - started >= self.timeout_seconds:
                    stop_reason = f"total timeout after {self.timeout_seconds}s"
                elif now - last_meaningful >= self.stall_timeout_seconds:
                    stop_reason = (
                        "no meaningful progress for "
                        f"{self.stall_timeout_seconds}s"
                    )
                elif completed_tool_calls >= self.max_tool_calls:
                    stop_reason = f"tool-call limit reached ({self.max_tool_calls})"
                elif consecutive_repeats >= self.max_consecutive_repeats:
                    stop_reason = (
                        "repeated the same completed tool call "
                        f"{self.max_consecutive_repeats + 1} times"
                    )

                if now - last_heartbeat >= 5.0 or stop_reason:
                    progress = {
                        "status": "stopping" if stop_reason else "running",
                        "task_id": task_id,
                        "model": model,
                        "variant": variant,
                        "pid": process.pid,
                        "session_id": session_id,
                        "started_at": started_wall,
                        "updated_at": self._now(),
                        "elapsed_seconds": round(now - started, 1),
                        "seconds_since_meaningful_progress": round(
                            now - last_meaningful, 1
                        ),
                        "meaningful_progress": {
                            "unique_completed_tool_calls": len(tool_signatures),
                            "completed_tool_calls": completed_tool_calls,
                            "consecutive_repeated_tool_calls": consecutive_repeats,
                            "assistant_text_chars": sum(map(len, texts)),
                            "has_verdict_candidate": self._extract_verdict_report(texts)
                            is not None,
                        },
                        "event_counts": event_counts,
                        "token_usage": {
                            "initial_input_tokens": initial_input_tokens,
                            "latest_step": (finish or {}).get("tokens"),
                        },
                        "last_action": last_action,
                        "stop_reason": stop_reason,
                    }
                    atomic_write_json(progress_path, progress)
                    last_heartbeat = now
                if stop_reason and process.poll() is None:
                    self._stop_process(process)

        return_code = process.wait()
        atexit.unregister(stop_child_at_exit)
        if isolated_workspace is not None:
            isolated_workspace.cleanup()
        combined = "\n".join(texts).strip()
        result: dict[str, Any] = {
            "model": model,
            "variant": variant,
            "exit_code": return_code,
            "session_id": session_id,
            "stderr": "".join(stderr_lines)[-8000:],
            "events": events,
            "text": combined,
            "finish": finish,
            "initial_input_tokens": initial_input_tokens,
            "stop_reason": stop_reason,
            "progress": read_json(progress_path, default={}),
        }
        if not combined:
            result["error"] = stop_reason or "OpenCode returned no assistant text"
            self._finalize_progress(progress_path, result)
            return result
        report = self._extract_verdict_report(texts)
        if report is None:
            if stop_reason:
                result["error"] = stop_reason
            elif return_code != 0:
                result["error"] = f"OpenCode exited {return_code}"
            else:
                result["error"] = "OpenCode returned no valid verdict JSON"
            self._finalize_progress(progress_path, result)
            return result
        report = self._prepare_report(task_id, report)
        result["report"] = report
        self._finalize_progress(progress_path, result)
        return result

    @staticmethod
    def _extract_verdict_report(texts: list[str]) -> dict[str, Any] | None:
        """Find a verdict object even when OpenCode prefixes it with narration."""
        decoder = json.JSONDecoder()
        for text in reversed(texts):
            try:
                candidate = parse_json_response(text)
                if str(candidate.get("verdict", "")).upper() in {"RESOLVED", "UNRESOLVED"}:
                    return candidate
            except ValueError:
                pass
            for index, char in enumerate(text):
                if char != "{":
                    continue
                try:
                    candidate, _ = decoder.raw_decode(text[index:])
                except json.JSONDecodeError:
                    continue
                if isinstance(candidate, dict) and str(candidate.get("verdict", "")).upper() in {
                    "RESOLVED",
                    "UNRESOLVED",
                }:
                    return candidate
        return None

    @classmethod
    def _recover_attempt(
        cls, task_id: str, model: str, path: Path
    ) -> dict[str, Any] | None:
        attempt = read_json(path)
        if not isinstance(attempt, dict):
            return None
        report = attempt.get("report")
        if not isinstance(report, dict):
            text = attempt.get("text")
            if not isinstance(text, str):
                return None
            report = cls._extract_verdict_report([text])
        if report is None:
            return None
        attempt["model"] = model
        attempt["report"] = cls._prepare_report(task_id, report)
        attempt["recovered_from_existing_output"] = True
        attempt.pop("error", None)
        return attempt

    @staticmethod
    def _prepare_report(task_id: str, report: dict[str, Any]) -> dict[str, Any]:
        verdict = str(report.get("verdict", "")).upper()
        if verdict not in {"RESOLVED", "UNRESOLVED"}:
            raise ValueError("response verdict must be RESOLVED or UNRESOLVED")
        report["task_id"] = task_id
        report["status"] = "completed" if verdict == "RESOLVED" else "blocked"
        for key in (
            "checks_performed",
            "evidence",
            "findings",
            "limitations",
            "criterion_results",
        ):
            report.setdefault(key, [])
        return report

    @staticmethod
    def _tool_signature(tool: str, value: Any) -> str:
        return tool + ":" + json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)

    @staticmethod
    def _input_preview(value: Any) -> str:
        preview = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
        return preview[:180] + ("..." if len(preview) > 180 else "")

    @staticmethod
    def _stop_process(process: subprocess.Popen[str]) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    @classmethod
    def _finalize_progress(cls, path: Path, result: dict[str, Any]) -> None:
        progress = read_json(path, default={})
        events = result.get("events") or []
        event_counts: dict[str, int] = {}
        completed_signatures: list[str] = []
        for event in events:
            event_type = str(event.get("type", "unknown"))
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            if event_type == "tool_use":
                part = event.get("part", {})
                state = part.get("state", {})
                if state.get("status") == "completed":
                    completed_signatures.append(
                        cls._tool_signature(str(part.get("tool", "unknown")), state.get("input"))
                    )
        text = str(result.get("text", ""))
        meaningful = progress.setdefault("meaningful_progress", {})
        meaningful.update(
            {
                "unique_completed_tool_calls": len(set(completed_signatures)),
                "completed_tool_calls": len(completed_signatures),
                "assistant_text_chars": len(text),
                "has_verdict_candidate": bool(result.get("report")),
            }
        )
        progress.update(
            {
                "status": "completed" if result.get("report") else "failed",
                "completed_at": cls._now(),
                "updated_at": cls._now(),
                "exit_code": result.get("exit_code"),
                "stop_reason": result.get("stop_reason"),
                "error": result.get("error"),
                "verdict": (result.get("report") or {}).get("verdict"),
                "event_counts": event_counts,
                "last_action": (
                    "valid verdict received"
                    if result.get("report")
                    else progress.get("last_action")
                ),
            }
        )
        atomic_write_json(path, progress)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _request(
        self,
        task: dict[str, Any],
        report: dict[str, Any],
        primary_error: str | None,
        *,
        primary_mode: bool = False,
    ) -> str:
        introduction = (
            "Perform this single read-only data-audit task as the primary investigator. "
            "Inspect the repository directly, satisfy every completion criterion, and "
            "return the required JSON object."
            if primary_mode
            else "Resolve this single read-only data-audit escalation. The primary agent "
            "could not produce a complete verdict. Inspect the repository directly, close "
            "the evidence gap, and return the required JSON object."
        )
        return (
            introduction
            + " DISCOVER is a discovery instruction, never a literal object name.\n\n"
            "REPOSITORY ROOT:\n"
            + str(self.root)
            + "\n\n"
            "CHECKLIST TASK:\n"
            + json.dumps(task, indent=2, ensure_ascii=False)
            + ("\n\nRUN CONTEXT:\n" if primary_mode else "\n\nPRIMARY REPORT:\n")
            + json.dumps(report, indent=2, ensure_ascii=False)
            + "\n\nPRIMARY ERROR:\n"
            + json.dumps(primary_error, ensure_ascii=False)
        )

    @staticmethod
    def _safe_model(model: str) -> str:
        return model.replace("/", "__").replace(":", "_")

    @staticmethod
    def _attempt_summary(attempt: dict[str, Any]) -> dict[str, Any]:
        finish = attempt.get("finish") or {}
        return {
            "model": attempt.get("model"),
            "session_id": attempt.get("session_id"),
            "error": attempt.get("error"),
            "tokens": finish.get("tokens"),
            "initial_input_tokens": attempt.get("initial_input_tokens"),
        }
