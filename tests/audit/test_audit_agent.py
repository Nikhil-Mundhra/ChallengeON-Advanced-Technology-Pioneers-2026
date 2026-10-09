from __future__ import annotations

import json
import io
import subprocess
from pathlib import Path

import pytest


from audit_agent.checklist import next_ready_task, validate_checklist
from audit_agent.dashboard import build_snapshot, render_dashboard
from audit_agent.discovery import context_for_task, ensure_repository_map
from audit_agent.escalation import OpenCodeEscalator
from audit_agent.issues import apply_decision, candidate_issues, render_markdown
from audit_agent.local_model import OpenAICompatibleClient, parse_json_response
from audit_agent.runner import AuditRunner
from audit_agent.storage import atomic_write_json, read_json
from audit_agent.tools import ReadOnlyTools, ToolError


def sample_checklist():
    return {
        "tasks": [
            {"id": "A", "prerequisites": ["NONE"]},
            {"id": "B", "prerequisites": ["A"]},
        ],
        "execution_order": [{"task_ids": ["A", "B"]}],
        "final_completeness_checks": ["The checklist contains 2 bounded tasks."],
    }


def test_opencode_default_tool_call_limit_is_30(tmp_path: Path):
    escalator = OpenCodeEscalator(tmp_path, tmp_path / "escalations")
    assert escalator.max_tool_calls == 30


def test_opencode_adaptive_order_prefers_observed_verdict_rate(tmp_path: Path):
    output = tmp_path / "escalations"
    atomic_write_json(
        output / "A" / "summary.json",
        {
            "selected_model": "model/longcat",
            "attempts": [
                {"model": "model/big", "error": "failed"},
                {"model": "model/longcat", "error": None},
            ],
        },
    )
    atomic_write_json(
        output / "B" / "summary.json",
        {
            "selected_model": None,
            "attempts": [{"model": "model/failed", "error": "stalled"}],
        },
    )
    escalator = OpenCodeEscalator(
        tmp_path,
        output,
        models=["model/big", "model/longcat", "model/untested", "model/failed"],
    )

    assert escalator._ordered_models() == [
        "model/longcat",
        "model/untested",
        "model/big",
        "model/failed",
    ]


def test_opencode_explicit_order_can_disable_adaptation(tmp_path: Path):
    escalator = OpenCodeEscalator(
        tmp_path,
        tmp_path / "escalations",
        models=["model/b", "model/a"],
        adaptive_ordering=False,
    )
    assert escalator._ordered_models() == ["model/b", "model/a"]


def test_space_bunny_defaults_to_medium_variant(tmp_path: Path):
    escalator = OpenCodeEscalator(tmp_path, tmp_path / "escalations")
    assert escalator.model_variants["opencode/space-bunny-free"] == "medium"


def test_scheduler_respects_dependencies():
    checklist = sample_checklist()
    state = {"tasks": {"A": {"status": "pending"}, "B": {"status": "pending"}}}
    assert next_ready_task(checklist, state)["id"] == "A"
    state["tasks"]["A"]["status"] = "completed"
    assert next_ready_task(checklist, state)["id"] == "B"


def test_terminal_inconclusive_prerequisite_does_not_deadlock_queue():
    checklist = sample_checklist()
    state = {"tasks": {"A": {"status": "inconclusive"}, "B": {"status": "pending"}}}
    assert next_ready_task(checklist, state)["id"] == "B"


def test_validation_detects_declared_count_mismatch():
    checklist = sample_checklist()
    checklist["final_completeness_checks"] = ["The checklist contains 83 bounded tasks."]
    assert "declared task count 83" in validate_checklist(checklist)[0]


def test_tools_reject_escape_and_mutating_sql(tmp_path: Path):
    tools = ReadOnlyTools(tmp_path)
    with pytest.raises(ToolError):
        tools.read_text("../outside")
    with pytest.raises(ToolError):
        tools.duckdb_query("db.duckdb", "DROP TABLE x")


def test_issue_add_candidates_and_render(tmp_path: Path):
    issues = []
    finding = {
        "title": "Guest rows duplicated",
        "category": "keys",
        "claim": "Guest key duplicates exist",
        "fingerprints": ["guest:key:duplicate"],
        "affected_paths": ["guest.parquet"],
        "evidence": [{"source": "guest.parquet", "observation": "2 duplicates"}],
    }
    decision = {
        "decision": "ADD",
        "target_issue_id": None,
        "issue": {
            "title": finding["title"],
            "priority": "P1",
            "category": "keys",
            "summary": finding["claim"],
            "why_it_matters": "Double counting",
            "smallest_remedy": "Enforce the key",
            "fingerprints": finding["fingerprints"],
            "affected_paths": finding["affected_paths"],
            "evidence": finding["evidence"],
        },
    }
    assert apply_decision(issues, decision, finding, "KEY-001") == "ISSUE-0001"
    assert candidate_issues(finding, issues)[0]["id"] == "ISSUE-0001"
    target = tmp_path / "issues.md"
    render_markdown(issues, target)
    assert "ISSUE-0001" in target.read_text()


def test_atomic_json_round_trip(tmp_path: Path):
    path = tmp_path / "state.json"
    atomic_write_json(path, {"ok": True})
    assert read_json(path) == {"ok": True}


def test_model_response_parser_rejects_prose():
    with pytest.raises(ValueError):
        parse_json_response("```json\n{}\n```")


def test_qwen_client_uses_openai_shape_and_disables_thinking(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["payload"] = json.loads(kwargs["input"])
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"role": "assistant", "content": '{"ok":true}'},
                        }
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = OpenAICompatibleClient(max_tokens=1234)
    result = client.chat([{"role": "user", "content": "return json"}])

    assert result == '{"ok":true}'
    assert "http://localhost:8000/v1/chat/completions" in captured["command"]
    assert captured["payload"]["stream"] is True
    assert captured["payload"]["model"] == "mlx-community/Qwen3.5-4B-MLX-4bit"
    assert captured["payload"]["max_tokens"] == 1234
    assert captured["payload"]["chat_template_kwargs"] == {
        "enable_thinking": False
    }
    assert "format" not in captured["payload"]


def test_qwen_client_rejects_reasoning_only_response(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "length",
                            "message": {"role": "assistant", "reasoning": "still thinking"},
                        }
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="enable_thinking=false"):
        OpenAICompatibleClient().chat([{"role": "user", "content": "test"}])


def test_qwen_client_compacts_oversized_prompt_without_losing_head_or_tail():
    client = OpenAICompatibleClient(max_prompt_chars=180)
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "old" * 100},
        {"role": "user", "content": "recent evidence"},
    ]

    bounded = client._bounded_messages(messages)

    assert bounded[0] == messages[0]
    assert bounded[1] == messages[1]
    assert "CONTEXT COMPACTION" in bounded[2]["content"]
    assert bounded[-1] == messages[-1]
    assert sum(len(item["content"]) for item in bounded) <= 180


def test_opencode_escalator_parses_json_events(tmp_path: Path, monkeypatch):
    report = {
        "verdict": "RESOLVED",
        "summary": "done",
        "findings": [],
    }
    stdout = "\n".join(
        [
            json.dumps(
                {
                    "type": "text",
                    "sessionID": "ses_test",
                    "part": {"text": json.dumps(report)},
                }
            ),
            json.dumps(
                {
                    "type": "step_finish",
                    "sessionID": "ses_test",
                    "part": {"tokens": {"input": 10, "output": 5}},
                }
            ),
        ]
    )

    class FakePopen:
        def __init__(self, *args, **kwargs):
            self.stdout = io.StringIO(stdout)
            self.stderr = io.StringIO("")
            self.returncode = 0
            self.pid = 12345

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    escalator = OpenCodeEscalator(
        tmp_path, tmp_path / "escalations", models=["test/model"], isolated=False
    )
    result, metadata = escalator.escalate(
        {"id": "TASK-1", "completion_criteria": ["done"]}, {}
    )
    assert result["status"] == "completed"
    assert metadata["selected_model"] == "test/model"
    assert metadata["attempts"][0]["session_id"] == "ses_test"


def test_opencode_escalator_rejects_empty_success(tmp_path: Path, monkeypatch):
    class FakePopen:
        def __init__(self, *args, **kwargs):
            self.stdout = io.StringIO("")
            self.stderr = io.StringIO("")
            self.returncode = 0
            self.pid = 12345

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    escalator = OpenCodeEscalator(
        tmp_path, tmp_path / "escalations", models=["test/model"], isolated=False
    )
    with pytest.raises(RuntimeError, match="no assistant text"):
        escalator.escalate({"id": "TASK-1"}, {})


def test_opencode_escalator_extracts_verdict_after_narration():
    report = OpenCodeEscalator._extract_verdict_report(
        ['Evidence is complete.\n\n{"verdict":"RESOLVED","summary":"done"}']
    )
    assert report == {"verdict": "RESOLVED", "summary": "done"}


def test_opencode_escalator_recovers_prior_embedded_verdict(tmp_path: Path, monkeypatch):
    task_dir = tmp_path / "escalations" / "TASK-1"
    task_dir.mkdir(parents=True)
    atomic_write_json(
        task_dir / "test__model.json",
        {
            "model": "test/model",
            "error": "not valid JSON",
            "text": 'Finished.\n{"verdict":"RESOLVED","summary":"recovered"}',
        },
    )

    def unexpected_popen(*args, **kwargs):
        raise AssertionError("recovery should not start another model")

    monkeypatch.setattr(subprocess, "Popen", unexpected_popen)
    escalator = OpenCodeEscalator(
        tmp_path, tmp_path / "escalations", models=["test/model"], isolated=False
    )
    result, metadata = escalator.escalate({"id": "TASK-1"}, {})
    assert result["status"] == "completed"
    assert result["summary"] == "recovered"
    assert metadata["selected_model"] == "test/model"


def test_runner_uses_opencode_as_primary_without_calling_qwen(tmp_path: Path):
    checklist = {
        "tasks": [{"id": "TASK-1", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["TASK-1"]}],
        "final_completeness_checks": ["The checklist contains 1 bounded tasks."],
    }
    checklist_path = tmp_path / "checklist.json"
    atomic_write_json(checklist_path, checklist)

    class NeverQwen:
        def chat(self, messages):
            raise AssertionError("Qwen should not be called by the OpenCode finder")

    class FakeOpenCode:
        def investigate(self, task, prerequisites, repository_context=None):
            return (
                {
                    "task_id": task["id"],
                    "status": "completed",
                    "verdict": "RESOLVED",
                    "summary": "done",
                    "findings": [],
                },
                {"status": "resolved", "selected_model": "test/model"},
            )

    runner = AuditRunner(
        tmp_path,
        checklist_path,
        tmp_path / "audit",
        tmp_path / "issues.md",
        NeverQwen(),
        escalator=FakeOpenCode(),
        finder_backend="opencode",
    )
    assert runner.run(max_tasks=1) == 1
    state = read_json(runner.state_path)
    assert state["tasks"]["TASK-1"]["status"] == "completed"
    assert state["tasks"]["TASK-1"]["finder_backend"] == "opencode"


def test_runner_labels_qwen_fallback_when_opencode_fails(tmp_path: Path):
    checklist = {
        "tasks": [{"id": "TASK-1", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["TASK-1"]}],
        "final_completeness_checks": ["The checklist contains 1 bounded tasks."],
    }
    checklist_path = tmp_path / "checklist.json"
    atomic_write_json(checklist_path, checklist)

    class FakeQwen:
        calls = []

        def chat(self, messages, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return json.dumps(
                    {"type": "ready_to_finalize", "reason": "evidence complete"}
                )
            return json.dumps(
                {
                    "type": "final",
                    "report": {
                        "status": "completed",
                        "summary": "local fallback completed",
                        "findings": [],
                    },
                }
            )

    class BrokenOpenCode:
        def investigate(self, task, prerequisites, repository_context=None):
            raise RuntimeError("remote unavailable")

    runner = AuditRunner(
        tmp_path,
        checklist_path,
        tmp_path / "audit",
        tmp_path / "issues.md",
        FakeQwen(),
        escalator=BrokenOpenCode(),
        finder_backend="opencode",
    )
    assert runner.run(max_tasks=1) == 1
    record = read_json(runner.state_path)["tasks"]["TASK-1"]
    assert record["status"] == "completed"
    assert record["finder_backend"] == "qwen_fallback"
    assert record["escalation"]["status"] == "failed_with_qwen_fallback"
    assert runner.client.calls == [
        {},
        {"max_tokens": 8192, "timeout_seconds": 900},
    ]


def test_opencode_then_qwen_failure_does_not_repeat_escalation(tmp_path: Path):
    checklist = {
        "tasks": [{"id": "TASK-1", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["TASK-1"]}],
        "final_completeness_checks": ["The checklist contains 1 bounded tasks."],
    }
    checklist_path = tmp_path / "checklist.json"
    atomic_write_json(checklist_path, checklist)

    class TimedOutQwen:
        def chat(self, messages):
            raise RuntimeError("local Qwen timed out")

    class UnavailableOpenCode:
        investigate_calls = 0

        def investigate(self, task, prerequisites, repository_context=None):
            self.investigate_calls += 1
            raise RuntimeError("all OpenCode models failed")

        def escalate(self, *args, **kwargs):
            raise AssertionError("OpenCode must not be invoked a second time")

    opencode = UnavailableOpenCode()
    runner = AuditRunner(
        tmp_path,
        checklist_path,
        tmp_path / "audit",
        tmp_path / "issues.md",
        TimedOutQwen(),
        escalator=opencode,
        finder_backend="opencode",
    )

    assert runner.run(max_tasks=1) == 1
    record = read_json(runner.state_path)["tasks"]["TASK-1"]
    assert opencode.investigate_calls == 1
    assert record["status"] == "failed"
    assert record["finder_backend"] == "qwen_fallback"
    assert record["escalation"]["status"] == "failed_with_qwen_fallback"
    assert "local Qwen timed out" in record["last_error"]


def test_repository_map_is_versioned_reused_and_scoped(tmp_path: Path):
    (tmp_path / "src" / "engine").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "engine" / "simulator.py").write_text(
        "class TourismDigitalTwin:\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_simulator.py").write_text(
        "from engine.simulator import TourismDigitalTwin\n", encoding="utf-8"
    )
    audit_dir = tmp_path / "audit"

    first = ensure_repository_map(tmp_path, audit_dir)
    second = ensure_repository_map(tmp_path, audit_dir)
    context = context_for_task(
        first,
        {"scope": {"files": ["src/engine/simulator.py"], "tables_or_sheets": []}},
    )

    assert first == second
    assert (audit_dir / "discovery" / "repository_map.json").exists()
    assert (
        audit_dir / "discovery" / f"repository_map.{first['fingerprint'][:12]}.json"
    ).exists()
    assert context["scoped_source_files"][0]["symbols"][0]["name"] == "TourismDigitalTwin"
    assert context["related_source_files"][0]["path"] == "tests/test_simulator.py"
    assert "Navigation metadata only" in context["contract"]


def test_initialize_recovers_interrupted_running_task(tmp_path: Path):
    checklist = {
        "tasks": [{"id": "TASK-1", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["TASK-1"]}],
        "final_completeness_checks": ["The checklist contains 1 bounded tasks."],
    }
    checklist_path = tmp_path / "checklist.json"
    atomic_write_json(checklist_path, checklist)
    audit_dir = tmp_path / "audit"
    atomic_write_json(
        audit_dir / "run_state.json",
        {
            "tasks": {
                "TASK-1": {
                    "status": "running",
                    "attempts": 1,
                    "last_error": None,
                }
            }
        },
    )
    atomic_write_json(
        audit_dir / "escalations" / "TASK-1" / "progress.json",
        {
            "task_id": "TASK-1",
            "status": "interrupted",
            "stop_reason": "controller_interrupted",
        },
    )

    runner = AuditRunner(
        tmp_path,
        checklist_path,
        audit_dir,
        tmp_path / "issues.md",
        OpenAICompatibleClient(),
    )
    state = runner.initialize()

    assert state["tasks"]["TASK-1"]["status"] == "retry"
    assert "controller_interrupted" in state["tasks"]["TASK-1"]["last_error"]


def test_dashboard_builds_progress_summary(tmp_path: Path):
    audit_dir = tmp_path / "audit"
    atomic_write_json(
        audit_dir / "run_state.json",
        {
            "updated_at": "2026-01-01T00:00:00+00:00",
            "validation_warnings": ["sample warning"],
            "tasks": {
                "A": {"status": "completed"},
                "B": {"status": "running", "finder_backend": "opencode"},
            },
        },
    )
    atomic_write_json(audit_dir / "issues.json", [{"status": "open"}])
    atomic_write_json(
        audit_dir / "escalations" / "B" / "progress.json",
        {
            "status": "running",
            "task_id": "B",
            "model": "test/model",
            "elapsed_seconds": 12,
            "seconds_since_meaningful_progress": 2,
            "updated_at": "2026-01-01T00:00:00+00:00",
            "meaningful_progress": {
                "unique_completed_tool_calls": 3,
                "completed_tool_calls": 3,
                "consecutive_repeated_tool_calls": 0,
                "assistant_text_chars": 20,
                "has_verdict_candidate": False,
            },
            "token_usage": {"initial_input_tokens": 2500},
            "last_action": "query completed",
        },
    )
    checklist_path = tmp_path / "checklist.json"
    atomic_write_json(
        checklist_path,
        {"tasks": [{"id": "A", "title": "Done"}, {"id": "B", "title": "Live"}]},
    )

    snapshot = build_snapshot(audit_dir / "run_state.json", audit_dir, checklist_path)
    rendered = render_dashboard(snapshot, color=False)
    assert snapshot["percent_complete"] == 50.0
    assert snapshot["open_issues"] == 1
    assert snapshot["active_tasks"][0]["progress"]["model"] == "test/model"
    assert "Overall" in rendered
    assert "B  Live" in rendered
    assert "2,500 initial tokens" in rendered
