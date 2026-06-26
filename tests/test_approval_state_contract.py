from __future__ import annotations

import json

import phantom_flow.runner as runner
from phantom_flow.runner import ApprovalRequiredError, run_flow


def _approval_flow():
    return {
        "name": "approval-demo",
        "version": 1,
        "trigger": {"type": "manual"},
        "pipeline": [
            {
                "id": "count",
                "block": "pipeline.regex_count",
                "input": "AI ai",
                "pattern": "AI",
            },
            {
                "id": "risky",
                "block": "pipeline.subprocess",
                "requires_approval": True,
                "risk_reason": "would execute a local command",
                "cmd": ["python", "-c", "print('must-not-run')"],
            },
        ],
    }


def test_requires_approval_blocks_step_before_execution(monkeypatch):
    def _must_not_run(_spec, _ctx):  # pragma: no cover - must never run
        raise AssertionError("approval-gated step executed without approval")

    monkeypatch.setitem(runner.BLOCK_REGISTRY, "pipeline.subprocess", _must_not_run)

    try:
        run_flow(_approval_flow(), dry_run=False)
    except ApprovalRequiredError as exc:
        record = exc.record
        assert record.status == "blocked"
        assert [step.status for step in record.steps] == ["ok", "blocked"]
        assert record.steps[-1].id == "risky"
        assert "approval required" in (record.steps[-1].error or "").lower()
        assert "pipeline.risky -> pipeline.subprocess [requires approval]" in exc.plan
    else:  # pragma: no cover
        raise AssertionError("approval-gated step must block without approval")


def test_approval_allows_step_execution(monkeypatch):
    def _approved(_spec, _ctx):
        return {"returncode": 0, "stdout": "approved", "stderr": "", "timed_out": False}

    monkeypatch.setitem(runner.BLOCK_REGISTRY, "pipeline.subprocess", _approved)

    summary = run_flow(_approval_flow(), approvals={"risky"})

    assert summary["record"].status == "ok"
    assert [step.status for step in summary["record"].steps] == ["ok", "ok"]
    assert summary["context"]["risky"]["stdout"] == "approved"


def test_dry_run_marks_approval_gate_without_executing():
    summary = run_flow(_approval_flow(), dry_run=True, strict=True)

    assert summary["record"].status == "ok"
    assert summary["record"].steps == []
    assert "pipeline.risky -> pipeline.subprocess [requires approval]" in summary["plan"]


def test_cli_state_dir_writes_state_and_event_artifacts(tmp_path, monkeypatch):
    monkeypatch.setitem(
        runner.BLOCK_REGISTRY,
        "pipeline.subprocess",
        lambda _spec, _ctx: {"returncode": 0, "stdout": "ok", "stderr": "", "timed_out": False},
    )
    flow = tmp_path / "approval.yaml"
    state_dir = tmp_path / "state"
    flow.write_text(
        "name: approval-cli\n"
        "version: 1\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: count\n"
        "    block: pipeline.regex_count\n"
        "    input: 'AI ai'\n"
        "    pattern: AI\n"
        "  - id: risky\n"
        "    block: pipeline.subprocess\n"
        "    requires_approval: true\n"
        "    risk_reason: would execute a local command\n"
        "    cmd: ['python', '-c', 'print(1)']\n",
        encoding="utf-8",
    )

    rc = runner._main(
        [
            str(flow),
            "--validate",
            "--approve",
            "risky",
            "--run-id",
            "demo-run-001",
            "--state-dir",
            str(state_dir),
        ]
    )

    assert rc == 0
    run_dir = state_dir / "runs" / "demo-run-001"
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    index = [
        json.loads(line)
        for line in (state_dir / "runs.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert state["schema_version"] == 1
    assert state["run_id"] == "demo-run-001"
    assert state["record"]["status"] == "ok"
    assert state["approvals"] == ["risky"]
    assert "context" not in state
    assert [event["status"] for event in events] == ["ok", "ok"]
    assert index[-1]["run_id"] == "demo-run-001"
    assert index[-1]["status"] == "ok"


def test_cli_unapproved_step_exits_3_and_writes_blocked_state(tmp_path, monkeypatch):
    monkeypatch.setitem(
        runner.BLOCK_REGISTRY,
        "pipeline.subprocess",
        lambda _spec, _ctx: {"returncode": 0, "stdout": "bad", "stderr": "", "timed_out": False},
    )
    flow = tmp_path / "blocked.yaml"
    state_dir = tmp_path / "state"
    flow.write_text(
        "name: blocked-cli\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: risky\n"
        "    block: pipeline.subprocess\n"
        "    requires_approval: true\n"
        "    cmd: ['python', '-c', 'print(1)']\n",
        encoding="utf-8",
    )

    rc = runner._main(
        [
            str(flow),
            "--validate",
            "--run-id",
            "blocked-run-001",
            "--state-dir",
            str(state_dir),
        ]
    )

    assert rc == 3
    state = json.loads(
        (state_dir / "runs" / "blocked-run-001" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    assert state["record"]["status"] == "blocked"
    assert state["record"]["steps"][0]["status"] == "blocked"
    assert "approval required" in state["error"].lower()
    assert "context" not in state


def test_outbound_requires_approval_blocks_before_execution(monkeypatch):
    def _must_not_run(_spec, _ctx):  # pragma: no cover - must never run
        raise AssertionError("approval-gated outbound action executed")

    monkeypatch.setitem(runner.BLOCK_REGISTRY, "actions.log_append", _must_not_run)
    flow = {
        "name": "outbound-approval",
        "trigger": {"type": "manual"},
        "pipeline": [
            {"id": "gate", "block": "pipeline.if", "condition": "1 == 1"},
        ],
        "outbound": [
            {
                "id": "write_log",
                "block": "actions.log_append",
                "when": "${gate.true}",
                "requires_approval": True,
                "path": "unused.log",
                "line": "must-not-run",
            }
        ],
    }

    try:
        run_flow(flow)
    except ApprovalRequiredError as exc:
        assert exc.record.status == "blocked"
        assert exc.record.steps[-1].id == "write_log"
        assert exc.record.steps[-1].status == "blocked"
    else:  # pragma: no cover
        raise AssertionError("approval-gated outbound action must block")


def test_outbound_success_is_recorded_with_action_id(monkeypatch):
    monkeypatch.setitem(runner.BLOCK_REGISTRY, "actions.stdout", lambda _spec, _ctx: {})
    flow = {
        "name": "outbound-record",
        "trigger": {"type": "manual"},
        "pipeline": [
            {"id": "gate", "block": "pipeline.if", "condition": "1 == 1"},
        ],
        "outbound": [
            {
                "id": "notify",
                "block": "actions.stdout",
                "when": "${gate.true}",
                "line": "ok",
            }
        ],
    }

    summary = run_flow(flow)

    assert [(step.id, step.status) for step in summary["record"].steps] == [
        ("gate", "ok"),
        ("notify", "ok"),
    ]


def test_error_redaction_covers_authorization_bearer_header():
    redacted = runner._redact_error_text(
        "request failed Authorization: Bearer raw-secret-token and token=abc"
    )

    assert "raw-secret-token" not in redacted
    assert "token=abc" not in redacted
    assert "<redacted>" in redacted
