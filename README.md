# phantom-flow

[![CI](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)

> A small, **local-first YAML workflow runner**. You write a flow as a YAML
> file — a trigger plus a pipeline of named blocks — and the runner executes
> (or `--dry-run` plans) it. It can optionally route an LLM step through the
> [phantom-mesh](https://github.com/markl-a/phantom-mesh) `phantom` CLI, and
> falls back to a deterministic stub when that CLI is absent.

This README describes **what the engine actually does today** and how to use it.
For project status — what is shipped, in progress, or planned (cluster dispatch,
event triggers, a visual editor, a marketplace, …) — see
[`ROADMAP.md`](ROADMAP.md), the single source of truth. For a map of all docs,
see [`docs/INDEX.md`](docs/INDEX.md).

## What it is (and isn't)

- **Is:** ~750 lines of near-stdlib Python (`phantom_flow/`) — a YAML flow
  loader, a `${...}` variable substitutor, a small pluggable block registry,
  schema validation, structured run records, and a CLI.
- **Is not (yet):** cluster-aware, event-driven, a visual editor, an n8n
  replacement, or anything with 600+ integrations. The only hard dependency
  is PyYAML.

## Install

```bash
git clone https://github.com/markl-a/phantom-flow
cd phantom-flow
pip install -r requirements.txt        # just PyYAML
# optional: pip install -e ".[youtube]" # adds youtube_transcript_api
```

## Quickstart

```bash
# Lint a flow: validate its schema + check every block name, no network/LLM.
python -m phantom_flow.runner flows/jobseek-daily.yaml --dry-run --strict --validate

# Run a fully-offline example end to end (file:// fetch + stub LLM):
PHANTOM_FLOW_SAMPLE="file:///$(pwd)/flows/samples/ai-jobs-sample.txt" \
PHANTOM_FLOW_STUB_LLM=1 \
  python -m phantom_flow.runner flows/examples/local-text-summary.yaml --json
```

`PHANTOM_FLOW_STUB_LLM=1` forces the deterministic stub LLM, so runs are
hermetic. Without it (and with a `phantom` CLI on PATH) the `llm_summarize`
block routes the prompt through `phantom exec`.

## Flow shape

```yaml
name: my-flow
version: 1
trigger:
  type: cron        # cron | webhook | event | manual  (only the shape is
  schedule: "0 9 * * *"   #   validated; cron/manual are what you run by hand)
pipeline:
  - id: fetch
    block: tools.http_get
    url: "https://example.com"        # or file:// for offline runs
  - id: count
    block: pipeline.regex_count
    input: "${fetch.body}"
    pattern: "AI"
  - id: gate
    block: pipeline.if
    condition: "${count.value} > 0"
  - id: summary
    block: pipeline.llm_summarize
    input: "${fetch.body}"
outbound:
  - block: actions.stdout
    when: "${gate.true}"              # optional gate
    line: "hits=${count.value} summary=${summary.summary}"
```

`${...}` resolves `step.field`, `date.today`, `date.now`, and `env.X`.

### Built-in blocks (9)

| Block | What it does |
|-------|--------------|
| `tools.http_get` | GET a URL (`http(s)://` or `file://`); returns status/body/body_len |
| `tools.youtube_transcript` | Fetch a transcript (optional dep; cached-sample fallback) |
| `pipeline.regex_count` | Count regex matches in text |
| `pipeline.filter` | Keep keywords present in text |
| `pipeline.if` | `>` / `<` / `==` condition → `{true,false}` |
| `pipeline.llm_summarize` | Summarise via phantom LLM driver (stub fallback) |
| `pipeline.subprocess` | Run a command (bounded timeout, captured stdout/stderr) |
| `actions.log_append` | Append a line to a file |
| `actions.stdout` | Print a line |

Add your own by registering a `fn(spec, ctx) -> dict` in
`phantom_flow.runner.BLOCK_REGISTRY`.

## Bundled flows

- `flows/examples/local-text-summary.yaml`, `flows/examples/keyword-report.yaml`
  — **fully offline**, run end to end with the stub LLM (tested in CI).
- `flows/jobseek-daily.yaml` — a real cron-shaped flow that scrapes a public
  jobs page; needs the network to run for real (dry-run/lint is offline).
- `flows/youtube-summarize.yaml` — transcript → summary; needs the optional
  `youtube` extra (or uses the bundled cached transcript).
- `flows/example-webhook.yaml` — a webhook-triggered flow; run
  `python -m phantom_flow.runner serve flows/example-webhook.yaml` to start the
  stdlib HTTP listener, then POST to its `trigger.url`.

## Tests

Hermetic and offline — no network, no real LLM (stub via
`PHANTOM_FLOW_STUB_LLM=1`), no writes outside `tmp_path`.

```bash
python -m pytest -ra -q
```

## The vendored subtrees

`ai_automation_framework/` and `data_analysis/` are two subtree-merged sister
repos. **They are NOT imported by the engine** and are not part of its
dependency surface or installable package. They are kept as a *staged source*
of tools to wrap into blocks incrementally (see [`DESIGN.md`](DESIGN.md) §4 and
[`ROADMAP.md`](ROADMAP.md)). Treat "30+ tools" as a *future* integration goal,
not a shipped capability — today the engine ships the 9 native blocks above.

## License

Apache-2.0. © 2026 Mark Lai ([markl-a](https://github.com/markl-a)). The two
subtree-merged repos are MIT (`ai_automation_framework/LICENSE`,
`data_analysis/LICENSE`), compatible with Apache-2.0.
