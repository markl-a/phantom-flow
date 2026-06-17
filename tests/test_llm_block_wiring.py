"""E2E wiring tests: the llm_summarize block must expose the LLM driver's
offline/test + diagnostics features through the PRODUCTION runner path.

These guard two features that are unit-tested on ``PhantomLLM`` but were DEAD
in the runner path:

  GAP 1: ``force_stub`` — a flow must be able to request the deterministic
         stub per-step (not only via the global PHANTOM_FLOW_STUB_LLM env var).
  GAP 2: ``LLMResult.error`` — when the driver degrades to the stub, the
         *reason* must surface in the block output (ctx / run record), not be
         silently dropped.

All tests are hermetic: no network, no real `phantom` CLI is ever spawned.
"""

from __future__ import annotations

import phantom_flow.llm_driver as drv
import phantom_flow.runner as runner
from phantom_flow.runner import run_flow


def _llm_flow(extra_step_keys=None):
    step = {"id": "sum", "block": "pipeline.llm_summarize",
            "input": "some text to summarise", "prompt": "Summarise:"}
    if extra_step_keys:
        step.update(extra_step_keys)
    return {
        "name": "llm-wiring",
        "trigger": {"type": "manual"},
        "pipeline": [step],
    }


# ---------- GAP 1: force_stub reachable from a flow spec ----------

def test_force_stub_spec_key_short_circuits_cli(monkeypatch):
    """A flow setting ``force_stub: true`` must NEVER spawn the phantom CLI,
    even when a `phantom` binary looks present and the env var is unset."""
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)
    # A CLI looks installed...
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")

    def _boom(*_a, **_k):  # pragma: no cover - must never run when stubbed
        raise AssertionError("subprocess.run must not be called when force_stub")

    monkeypatch.setattr(drv.subprocess, "run", _boom)

    summary = run_flow(_llm_flow({"force_stub": True}), dry_run=False)
    ctx = summary["context"]
    assert ctx["sum"]["backend"] == "stub"
    assert ctx["sum"]["summary"].startswith("[stub-llm]")
    assert summary["record"].status == "ok"


# ---------- GAP 2: degrade reason surfaces through the runner ----------

def test_llm_block_surfaces_degrade_error(monkeypatch):
    """When the driver falls back to the stub, the block output must carry the
    reason (LLMResult.error), not silently drop it."""
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")

    def _fail(cmd, **kw):
        class _P:
            stdout = ""
            stderr = "boom: provider auth failed"
            returncode = 3
        return _P()

    monkeypatch.setattr(drv.subprocess, "run", _fail)

    summary = run_flow(_llm_flow(), dry_run=False)
    out = summary["context"]["sum"]
    assert out["backend"] == "stub"
    assert "error" in out
    assert out["error"] and "boom: provider auth failed" in out["error"]


def test_llm_block_error_empty_on_clean_stub(monkeypatch):
    """A clean stub (no CLI, no failure) must report no error string."""
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    summary = run_flow(_llm_flow(), dry_run=False)
    out = summary["context"]["sum"]
    assert out["backend"] == "stub"
    # key present, but no failure reason for a deliberate/clean stub
    assert out.get("error") in (None, "")
