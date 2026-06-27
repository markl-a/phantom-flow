"""phantom-mesh LLM driver.

Spec calls for swapping the LangChain LLM client (currently used inside
`ai_automation_framework/llm/`) for the phantom-mesh provider trait, accessed
via the `phantom event capture` CLI.

This module is the first step of that swap: a minimal driver that any
pipeline block in `phantom_flow.runner` can call without pulling in
LangChain. The merged framework's own call sites still use LangChain — that
deeper swap is tracked in `docs/2026-05-22-tier1-initial-dev.md`.

Usage::

    from phantom_flow.llm_driver import PhantomLLM
    llm = PhantomLLM()
    text = llm.complete("Summarise: ...")

If the `phantom` CLI is unavailable (e.g. on a CI runner without the mesh
installed), the driver falls back to an echo-style stub so dry-runs and
unit tests still pass.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResult:
    text: str
    backend: str  # "phantom" | "stub"
    raw: Optional[str] = None
    error: Optional[str] = None  # populated when a phantom call failed/fell back


class PhantomLLM:
    """Minimal wrapper around `phantom event capture`.

    The phantom-mesh CLI exposes provider-routed LLM calls through its event
    system. We invoke it as a subprocess so this driver has zero Python
    dependency on the phantom Rust crate.
    """

    def __init__(self, model_hint: str = "auto", timeout: float = 60.0,
                 force_stub: bool = False) -> None:
        self.model_hint = model_hint
        self.timeout = timeout
        self.force_stub = force_stub
        self._cli = shutil.which("phantom")

    @property
    def available(self) -> bool:
        if self.force_stub:
            return False
        return self._cli is not None and os.environ.get("PHANTOM_FLOW_STUB_LLM") != "1"

    def complete(self, prompt: str, *, system: Optional[str] = None) -> LLMResult:
        if not self.available:
            return self._stub(prompt, system)

        # Invoke the real provider-routed completion via `phantom exec`.
        # This mirrors the working pattern in the ai-feed repo
        # (summarize.py): shell `phantom exec <prompt>` and return stdout.
        # The previous `phantom event capture --kind llm.complete` form used
        # an unknown flag and silently fell back to a fake stub summary.
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        # Optional, env-driven provider override. When PHANTOM_PROVIDER is set
        # and non-empty, route the call to that provider via `--provider <val>`
        # inserted right after "exec". Unset/empty leaves the argv unchanged so
        # default behavior is preserved.
        argv = [self._cli, "exec"]
        provider = (os.environ.get("PHANTOM_PROVIDER") or "").strip()
        if provider:
            argv += ["--provider", provider]
        argv.append(full_prompt)
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,  # bounded: never blocks the flow forever
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._stub(
                prompt, system,
                error=f"phantom exec timed out after {self.timeout}s",
            )
        except FileNotFoundError as exc:
            # Binary vanished between which() and exec (e.g. uninstalled mid-run).
            return self._stub(prompt, system,
                              error=f"phantom binary not found: {exc}")
        except OSError as exc:  # exec format error, permission, etc.
            return self._stub(prompt, system,
                              error=f"phantom exec OSError: {exc}")

        text = self._clean_stdout(proc.stdout)
        if proc.returncode != 0 or not text:
            # Capture stderr so the caller can see *why* we fell back rather
            # than getting a silent stub.
            stderr = (proc.stderr or "").strip()
            reason = (
                f"phantom exec rc={proc.returncode}"
                + (f": {stderr}" if stderr else "")
                if proc.returncode != 0
                else "phantom exec produced empty output"
            )
            return self._stub(prompt, system, error=reason)

        return LLMResult(text=text, backend="phantom", raw=proc.stdout)

    @staticmethod
    def _clean_stdout(stdout: str) -> str:
        """Drop provider-failover noise lines that `phantom exec` prints.

        e.g. ``  [provider gemini] unavailable, trying next — rate limit``.
        The real completion is whatever remains.
        """
        if not stdout:
            return ""
        kept = []
        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("[provider ") or (
                "] unavailable, trying next" in stripped
            ):
                continue
            kept.append(line)
        return "\n".join(kept).strip()

    def _stub(self, prompt: str, system: Optional[str],
              error: Optional[str] = None) -> LLMResult:
        head = (prompt or "").splitlines()[0] if prompt else ""
        return LLMResult(
            text=f"[stub-llm] {head[:120]}",
            backend="stub",
            error=error,
        )


__all__ = ["PhantomLLM", "LLMResult"]
