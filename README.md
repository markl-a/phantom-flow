# phantom-flow

[![CI](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml)

> **Self-hosted + cluster-aware + AI-native + cross-device workflow engine** on
> top of [phantom-mesh](https://github.com/markl-a/phantom-mesh) — n8n / Zapier
> 的本地化替代品,招聘對齊 鴻海 C3 / Modal / 中型 AI 新創,副業 NT$199-499/月
> 自架 Pro tier。

![status: alpha · Tier 1](https://img.shields.io/badge/status-alpha%20%C2%B7%20Tier%201-orange)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

## 30-second demo

[`docs/demo.cast`](docs/demo.cast) — asciinema recording of `phantom_flow.runner flows/jobseek-daily.yaml --dry-run` parsing a cron-triggered 6-step pipeline.

```sh
# play in a terminal (requires asciinema)
asciinema play docs/demo.cast

# or view the captured text without any tooling:
cat docs/demo.cast | jq -r '.[] | select(.[1]=="o") | .[2]'
```

Self-hosted on purpose — no upload to asciinema.org, no third-party tracking.

## 一句話 niche

n8n / Zapier / Make 都是 cloud-first + 不會 cluster dispatch;Temporal 是
重量級 JVM;Apple Shortcuts 是 Apple-only;LangChain 不是 event-driven。
**phantom-flow 是第一個 self-hosted + cluster-aware + AI-native + cross-device**
workflow engine — 同一份 YAML 可以 dispatch 到你的 GPU 機、always-on Pi、或
手機,Rust+Python 原生 + 100% local-first。

| Competitor          | Their edge                  | Why phantom-flow exists                            |
|---------------------|-----------------------------|----------------------------------------------------|
| **n8n**             | 600+ integrations, visual   | Needs Node.js; not cluster-aware; not AI-native    |
| **Zapier**          | 7,000+ apps                 | SaaS only — phantom is on-prem / local-first       |
| **Make**            | Polished visual editor      | Not cluster-aware; cannot dispatch to a GPU node   |
| **Temporal.io**     | Enterprise-grade workflow   | Heavy JVM; phantom-flow is lightweight Rust+Python |
| **LangChain**       | LLM chaining                | Not event-driven; phantom-flow is                  |
| **Apple Shortcuts** | Simple                      | Apple-only; phantom-flow runs on 5 OSes            |

## Status (2026-05-22)

- ✅ **Tier 1 shipped**:
  - `phantom_flow/runner.py` — YAML flow executor (n8n-style) with
    `--dry-run` planner
  - `phantom_flow/llm_driver.py` — swaps LangChain LLM → phantom event
    capture for one code path
  - `flows/jobseek-daily.yaml` — **real daily-running flow** (cron 09:00)
  - `flows/example-webhook.yaml` — declaration-only spec demo
  - 兩個既有 repo subtree-merged: `ai_automation_framework/` (17+ automation
    tools, RAG, agent framework, persistent memory) + `data_analysis/`
    (Streamlit app, K-Means/DBSCAN/RFM/CLV, its own pytest suite, multi-LLM cost
    routing)
- 🟡 **Tier 2 next**: 全面 LLM provider 改走 phantom-mesh provider trait
  (現在只 1 條 code path);memory backend SQLite/Redis → phantom FTS5;
  3+ 個真實 flow(現只 1 個 jobseek-daily)。
- 🟡 **Tier 3 (M2-M3, ~2026-07)**: visual flow editor、marketplace templates、
  健康 + 學習 flow。

## 30-second quickstart

```bash
git clone https://github.com/markl-a/phantom-flow
cd phantom-flow

# 跑 jobseek-daily flow 的 dry-run(印 trigger + pipeline + outbound,不碰
# 網路 / 檔案)
python -m phantom_flow.runner flows/jobseek-daily.yaml --dry-run

# 跑真實版(需 merged subtree code + Python deps)
python -m phantom_flow.runner flows/jobseek-daily.yaml
```

## Architecture (within phantom-mesh ecosystem)

phantom-flow 是 **P2 分身連線 + P3 進化網** 的執行層:把 phantom-mesh 的
event capture / FTS5 memory / provider trait 串成可重複的 workflow,並用
cluster-aware dispatch 把重負載送到對的 mesh 節點。

```
YAML flow (flows/*.yaml)
   ↓
phantom_flow.runner  (n8n-style executor + dry-run planner)
   ↓
phantom_flow.llm_driver  →  phantom-mesh provider trait
   ↓                         (Claude / Gemini / local / Modal spill)
trigger (cron / webhook / event)
   ↓
dispatch decision  →  Mac M-series  |  GPU node  |  always-on Pi  |  phone
   ↓
phantom event capture  →  FTS5 memory  →  phantom-companion ⑦ 觀察
```

Pillars served: **P2** (分身連線 — workflow 跨裝置 dispatch)、**P3** (進化網
— 每次 flow 執行回寫 FTS5,讓 ⑦ companion 學模式)、**P1** (跨平台 — 5 OSes)。

## Target users (recruiter / co-builder angle)

- **Recruiters (招聘)**: 鴻海 C3 AI Service / Modal / Together / 中型 AI
  新創。Workflow engine 經驗在 2026 是 high-signal: 證明能做 distributed
  systems + DAG scheduler + LLM cost routing + 真實 production cron。Rust +
  Python 雙語、AI-native 是 differentiator。
- **副業 angle (NT$ 199-499 / 月 Pro tier)**: n8n self-hosted 市場已被驗
  證,中文圈 + AI-native + 跨裝置這個位置目前是空的。+ Hahow 課程「自架
  phantom-flow 取代 Zapier」+ premium template marketplace。
- **人生 (life)**: 直接吃 C4 (注意力切換)、C5 (求職 + 副業)、C7 (個人
  財務)、C8 (家人健康) — 重複的事 automate 掉。
- **Co-builders**: 想要 self-hosted + AI-native 工作流的 indie hacker /
  homelab 玩家;跨裝置 dispatch 是其他 OSS 沒有的差異化。

## Roadmap (per master plan)

- 詳細設計: [`docs/06-phantom-flow.md`](docs/)
- 七專案總圖: [phantom-mesh planning tree](https://github.com/markl-a/phantom-mesh)

3-bullet:

1. **M2** — 全面 provider trait、FTS5 memory backend、3+ flows、visual editor MVP。
2. **M3** — marketplace、premium templates、健康 + 學習 flow。
3. **Post-M3** — NT$199-499/月 Pro tier 公開上線、Hahow 課程。

## Sibling scaffold (do not confuse)

`~/Documents/GitHub/hailmary/phantom-flow/` 是更早的 launchd heartbeat
(每日 ping),保留不動。本 repo 是 M1 W2-4 substantial merge 的所在地。

## License

Apache-2.0. © 2026 Mark Lai ([markl-a](https://github.com/markl-a)). 兩個
subtree-merged repo 原始為 MIT (`ai_automation_framework/LICENSE`,
`data_analysis/LICENSE`),與 Apache-2.0 相容。
