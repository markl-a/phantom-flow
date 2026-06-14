# phantom-flow — DESIGN（檢查 + 定位，2026-06-02；2026-06-14 更新）

> minimal local-first YAML workflow runner（~500 行，n8n 風格）。**不是**
> cluster-aware / event-driven / cross-device——那些只是下方第 4 節的未來計畫。

> **2026-06-14 更新**：`ai_automation_framework/`（~6 萬行）+ `data_analysis/`
> （~4 萬行）兩個 vendored 子樹**已從 repo 移除**——引擎從未 import 它們。下方
> 第 4 節「未來整合」的內容因此純屬計畫;真要用再從原始 repo re-vendor。

## 1. 真實結構
- **引擎本體 `phantom_flow/`（~500 行）**：`runner.py`（YAML flow runner + blocks）、`llm_driver.py`（phantom LLM 包裝）、`__init__`。

## 2. 核心功能 + 入口
`runner.py` 跑 YAML flow，現有 blocks：`http_get / regex_count / filter / llm_summarize / if / subprocess`。flows/：`example-webhook.yaml`、`jobseek-daily.yaml`。

## 3. 與 phantom 協同
- 🔴 **待修**：`llm_driver.PhantomLLM` 現呼叫 `phantom event capture --kind llm.complete --json -`（推測式介面，phantom CLI 實際不吃 → 永遠 fallback stub）。**改走 `phantom exec`**（真正的 provider-trait 介面，跟 ai-feed/secure-connector 同一做法）。
- 未來 block 可 `phantom dispatch` 路由到指定 node（cluster-aware）。

## 4. 🔭 未來整合（決策 2026-06-02：保留 10 萬行，當 staged 工具源，不砍）
`ai_automation_framework` + `data_analysis` **目前未被引擎 import**，但**不是死重量**——它們是「30+ 工具」的來源庫，計畫**包成 phantom 可調用的 flow block / MCP tool**：

| 來源 | 內容 | 整合成 |
|---|---|---|
| `ai_automation_framework/` | 17+ 自動化工具（email / web scraping / API / 排程 / DevOps）+ RAG | runner block `uses: automation.<tool>`（import/shell 該模組）|
| `data_analysis/` | 聚類(K-Means/DBSCAN/GMM)、RFM/CLV、Streamlit dashboard | runner block `uses: analysis.<algo>` |

**整合方式**：每個工具寫一層薄 adapter block（讀 flow `with:` 參數 → 呼對應模組 → 回結果進 ctx），逐步把常用的先接（不需一次全包）。也可經 mcp_bridge 露成 MCP tool 給 Claude Desktop。

**誠實標註**：README 現吹「merge gives 30+ tools」要改成「**vendored；逐步整合中，目前引擎用 6 個 native blocks**」——別讓人以為 30+ 工具已可用。

## 5. 待辦
- 🔴 `llm_driver` → `phantom exec`（接通 LLM，現永遠 stub）。
- 🔴 引擎**零測試** → 補 runner / llm_driver 測試。
- 🟡 逐步把 vendored 工具包成 block（未來整合，按需求挑）。
- 🟡 README 對齊（vendored / 整合中，別吹未整合的工具數）。
- 🟢 cluster-aware dispatch block（spec 目標）。

## 6. 風險
- vendored 10 萬行的 **license / scrub**（開源前掃；含他人程式碼要確認授權相容 Apache-2.0）。
- 不整合就一直是肥肉 → 整合要有實際 flow 需求驅動，別為包而包。
