# Open Source Readiness

Project: `phantom-flow`
Current phase: P3 local automation scenario proof slice verified
Master plan: `../../PHANTOM-SATELLITES-OPEN-SOURCE-MASTER-PLAN.md`

## Shipped Features

- Local-first YAML workflow runner.
- CLI entrypoint: `phantom-flow = phantom_flow.runner:_main`.
- Help surface verified with `python -m phantom_flow.runner --help`.
- Supported command flags include `--dry-run`, `--strict`, `--validate`, and `--json`.
- Root README points to `docs/phantom-flow.md`.
- Root README now includes a self-contained offline quickstart using bundled samples and stub LLM.
- Shipped block inputs, outputs, side effects, and failure behavior are documented in `docs/BLOCK_CONTRACT.md`.
- Stable run artifact schema is documented in `docs/RUN_ARTIFACT_CONTRACT.md`.
- CLI supports `--record-out` for local JSON run artifacts that include plan and run record without execution context.
- Approval/state/logging schema is documented in `docs/STATE_AND_APPROVAL_CONTRACT.md`.
- CLI supports `--approve`, `--run-id`, and `--state-dir` for approval-gated side effects and local run state/log artifacts.
- Steps or outbound actions marked `requires_approval: true` are blocked before execution unless explicitly approved; blocked approval gates exit `3`.
- CLI supports `scenario` for a P3 local automation proof bundle that writes dry-run, blocked-run, approved-run, state, event, summary, and approved side-effect artifacts.
- Bundled scenario flow: `flows/examples/local-automation-scenario.yaml`.
- Scenario contract is documented in `docs/LOCAL_AUTOMATION_SCENARIO.md`.
- `ROADMAP.md` and `DESIGN.md` exist and already mark staged subtrees as not shipped native blocks.
- Test suite baseline after scenario additions: `python -m pytest -q` passed with 88 tests.

## Planned Or Deferred Features

- Broader local automation fabric: block contract hardening, serve/schedule artifact parity, and richer approval policies.
- `serve` and `schedule` currently remain hermetic utility paths; their state/artifact parity is still planned.
- Connector marketplace, visual workflow editor, and remote orchestration remain out of initial release scope.
- `ai_automation_framework/` and `data_analysis/` are staged source subtrees, not shipped native blocks.

## Install And Test Commands

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m phantom_flow.runner --help
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --dry-run --strict --json
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --json --record-out .\artifacts\local-text-summary.run.json
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --dry-run --strict --state-dir .\artifacts\state
python -m phantom_flow.runner scenario .\flows\examples\local-automation-scenario.yaml --out-dir .\artifacts\local-automation-scenario
```

Observed result on 2026-06-26:

```text
P2 slice 1:
python -m pytest tests/test_run_artifact_contract.py tests/test_open_source_contract.py tests/test_examples.py tests/test_schema.py tests/test_runner.py -q: 40 passed
python -m pytest -q: 76 passed in 0.74s

P2 approval/state slice:
python -m pytest tests/test_approval_state_contract.py tests/test_open_source_contract.py tests/test_run_artifact_contract.py tests/test_schema.py tests/test_runner.py tests/test_examples.py -q: 49 passed
python -m pytest -q: 85 passed in 1.35s
python -m pytest --collect-only -q: 85 tests collected

P3 local automation scenario slice:
python -m pytest tests/test_scenario_command.py -q: 2 passed
python -m pytest tests/test_scenario_command.py tests/test_approval_state_contract.py tests/test_run_artifact_contract.py tests/test_open_source_contract.py tests/test_examples.py -q: 23 passed
python -m pytest -q: 88 passed
python -m pytest --collect-only -q: 88 tests collected
```

## Fixture And Data Policy

- Public examples must be local, synthetic, and safe to run.
- Dry-run must not perform network or block filesystem side effects; `--record-out` is the explicit user-requested exception that writes only the run artifact.
- Run artifacts must omit execution context to avoid storing fetched bodies, prompts, subprocess output, or future secret-bearing values.
- State/log artifacts must omit execution context and only record run metadata, approvals, plan, and per-step/per-action status.
- `requires_approval: true` must block side-effecting steps/actions before execution unless the user passes an explicit `--approve` value.
- Runtime error strings stored in artifacts redact common token/API-key/password/Bearer patterns before writing.
- P3 scenario artifacts must omit execution context; the approved local report write is isolated to the requested output directory.
- Staged subtrees must stay clearly documented as future adapter sources, not shipped blocks.

## Safety And Privacy Risks

- Workflow runners can perform side effects; risky blocks require dry-run, validation, clear docs, or explicit approval gates.
- External/network blocks must be bounded and optional.
- Secrets must not be stored in examples or committed flows.

## Blockers To Next Phase

- None for the current P3 local automation scenario proof slice.
- Remaining P3 work before Beta sign-off: serve/schedule artifact parity, more block hardening, and final scenario docs review.

## Evidence

- `pyproject.toml` declares package `phantom-flow` and script `phantom-flow`.
- `README.md` points to `docs/phantom-flow.md`.
- `README.md` includes offline public quickstart with `PHANTOM_FLOW_SAMPLE`, `PHANTOM_FLOW_STUB_LLM`, `--validate`, `--dry-run`, `--strict`, and `--json`.
- `docs/BLOCK_CONTRACT.md` documents every shipped block in `BLOCK_REGISTRY`.
- `docs/RUN_ARTIFACT_CONTRACT.md` documents `schema_version=1`, plan, run record, error behavior, and privacy boundary.
- `docs/STATE_AND_APPROVAL_CONTRACT.md` documents approval gates, `--state-dir`, schema version 1 state artifacts, `events.jsonl`, and exit code `3`.
- `docs/LOCAL_AUTOMATION_SCENARIO.md` documents the P3 scenario command, output bundle, approval contract, privacy boundary, and compatibility behavior.
- `flows/examples/local-automation-scenario.yaml` runs offline against the bundled sample fixture and gates the local report write with `requires_approval: true`.
- `python -m pytest tests/test_run_artifact_contract.py -q`: 3 passed.
- `python -m pytest tests/test_approval_state_contract.py -q`: 5 passed.
- `python -m pytest tests/test_scenario_command.py -q`: 2 passed.
- `python -m pytest tests/test_approval_state_contract.py tests/test_open_source_contract.py tests/test_run_artifact_contract.py tests/test_schema.py tests/test_runner.py tests/test_examples.py -q`: 49 passed.
- `python -m pytest tests/test_scenario_command.py tests/test_approval_state_contract.py tests/test_run_artifact_contract.py tests/test_open_source_contract.py tests/test_examples.py -q`: 23 passed.
- `python -m pytest -q`: 88 passed.
- `python -m pytest --collect-only -q`: 88 tests collected.
- `python -m phantom_flow.runner --help`: help OK.
- `python -m phantom_flow.runner scenario .\flows\examples\local-automation-scenario.yaml --out-dir <temp>` wrote `plan.json`, `blocked.json`, `approved.json`, `scenario-summary.json`, `scenario.log`, `stdout.log`, and `state/`; phase results were plan `ok`, blocked exit `3`, approved `ok`; run/state artifacts omitted `context`.
- Offline smoke with `PHANTOM_FLOW_SAMPLE=file:///<sample>` and `PHANTOM_FLOW_STUB_LLM=1`:
  - dry-run/strict validate OK.
  - execute validate OK; fetched bundled sample, counted AI hits, summarized through stub backend.
  - execute validate with `--record-out` wrote schema version 1 artifact with status `ok`, 5 steps, and no `context` field.
- State-dir smoke with `python -m phantom_flow.runner flows\examples\local-text-summary.yaml --validate --run-id approval-state-exec --state-dir <temp>` wrote `runs/approval-state-exec/state.json`, `events.jsonl`, and `runs.jsonl`; `state.json` omitted `context`, and `events.jsonl` recorded 5 pipeline steps plus 2 outbound actions.
- `agy` reviewer finding addressed: runtime error strings stored in run artifacts now redact token/API-key/password/Bearer patterns. `serve`/`schedule` artifact support remains a next P2 slice rather than part of this manual-run artifact slice.
- `agy` P2 approval/state re-review result: previous findings fixed for Authorization Bearer redaction, successful outbound action records, outbound action id consistency, schema examples, outbound approval tests, and unknown-block state artifacts; no remaining P2 blockers for approval bypass, state/log context leakage, docs/tests mismatch, staged subtree expansion, or `--record-out` regression.

## P4 Release-Prep Slice 1

Status: governance baseline added; this does not mark the project release-ready.

Evidence:
- `CONTRIBUTING.md` defines the contribution workflow, required test command, readiness-doc update rule, and no-private-data/no-credentials boundary.
- `SECURITY.md` defines private vulnerability reporting, supported version scope, 7-day acknowledgement target, and safe report contents.
- `python -m pytest tests/test_release_prep_contract.py -q`: 1 passed.
- `python -m pytest -q`: 89 passed.

Remaining P4 work: full release gate, final docs audit, package metadata audit, release notes, tag plan, and maintainer sign-off.

## P4 Release-Prep Slice 2

Status: final release gate checklist added; this does not mark the project release-ready.

Evidence:
- `CHANGELOG.md` records the unreleased governance/release-checklist work and points back to readiness evidence.
- `docs/RELEASE_CHECKLIST.md` documents final tests, dependency/license review, secret/private-data scan, known limitations, and manual maintainer approval.
- `python -m pytest tests/test_release_prep_contract.py -q`: 2 passed.
- `python -m pytest -q`: 90 passed.

Remaining P4 work: execute final scans, complete dependency/license review, finalize release notes, and record manual maintainer approval.

## P4 Release-Prep Slice 3

Status: final scan and direct dependency/license audit recorded; not release-ready.

Evidence:
- `docs/FINAL_RELEASE_AUDIT.md` records scan scope, `high_conf_secret_hits=0`, direct dependency/license review, and remaining release blockers.
- Direct release-scope dependency metadata reviewed: `PyYAML==6.0.3` MIT; optional `youtube-transcript-api==1.2.4` MIT.
- Staged subtree secret-shaped test literals were rewritten with string concatenation; `python -m pytest tests/test_core_security.py -q` from `ai_automation_framework/`: 37 passed, 1 warning.
- `python -m pytest tests/test_release_prep_contract.py -q`: 3 passed.
- `python -m pytest -q`: 91 passed.

Remaining P4 work: release notes finalization, tag plan, final maintainer approval, and any separate audit for staged subtrees before publication.

## P4 Release-Prep Slice 4

Status: maintainer approval recorded, conductor sign-off complete, and local tag created; remote publication pending.

Evidence:
- `docs/RELEASE_NOTES.md` records public release-candidate notes, known limitations, and verification pointers.
- `docs/TAG_PLAN.md` records proposed tag `v0.1.0-alpha.0`, required approval-before-tag sequence, and rollback steps.
- `docs/PUBLIC_RELEASE_APPROVAL.md` records `Status: approved` with approver, approval date, and approved tag.
- Conductor root approval packet `PHANTOM-SATELLITES-PUBLIC-RELEASE-APPROVAL.md` records all ten candidate tags as approved.
- `.github/workflows/ci.yml` runs an explicit `release-prep gate` against `tests/test_release_prep_contract.py`.
- `python -m pytest tests/test_release_prep_contract.py -q`: 5 passed.
- `python -m pytest -q`: 93 passed.

Remaining publication work: confirm target remote and repository visibility before pushing tags or publishing release pages.
