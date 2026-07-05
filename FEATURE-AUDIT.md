# phantom-flow — Feature Audit

Honest status of what is shipped and tested versus what is roadmap. Grounded in
the actual engine package `phantom_flow/` (`runner.py`, `mcp_server.py`,
`activity.py`, `llm_driver.py`), its 21 test modules under `tests/`, and the
bundled `flows/` fixtures. Update this file when status changes.

The shipped product is a **local-first YAML workflow runner**. PyYAML is the
single hard runtime dependency; the `mcp` SDK is an optional `[mcp]` extra used
only by the MCP server. All tests are hermetic and offline.

Legend: **Shipped + tested** = working code with tests in `tests/`;
**Staged (not wired)** = source present in the tree but NOT imported by the
engine; **Roadmap** = not implemented.

## Engine status (`phantom_flow/`)

| Capability | Status | Notes |
| --- | --- | --- |
| YAML flow engine + 9 native blocks | Shipped + tested | `tools.http_get`, `tools.youtube_transcript`, `pipeline.regex_count`, `pipeline.filter`, `pipeline.if`, `pipeline.subprocess`, `pipeline.llm_summarize`, `actions.log_append`, `actions.stdout`, resolved via `BLOCK_REGISTRY`. Tests: `test_runner`, `test_filter_block`, `test_if_block`, `test_http_get_bounded`, `test_youtube_block`, `test_schema`, `test_timeout_bounded`. |
| `${...}` templating + all-errors schema validation | Shipped + tested | `--validate` / `--dry-run` / `--strict` / `--json` CLI modes. Tests: `test_schema`, `test_runner`, `test_examples`. |
| Structured run artifacts (`--record-out`) | Shipped + tested | Stable documented JSON schema. Tests: `test_run_artifact_contract`. |
| Local state / event store (`--state-dir`) | Shipped + tested | Documented schema. Tests: `test_approval_state_contract`. |
| Approval gating (`requires_approval`) | Shipped + tested | Blocked gates exit `3` and still record artifacts; released via `--approve <id|block|all>`. Tests: `test_approval_state_contract`, `test_scenario_command`. |
| LLM steps (`llm_driver`) | Shipped + tested | Route through phantom-mesh when a CLI backend is present; deterministic offline stub otherwise (`PHANTOM_FLOW_STUB_LLM=1`). Tests: `test_llm_driver`, `test_llm_block_wiring`. |
| Triggers: webhook listener (`serve`) + cron matcher (`schedule --once`) | Shipped + tested | Pure-stdlib. Tests: `test_webhook_listener`, `test_cron_schedule`. |
| `/activity` HTTP reporter | Shipped + tested | Publishes live node status to the mesh. Tests: `test_activity`. |
| MCP server (`mcp_server`) | Shipped + tested | Thin FastMCP wrapper exposing `flow_run` + `flow_list_blocks`; **adds no new engine behavior** — every tool wraps an already-tested runner function. Requires the `[mcp]` extra. Tests: `test_mcp_server`. |
| Docs-honesty guard | Shipped + tested | `test_docs_honest`, `test_open_source_contract`, `test_packaging`, `test_release_prep_contract` keep the docs/claims aligned with the engine. |

## Run the MCP server

```powershell
python -m pip install -e .[mcp]
python -m phantom_flow.mcp_server   # or the console script:
phantom-flow-mcp
```

Exposes `flow_run` and `flow_list_blocks` over JSON-RPC. Block contract:
[docs/BLOCK_CONTRACT.md](docs/BLOCK_CONTRACT.md).

## Staged, NOT wired into the engine

The `ai_automation_framework/` and `data_analysis/` subtrees are **staged source
only**. They are large reference/example corpora kept as future block-adapter
sources. They are **not imported by `phantom_flow`**, are not on the tested path,
and their presence does NOT mean those tools are usable native blocks today.
Treat any capability living only in those subtrees as unshipped.

## Honest limitations

- Only the 9 native blocks above are real engine capabilities; the breadth of
  the staged subtrees is not exposed through the runner.
- LLM output quality depends on the configured mesh CLI backend; the stub path
  exists for reproducible tests/demos, not for real content value.

## Roadmap (not yet shipped)

- `pipeline.generate` block (image / music / video / TTS via mesh MCP tools).
- Governed outbound-publish blocks routed through the phantom-mesh governor +
  flight-recorder + phone approval.
- A long-running cron daemon (today: `schedule --once`).
- Block adapters over the staged `ai_automation_framework/` and `data_analysis/`
  sources. See [ROADMAP.md](ROADMAP.md) and [DESIGN.md](DESIGN.md).
