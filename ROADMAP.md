# phantom-flow — ROADMAP

> ⭐ **This file is the single source of truth for project status.** The README
> is the front door (positioning + quickstart); it does not carry its own status
> lists — it points here. Everything below is grounded in real merged commits and
> the as-built engine, not aspiration. A capability only appears under **Shipped**
> once it is implemented **and** covered by a test.
>
> _Last updated: 2026-06-19._

## Status legend

- 🟢 **Shipped** — implemented and test-covered on `main`.
- 🟡 **In progress** — partial / prototype / staged source not yet wired.
- 🔴 **Planned-next** — designed or claimed elsewhere, not built.

## Shipped

The shipped engine is a small, local-first YAML workflow runner
(`phantom_flow/`, ~750+ lines, near-stdlib, only hard dependency PyYAML).

- 🟢 **YAML flow loader + `${...}` substitution** — resolves `step.field`,
  `date.today`, `date.now`, `env.X`.
- 🟢 **9 native blocks** — `tools.http_get` (incl. `file://`),
  `tools.youtube_transcript`, `pipeline.regex_count`, `pipeline.filter`,
  `pipeline.if`, `pipeline.llm_summarize`, `pipeline.subprocess`,
  `actions.log_append`, `actions.stdout`.
- 🟢 **CLI flags** — `--dry-run`, `--strict` (registry lint), `--validate`
  (schema), `--json`.
- 🟢 **Schema validation** (`validate_flow`) + **structured run records**
  (`RunRecord`). _(commit `1b4c9b8`)_
- 🟢 **LLM driver via `phantom exec`** with a deterministic stub fallback;
  `force_stub` / `timeout` / `model_hint` are wired into the production
  `llm_summarize` path and the degrade reason is surfaced.
  _(commits `8b481c2`, `a042870`)_
- 🟢 **Hardened subprocess boundary** — bounded timeout, stderr capture,
  fallbacks; `http_get` `max_bytes` null/0 coerced to a bounded default.
  _(commits `5af105f`, `2284eea`, `c2602a4`)_
- 🟢 **HTTP webhook listener** — `phantom-flow serve <flow>` starts a stdlib
  `http.server` listener; a POST to the flow's `trigger.url` seeds
  `ctx["event"]` and drives the existing `run_flow`. Turns
  `trigger.type=webhook` from declaration-only into real POST-triggered runs.
  stdlib-only (no fastapi/uvicorn). _(commits `f9de0d5`, `b9f3315`)_
- 🟢 **Cron scheduler (one-shot, hermetic)** — `schedule_matches(expr, dt)` is a
  pure-stdlib 5-field cron matcher (`*`, lists, ranges, `*/n`; no croniter).
  `phantom-flow schedule <flow> --once [--now ISO]` runs the flow when the
  schedule is due, prints "not due" otherwise. Time is injectable via `--now`
  (no real clock needed). _(commits `ad4c12d`, `7975a36`)_
- 🟢 **Bundled offline example flows** — `flows/examples/local-text-summary.yaml`
  and `flows/examples/keyword-report.yaml` run end to end with the stub LLM.
  _(commit `654e464`)_
- 🟢 **Hermetic pytest suite + CI** — runner / llm_driver / schema / examples /
  packaging; no network, no real LLM, no writes outside `tmp_path`.
  GitHub Actions workflow (`.github/workflows/ci.yml`). _(commits `2f131b3`,
  `20cebee`)_

## In progress

- 🟡 **Cron scheduler daemon loop** — the `--once` matcher is shipped, but the
  long-running sleep-loop daemon is honestly deferred (the `schedule`
  subcommand prints "daemon loop is not implemented"). An external scheduler
  (launchd / systemd / phantom-mesh) invokes the one-shot runner today.
- 🟡 **Wrap the vendored subtrees into blocks** — `ai_automation_framework/`
  (automation tools, RAG) and `data_analysis/` (clustering, RFM/CLV) are kept
  as a *staged source* (see [`../DESIGN.md`](DESIGN.md) §4). "30+ tools" is a
  *goal*, not a shipped count; the engine has 9 native blocks. Each tool needs
  a thin `fn(spec, ctx)` adapter block before it counts.

## Planned-next (claimed elsewhere, NOT built)

### Triggers & execution
- 🔴 **Event-driven triggers** — reacting to phantom-mesh events
  (`trigger.type=event` validates as a shape only).

### Distribution
- 🔴 **Cluster-aware dispatch** — sending a heavy block/flow to a specific mesh
  node (GPU box / always-on Pi / phone). Early docs claimed "cluster-aware" as a
  differentiator; it is not implemented.
- 🔴 **Cross-device / 5-OS execution** — the runner is plain Python and should
  run anywhere Python does, but this is untested and unclaimed beyond that.

### Integrations & tooling
- 🔴 **phantom FTS5 memory backend** — wire run records / context into
  phantom-mesh's memory.
- 🔴 **Visual flow editor** — n8n-style. Not started.
- 🔴 **Marketplace / premium templates** — not started.
- 🔴 **More outbound actions** — email / Slack / Discord / GitHub / Calendar.
  Today: `log_append`, `stdout`.

## Principle

A capability only graduates from **Planned-next** to **Shipped** once it is
implemented **and** covered by a test. Until then it lives lower in this file.
