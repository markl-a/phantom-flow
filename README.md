# phantom-flow

[![CI](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml)

> A **minimal local-first workflow runner** (n8n-style, ~500 LOC). Define a
> flow in YAML, run it from the CLI. No daemon, no cloud, no Node.js.

![status: alpha](https://img.shields.io/badge/status-alpha-orange)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)

## What it actually is

`phantom_flow/runner.py` reads a YAML flow and executes a linear pipeline of
named blocks, with `${...}` variable substitution between steps. It runs
in-process when you invoke it; there is no scheduler, no HTTP listener, and no
cross-machine dispatch — those would be your OS cron / a reverse proxy / your
own glue. The whole engine is ~500 lines of Python (`wc -l phantom_flow/*.py`).

The optional LLM block (`pipeline.llm_summarize`) shells out to a `phantom`
CLI via `phantom_flow/llm_driver.py`; when that CLI is not installed it falls
back to a deterministic stub so dry-runs and tests still pass.

### Blocks in `BLOCK_REGISTRY`

| Block                      | What it does                                            |
|----------------------------|--------------------------------------------------------|
| `tools.http_get`           | HTTP GET a URL (capped bytes, custom UA, timeout)       |
| `tools.youtube_transcript` | Fetch a YouTube transcript, with a cached-file fallback |
| `pipeline.regex_count`     | Count regex matches in text                             |
| `pipeline.filter`          | Keyword filter; reports matches + a `passes` boolean    |
| `pipeline.if`              | Tiny `<`, `>`, `==` gate → `{true, false}`              |
| `pipeline.llm_summarize`   | Summarize text via the LLM driver (stub if no CLI)      |
| `pipeline.subprocess`      | Escape hatch: run an external command                   |
| `actions.log_append`       | Append a line to a log file                             |
| `actions.stdout`           | Print a line to stdout                                  |

### Triggers

The flow YAML declares a `trigger` (`cron` / `webhook` / `event` / `manual`),
but the runner does **not** fire on triggers itself — it only records the
trigger in the plan. Actually scheduling a flow is up to you (e.g. an OS cron
entry that calls `python -m phantom_flow.runner ...`). `example-webhook.yaml`
is a declaration-only spec: there is no HTTP listener.

## Quickstart

```bash
git clone https://github.com/markl-a/phantom-flow
cd phantom-flow
pip install pyyaml

# Dry-run: parse + print trigger / pipeline / outbound plan. No network,
# no filesystem writes.
python -m phantom_flow.runner flows/jobseek-daily.yaml --dry-run

# Execute for real (does HTTP GET + log append; LLM step uses the stub
# unless a `phantom` CLI is on PATH).
python -m phantom_flow.runner flows/jobseek-daily.yaml
```

### A flow looks like this

```yaml
name: jobseek-daily
trigger:
  type: cron
  schedule: "0 9 * * *"        # recorded in the plan; the runner does not schedule
pipeline:
  - id: scrape
    block: tools.http_get
    url: "https://example.com/jobs"
  - id: gate
    block: pipeline.if
    condition: "${scrape.status} == 200"
outbound:
  - block: actions.stdout
    when: "${gate.true}"          # optional gate
    line: "scraped ${scrape.body_len} bytes"
```

## Tests

```bash
pip install pyyaml pytest
pytest -q
```

`tests/test_runner.py` covers `load_flow`, the dry-run planner, `${...}`
placeholder resolution, the `filter` / `regex_count` / `if` blocks, and the
stub-LLM path. CI runs the same `pytest` on every push / PR.

## Relationship to phantom-mesh

The LLM driver can optionally route completions through the
[phantom-mesh](https://github.com/markl-a/phantom-mesh) `phantom` CLI
(`phantom exec`). That is the only integration point; phantom-flow does not
depend on phantom-mesh at import time and runs fully standalone.

## License

Apache-2.0. © 2026 Mark Lai ([markl-a](https://github.com/markl-a)).
