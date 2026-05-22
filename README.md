# phantom-flow

> **Event-driven, cluster-aware workflow engine on top of [phantom-mesh](https://github.com/markl-a/phantom-mesh).**
> Self-hosted n8n / Zapier — Rust+Python native, AI-native, cross-device, 100% local-first.

**Status:** `alpha` (M1 W2-4, 2026-05-22)
Full spec: [`docs/projects/06-phantom-flow.md`](https://github.com/markl-a/phantom-mesh) in the phantom-mesh planning tree.

---

## Why this repo exists

This is one of the **14-point three-way wins** in the phantom-mesh roadmap
(招聘 / 副業 / 人生 simultaneously):

- **招聘**: positions me for AI Service / Modal / Together / 鴻海 C3 AI Service roles —
  workflow-engine experience is high-signal.
- **副業**: n8n self-hosted market is validated; NT$ 199-499/mo Pro tier + Hahow
  course + premium templates are realistic paths.
- **人生**: covers C4 (attention switching), C5 (job seek + side gigs), C7
  (personal finance), C8 (parents' health) — automates the repetitive things.

It is the **single highest-priority project** in the 7-project lineup because
the two source repos below already self-identify as "phantom-mesh ecosystem
layers", which makes the merge cost the lowest of all 7.

---

## Niche vs incumbents

| Competitor          | Their edge                  | Why phantom-flow exists                            |
|---------------------|-----------------------------|----------------------------------------------------|
| **n8n**             | 600+ integrations, visual   | Needs Node.js; not cluster-aware; not AI-native    |
| **Zapier**          | 7,000+ apps                 | SaaS only — phantom is on-prem / local-first       |
| **Make**            | Polished visual editor      | Not cluster-aware; cannot dispatch to a GPU node   |
| **Temporal.io**     | Enterprise-grade workflow   | Heavy JVM; phantom-flow is lightweight Rust+Python |
| **LangChain**       | LLM chaining                | Not event-driven; phantom-flow is                  |
| **Apple Shortcuts** | Simple                      | Apple-only; phantom-flow runs on 5 OSes            |

**Unique position:** the first **self-hosted + cluster-aware + AI-native +
cross-device** workflow engine. Same YAML can be dispatched to your GPU box,
your always-on Pi, or your phone.

---

## What is in this repo today (alpha)

```
phantom-flow/
├── README.md
├── LICENSE                              # Apache-2.0
├── .gitignore
├── phantom_flow/                        # the wrapper layer (NEW, this repo)
│   ├── __init__.py
│   ├── runner.py                        # YAML flow executor (n8n-style)
│   └── llm_driver.py                    # swaps LangChain LLM → phantom event capture
├── flows/
│   ├── jobseek-daily.yaml               # REAL daily-running flow (cron 09:00)
│   └── example-webhook.yaml             # declaration-only spec demo
├── ai_automation_framework/             # SUBTREE-MERGED from Automation_with_Agent
│   ├── core/, tools/, rag/, agents/, workflows/, llm/, integrations/, plugins/
│   └── (17+ automation tools, RAG, agent framework, persistent memory)
├── data_analysis/                       # SUBTREE-MERGED from Data-Analysis-with-Agents
│   ├── app.py (Streamlit), kaggle_solutions/, notebooks/, models/, examples/
│   └── (K-Means/DBSCAN/RFM/CLV, 377 pytest, multi-LLM cost routing)
└── docs/
    └── 2026-05-22-tier1-initial-dev.md  # what landed + what's deferred
```

> The existing scaffold at `~/Documents/GitHub/hailmary/phantom-flow/` is
> **not** this repo — it carries a launchd cron that ships a daily heartbeat
> and stays untouched. This top-level repo is where the M1 W2-4 substantial
> merge lives.

---

## Run the one real flow (dry-run)

```bash
python -m phantom_flow.runner flows/jobseek-daily.yaml --dry-run
```

Prints the trigger, the pipeline plan, and the outbound actions without
touching the network or filesystem. Drop `--dry-run` to actually execute
(needs the merged subtree code + Python deps).

---

## Roadmap (the things this Tier 1 dev does NOT yet do)

- **Full LLM driver swap**: currently `phantom_flow/llm_driver.py` wraps
  `phantom event capture` for one code path. The LangChain call sites inside
  `ai_automation_framework/` are still LangChain-direct — spec wants
  them all routed through the phantom provider trait.
- **Memory backend swap**: spec says SQLite/Redis → phantom FTS5. Not done.
- **Visual flow editor**: deferred to M2+.
- **Marketplace templates**: deferred to M2+.
- **3+ real flows**: 1 today (`jobseek-daily.yaml`). Health + study flows still TODO.

---

## License

Apache-2.0. The two subtree-merged repos arrive under their original MIT
license (`ai_automation_framework/LICENSE`, `data_analysis/LICENSE`). Both
licenses are compatible.
