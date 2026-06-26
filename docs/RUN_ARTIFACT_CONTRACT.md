# Run Artifact Contract

`phantom-flow` can write a stable local run artifact with `--record-out`.
This is the P2 public interface for run history, step status, and failure
reason capture.

## Command

```powershell
$sample = (Resolve-Path .\flows\samples\ai-jobs-sample.txt).Path.Replace("\", "/")
$env:PHANTOM_FLOW_SAMPLE = "file:///$sample"
$env:PHANTOM_FLOW_STUB_LLM = "1"
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --json --record-out .\artifacts\local-text-summary.run.json
```

For lint-only support, combine it with dry-run and strict validation:

```powershell
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --dry-run --strict --record-out .\artifacts\local-text-summary.plan.json
```

## Schema

The artifact is JSON:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-26T12:00:00",
  "flow": {
    "name": "local-text-summary",
    "file": "local-text-summary.yaml"
  },
  "dry_run": false,
  "record": {
    "run_id": "run-20260626T120000-1234",
    "name": "local-text-summary",
    "version": 1,
    "trigger_type": "manual",
    "dry_run": false,
    "status": "ok",
    "started_at": "2026-06-26T12:00:00",
    "finished_at": "2026-06-26T12:00:01",
    "steps": [
      {
        "id": "fetch",
        "block": "tools.http_get",
        "status": "ok",
        "error": null
      }
    ]
  },
  "plan": [
    "trigger: manual (-)",
    "pipeline.fetch -> tools.http_get"
  ],
  "error": null
}
```

## Error Behavior

If a block raises during execution, `phantom-flow` exits 1 and still writes the
artifact when `--record-out` is provided. The `record.status` becomes `error`,
the failed step has `status: "error"`, and `error` contains the surfaced
failure message after secret-like values such as tokens, API keys, passwords,
and Bearer credentials are redacted.

Schema validation failures happen before a run record exists and currently do
not write a run artifact.

## Privacy Boundary

The artifact intentionally omits the execution `context`. Block outputs may
contain fetched page bodies, prompts, subprocess output, file paths, or future
secret-bearing values. Public support tooling should use this artifact for run
status and failure triage, not as a full data export.

## Compatibility

- `schema_version` is the compatibility key for parsers.
- New optional top-level fields may be added in later versions.
- Existing fields in schema version 1 must keep their meaning until a new
  schema version is introduced.
