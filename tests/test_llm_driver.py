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


# ---------- subprocess boundary hardening (P1-3) ----------

def _fake_proc(stdout="", stderr="", returncode=0):
    class _P:
        pass
    p = _P()
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


def test_complete_passes_bounded_timeout(monkeypatch):
    """The subprocess call must always carry a finite, bounded timeout."""
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)
    seen = {}

    def _capture(cmd, **kw):
        seen.update(kw)
        return _fake_proc(stdout="ok answer", returncode=0)

    monkeypatch.setattr(drv.subprocess, "run", _capture)
    llm = PhantomLLM(timeout=7.0)
    res = llm.complete("hi")
    assert res.backend == "phantom"
    assert res.text == "ok answer"
    # bounded timeout was forwarded to subprocess.run
    assert seen.get("timeout") == 7.0
    assert isinstance(seen.get("timeout"), (int, float))


def test_complete_timeout_falls_back_to_stub_and_records_stderr(monkeypatch):
    """A TimeoutExpired must degrade to the stub AND surface a reason."""
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)

    def _timeout(cmd, **kw):
        raise drv.subprocess.TimeoutExpired(cmd, kw.get("timeout", 1))

    monkeypatch.setattr(drv.subprocess, "run", _timeout)
    res = PhantomLLM(timeout=1.0).complete("hello")
    assert res.backend == "stub"
    assert res.text.startswith("[stub-llm]")
    # the failure reason is captured (not silently swallowed)
    assert res.error and "timed out" in res.error.lower()


def test_complete_missing_binary_falls_back_to_stub(monkeypatch):
    """FileNotFoundError at exec time (binary vanished) must stub, not crash."""
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)

    def _missing(cmd, **kw):
        raise FileNotFoundError(2, "No such file or directory", cmd[0])

    monkeypatch.setattr(drv.subprocess, "run", _missing)
    res = PhantomLLM().complete("hello")
    assert res.backend == "stub"
    assert res.error and "not found" in res.error.lower()


def test_complete_nonzero_exit_captures_stderr(monkeypatch):
    """A non-zero exit must stub AND capture the subprocess stderr text."""
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)

    def _fail(cmd, **kw):
        return _fake_proc(stdout="", stderr="boom: provider auth failed",
                          returncode=3)

    monkeypatch.setattr(drv.subprocess, "run", _fail)
    res = PhantomLLM().complete("hello")
    assert res.backend == "stub"
    assert res.error and "boom: provider auth failed" in res.error


def test_complete_oserror_falls_back_to_stub(monkeypatch):
    """A generic OSError (e.g. exec format error) must stub, not propagate."""
    monkeypatch.setattr(drv.shutil, "which", lambda _name: "/usr/bin/phantom")
    monkeypatch.delenv("PHANTOM_FLOW_STUB_LLM", raising=False)

    def _oserror(cmd, **kw):
        raise OSError("Exec format error")

    monkeypatch.setattr(drv.subprocess, "run", _oserror)
    res = PhantomLLM().complete("hello")
    assert res.backend == "stub"
    assert res.error and "exec format error" in res.error.lower()
