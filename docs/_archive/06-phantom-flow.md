> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-flow.md;此為歷史版本。

# ⑥ phantom-flow

> ⚠️ **這是原始「願景 / spec」文件，不是 as-built 描述。** 下文許多功能
> （event-driven、cluster-aware、視覺化編輯器、30+ 工具、5 OS、webhook listener）
> 為**未實作的目標**。引擎現況請看 [`../README.md`](../README.md)；目標 vs 現實的
> 誠實對照看 [`../ROADMAP.md`](../ROADMAP.md)。

> **（願景）Event-driven 跨服務工作流引擎,跑在 phantom-mesh 上,直接 merge 自 Automation_with_Agent + Data-Analysis-with-Agents**
> 招聘 + 副業 + 應用三贏的項目,改裝資產最完整

## 一句話定位

「phantom-mesh 上的 n8n / Zapier — 把 phantom 的 trigger / RAG / skill / tool 組成 pipeline,自動對外執行(email / Slack / GitHub / Calendar / 任何 API)。」

## 對齊 BIG-GOAL

- **P1 跨裝置 mesh**:flow 可以指定在哪個 node 跑(GPU node / always-on node / mobile node)
- **P2 多模態**:trigger 可以是 multimodal event(食物照片 → 卡路里 calculator)
- **P3 進化網**:flow 跑成功的 sequence 自動萃取成 skill

## 現有資產(改裝來源)

### Automation_with_Agent(v0.5.0,已存在)
**README**:「Phantom Mesh 生態系統的應用自動化和 AIOps 層」

已有:
- 5 級學習路徑(level 1-5,從基礎到 AI 輔助開發)
- 完整 RAG 系統(含 HyDE + reranking)
- **17+ 自動化工具**:email、db、web scraping、排程、API、雲端、DevOps
- Agent framework + persistent memory(SQLite + Redis)
- 使用追蹤、回應快取、token 預算管理
- LangChain + Pydantic + Selenium/Playwright

### Data-Analysis-with-Agents(已存在)
**README**:「Phantom Mesh 生態系的資料科學與分析層」

已有:
- K-Means / DBSCAN / GMM / Hierarchical 聚類
- RFM / CLV 預測
- 2,019 個 Kaggle 解決方案
- Streamlit dashboard
- multi-LLM 路由 + cost tracking
- 377 個 pytest

→ **合併** = phantom-flow 起步就有 30+ 工具 + RAG + 聚類 + 資料分析 + dashboard 框架,**改裝成本是 7 個項目中最低**。

## 競品分析

| 競品 | 強項 | phantom-flow 差異 |
|---|---|---|
| **n8n self-hosted** | 600+ integrations,可視化 | phantom-flow 用 phantom-mesh Rust 跑,跨裝置 + AI-native + 不裝 Node.js |
| **Zapier** | 7000+ apps | SaaS,不能 on-prem;phantom 100% local |
| **Make (Integromat)** | 視覺化好 | 本專案為 cluster-aware,可 dispatch to specific node |
| **LangChain agents** | LLM 鏈 | 不是 event-driven workflow;phantom 是 |
| **Apple Shortcuts** | 簡單 | 只 Apple 生態,phantom 跨 5 OS |
| **Temporal.io** | 企業 workflow | 重量級 Java,phantom 為輕量 Rust |

**niche**:**第一個 self-hosted + cluster-aware + AI-native + cross-device workflow engine**。

## 核心功能

### Trigger types
- **時間**:cron / interval / 一次性
- **事件**:phantom-mesh event(skill 成功 / Hermes judge / 新檔案)
- **外部 webhook**:GitHub / Slack / 任何 HTTP POST
- **multimodal**:語音指令 / 拍照 / 螢幕截圖

### Pipeline blocks
- **RAG query**:從 phantom FTS5 抓資料
- **LLM call**:走 provider trait,自動選最便宜/最強
- **聚類分析**:reuse Data-Analysis 17 個算法
- **資料抓取**:reuse Automation 17 個工具(playwright / selenium / API)
- **判斷/路由**:if-else / 多分支
- **人工介入**:推 Telegram / mobile app 等回應

### Outbound actions
- email / SMS
- Slack / Discord / LINE
- GitHub commit / PR / issue
- Google Calendar / 任務管理
- 任何 HTTP API
- phantom-mesh dispatch to other node

## 真實使用情境

| 場景 | trigger | pipeline | action |
|---|---|---|---|
| 求職新機會 | feed 抓到職缺 | secure 確認符合 + LLM 寫 cover letter | email 推到 inbox |
| 學習推送 | feed 抓到新 paper | 摘要 + 判斷是否相關領域 | GitHub issue 排到下週讀 |
| 健康異常 | secure 偵測睡眠 3 天異常 | LLM 判斷 + 找 Calendar 空檔 | 發提醒 + 自動排運動 |
| 家人用藥 | 用藥日前一天 | LLM 草擬 message | LINE 推 + Sheet 紀錄 |
| LLM 成本 | mesh 偵測本月超 80% | 自動 throttle + 推 model 建議 | 通知 + 紀錄 |
| 接案 lead | 平台新案 | secure 評估值得做 | 自動草擬報價單 PDF |
| 自動記帳 | Email 來信用卡帳單 | LLM 解析 + 分類 | 寫進 Google Sheet |

## 招聘 / 副業 / 應用評分

| 維度 | 評分 | 對應 |
|---|---|---|
| **招聘** | ⭐⭐⭐⭐ | 鴻海 C3 AI Service / 中型 AI SaaS / Modal / Together |
| **副業** | ⭐⭐⭐⭐⭐ | **n8n self-hosted 級別市場**,訂閱模式 |
| **個人應用** | ⭐⭐⭐⭐⭐ | 自動化重複事(注意力 / 求職 / 財務 / 家人健康同時打) |

## MVP scope

### Must have(M1 W2-4)
- [ ] **Merge** Automation_with_Agent + Data-Analysis-with-Agents 進 phantom-flow repo
- [ ] 改 LLM driver 走 phantom-mesh provider trait(原本 LangChain → phantom client)
- [ ] 改 memory 走 phantom FTS5(原本 SQLite/Redis → phantom backend)
- [ ] 5 個 trigger types + 5 個 outbound actions
- [ ] CLI: `phantom flow define <yaml>` 跑 pipeline
- [ ] Web UI MVP(看 flow status + 觸發 history)
- [ ] 3 個 demo flow(求職 + 學習 + 健康各 1)

### Nice to have(M2+)
- [ ] 視覺化 flow editor(像 n8n)
- [ ] Marketplace:flow templates 用戶分享
- [ ] cross-cluster scheduling(dispatch to GPU node 跑重的)
- [ ] 串接 ④ secure-connector 的所有模組
- [ ] 串接 ⑦ companion 的行為分析回饋

### NOT doing
- 取代 Apache Airflow(本專案不做 data pipeline,做 individual workflow)
- 視覺 flow 編輯器一開始就要(先 YAML / TOML)
- 對外 SaaS(local-first 違反)

## 改裝計畫(具體 steps)

```bash
# 1. 建新 repo
git init phantom-flow

# 2. 從兩個 repo subtree merge
git subtree add --prefix=ai_automation_framework \
  https://github.com/markl-a/Automation_with_Agent main
git subtree add --prefix=data_analysis \
  https://github.com/markl-a/Data-Analysis-with-Agents main

# 3. 統一目錄結構
phantom-flow/
├── core/                  # 從 Automation_with_Agent.core 改
├── triggers/              # 新寫
├── pipeline/              # 從 Automation_with_Agent.workflows 改
├── tools/                 # 從 Automation_with_Agent.tools 改(17+)
├── analysis/              # 從 Data-Analysis-with-Agents 改(聚類 / RFM)
├── ui/                    # Streamlit + Next.js(從 Data-Analysis 改)
└── examples/              # 7 個典型 flow

# 4. 改 LLM driver
sed -i 's/from langchain/from phantom_mesh/g' core/llm_client.py
# (示意,實際要看程式碼結構)

# 5. 改 memory backend
# 從 SQLite/Redis → phantom FTS5 client

# 6. 寫 docker-compose 跑起來
```

## 風險

- **Merge 衝突**:兩個 repo code style 可能不一致,要有時間 polish
- **依賴衝突**:LangChain vs phantom 內 LLM client 可能 dependency hell
- **n8n 競爭**:n8n 已大紅,phantom-flow 的差異化(cluster-aware)需要清楚展示
- **scope creep**:n8n 600+ integrations 為 5 年累積,30 個就夠 demo

## 變現路徑

| 路徑 | 細節 |
|---|---|
| Pro tier SaaS | 多 user / 視覺編輯器 / advanced trigger,訂閱制 |
| 線上課程 | 「自架你的私人 Zapier」 |
| Marketplace template | premium flow templates 上架 |
| 顧問接案 | 中小公司客製 flow |

## 為什麼放 M1 W2-4(立即開始)

- **改裝資產最完整**(兩個 repo 已存在 + 已知它們自己定位是 phantom 生態系)
- **改裝路徑最清楚**:merge → 改 LLM driver → 改 memory → ship
- **應用情境覆蓋廣**(自動化覆蓋多個 daily 場景)
- **副業變現速度最快**(n8n 市場現成、訂閱模式驗證)
- **招聘信號中等但 niche 鮮明**
- **W4 末** 就可以開始投履歷時寫進去

---

*Sanitized public spec. Author: Mark Lai ([@markl-a](https://github.com/markl-a)).*
