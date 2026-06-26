# Local Automation Scenario

This P3 scenario proves the public value of `phantom-flow` as a local-first
automation fabric:

1. validate and plan a workflow without side effects;
2. block a side-effecting local write until explicit approval;
3. run the same workflow after approval;
4. write stable run, state, event, and summary artifacts.

The scenario is fully offline. It uses the bundled
`flows/samples/ai-jobs-sample.txt` fixture and forces the deterministic stub LLM.

## Command

```powershell
python -m phantom_flow.runner scenario `
  .\flows\examples\local-automation-scenario.yaml `
  --out-dir .\artifacts\local-automation-scenario
```

The command sets these values for the scenario run:

- `PHANTOM_FLOW_SAMPLE`: `file://` URL for the bundled sample fixture.
- `PHANTOM_FLOW_STUB_LLM`: `1`.
- `PHANTOM_FLOW_SCENARIO_LOG`: local path for the approved report write.

## Output Bundle

The output directory contains:

- `plan.json`: dry-run artifact with the strict plan and no executed steps.
- `blocked.json`: execution artifact for the unapproved run; expected exit code
  inside the summary is `3` and `record.status` is `blocked`.
- `approved.json`: execution artifact for the approved run; expected
  `record.status` is `ok`.
- `state/`: local state store with `state.json`, `events.jsonl`, and
  `runs.jsonl` entries for each phase.
- `scenario.log`: the approved side-effect artifact written by
  `actions.log_append`.
- `stdout.log`: stdout emitted by the scenario flow's `actions.stdout` step.
- `scenario-summary.json`: bundle-level summary with phase exit codes and
  record statuses.

## Approval Contract

The bundled scenario flow has one approval-gated outbound action:

```yaml
outbound:
  - id: write_report
    block: actions.log_append
    requires_approval: true
```

The scenario command first runs without approvals and expects the action to be
blocked before the file write. It then reruns with the discovered approval id
(`write_report`) and expects the local report write to succeed.

## Privacy Boundary

The run and state artifacts intentionally omit execution `context`. They record
metadata, plan text, approvals, step/action status, and redacted failure
messages only. The fetched fixture body, prompt text, LLM output body, and
future secret-bearing block outputs must not be written into `plan.json`,
`blocked.json`, `approved.json`, or `state/*.json`.

## Compatibility

- `scenario-summary.json` uses `schema_version: 1`.
- The command exits `0` only when plan is `ok`, blocked run exits `3`, and
  approved run is `ok`.
- Scenario flows must include at least one `requires_approval` gate.
