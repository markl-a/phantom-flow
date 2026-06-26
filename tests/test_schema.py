"""Tests for flow-schema validation + structured run records (P2-1)."""

from __future__ import annotations

import phantom_flow.runner as runner
from phantom_flow.runner import (
    FlowExecutionError,
    FlowValidationError,
    RunRecord,
    StepRecord,
    run_flow,
    validate_flow,
)


def _valid_flow():
    return {
        "name": "demo",
        "version": 1,
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "pipeline": [
            {"id": "count", "block": "pipeline.regex_count",
             "input": "AI ai", "pattern": "AI"},
        ],
        "outbound": [
            {"block": "actions.stdout", "line": "hi"},
        ],
    }


# ---------- validate_flow: happy path ----------

def test_validate_flow_accepts_valid():
    flow = _valid_flow()
    # returns the flow unchanged on success (chaining-friendly)
    assert validate_flow(flow) is flow


def test_validate_flow_requires_name():
    flow = _valid_flow()
    del flow["name"]
    try:
        validate_flow(flow)
    except FlowValidationError as exc:
        assert "name" in str(exc)
    else:
        raise AssertionError("missing name must raise FlowValidationError")


def test_validate_flow_rejects_non_mapping():
    try:
        validate_flow(["not", "a", "flow"])
    except FlowValidationError as exc:
        assert "mapping" in str(exc).lower()
    else:
        raise AssertionError("non-mapping flow must raise")


def test_validate_flow_rejects_bad_trigger_type():
    flow = _valid_flow()
    flow["trigger"]["type"] = "telepathy"
    try:
        validate_flow(flow)
    except FlowValidationError as exc:
        assert "trigger" in str(exc).lower()
    else:
        raise AssertionError("unknown trigger type must raise")


def test_validate_flow_requires_pipeline_list():
    flow = _valid_flow()
    flow["pipeline"] = "not-a-list"
    try:
        validate_flow(flow)
    except FlowValidationError as exc:
        assert "pipeline" in str(exc).lower()
    else:
        raise AssertionError("non-list pipeline must raise")


def test_validate_flow_requires_step_block():
    flow = _valid_flow()
    flow["pipeline"][0].pop("block")
    try:
        validate_flow(flow)
    except FlowValidationError as exc:
        assert "block" in str(exc).lower()
    else:
        raise AssertionError("pipeline step without block must raise")


def test_validate_flow_collects_multiple_errors():
    bad = {"trigger": {"type": "telepathy"}, "pipeline": [{"id": "x"}]}
    try:
        validate_flow(bad)
    except FlowValidationError as exc:
        # name missing + bad trigger + step-without-block -> >= 3 problems
        assert len(exc.errors) >= 3
    else:
        raise AssertionError("multiple problems must raise once")


# ---------- run_flow integration with validation ----------

def test_run_flow_validate_flag_rejects_bad_flow():
    bad = {"pipeline": "nope"}
    try:
        run_flow(bad, dry_run=True, validate=True)
    except FlowValidationError:
        pass
    else:
        raise AssertionError("run_flow(validate=True) must reject a bad flow")


# ---------- RunRecord ----------

def test_run_flow_returns_run_record(monkeypatch):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    summary = run_flow(_valid_flow(), dry_run=False)
    record = summary["record"]
    assert isinstance(record, RunRecord)
    assert record.name == "demo"
    assert record.version == 1
    assert record.trigger_type == "cron"
    assert record.status == "ok"
    assert record.dry_run is False
    # one pipeline step + one outbound action -> two StepRecords
    assert len(record.steps) == 2
    step = record.steps[0]
    assert isinstance(step, StepRecord)
    assert step.id == "count"
    assert step.block == "pipeline.regex_count"
    assert step.status == "ok"
    assert record.steps[1].id == "outbound:actions.stdout"
    assert record.steps[1].status == "ok"
    # timestamps present and ordered
    assert record.started_at and record.finished_at
    assert record.finished_at >= record.started_at


def test_run_record_dry_run_has_no_step_execution():
    summary = run_flow(_valid_flow(), dry_run=True)
    record = summary["record"]
    assert record.dry_run is True
    assert record.status == "ok"
    # dry-run plans but does not execute steps
    assert record.steps == []


def test_run_record_to_dict_is_json_serialisable():
    import json
    record = RunRecord(name="x", version=1, trigger_type="manual",
                       dry_run=True, status="ok",
                       started_at="t0", finished_at="t1", steps=[])
    d = record.to_dict()
    assert d["name"] == "x"
    assert d["status"] == "ok"
    # round-trips through json without error
    json.dumps(d)


# ---------- CLI wiring for --validate ----------

def test_cli_validate_rejects_bad_flow(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("trigger:\n  type: telepathy\npipeline:\n  - id: x\n",
                   encoding="utf-8")
    rc = runner._main([str(bad), "--validate", "--dry-run"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "invalid flow" in err
    assert "trigger" in err.lower()


def test_cli_json_includes_run_record(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    good = tmp_path / "good.yaml"
    good.write_text(
        "name: cli-demo\nversion: 1\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n  - id: count\n    block: pipeline.regex_count\n"
        "    input: 'AI ai'\n    pattern: AI\n",
        encoding="utf-8",
    )
    rc = runner._main([str(good), "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"record"' in out
    assert '"status": "ok"' in out


def test_run_record_captures_failed_step(monkeypatch):
    """A block raising mid-run is recorded as a failed StepRecord and the
    partial RunRecord is carried on the raised FlowExecutionError."""
    def _boom(spec, ctx):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(runner.BLOCK_REGISTRY, "pipeline.regex_count", _boom)
    try:
        run_flow(_valid_flow(), dry_run=False)
    except FlowExecutionError as exc:
        record = exc.record
        assert record.status == "error"
        assert len(record.steps) == 1
        failed = record.steps[0]
        assert failed.id == "count"
        assert failed.status == "error"
        assert "kaboom" in (failed.error or "")
        # the original exception is chained for debugging
        assert isinstance(exc.__cause__, RuntimeError)
    else:
        raise AssertionError("a raising block must surface as FlowExecutionError")
