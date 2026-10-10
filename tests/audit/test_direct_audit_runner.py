"""Unit and integration tests for scripts/direct_audit_runner.py."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

import direct_audit_runner
from audit_agent.tools import ReadOnlyTools


REQUIRED_REPORT_KEYS = {
    "task_id",
    "status",
    "summary",
    "checks_performed",
    "evidence",
    "findings",
    "limitations",
    "criterion_results",
}

EXPECTED_TASK_IDS = [
    "REPRO-003",
    "REPRO-004",
    "TEST-001",
    "TEST-002",
    "TEST-003",
    "CONS-001",
    "CONS-002",
    "CONS-003",
    "CONS-004",
    "SEC-001",
    "SEC-002",
    "SEC-003",
    "DOC-001",
    "DOC-002",
    "DOC-003",
    "VS-001",
    "VS-002",
    "VS-003",
    "VS-004",
    "VS-005",
    "VS-006",
    "VS-007",
    "VS-008",
]


def test_build_evidence_structure():
    ev_default = direct_audit_runner.build_evidence("test_source", "loc/1", "obs text")
    assert ev_default == {
        "source": "test_source",
        "locator": "loc/1",
        "observation": "obs text",
        "evidence_level": "INSPECTED",
    }

    ev_custom = direct_audit_runner.build_evidence("test_src", "loc/2", "obs 2", evidence_level="REPRODUCED")
    assert ev_custom["evidence_level"] == "REPRODUCED"


def test_utc_now_format():
    now_str = direct_audit_runner.utc_now()
    dt = datetime.fromisoformat(now_str)
    assert dt.tzinfo is not None


def test_task_handlers_registry_has_all_tasks():
    assert set(EXPECTED_TASK_IDS).issubset(set(direct_audit_runner.TASK_HANDLERS.keys()))
    for task_id in EXPECTED_TASK_IDS:
        handler = direct_audit_runner.TASK_HANDLERS[task_id]
        assert callable(handler)


@pytest.mark.parametrize("task_id", ["CONS-001", "CONS-002", "CONS-003", "SEC-001", "SEC-002", "DOC-001", "DOC-003", "VS-004", "VS-007", "VS-008"])
def test_data_inspection_handlers_conform_to_schema(task_id: str):
    tools = ReadOnlyTools(ROOT_DIR)
    task = {"id": task_id, "title": f"Test {task_id}"}
    handler = direct_audit_runner.TASK_HANDLERS[task_id]
    report = handler(tools, task)

    assert REQUIRED_REPORT_KEYS.issubset(set(report.keys()))
    assert report["task_id"] == task_id
    assert report["status"] in {"completed", "blocked", "failed"}
    assert isinstance(report["summary"], str) and len(report["summary"]) > 0
    assert isinstance(report["checks_performed"], list) and len(report["checks_performed"]) > 0
    assert isinstance(report["evidence"], list)
    for ev in report["evidence"]:
        assert {"source", "locator", "observation", "evidence_level"}.issubset(set(ev.keys()))
    assert isinstance(report["criterion_results"], list) and len(report["criterion_results"]) > 0


def test_simulation_handler_domestic_decoupling():
    tools = ReadOnlyTools(ROOT_DIR)
    task = {"id": "CONS-004", "title": "Defaults and Domestic Decoupling"}
    report = direct_audit_runner.audit_CONS_004(tools, task)

    assert report["task_id"] == "CONS-004"
    assert report["status"] == "completed"
    assert any("domestic decoupling" in c.get("criterion", "").lower() for c in report["criterion_results"])


def test_simulation_handler_uk_value_stream():
    tools = ReadOnlyTools(ROOT_DIR)
    task = {"id": "VS-001", "title": "Trace UK Market"}
    report = direct_audit_runner.audit_VS_001(tools, task)

    assert report["task_id"] == "VS-001"
    assert report["status"] == "completed"
    assert any("UK" in ev["observation"] for ev in report["evidence"])


def test_simulation_handler_cold_start():
    tools = ReadOnlyTools(ROOT_DIR)
    task = {"id": "VS-006", "title": "Cold start Brazil"}
    report = direct_audit_runner.audit_VS_006(tools, task)

    assert report["task_id"] == "VS-006"
    assert report["status"] == "completed"
    assert any("cold_start" in ev["observation"].lower() for ev in report["evidence"])


def test_run_pipeline_terminates_when_all_complete(tmp_path: Path, monkeypatch, capsys):
    checklist_data = {
        "tasks": [{"id": "CONS-001", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["CONS-001"]}],
        "final_completeness_checks": [],
    }
    state_data = {
        "tasks": {"CONS-001": {"status": "completed"}},
        "updated_at": direct_audit_runner.utc_now(),
    }
    checklist_path = tmp_path / "checklist.json"
    checklist_path.write_text(json.dumps(checklist_data))
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    state_path = audit_dir / "run_state.json"
    state_path.write_text(json.dumps(state_data))
    issues_path = audit_dir / "issues.json"
    issues_path.write_text("[]")

    monkeypatch.setattr(direct_audit_runner, "ROOT_DIR", tmp_path)
    meta_checklist_dir = tmp_path / "meta" / "audits" / "data_issues"
    meta_checklist_dir.mkdir(parents=True)
    (meta_checklist_dir / "checklist.json").write_text(json.dumps(checklist_data))

    direct_audit_runner.run_pipeline()
    captured = capsys.readouterr()
    assert "All tasks in checklist are complete or terminal!" in captured.out


def test_run_pipeline_executes_pending_task_and_records_decision(tmp_path: Path, monkeypatch):
    finding = {
        "title": "Sample Finding",
        "priority": "P2",
        "category": "test:sample",
        "claim": "Sample claim text",
        "why_it_matters": "Matters for test",
        "smallest_remedy": "Fix remedy",
        "fingerprints": ["sample:fingerprint:1"],
        "affected_paths": ["sample.py"],
        "evidence": "evidence string",
    }
    mock_report = {
        "task_id": "TEST-TASK",
        "status": "completed",
        "summary": "Completed test task",
        "checks_performed": ["Check 1"],
        "evidence": [direct_audit_runner.build_evidence("s", "l", "o")],
        "findings": [finding],
        "limitations": [],
        "criterion_results": [{"criterion": "crit", "status": "verified", "evidence": "ev"}],
    }

    mock_handler = MagicMock(return_value=mock_report)

    checklist_data = {
        "tasks": [{"id": "TEST-TASK", "title": "Test Task", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["TEST-TASK"]}],
        "final_completeness_checks": [],
    }
    state_data = {
        "tasks": {"TEST-TASK": {"status": "pending", "attempts": 0}},
        "updated_at": direct_audit_runner.utc_now(),
    }
    meta_checklist_dir = tmp_path / "meta" / "audits" / "data_issues"
    meta_checklist_dir.mkdir(parents=True)
    (meta_checklist_dir / "checklist.json").write_text(json.dumps(checklist_data))

    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    state_path = audit_dir / "run_state.json"
    state_path.write_text(json.dumps(state_data))
    issues_path = audit_dir / "issues.json"
    issues_path.write_text("[]")

    monkeypatch.setattr(direct_audit_runner, "ROOT_DIR", tmp_path)
    monkeypatch.setitem(direct_audit_runner.TASK_HANDLERS, "TEST-TASK", mock_handler)

    direct_audit_runner.run_pipeline()

    # Verify task result was written
    result_file = audit_dir / "task_results" / "TEST-TASK.json"
    assert result_file.exists()
    assert json.loads(result_file.read_text())["task_id"] == "TEST-TASK"

    # Verify state was updated
    updated_state = json.loads(state_path.read_text())
    assert updated_state["tasks"]["TEST-TASK"]["status"] == "completed"
    assert updated_state["tasks"]["TEST-TASK"]["finder_backend"] == "direct_audit"
    assert len(updated_state["tasks"]["TEST-TASK"]["accepted_issue_ids"]) == 1

    # Verify decision was written and issue added
    decision_file = audit_dir / "manager_decisions" / "TEST-TASK.json"
    assert decision_file.exists()
    decisions = json.loads(decision_file.read_text())
    assert len(decisions) == 1
    assert decisions[0]["decision"]["decision"] == "ADD"

    # Verify issues.json and issues.md were updated
    issues = json.loads(issues_path.read_text())
    assert len(issues) == 1
    assert issues[0]["title"] == "Sample Finding"
    assert (audit_dir / "issues.md").exists()


def test_run_pipeline_merges_finding_with_matching_fingerprint(tmp_path: Path, monkeypatch):
    existing_issue = {
        "id": "ISSUE-0001",
        "title": "Existing Issue",
        "fingerprints": ["sample:fingerprint:1"],
    }
    finding = {
        "title": "Related Finding",
        "priority": "P2",
        "category": "test:sample",
        "claim": "Overlapping fingerprint claim",
        "fingerprints": ["sample:fingerprint:1"],
        "evidence": "evidence string",
    }
    mock_report = {
        "task_id": "TEST-MERGE",
        "status": "completed",
        "summary": "Merged task",
        "checks_performed": ["Check"],
        "evidence": [],
        "findings": [finding],
        "limitations": [],
        "criterion_results": [],
    }

    mock_handler = MagicMock(return_value=mock_report)
    checklist_data = {
        "tasks": [{"id": "TEST-MERGE", "title": "Merge Task", "prerequisites": ["NONE"]}],
        "execution_order": [{"task_ids": ["TEST-MERGE"]}],
        "final_completeness_checks": [],
    }
    state_data = {
        "tasks": {"TEST-MERGE": {"status": "pending", "attempts": 0}},
        "updated_at": direct_audit_runner.utc_now(),
    }
    meta_checklist_dir = tmp_path / "meta" / "audits" / "data_issues"
    meta_checklist_dir.mkdir(parents=True)
    (meta_checklist_dir / "checklist.json").write_text(json.dumps(checklist_data))

    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    state_path = audit_dir / "run_state.json"
    state_path.write_text(json.dumps(state_data))
    issues_path = audit_dir / "issues.json"
    issues_path.write_text(json.dumps([existing_issue]))

    monkeypatch.setattr(direct_audit_runner, "ROOT_DIR", tmp_path)
    monkeypatch.setitem(direct_audit_runner.TASK_HANDLERS, "TEST-MERGE", mock_handler)

    direct_audit_runner.run_pipeline()

    decision_file = audit_dir / "manager_decisions" / "TEST-MERGE.json"
    assert decision_file.exists()
    decisions = json.loads(decision_file.read_text())
    assert len(decisions) == 1
    assert decisions[0]["decision"]["decision"] == "MERGE"
    assert decisions[0]["decision"]["target_issue_id"] == "ISSUE-0001"


@pytest.mark.parametrize("task_id", ["TEST-001", "TEST-002", "TEST-003", "VS-002", "VS-003", "VS-005"])
def test_additional_handlers_conform_to_schema(task_id: str):
    tools = ReadOnlyTools(ROOT_DIR)
    task = {"id": task_id, "title": f"Test {task_id}"}
    handler = direct_audit_runner.TASK_HANDLERS[task_id]
    report = handler(tools, task)

    assert REQUIRED_REPORT_KEYS.issubset(set(report.keys()))
    assert report["task_id"] == task_id
    assert report["status"] == "completed"

