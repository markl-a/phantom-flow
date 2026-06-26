"""End-to-end tests for the bundled stdlib-only example flows (P2-2).

These run the FULL pipeline offline: tools.http_get over a ``file://`` URL
(stdlib urllib, no network), regex_count, filter, if-gate, llm_summarize
through the stub driver, and stdout. No network, no real LLM, no writes
outside what the flow itself prints.
"""

from __future__ import annotations

from pathlib import Path

import phantom_flow.runner as runner
from phantom_flow.runner import (
    BLOCK_REGISTRY,
    load_flow,
    run_flow,
    validate_flow,
)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "flows" / "examples"


def _file_url(path: Path) -> str:
    return "file:///" + str(path.resolve()).replace("\\", "/").lstrip("/")


# ---------- http_get over file:// (stdlib, offline) ----------

def test_http_get_supports_file_url(tmp_path):
    sample = tmp_path / "page.txt"
    sample.write_text("we hire AI and LLM and agent engineers", encoding="utf-8")
    out = runner._block_http_get({"url": _file_url(sample)}, {})
    assert out["status"] == 200          # file:// normalised to 200
    assert "LLM" in out["body"]
    assert out["body_len"] > 0


# ---------- the example flows exist + are valid + lint clean ----------

def test_example_flows_exist():
    assert (EXAMPLES / "local-text-summary.yaml").exists()
    assert (EXAMPLES / "keyword-report.yaml").exists()
    assert (EXAMPLES / "local-automation-scenario.yaml").exists()


def test_example_flows_validate_and_strict_lint():
    for name in (
        "local-text-summary.yaml",
        "keyword-report.yaml",
        "local-automation-scenario.yaml",
    ):
        flow = load_flow(EXAMPLES / name)
        validate_flow(flow)  # must not raise
        summary = run_flow(flow, dry_run=True, strict=True)  # lint, no exec
        assert summary["record"].status == "ok"
        # every referenced block is registered
        for line in summary["plan"]:
            if "->" in line:
                block = line.split("->", 1)[1].strip().split()[0]
                assert block in BLOCK_REGISTRY


# ---------- full offline execution: http(file) -> regex -> summarize(stub) ----------

def test_local_text_summary_runs_end_to_end_offline(monkeypatch):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    sample = ROOT / "flows" / "samples" / "ai-jobs-sample.txt"
    monkeypatch.setenv("PHANTOM_FLOW_SAMPLE", _file_url(sample))

    flow = load_flow(EXAMPLES / "local-text-summary.yaml")
    summary = run_flow(flow, dry_run=False, validate=True)
    ctx = summary["context"]

    # fetched the local sample over file:// (no network)
    assert ctx["fetch"]["status"] == 200
    assert ctx["fetch"]["body_len"] > 0
    # regex counted at least one AI hit
    assert ctx["count"]["value"] >= 1
    # the gate opened
    assert ctx["gate"]["true"] is True
    # summarised through the STUB (proves no real provider hit)
    assert ctx["summary"]["backend"] == "stub"
    assert ctx["summary"]["summary"].startswith("[stub-llm]")
    # run record is healthy
    assert summary["record"].status == "ok"
    assert [s.id for s in summary["record"].steps] == [
        "fetch", "count", "filter", "gate", "summary",
        "outbound:actions.stdout", "outbound:actions.stdout",
    ]


def test_keyword_report_runs_end_to_end_offline(monkeypatch):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    sample = ROOT / "flows" / "samples" / "ai-jobs-sample.txt"
    monkeypatch.setenv("PHANTOM_FLOW_SAMPLE", _file_url(sample))

    flow = load_flow(EXAMPLES / "keyword-report.yaml")
    summary = run_flow(flow, dry_run=False, validate=True)
    ctx = summary["context"]
    assert ctx["fetch"]["status"] == 200
    assert ctx["matched"]["matched_count"] >= 1
    assert ctx["report"]["backend"] == "stub"
    assert summary["record"].status == "ok"
