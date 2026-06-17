"""Regression: a flow that sets `timeout: null` (or 0) must NOT make a block's
subprocess/urlopen unbounded — the hardened boundary promises a finite timeout.
(codex review finding on sat/flow-final: `spec.get("timeout", D)` only applied
the default when the key was ABSENT, so an explicit null/0 leaked None through.)
"""
import subprocess

from phantom_flow import runner


def test_subprocess_timeout_null_or_zero_coerces_to_bounded_default(monkeypatch):
    seen = []

    def fake_run(cmd, **kw):
        seen.append(kw.get("timeout"))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    # explicit null, explicit 0, and absent — all must end up finite (> 0), never None
    runner._block_subprocess({"cmd": "echo hi", "timeout": None}, {})
    runner._block_subprocess({"cmd": "echo hi", "timeout": 0}, {})
    runner._block_subprocess({"cmd": "echo hi"}, {})

    assert seen and all(t is not None and t > 0 for t in seen), seen
