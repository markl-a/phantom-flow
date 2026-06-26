# State And Approval Contract

`phantom-flow` supports a local approval gate and a local state/log store for
manual source-checkout runs. This is the P2 public interface for controlled
side effects and run history.

## Approval Gate

Any pipeline step or outbound action may opt into an explicit approval gate:

```yaml
pipeline:
  - id: risky
    block: pipeline.subprocess
    requires_approval: true
    risk_reason: would execute a local command
    cmd: ["python", "-c", "print('approved')"]
```

Run without approval:

```powershell
python -m phantom_flow.runner .\flows\my-flow.yaml --validate
```

The runner exits `3`, does not execute the gated step/action, and records a
`blocked` step when `--record-out` or `--state-dir` is provided.

Run with approval:

```powershell
python -m phantom_flow.runner .\flows\my-flow.yaml --validate --approve risky
```

`--approve` accepts a step/action id, a block name, or `all`. Dry-run still does
not execute any blocks, but marks gated steps in the plan with
`[requires approval]`.

## State Store

Use `--state-dir` to write local state and event artifacts:

```powershell
python -m phantom_flow.runner .\flows\my-flow.yaml `
  --validate `
  --approve risky `
  --run-id demo-run-001 `
  --state-dir .\artifacts\state
```

The state store writes:

- `runs/<run-id>/state.json`: run-level state, plan, approvals, and record.
- `runs/<run-id>/events.jsonl`: one JSON line per recorded step/action.
- `runs.jsonl`: append-only run index.

## State Schema

`state.json` uses schema version 1:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-26T12:00:00",
  "run_id": "demo-run-001",
  "flow": {
    "name": "local-text-summary",
    "file": "local-text-summary.yaml"
  },
  "dry_run": false,
  "approvals": ["risky"],
  "record": {
    "run_id": "demo-run-001",
    "name": "local-text-summary",
    "version": 1,
    "trigger_type": "manual",
    "dry_run": false,
    "status": "ok",
    "started_at": "2026-06-26T12:00:00",
    "finished_at": "2026-06-26T12:00:01",
    "steps": [
      {
        "id": "risky",
        "block": "pipeline.subprocess",
        "status": "ok",
        "error": null
      }
    ]
  },
  "plan": ["pipeline.risky -> pipeline.subprocess [requires approval]"],
  "error": null
}
```

## Privacy Boundary

State artifacts intentionally omit execution `context`. They record run status,
step/action status, failure reason, approval ids, and plan text only. Successful
outbound actions are recorded in the same event stream as pipeline steps. This
keeps fetched bodies, prompts, subprocess output, future secret-bearing values,
and large block outputs out of the public state/log contract.

## Compatibility

- `schema_version` is the compatibility key for state parsers.
- Exit code `3` means an approval-gated step/action was blocked before
  execution.
- Existing fields in schema version 1 must keep their meaning until a new
  schema version is introduced.
