from __future__ import annotations

import json
from pathlib import Path

import phantom_flow.runner as runner


ROOT = Path(__file__).resolve().parent.parent


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_scenario_command_writes_plan_blocked_and_approved_bundle(tmp_path):
    flow = ROOT / "flows" / "examples" / "local-automation-scenario.yaml"
    sample = ROOT / "flows" / "samples" / "ai-jobs-sample.txt"
    out_dir = tmp_path / "scenario"

    rc = runner._main(
        [
            "scenario",
            str(flow),
            "--sample",
            str(sample),
            "--out-dir",
            str(out_dir),
            "--run-id-prefix",
            "p3-demo",
        ]
    )

    assert rc == 0
    summary = _read_json(out_dir / "scenario-summary.json")
    plan = _read_json(out_dir / "plan.json")
    blocked = _read_json(out_dir / "blocked.json")
    approved = _read_json(out_dir / "approved.json")

    assert summary["status"] == "ok"
    assert summary["flow"]["name"] == "local-automation-scenario"
    assert summary["approvals"] == ["write_report"]
    assert summary["artifacts"]["stdout_log"] == "stdout.log"
    assert summary["phase_results"] == {
        "plan": {"exit_code": 0, "record_status": "ok"},
        "blocked": {"exit_code": 3, "record_status": "blocked"},
        "approved": {"exit_code": 0, "record_status": "ok"},
    }

    assert plan["dry_run"] is True
    assert plan["record"]["steps"] == []
    assert "context" not in plan
    assert "pipeline.fetch -> tools.http_get" in plan["plan"]
    assert "outbound -> actions.log_append  [gated by ${gate.true}] [requires approval]" in plan["plan"]

    assert blocked["record"]["status"] == "blocked"
    assert blocked["record"]["steps"][-1]["id"] == "write_report"
    assert blocked["record"]["steps"][-1]["status"] == "blocked"
    assert blocked["error"]
    assert "context" not in blocked

    assert approved["record"]["status"] == "ok"
    assert approved["record"]["steps"][-2]["id"] == "write_report"
    assert approved["record"]["steps"][-2]["status"] == "ok"
    assert approved["record"]["steps"][-1]["id"] == "print_summary"
    assert "context" not in approved

    scenario_log = out_dir / "scenario.log"
    assert scenario_log.exists()
    assert "[local-automation-scenario] AI hits=" in scenario_log.read_text(
        encoding="utf-8"
    )
    assert "summary: [stub-llm]" in (out_dir / "stdout.log").read_text(
        encoding="utf-8"
    )

    blocked_state = _read_json(out_dir / "state" / "runs" / "p3-demo-blocked" / "state.json")
    approved_state = _read_json(out_dir / "state" / "runs" / "p3-demo-approved" / "state.json")
    assert blocked_state["record"]["status"] == "blocked"
    assert approved_state["record"]["status"] == "ok"
    assert "context" not in blocked_state
    assert "context" not in approved_state


def test_scenario_command_requires_an_approval_gate(tmp_path):
    flow = tmp_path / "no-gate.yaml"
    flow.write_text(
        "name: no-gate\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: count\n"
        "    block: pipeline.regex_count\n"
        "    input: AI\n"
        "    pattern: AI\n",
        encoding="utf-8",
    )
    sample = ROOT / "flows" / "samples" / "ai-jobs-sample.txt"

    rc = runner._main(
        [
            "scenario",
            str(flow),
            "--sample",
            str(sample),
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )

    assert rc == 2
