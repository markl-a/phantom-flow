# phantom-flow ROADMAP

This file is the current status guard for `phantom-flow`. The shipped product is a small local-first YAML workflow runner; anything below that is marked as future work until it is implemented and covered by tests.

## Shipped

- Local-first YAML flow loading and `${...}` substitution.
- 9 native blocks: `tools.http_get`, `tools.youtube_transcript`, `pipeline.regex_count`, `pipeline.filter`, `pipeline.if`, `pipeline.llm_summarize`, `pipeline.subprocess`, `actions.log_append`, and `actions.stdout`.
- CLI validation / dry-run / JSON output paths.
- LLM summary block through `phantom exec` with deterministic stub fallback.
- Bounded subprocess and HTTP read boundaries.
- HTTP webhook listener for `trigger.type=webhook`.
- Cron one-shot scheduler for externally managed scheduling.
- Offline example flows and hermetic pytest coverage.

## In Progress

- Cron daemon loop. The one-shot scheduler exists; the long-running sleep loop is not implemented.
- Wrapping staged source trees into flow blocks. `ai_automation_framework/` and `data_analysis/` are kept as sources for future adapters, not as shipped native blocks.

## Planned / Not Implemented

These items are roadmap goals. They are aspirational until code and tests land.

- Event trigger support beyond validation shape, such as `trigger.type=event`.
- Cluster-aware dispatch to route heavy work to a selected mesh node.
- Cross-device execution claims beyond normal Python portability testing.
- Visual flow editor.
- Marketplace and premium templates.
- More outbound actions such as email, Slack, Discord, GitHub, and Calendar.

## Principle

A capability only moves to shipped after it is implemented and covered by tests. Until then, docs must describe it as not implemented or aspirational.

See [docs/phantom-flow.md](docs/phantom-flow.md) for usage and [DESIGN.md](DESIGN.md) for the design boundary.
