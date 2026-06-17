"""Unit tests for phantom_flow.llm_driver.

All tests are hermetic: they never invoke a real `phantom` CLI or any network
LLM. The driver is exercised only through its stub path (the dry-run gate).
"""

from __future__ import annotations

import phantom_flow.llm_driver as drv
from phantom_flow.llm_driver import LLMResult, PhantomLLM


def test_force_stub_never_calls_cli(monkeypatch):
    """force_stub=True must short-circuit to the stub regardless of CLI."""
    # Even if a `phantom` CLI looks present, force_stub wins and no subprocess
    # is ever spawned.
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")

    def _boom(*_a, **_k):  # pragma: no cover - must never run
        raise AssertionError("subprocess.run must not be called when stubbed")

    monkeypatch.setattr(drv.subprocess, "run", _boom)

    llm = PhantomLLM(force_stub=True)
    assert llm.available is False
    res = llm.complete("Summarise: hello world")
    assert isinstance(res, LLMResult)
    assert res.backend == "stub"
    assert res.text.startswith("[stub-llm]")
    assert "hello world" in res.text or "Summarise" in res.text


def test_env_var_forces_stub(monkeypatch):
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    llm = PhantomLLM()
    assert llm.available is False
    assert llm.complete("x").backend == "stub"


def test_unavailable_when_no_cli(monkeypatch):
    monkeypatch.setattr(drv.shutil, "which", lambda _name: None)
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)
    llm = PhantomLLM()
    assert llm.available is False
    assert llm.complete("anything").backend == "stub"


def test_clean_stdout_drops_provider_noise():
    raw = (
        "  [provider gemini] unavailable, trying next — rate limit\n"
        "[provider openai] unavailable, trying next\n"
        "Real answer line one\n"
        "Real answer line two\n"
    )
    cleaned = PhantomLLM._clean_stdout(raw)
    assert cleaned == "Real answer line one\nReal answer line two"


def test_clean_stdout_empty():
    assert PhantomLLM._clean_stdout("") == ""
