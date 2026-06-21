> ARCHIVED 2026-06-19 — frozen historical snapshot; current status lives in [/ROADMAP.md](../../ROADMAP.md).

# phantom-flow Tier 1 initial dev — 2026-05-22

> One of the **14-point three-way wins**; M1 W2-4 in the master plan. Highest
> priority of the 7 projects because two source repos already self-identify
> as "phantom-mesh ecosystem layers", so the merge cost is the lowest.

## What got merged in

Both source repos were subtree-merged with `--squash` so this repo carries a
single squashed commit per upstream instead of the full history:

| Subtree prefix              | Source                                                  | Entry points |
|-----------------------------|---------------------------------------------------------|--------------|
| `ai_automation_framework/`  | `https://github.com/markl-a/Automation_with_Agent` @ main | `ai_automation_framework/` (nested: `core/`, `tools/` 17+ files, `rag/`, `agents/`, `workflows/`, `llm/`, `integrations/`, `plugins/`), `demo.py`, `test_all_features.py`, `test_di_basic.py`, `test_import_compatibility.py`, `test_metrics.py`, `test_pydantic_integration.py`, `Makefile`, `pyproject.toml` |
| `data_analysis/`            | `https://github.com/markl-a/Data-Analysis-with-Agents` @ main | `app.py` (Streamlit dashboard), `kaggle_solutions/`, `notebooks/`, `models/`, `examples/` (27 entries), `config/`, `data/`, `ARCHITECTURE.md`, `AI_ASSISTANCE_GUIDE.md`, `CASE_STUDIES.md`, `KAGGLE_COMPETITIONS_SUGGESTIONS.md` |

Git log:

```
887a6ff Merge commit '...' as 'data_analysis'
1857766 Squashed 'data_analysis/' content from commit 49a4471
a668264 Merge commit '...' as 'ai_automation_framework'
b277a02 Squashed 'ai_automation_framework/' content from commit c8ebdf8
f7f36c2 init: README + LICENSE + .gitignore for top-level phantom-flow repo
```

Future re-merges:

```bash
git subtree pull --prefix=ai_automation_framework \
  https://github.com/markl-a/Automation_with_Agent.git main --squash
git subtree pull --prefix=data_analysis \
  https://github.com/markl-a/Data-Analysis-with-Agents.git main --squash
```

## What this Tier 1 dev produced (on top of the merge)

- `phantom_flow/__init__.py` — package marker (5 LOC).
- `phantom_flow/llm_driver.py` — first step of the LangChain → phantom
  provider trait swap. `PhantomLLM.complete()` shells into
  `phantom event capture --kind llm.complete` and degrades to a stub when
  the CLI is missing (~95 LOC).
- `phantom_flow/runner.py` — minimal n8n-style YAML executor (~290 LOC):
  trigger (cron / webhook / event / manual declarative), 6 pipeline blocks
  (`tools.http_get`, `pipeline.regex_count`, `pipeline.filter`,
  `pipeline.llm_summarize`, `pipeline.if`, `pipeline.subprocess`), 2
  outbound actions (`actions.log_append`, `actions.stdout`), `${...}` var
  substitution with `step.field` / `date.today` / `date.now` / `env.X`.
- `flows/jobseek-daily.yaml` — REAL flow that runs the 09:00 cron 104.com.tw
  scan, filters AI keywords, asks the phantom LLM driver to summarise,
  appends to `~/.phantom-mesh/logs/phantom-flow/<YYYY-MM-DD>.log`.
- `flows/example-webhook.yaml` — declaration-only spec demo (the executor
  does not yet listen on HTTP).
- `README.md`, `LICENSE` (Apache-2.0), `.gitignore`.

## Smoke test (passing on this commit)

```
$ python -m phantom_flow.runner flows/jobseek-daily.yaml --dry-run
phantom-flow runner :: jobseek-daily.yaml
  name    = jobseek-daily
  version = 1
  mode    = DRY RUN
  llm_cli = ~/.cargo/bin/phantom
--- plan ---
  trigger: cron (0 9 * * *)
  pipeline.scrape_104 -> tools.http_get
  pipeline.filter_ai_only -> pipeline.filter
  pipeline.count_hits -> pipeline.regex_count
  pipeline.gate -> pipeline.if
  pipeline.llm_summarize -> pipeline.llm_summarize
  outbound -> actions.log_append  [gated by ${gate.true}]
  outbound -> actions.stdout
```

An end-to-end in-process test (filter → regex_count → if-gate → log_append)
also passes — exercises var substitution + gating without network or LLM.

## What is still to do (deferred from Tier 1)

- **Full LLM driver swap inside the merged subtree.** Right now
  `phantom_flow/llm_driver.py` is the only path that routes through phantom.
  Every `from langchain...` call site under
  `ai_automation_framework/llm/` and `ai_automation_framework/agents/` still
  hits LangChain directly. Spec requires sweeping all of them onto the
  provider trait.
- **Memory backend swap to phantom FTS5.** Source repos use SQLite + Redis;
  spec wants phantom's FTS5 client. Not started.
- **3+ real flows.** Today: 1 (`jobseek-daily.yaml`). Spec calls for at
  least 3 (求職 + 學習 + 健康). Health pipeline and study-paper pipeline
  are still TODO.
- **Visual flow editor.** Deferred to M2+.
- **Marketplace templates.** Deferred to M2+.
- **HTTP webhook listener.** `example-webhook.yaml` declares the shape but
  the runner cannot listen yet — needs phantom-mesh HTTP-surface wiring.
- **`phantom flow define <yaml>` CLI.** Spec asks for this verb; Tier 1
  ships `python -m phantom_flow.runner <yaml>` instead. Wrapping it into
  the phantom CLI proper is M1 W3.
- **5 trigger types × 5 outbound actions.** Spec target. Today: 4 declared
  trigger types but only cron/manual actually fire; 2 outbound actions
  implemented out of the 5 minimum.

## Real flow count today vs spec

- Spec wants: **3+ real flows** (求職 / 學習 / 健康).
- Tier 1 ships: **1** (`jobseek-daily.yaml`).
- Gap: 2 flows + their backing tools (paper-fetch RSS block; phantom secure
  sleep-data ingestion block).

## Biggest single gap to actually replace n8n

The 600+ integration count. Even with 17 tools merged in from
`ai_automation_framework/tools/`, we are two orders of magnitude short and
none of them are yet exposed as drop-in `block:` names in `BLOCK_REGISTRY`.
The shortest path is to auto-generate registry shims from the merged tool
modules, not to hand-port them — that's the M2 unlock.
