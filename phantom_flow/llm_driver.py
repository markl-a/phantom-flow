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

import json
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


class PhantomLLM:
    """Minimal wrapper around `phantom event capture`.

    The phantom-mesh CLI exposes provider-routed LLM calls through its event
    system. We invoke it as a subprocess so this driver has zero Python
    dependency on the phantom Rust crate.
    """

    def __init__(self, model_hint: str = "auto", timeout: float = 60.0) -> None:
        self.model_hint = model_hint
        self.timeout = timeout
        self._cli = shutil.which("phantom")

    @property
    def available(self) -> bool:
        return self._cli is not None and os.environ.get("PHANTOM_FLOW_STUB_LLM") != "1"

    def complete(self, prompt: str, *, system: Optional[str] = None) -> LLMResult:
        if not self.available:
            return self._stub(prompt, system)

        # Invoke: `phantom event capture --kind llm.complete --json -`
        # The exact subcommand surface is stabilising; we use a defensive
        # form that the phantom CLI is expected to accept (kind + JSON
        # payload on stdin, JSON line on stdout).
        payload = {
            "model_hint": self.model_hint,
            "system": system or "",
            "prompt": prompt,
        }
        try:
            proc = subprocess.run(
                [self._cli, "event", "capture",
                 "--kind", "llm.complete", "--json", "-"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return self._stub(prompt, system)

        if proc.returncode != 0 or not proc.stdout.strip():
            return self._stub(prompt, system)

        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
            text = out.get("text") or out.get("completion") or ""
            return LLMResult(text=text, backend="phantom", raw=proc.stdout)
        except (json.JSONDecodeError, IndexError):
            return LLMResult(text=proc.stdout.strip(), backend="phantom",
                             raw=proc.stdout)

    def _stub(self, prompt: str, system: Optional[str]) -> LLMResult:
        head = (prompt or "").splitlines()[0] if prompt else ""
        return LLMResult(
            text=f"[stub-llm] {head[:120]}",
            backend="stub",
        )


__all__ = ["PhantomLLM", "LLMResult"]
