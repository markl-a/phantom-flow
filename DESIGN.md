# phantom-flow DESIGN

`phantom-flow` is currently a compact local-first YAML runner. Its production engine lives in `phantom_flow/` and uses a small registry of native blocks to load a flow, resolve context substitutions, execute steps, and return a structured run record.

## Current Boundary

- The engine is local-first and near-stdlib, with PyYAML as the hard runtime dependency.
- `llm_summarize` can call `phantom exec` and degrades to a deterministic stub when the CLI path is unavailable.
- `trigger.type=webhook` is implemented through a stdlib HTTP listener.
- The cron path is a one-shot matcher/runner, intended to be called by an external scheduler today.

## Explicit Non-Goals Today

Event-driven mesh execution, cluster-aware dispatch, a visual editor, and a marketplace are roadmap items. They are not implemented in the current engine.

## Staged Sources

`ai_automation_framework/` and `data_analysis/` are staged source trees. They are kept as future integration material, but they are not imported by the engine and should not be counted as shipped native blocks.

Each useful tool from those trees needs a thin adapter block before it becomes part of the flow runtime. That adapter should take `with:` input, call the underlying module or command, and return structured data into the flow context.

## Roadmap Link

The implementation status lives in [ROADMAP.md](ROADMAP.md). Any future cluster-aware, event-driven, marketplace, or editor work should move through that roadmap first, then graduate to this design file only after implementation and tests exist.
