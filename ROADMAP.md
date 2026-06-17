# phantom-flow — ROADMAP

This file exists to keep the README and DESIGN **honest**: everything below is
**aspirational / not implemented yet**. The shipped engine is the small
local-first YAML runner described in [`README.md`](README.md). Earlier docs
claimed several of these as if they existed; they are future work.

## Status legend

- 🔴 not started
- 🟡 partial / prototype
- 🟢 shipped (moves out of this file into the README)

## Shipped today (for contrast)

- 🟢 YAML flow loader + `${...}` substitution
- 🟢 9 native blocks (http_get incl. `file://`, youtube_transcript,
  regex_count, filter, if, llm_summarize, subprocess, log_append, stdout)
- 🟢 `--dry-run`, `--strict` (registry lint), `--validate` (schema)
- 🟢 schema validation (`validate_flow`) + structured run records (`RunRecord`)
- 🟢 LLM driver via `phantom exec` with a deterministic stub fallback
- 🟢 hardened subprocess boundary (bounded timeout, stderr capture, fallbacks)
- 🟢 two fully-offline example flows, hermetic pytest suite, CI

## Future work (claimed elsewhere, NOT built)

### Triggers & execution
- 🔴 **HTTP webhook listener** — `flows/example-webhook.yaml` declares the
  shape, but there is no server. Only `cron`/`manual` flows run by hand today;
  `cron`/`webhook`/`event` are validated as *shapes* only.
- 🔴 **Real cron scheduler** — flows declare a `schedule`; an external
  scheduler (launchd / systemd / phantom-mesh) must invoke the runner.
- 🔴 **Event-driven triggers** — reacting to phantom-mesh events.

### Distribution
- 🔴 **Cluster-aware dispatch** — sending a heavy block/flow to a specific
  mesh node (GPU box / always-on Pi / phone). The README previously claimed
  "cluster-aware" as a differentiator; it is not implemented.
- 🔴 **Cross-device / 5-OS execution** — the runner is plain Python and should
  run anywhere Python does, but this is untested and unclaimed beyond that.

### Integrations & tooling
- 🟡 **Wrap the vendored subtrees into blocks** — `ai_automation_framework/`
  (automation tools, RAG) and `data_analysis/` (clustering, RFM/CLV) are kept
  as a staged source (DESIGN.md §4). "30+ tools" is a *goal*, not a shipped
  count; the engine has 9 native blocks. Each tool needs a thin
  `fn(spec, ctx)` adapter block before it counts.
- 🔴 **phantom FTS5 memory backend** — wire run records / context into
  phantom-mesh's memory.
- 🔴 **Visual flow editor** — n8n-style. Not started.
- 🔴 **Marketplace / premium templates** — not started.
- 🔴 **More outbound actions** — email / Slack / Discord / GitHub / Calendar.
  Today: `log_append`, `stdout`.

## Principle

A capability only graduates to the README once it is implemented **and**
covered by a test. Until then it lives here.
