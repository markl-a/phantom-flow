"""Unit tests for phantom_flow.runner.

Hermetic + offline: no network (`tools.http_get` is never exercised), no real
LLM (the llm_summarize block runs through the stub driver via the dry-run gate
PHANTOM_FLOW_STUB_LLM=1), no filesystem writes outside tmp_path.
"""

from __future__ import annotations

import phantom_flow.runner as runner
from phantom_flow.runner import (
    BLOCK_REGISTRY,
    FlowExecutionError,
    _gate_passes,
    _lookup,
    _resolve,
    run_flow,
)


# ---- a fully offline flow used by several tests ----
def _offline_flow():
    return {
        "name": "offline-demo",
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "pipeline": [
            {"id": "count", "block": "pipeline.regex_count",
             "input": "AI ai AI ml", "pattern": "AI"},
            {"id": "pick", "block": "pipeline.filter",
             "input": "we want LLM and agent roles",
             "keywords": ["LLM", "nope", "agent"]},
            {"id": "gate", "block": "pipeline.if",
             "condition": "${count.value} > 0"},
            {"id": "sum", "block": "pipeline.llm_summarize",
             "input": "some text", "prompt": "Summarise:"},
        ],
        "outbound": [
            {"block": "actions.stdout", "when": "${gate.true}",
             "line": "hits=${count.value}"},
        ],
    }


# ---------- dry-run planning / ordering ----------

def test_dry_run_plan_ordering():
    summary = run_flow(_offline_flow(), dry_run=True)
    assert summary["dry_run"] is True
    assert summary["name"] == "offline-demo"
    # context is untouched in dry-run (no block executed)
    assert summary["context"] == {}
    assert summary["plan"] == [
        "trigger: cron (0 9 * * *)",
        "pipeline.count -> pipeline.regex_count",
        "pipeline.pick -> pipeline.filter",
        "pipeline.gate -> pipeline.if",
        "pipeline.sum -> pipeline.llm_summarize",
        "outbound -> actions.stdout  [gated by ${gate.true}]",
    ]


def test_dry_run_never_constructs_llm(monkeypatch):
    """The dry-run gate must keep the LLM driver entirely out of the path."""
    def _boom(*_a, **_k):  # pragma: no cover - must never run in dry-run
        raise AssertionError("PhantomLLM must not be built during dry-run")

    monkeypatch.setattr("phantom_flow.llm_driver.PhantomLLM", _boom)
    summary = run_flow(_offline_flow(), dry_run=True)
    assert any("llm_summarize" in line for line in summary["plan"])


# ---------- real (offline) execution through the stub driver ----------

def test_execute_offline_with_stub_llm(monkeypatch):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    summary = run_flow(_offline_flow(), dry_run=False)
    ctx = summary["context"]
    # steps executed in declared order
    assert list(ctx.keys()) == ["count", "pick", "gate", "sum"]
    assert ctx["count"]["value"] == 3
    assert ctx["pick"]["matched"] == ["LLM", "agent"]
    assert ctx["pick"]["passes"] is True
    assert ctx["gate"]["true"] is True
    # LLM went through the stub — proves no real provider was called
    assert ctx["sum"]["backend"] == "stub"
    assert ctx["sum"]["summary"].startswith("[stub-llm]")


def test_execute_unknown_block_raises():
    flow = {"pipeline": [{"id": "x", "block": "pipeline.does_not_exist"}]}
    try:
        run_flow(flow, dry_run=False)
    except FlowExecutionError as exc:
        assert "does_not_exist" in str(exc)
        assert exc.record.status == "error"
        assert exc.record.steps[0].status == "error"
    else:  # pragma: no cover
        raise AssertionError("expected FlowExecutionError for unknown block")


# ---------- strict dry-run validation (new) ----------

def test_strict_dry_run_flags_unknown_block():
    flow = {"pipeline": [{"id": "x", "block": "pipeline.typo_block"}]}
    try:
        run_flow(flow, dry_run=True, strict=True)
    except KeyError as exc:
        assert "typo_block" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("strict dry-run should reject unknown blocks")


def test_strict_dry_run_passes_for_known_blocks():
    # all blocks are registered -> strict dry-run must not raise
    summary = run_flow(_offline_flow(), dry_run=True, strict=True)
    assert summary["dry_run"] is True
    assert summary["context"] == {}


# ---------- helpers ----------

def test_resolve_nested_and_missing():
    ctx = {"a": {"b": "deep"}, "n": {"value": 7}}
    assert _resolve("x=${a.b}", ctx) == "x=deep"
    assert _resolve("v=${n.value}", ctx) == "v=7"
    # missing keys resolve to empty string, never raise
    assert _resolve("m=${nope.gone}", ctx) == "m="
    # nested structures are resolved recursively
    assert _resolve({"k": ["${a.b}", 1]}, ctx) == {"k": ["deep", 1]}


def test_lookup_env(monkeypatch):
    monkeypatch.setenv("PHANTOM_TEST_VAR", "hello")
    assert _lookup("env.PHANTOM_TEST_VAR", {}) == "hello"
    assert _lookup("env.UNSET_VAR_XYZ", {}) == ""


def test_gate_passes_truthy_values():
    assert _gate_passes(None, {}) is True          # no gate -> always pass
    assert _gate_passes("", {}) is True
    assert _gate_passes("${g.true}", {"g": {"true": "true"}}) is True
    assert _gate_passes("${g.true}", {"g": {"true": "false"}}) is False
    assert _gate_passes("yes", {}) is True
    assert _gate_passes("no", {}) is False


# ---------- subprocess block hardening (P1-3) ----------

def test_subprocess_block_missing_binary_does_not_crash(monkeypatch):
    """A missing binary must yield a structured error dict, not raise."""
    def _missing(cmd, **kw):
        raise FileNotFoundError(2, "No such file or directory", cmd[0])

    monkeypatch.setattr(runner.subprocess, "run", _missing)
    out = runner._block_subprocess(
        {"cmd": ["definitely_not_a_real_binary_xyz", "--help"]}, {})
    assert out["returncode"] != 0
    assert out["timed_out"] is False
    assert "not found" in out["stderr"].lower()
    assert out["stdout"] == ""


def test_subprocess_block_timeout_is_bounded(monkeypatch):
    """A timeout must be caught and reported, never propagated."""
    seen = {}

    def _timeout(cmd, **kw):
        seen.update(kw)
        raise runner.subprocess.TimeoutExpired(cmd, kw.get("timeout", 1))

    monkeypatch.setattr(runner.subprocess, "run", _timeout)
    out = runner._block_subprocess({"cmd": ["sleep", "999"], "timeout": 2}, {})
    assert out["timed_out"] is True
    assert out["returncode"] != 0
    assert seen.get("timeout") == 2
    assert "timed out" in out["stderr"].lower()


def test_subprocess_block_captures_stdout_stderr_returncode(monkeypatch):
    """Happy path returns captured streams and exit code."""
    class _P:
        stdout = "hello-out"
        stderr = "warn-err"
        returncode = 0

    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: _P())
    out = runner._block_subprocess({"cmd": ["echo", "hi"]}, {})
    assert out == {"stdout": "hello-out", "stderr": "warn-err",
                   "returncode": 0, "timed_out": False}


def test_subprocess_block_default_timeout_applied(monkeypatch):
    """When no timeout is given, a finite default is still passed down."""
    seen = {}

    class _P:
        stdout = ""
        stderr = ""
        returncode = 0

    def _run(cmd, **kw):
        seen.update(kw)
        return _P()

    monkeypatch.setattr(runner.subprocess, "run", _run)
    runner._block_subprocess({"cmd": ["echo", "x"]}, {})
    assert isinstance(seen.get("timeout"), (int, float))
    assert seen["timeout"] > 0


def test_registry_has_expected_native_blocks():
    # the engine's native block contract (DESIGN.md §2 + youtube addition)
    for name in (
        "tools.http_get", "tools.youtube_transcript",
        "pipeline.regex_count", "pipeline.filter", "pipeline.llm_summarize",
        "pipeline.if", "pipeline.subprocess",
        "actions.log_append", "actions.stdout",
    ):
        assert name in BLOCK_REGISTRY
