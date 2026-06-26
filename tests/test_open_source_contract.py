from __future__ import annotations

from pathlib import Path

from phantom_flow.runner import BLOCK_REGISTRY


ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_readme_contains_self_contained_public_quickstart():
    text = _read("README.md")

    assert "Quickstart" in text
    assert "PHANTOM_FLOW_SAMPLE" in text
    assert "PHANTOM_FLOW_STUB_LLM" in text
    assert "--validate --dry-run --strict --json" in text
    assert "--record-out" in text
    assert "flows\\examples\\local-text-summary.yaml" in text
    assert "docs/BLOCK_CONTRACT.md" in text
    assert "docs/RUN_ARTIFACT_CONTRACT.md" in text
    assert "docs/STATE_AND_APPROVAL_CONTRACT.md" in text
    assert "--state-dir" in text
    assert "--approve" in text
    assert "requires_approval: true" in text
    assert "phantom_flow.runner scenario" in text
    assert "local-automation-scenario.yaml" in text
    assert "docs/LOCAL_AUTOMATION_SCENARIO.md" in text


def test_block_contract_documents_every_shipped_block():
    text = _read("docs/BLOCK_CONTRACT.md")

    for block_name in sorted(BLOCK_REGISTRY):
        assert f"`{block_name}`" in text
    assert "Side effects" in text
    assert "Failure behavior" in text
    assert "`--dry-run`" in text


def test_run_artifact_contract_documents_stable_public_schema():
    text = _read("docs/RUN_ARTIFACT_CONTRACT.md")

    assert "--record-out" in text
    assert "schema_version" in text
    assert "record.status" in text
    assert '"run_id"' in text
    assert "steps" in text
    assert "context" in text
    assert "omits" in text
    assert "exits 1" in text


def test_state_and_approval_contract_documents_public_schema():
    text = _read("docs/STATE_AND_APPROVAL_CONTRACT.md")

    assert "requires_approval: true" in text
    assert "--approve risky" in text
    assert "--state-dir" in text
    assert "runs/<run-id>/state.json" in text
    assert "events.jsonl" in text
    assert "runs.jsonl" in text
    assert '"schema_version": 1' in text
    assert '"generated_at"' in text
    assert '"run_id"' in text
    assert '"trigger_type"' in text
    assert '"started_at"' in text
    assert '"finished_at"' in text
    assert "context" in text
    assert "omit" in text
    assert "Exit code `3`" in text


def test_local_automation_scenario_documents_p3_bundle():
    text = _read("docs/LOCAL_AUTOMATION_SCENARIO.md")

    assert "phantom_flow.runner scenario" in text
    assert "plan.json" in text
    assert "blocked.json" in text
    assert "approved.json" in text
    assert "scenario-summary.json" in text
    assert "scenario.log" in text
    assert "stdout.log" in text
    assert "requires_approval" in text
    assert "schema_version: 1" in text
    assert "context" in text
    assert "omit" in text
