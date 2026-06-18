> ARCHIVED 2026-06-19 — frozen historical snapshot; current status lives in [/ROADMAP.md](../../ROADMAP.md). All three gaps below are fixed and shipped.

# AUDIT — phantom-flow final form (second pass, branch sat/flow-final-form)

Audited current engine vs the final-form vision (bounded timeouts, honest
dry-run, force_stub for offline/test, clear per-step success/failure reporting,
features reachable + proven through the PRODUCTION runner path).

Baseline: 51 pytest passing on origin/main.

## Gaps (prioritised)

### GAP 1 — `force_stub` unit-tested but DEAD in the runner path
`PhantomLLM(force_stub=True)` is pinned by `tests/test_llm_driver.py::
test_force_stub_never_calls_cli`, but `runner._block_llm_summarize` always
constructs a bare `PhantomLLM()`. A flow has NO way to request the deterministic
offline stub per-step — only the global env var `PHANTOM_FLOW_STUB_LLM=1`.
Fix: read `force_stub` (+ `timeout`, `model_hint`) from the block spec and pass
them to the constructor.

### GAP 2 — `LLMResult.error` captured + tested in the driver but DROPPED by the runner
The driver records *why* it degraded to the stub (timeout / nonzero exit /
missing binary), pinned by 5 unit tests. But `_block_llm_summarize` returns only
`{summary, backend}` — `error` never reaches ctx / RunRecord, so per-step
reporting cannot reveal a silent LLM degrade. Fix: surface `error` in the block
output.

### GAP 3 — `tools.http_get` `max_bytes: null/0` → unbounded / empty read (UNSAFE)
The `timeout` null/0 hole was fixed (`spec.get("timeout") or 30`) but the
analogous `max_bytes` was not: `resp.read(spec.get("max_bytes", 50*1024))` — an
explicit `null` makes `resp.read(None)` read the ENTIRE response (unbounded
memory); `0` truncates to empty. Fix: coerce null/0 to the bounded default with
the same `or` pattern.

All three are reachable + proven through the production `run_flow` path.
