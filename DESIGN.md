# phantom-flow — DESIGN（檢查 + 定位，更新 2026-06-17）

> A small **local-first YAML workflow runner** on top of phantom-mesh.
>
> ⚠️ 誠實標註：本引擎**目前不是** event-driven、也**不是** cluster-aware。那些是
> 路線圖目標（見 [`ROADMAP.md`](ROADMAP.md)），不是已實作功能。早期文件把它們
> 當成既有差異化在吹，已在此修正。

## 1. 真實結構
- **引擎本體 `phantom_flow/`（~750 行，near-stdlib，唯一硬依賴 PyYAML）**：
  `runner.py`（YAML loader + `${...}` 變數替換 + block registry + schema 驗證 +
  run-record + CLI）、`llm_driver.py`（phantom `exec` 包裝 + stub fallback）、`__init__`。
- **`ai_automation_framework/` + `data_analysis/` = subtree-merge 進來的來源 repo**，
  **引擎不 import**（見 §4）。

## 2. 核心功能 + 入口
`runner.py` 跑 YAML flow。現有 9 個 native blocks：
`tools.http_get`（支援 `file://`）、`tools.youtube_transcript`、
`pipeline.regex_count / filter / if / llm_summarize / subprocess`、
`actions.log_append / stdout`。
CLI 旗標：`--dry-run`、`--strict`（registry lint）、`--validate`（schema）、`--json`。
flows/：`jobseek-daily.yaml`、`youtube-summarize.yaml`、`example-webhook.yaml`
（declaration-only，無 HTTP listener）、`examples/`（兩個全離線可跑的範例）。

## 3. 與 phantom 協同
- 🟢 **已修**：`llm_driver.PhantomLLM` 改走 `phantom exec`（真正的 provider-trait
  介面）。subprocess boundary 已 harden：bounded timeout、stderr capture、binary
  缺失/timeout/OSError 一律 degrade 成 stub 並把原因記在 `LLMResult.error`。
- 🔴 **未來**（ROADMAP）：block 經 `phantom dispatch` 路由到指定 node（cluster-aware）
  尚未實作。

## 4. 🔭 未來整合（決策 2026-06-02：保留 10 萬行，當 staged 工具源，不砍）
`ai_automation_framework` + `data_analysis` **目前未被引擎 import**，但**不是死重量**——它們是「30+ 工具」的來源庫，計畫**包成 phantom 可調用的 flow block / MCP tool**：

| 來源 | 內容 | 整合成 |
|---|---|---|
| `ai_automation_framework/` | 17+ 自動化工具（email / web scraping / API / 排程 / DevOps）+ RAG | runner block `uses: automation.<tool>`（import/shell 該模組）|
| `data_analysis/` | 聚類(K-Means/DBSCAN/GMM)、RFM/CLV、Streamlit dashboard | runner block `uses: analysis.<algo>` |

**整合方式**：每個工具寫一層薄 adapter block（讀 flow `with:` 參數 → 呼對應模組 → 回結果進 ctx），逐步把常用的先接（不需一次全包）。也可經 mcp_bridge 露成 MCP tool 給 Claude Desktop。

**誠實標註**（已落實於 README）：不要吹「30+ tools 已可用」。引擎目前是 **9 個
native blocks**；vendored 是 staged 工具源、逐步整合中（每個工具要先寫一層 adapter
block 才算數）。

> 決策仍然有效：**保留** vendored subtrees（不砍），當未來整合的來源。因此本輪
> **未刪除** `ai_automation_framework/` / `data_analysis/`；改為把 README/DESIGN
> 的浮誇宣稱對齊到現實（P2-3）。

## 5. 待辦狀態
- 🟢 `llm_driver` → `phantom exec`（已接通；缺 CLI 時 stub fallback）。
- 🟢 引擎測試（hermetic pytest suite：runner / llm_driver / schema / examples / packaging）。
- 🟢 schema 驗證 + structured run records。
- 🟢 兩個全離線 example flows。
- 🟢 README/DESIGN 對齊現實 + 新增 [`ROADMAP.md`](ROADMAP.md)。
- 🟡 逐步把 vendored 工具包成 block（未來整合，按需求挑）。
- 🔴 cluster-aware dispatch block（**未實作**；ROADMAP 目標，先前被誤標為已完成）。

## 6. 風險
- vendored 10 萬行的 **license / scrub**（開源前掃；含他人程式碼要確認授權相容 Apache-2.0）。
- 不整合就一直是肥肉 → 整合要有實際 flow 需求驅動，別為包而包。
